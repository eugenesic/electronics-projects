import os
import sys
import warnings
import numpy as np
import matplotlib.pyplot as plt # Добавлено для графиков
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from scipy.optimize import minimize

# Отключаем лишние предупреждения
warnings.filterwarnings("ignore")

class SuppressOutput:
    """Контекстный менеджер для подавления вывода NgSpice в консоль"""
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

def get_closest_e24(value):
    """Округление до ближайшего номинала из стандартного ряда E24"""
    if value <= 0: return 0
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    exp = np.floor(np.log10(value))
    base = value / (10**exp)
    closest = min(e24, key=lambda x: abs(x - base))
    return round(closest * (10**exp), 4)

# --- Глобальные константы проектирования ---
TARGET_FREQ = 150        # Частота анализа (кГц)
TARGET_DB = -60          # Целевое затухание (дБ)
MAX_LEAKAGE_MA = 3.5     # Максимальный ток утечки (нормы безопасности)
LOAD_CURRENT_A = 10.0    # Рабочий ток нагрузки
DCR_OHM = 0.005          # Сопротивление обмоток дросселя (5 мОм)

def simulate_full_filter(params, mode='DM', frequencies=None):
    """
    params: [cx_uF, lcm_mH, cy_nF]
    Если frequencies задан (array), возвращает массив значений для графика.
    """
    cx, lcm, cy = params
    circuit = Circuit('EMC_Final_V5')
    
    if mode == 'DM':
        circuit.SinusoidalVoltageSource('input', 'n_in_p', 'n_in_n', amplitude=1@u_V)
        circuit.R('rs1', 'n_in_p', 'n1_p', 25@u_Ohm)
        circuit.R('rs2', 'n_in_n', 'n1_n', 25@u_Ohm)
    else: # Common Mode
        circuit.SinusoidalVoltageSource('input', 'n_common', circuit.gnd, amplitude=1@u_V)
        circuit.R('rs1', 'n_common', 'n1_p', 25@u_Ohm)
        circuit.R('rs2', 'n_common', 'n1_n', 25@u_Ohm)

    circuit.C('x1', 'n1_p', 'n1_n', cx@u_uF)
    circuit.L('cm1', 'n1_p', 'n2_p', lcm@u_mH)
    circuit.L('cm2', 'n1_n', 'n2_n', lcm@u_mH)
    circuit.K('k_core', 'Lcm1', 'Lcm2', 0.995)
    circuit.R('dcr1', 'n2_p', 'n3_p', DCR_OHM@u_Ohm)
    circuit.R('dcr2', 'n2_n', 'n3_n', DCR_OHM@u_Ohm)
    circuit.C('y1', 'n3_p', circuit.gnd, cy@u_nF)
    circuit.C('y2', 'n3_n', circuit.gnd, cy@u_nF)
    circuit.R('load', 'n3_p', 'n3_n', 50@u_Ohm)

    with SuppressOutput():
        sim = circuit.simulator()
        if frequencies is None:
            # Точечный расчет для оптимизатора
            f = TARGET_FREQ * 1e3
            res = sim.ac(start_frequency=f, stop_frequency=f, number_of_points=1, variation='lin')
            v_out = abs(complex(res.n3_p[0] - res.n3_n[0])) if mode == 'DM' else abs(complex(res.n3_p[0]))
            return 20 * np.log10(v_out + 1e-15)
        else:
            # Широкий диапазон для графика
            res = sim.ac(start_frequency=frequencies[0], stop_frequency=frequencies[-1], 
                         number_of_points=len(frequencies), variation='dec')
            if mode == 'DM':
                v_out = [abs(complex(p - n)) for p, n in zip(res.n3_p, res.n3_n)]
            else:
                v_out = [abs(complex(p)) for p in res.n3_p]
            return 20 * np.log10(np.array(v_out) + 1e-15)

def objective(params):
    cx_val, lcm_val, cy_val = params
    if any(p <= 0.001 for p in params): return 1e12
    leakage_ma = 230 * 2 * np.pi * 50 * (cy_val * 1e-9) * 1000
    if leakage_ma > MAX_LEAKAGE_MA:
        return 1e9 + (leakage_ma - MAX_LEAKAGE_MA) * 1000

    gain_dm = simulate_full_filter(params, mode='DM')
    gain_cm = simulate_full_filter(params, mode='CM')
    worst_case = max(gain_dm, gain_cm)
    
    penalty = 0
    if worst_case > TARGET_DB:
        penalty = 5e6 + (worst_case - TARGET_DB)**2 * 5000
    
    size_cost = (lcm_val * 1) + (cx_val * 1) + (cy_val * 1)
    return penalty + size_cost

# --- Основной цикл ---
print(f"\n[V5] СТАРТ: Комплексная оптимизация DM + CM фильтра...")
print(f"Цель: {TARGET_DB} dB на {TARGET_FREQ} кГц. Ток нагрузки: {LOAD_CURRENT_A} A")

initial_guess = [0.47, 5.0, 4.0] 
res = minimize(objective, initial_guess, method='Nelder-Mead', tol=1e-3)

if res.success:
    p = res.x
    real_p = [get_closest_e24(p[0]), get_closest_e24(p[1]), get_closest_e24(p[2])]
    
    # Финальные замеры
    final_dm = simulate_full_filter(real_p, mode='DM')
    final_cm = simulate_full_filter(real_p, mode='CM')
    p_loss = 2 * (LOAD_CURRENT_A**2 * DCR_OHM)

    print("\n" + "="*65)
    print(f"{'Компонент':<30} | {'Номинал E24':<15}")
    print("-" * 65)
    print(f"{'X-конденсатор (Cx)':<30} | {real_p[0]:>10.3f} uF")
    print(f"{'Синфазный дроссель (Lcm)':<30} | {real_p[1]:>10.3f} mH")
    print(f"{'Y-конденсаторы (Cy)':<30} | {real_p[2]:>10.3f} nF")
    print("-" * 65)
    print(f"Затухание DM (Дифференциальное): {final_dm:>8.2f} dB")
    print(f"Затухание CM (Синфазное):        {final_cm:>8.2f} dB")
    print(f"Статические потери мощности:     {p_loss:>8.2f} W")
    print("="*65)

    # --- Построение графиков ---
    print("\nГенерация графиков АЧХ...")
    f_axis = np.logspace(4, 7.5, 400) # Задаем желаемый диапазон
    
    # Важно: Нам нужно получить объект результата, чтобы вытащить оттуда частоты
    cx, lcm, cy = real_p
    circuit_dm = Circuit('Plot_DM')
    
    def get_plot_data(params, mode='DM'):
        cx, lcm, cy = params
        circuit = Circuit('EMC_Plot')
        if mode == 'DM':
            circuit.SinusoidalVoltageSource('input', 'n_in_p', 'n_in_n', amplitude=1@u_V)
            circuit.R('rs1', 'n_in_p', 'n1_p', 25@u_Ohm); circuit.R('rs2', 'n_in_n', 'n1_n', 25@u_Ohm)
        else:
            circuit.SinusoidalVoltageSource('input', 'n_common', circuit.gnd, amplitude=1@u_V)
            circuit.R('rs1', 'n_common', 'n1_p', 25@u_Ohm); circuit.R('rs2', 'n_common', 'n1_n', 25@u_Ohm)
        
        circuit.C('x1', 'n1_p', 'n1_n', cx@u_uF)
        circuit.L('cm1', 'n1_p', 'n2_p', lcm@u_mH); circuit.L('cm2', 'n1_n', 'n2_n', lcm@u_mH)
        circuit.K('k_core', 'Lcm1', 'Lcm2', 0.995)
        circuit.R('dcr1', 'n2_p', 'n3_p', DCR_OHM@u_Ohm); circuit.R('dcr2', 'n2_n', 'n3_n', DCR_OHM@u_Ohm)
        circuit.C('y1', 'n3_p', circuit.gnd, cy@u_nF); circuit.C('y2', 'n3_n', circuit.gnd, cy@u_nF)
        circuit.R('load', 'n3_p', 'n3_n', 50@u_Ohm)

        with SuppressOutput():
            sim = circuit.simulator()
            res = sim.ac(start_frequency=10@u_kHz, stop_frequency=30@u_MHz, number_of_points=100, variation='dec')
            freqs = np.array(res.frequency)
            v_out = [abs(complex(p - n)) for p, n in zip(res.n3_p, res.n3_n)] if mode == 'DM' else [abs(complex(p)) for p in res.n3_p]
            return freqs, 20 * np.log10(np.array(v_out) + 1e-15)

    freq_dm, db_dm = get_plot_data(real_p, mode='DM')
    freq_cm, db_cm = get_plot_data(real_p, mode='CM')

    plt.figure(figsize=(10, 6))
    plt.semilogx(freq_dm, db_dm, label='Differential Mode (DM)', color='blue', lw=2)
    plt.semilogx(freq_cm, db_cm, label='Common Mode (CM)', color='red', lw=2, linestyle='--')
    
    plt.axvline(x=TARGET_FREQ*1e3, color='green', linestyle=':', label=f'Target {TARGET_FREQ}kHz')
    plt.axhline(y=TARGET_DB, color='black', linestyle='-', alpha=0.3)
    
    plt.title(f'EMI Filter Performance\nCx={real_p[0]}uF, Lcm={real_p[1]}mH, Cy={real_p[2]}nF')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Attenuation (dB)')
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.legend()
    
    plt.savefig('emc_report.png', dpi=300)
    print("✅ График сохранен: emc_report.png")
    print("СТАТУС: ✅ Расчет завершен успешно\n")