import os
import sys
import warnings
import numpy as np
import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from scipy.optimize import minimize

# 1. Глушим ворнинги Python
warnings.filterwarnings("ignore")

# 2. Контекстный менеджер для очистки терминала от вывода NgSpice
class SuppressOutput:
    def __enter__(self):
        self.outnull = os.open(os.devnull, os.O_WRONLY)
        self.errnull = os.open(os.devnull, os.O_WRONLY)
        self.old_stdout = os.dup(sys.stdout.fileno())
        self.old_stderr = os.dup(sys.stderr.fileno())
        os.dup2(self.outnull, sys.stdout.fileno())
        os.dup2(self.errnull, sys.stderr.fileno())

    def __exit__(self, *_):
        os.dup2(self.old_stdout, sys.stdout.fileno())
        os.dup2(self.old_stderr, sys.stderr.fileno())
        os.close(self.old_stdout)
        os.close(self.old_stderr)
        os.close(self.outnull)
        os.close(self.errnull)

# 3. Функция подбора реальных номиналов (E24)
def get_closest_e24(value):
    if value <= 0: return 0
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
           3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    exponent = np.floor(np.log10(value))
    base = value / (10**exponent)
    closest_base = min(e24, key=lambda x: abs(x - base))
    return round(closest_base * (10**exponent), 4)

# 4. Основная функция симуляции
def simulate_filter(params, target_freq_khz=150, full_scan=False):
    l_val, c1_val, c2_val = params
    if l_val <= 0 or c1_val <= 0 or c2_val <= 0: return 0

    circuit = Circuit('EMC_Filter_Pro')
    circuit.SinusoidalVoltageSource('input', 'node_in', circuit.gnd, amplitude=1@u_V)
    circuit.R('source', 'node_in', 'n1', 50@u_Ohm)

    # Модель П-фильтра с паразитными параметрами
    # C1 + ESR/ESL
    circuit.C(1, 'n1', 'c1_int', c1_val@u_uF)
    circuit.R('c1_esr', 'c1_int', 'c1_esl_n', 10@u_mOhm)
    circuit.L('c1_esl', 'c1_esl_n', circuit.gnd, 2@u_nH)
    # L1 + DCR
    circuit.L(1, 'n1', 'l1_int', l_val@u_uH)
    circuit.R('l1_dcr', 'l1_int', 'n2', 50@u_mOhm)
    # C2 + ESR/ESL
    circuit.C(2, 'n2', 'c2_int', c2_val@u_uF)
    circuit.R('c2_esr', 'c2_int', 'c2_esl_n', 10@u_mOhm)
    circuit.L('c2_esl', 'c2_esl_n', circuit.gnd, 2@u_nH)

    circuit.R('load', 'n2', circuit.gnd, 50@u_Ohm)

    try:
        with SuppressOutput():
            simulator = circuit.simulator()
            if full_scan:
                # Сканирование диапазона для графика
                analysis = simulator.ac(start_frequency=10@u_kHz, stop_frequency=100@u_MHz, number_of_points=100, variation='dec')
                return analysis
            else:
                # Точечный замер для оптимизатора
                freq_hz = target_freq_khz * 1e3
                analysis = simulator.ac(start_frequency=freq_hz, stop_frequency=freq_hz, number_of_points=1, variation='lin')
                v_out = abs(complex(analysis.n2[0]))
                return 20 * np.log10(v_out + 1e-15)
    except:
        return 0

# 5. Настройки и оптимизация
TARGET_FREQ = 150 # kHz
TARGET_DB = -60

def objective(params):
    if any(p <= 0.1 for p in params): return 1e6
    gain = simulate_filter(params, TARGET_FREQ)
    return (gain - TARGET_DB)**2 if gain > TARGET_DB else 0

print(f"\n[1/3] Поиск оптимальных параметров (Цель: {TARGET_DB} dB)...")
res = minimize(objective, [10, 0.1, 0.1], method='Nelder-Mead', tol=1e-2)

if res.success:
    # 6. Подбор реальных деталей
    print("[2/3] Подбор компонентов из ряда E24...")
    ideal_params = res.x
    real_params = [get_closest_e24(p) for p in ideal_params]
    
    final_gain = simulate_filter(real_params, TARGET_FREQ)

    # 7. Вывод отчета
    print("\n" + "="*45)
    print(f"{'Компонент':<12} | {'Расчет':<10} | {'E24 (Реальный)':<12}")
    print("-" * 45)
    labels = ['L (uH)', 'C1 (uF)', 'C2 (uF)']
    for i in range(3):
        print(f"{labels[i]:<12} | {ideal_params[i]:10.3f} | {real_params[i]:12.3f}")
    print("-" * 45)
    print(f"Итоговое затухание: {final_gain:.2f} dB")
    print("="*45)

    # 8. Генерация финального графика
    print("[3/3] Построение АЧХ финального решения...")
    analysis = simulate_filter(real_params, full_scan=True)
    
    plt.figure(figsize=(10, 6))
    plt.semilogx(analysis.frequency, 20*np.log10(np.abs(analysis.n2)), label='Финальный фильтр (E24)', color='blue')
    plt.axhline(y=TARGET_DB, color='red', linestyle='--', label=f'Порог {TARGET_DB} dB')
    plt.axvline(x=TARGET_FREQ*1e3, color='green', linestyle=':', label=f'Частота помехи {TARGET_FREQ} kHz')
    
    plt.title("АЧХ оптимизированного EMC-фильтра")
    plt.xlabel("Частота (Гц)")
    plt.ylabel("Затухание (дБ)")
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.legend()
    plt.savefig('/workspace/final_emc_report.png')
    print("\n[ВЫПОЛНЕНО] Отчет сохранен в final_emc_report.png\n")

else:
    print("\n[ОШИБКА] Не удалось найти решение.")