import os
import sys
import warnings
import numpy as np
import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from scipy.optimize import minimize

# Отключаем мусор в консоли
warnings.filterwarnings("ignore")

class SuppressOutput:
    def __enter__(self):
        self.outnull = os.open(os.devnull, os.O_WRONLY); self.errnull = os.open(os.devnull, os.O_WRONLY)
        self.old_stdout = os.dup(sys.stdout.fileno()); self.old_stderr = os.dup(sys.stderr.fileno())
        os.dup2(self.outnull, sys.stdout.fileno()); os.dup2(self.errnull, sys.stderr.fileno())
    def __exit__(self, *_):
        os.dup2(self.old_stdout, sys.stdout.fileno()); os.dup2(self.old_stderr, sys.stderr.fileno())
        os.close(self.old_stdout); os.close(self.old_stderr); os.close(self.outnull); os.close(self.errnull)

def get_closest_e24(value):
    if value <= 0: return 0
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    exp = np.floor(np.log10(value))
    base = value / (10**exp)
    closest = min(e24, key=lambda x: abs(x - base))
    return round(closest * (10**exp), 4)

def simulate_filter(params, target_freq_khz=150, r_load=50, full_scan=False):
    l_val, c1_val, c2_val = params
    circuit = Circuit('EMC_Optimizer_V4')
    circuit.SinusoidalVoltageSource('input', 'input_gen', circuit.gnd, amplitude=1@u_V)
    circuit.R('source', 'input_gen', 'n1', 50@u_Ohm)
    
    # Модель с паразитными параметрами
    circuit.C(1, 'n1', 'c1_i', c1_val@u_uF); circuit.R('c1r', 'c1_i', 'c1_l', 15@u_mOhm); circuit.L('c1l', 'c1_l', circuit.gnd, 3@u_nH)
    circuit.L(1, 'n1', 'l1_i', l_val@u_uH); circuit.R('l1r', 'l1_i', 'n2', 60@u_mOhm)
    circuit.C(2, 'n2', 'c2_i', c2_val@u_uF); circuit.R('c2r', 'c2_i', 'c2_l', 15@u_mOhm); circuit.L('c2l', 'c2_l', circuit.gnd, 3@u_nH)
    circuit.R('load', 'n2', circuit.gnd, r_load@u_Ohm)

    try:
        with SuppressOutput():
            sim = circuit.simulator()
            if full_scan:
                return sim.ac(start_frequency=10@u_kHz, stop_frequency=100@u_MHz, number_of_points=100, variation='dec')
            else:
                f = target_freq_khz * 1e3
                res = sim.ac(start_frequency=f, stop_frequency=f, number_of_points=1, variation='lin')
                return 20 * np.log10(abs(complex(res.n2[0])) + 1e-15)
    except: return 0

# --- ГЛОБАЛЬНЫЕ ЦЕЛИ ---
TARGET_FREQ = 150 # kHz
TARGET_DB = -60   # Целевое затухание

def objective(params):
    l, c1, c2 = params
    if any(p < 0.05 for p in params): return 1e12 # Запрет микро-значений
    
    # Симуляция в двух режимах нагрузки
    gain_50 = simulate_filter(params, TARGET_FREQ, r_load=50)
    gain_10 = simulate_filter(params, TARGET_FREQ, r_load=10)
    
    worst_gain = max(gain_50, gain_10)
    
    # 1. Если условие по затуханию не выполнено - огромный штраф
    if worst_gain > TARGET_DB:
        return 1e9 + (worst_gain - TARGET_DB)**2 * 1000
    
    # 2. Если ТЗ выполнено, минимизируем ГАБАРИТЫ. 
    # Коэффициент 10 для L, так как катушки больше и дороже кондеров.
    return (l * 10.0) + (c1 * 1.0) + (c2 * 1.0)

print(f"\n[V4] СТАРТ: Поиск минимальных габаритов при стабильном затухании < {TARGET_DB} dB...")

# Начинаем с запасом, чтобы Nelder-Mead было откуда "спускаться"
initial_guess = [20, 1.0, 1.0]
res = minimize(objective, initial_guess, method='Nelder-Mead', tol=1e-3)

if res.success:
    real_p = [get_closest_e24(p) for p in res.x]
    db_50 = simulate_filter(real_p, TARGET_FREQ, 50)
    db_10 = simulate_filter(real_p, TARGET_FREQ, 10)

    print("\n" + "="*55)
    print(f"{'Компонент':<18} | {'Расчет':<12} | {'E24 (Финал)':<12}")
    print("-" * 55)
    labels = ['L (uH)', 'C1 (uF)', 'C2 (uF)']
    for i in range(3):
        print(f"{labels[i]:<18} | {res.x[i]:10.3f}   | {real_p[i]:12.3f}")
    print("-" * 55)
    print(f"Затухание (High-Z 50 Ohm): {db_50:.2f} dB")
    print(f"Затухание (Low-Z 10 Ohm):  {db_10:.2f} dB")
    print("="*55)

    if max(db_50, db_10) <= TARGET_DB:
        print("СТАТУС: ТЗ ВЫПОЛНЕНО ✅ (Даже в худшем случае)")
    else:
        print("СТАТУС: НУЖЕН ПЕРЕСМОТР ❌ (Затухание недостаточно)")

    # Построение финального графика АЧХ
    ana_50 = simulate_filter(real_p, full_scan=True, r_load=50)
    ana_10 = simulate_filter(real_p, full_scan=True, r_load=10)

    plt.figure(figsize=(10, 6))
    plt.semilogx(ana_50.frequency, 20*np.log10(np.abs(ana_50.n2)), label='Нагрузка 50 Ом', color='blue', lw=2)
    plt.semilogx(ana_10.frequency, 20*np.log10(np.abs(ana_10.n2)), label='Нагрузка 10 Ом', color='orange', linestyle='--')
    plt.axhline(y=TARGET_DB, color='red', linestyle=':', label='Target -60 dB')
    plt.title(f"Финальная АЧХ фильтра (V4): L={real_p[0]}uH, C={real_p[1]}uF")
    plt.xlabel("Частота (Гц)"); plt.ylabel("Затухание (дБ)"); plt.grid(True, which="both", alpha=0.4)
    plt.legend(); plt.savefig('/workspace/v4_final_report.png')
    print("\n[ВЫПОЛНЕНО] График сохранен в v4_final_report.png\n")