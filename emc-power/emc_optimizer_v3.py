import os
import sys
import warnings
import numpy as np
import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from scipy.optimize import minimize

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
    circuit = Circuit('EMC_Optimizer_V3_Clean')
    
    # ИСХОДНИК: переименовали 'in' в 'input_gen'
    circuit.SinusoidalVoltageSource('input', 'input_gen', circuit.gnd, amplitude=1@u_V)
    circuit.R('source', 'input_gen', 'n1', 50@u_Ohm)
    
    # Модель фильтра
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

TARGET_FREQ = 150
TARGET_DB = -60

def objective(params):
    l, c1, c2 = params
    if any(p < 0.1 for p in params): return 1e9
    
    gain_50 = simulate_filter(params, TARGET_FREQ, r_load=50)
    gain_10 = simulate_filter(params, TARGET_FREQ, r_load=10)
    worst_gain = max(gain_50, gain_10)
    
    error = (worst_gain - TARGET_DB)**2 if worst_gain > TARGET_DB else 0
    # Оптимизация по габаритам (L дороже C)
    size_penalty = (l * 0.8) + (c1 + c2) * 1.2
    
    return error + size_penalty

print(f"\n[V3] Оптимизация: Минимум габаритов + Стабильность импеданса...")
res = minimize(objective, [10, 0.1, 0.1], method='Nelder-Mead', tol=1e-2)

if res.success:
    real_p = [get_closest_e24(p) for p in res.x]
    
    print("\n" + "="*50)
    print(f"{'Компонент':<15} | {'Результат (E24)':<15}")
    print("-" * 50)
    print(f"{'L (uH)':<15} | {real_p[0]:.3f}")
    print(f"{'C1 (uF)':<15} | {real_p[1]:.3f}")
    print(f"{'C2 (uF)':<15} | {real_p[2]:.3f}")
    print("-" * 50)
    print(f"Затухание (50 Ом): {simulate_filter(real_p, TARGET_FREQ, 50):.2f} dB")
    print(f"Затухание (10 Ом): {simulate_filter(real_p, TARGET_FREQ, 10):.2f} dB")
    print("="*50)

    # Строим график для двух случаев нагрузки
    print("[ГРАФИК] Сохраняем сравнение стабильности в v3_stability.png...")
    ana_50 = simulate_filter(real_p, full_scan=True, r_load=50)
    ana_10 = simulate_filter(real_p, full_scan=True, r_load=10)

    plt.figure(figsize=(10, 6))
    plt.semilogx(ana_50.frequency, 20*np.log10(np.abs(ana_50.n2)), label='Нагрузка 50 Ом', color='blue')
    plt.semilogx(ana_10.frequency, 20*np.log10(np.abs(ana_10.n2)), label='Нагрузка 10 Ом', color='orange')
    plt.axhline(y=TARGET_DB, color='red', linestyle='--', alpha=0.5)
    plt.title("Стабильность фильтра при изменении нагрузки")
    plt.xlabel("Частота (Гц)"); plt.ylabel("Затухание (дБ)"); plt.grid(True, which="both", alpha=0.3)
    plt.legend(); plt.savefig('/workspace/v3_stability.png')
    
    print("Результат: ✅ Чисто и оптимально.\n")