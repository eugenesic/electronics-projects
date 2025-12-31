import matplotlib.pyplot as plt
import numpy as np  # Добавили импорт numpy
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

def create_pi_filter(L_val, C1_val, C2_val, R_load=50):
    circuit = Circuit('EMC Pi-Filter Optimization')
    
    # Входное напряжение. Изменили 'in' на 'node_in'
    circuit.SinusoidalVoltageSource('input', 'node_in', circuit.gnd, amplitude=1@u_V)
    
    # Сопротивление источника
    circuit.R('source', 'node_in', 'n1', 50@u_Ohm)
    
    # П-фильтр: C1 - L1 - C2
    circuit.C(1, 'n1', circuit.gnd, C1_val@u_uF)
    circuit.L(1, 'n1', 'n2', L_val@u_uH)
    circuit.C(2, 'n2', circuit.gnd, C2_val@u_uF)
    
    # Нагрузка
    circuit.R('load', 'n2', circuit.gnd, R_load@u_Ohm)
    
    return circuit

# Параметры симуляции
circuit = create_pi_filter(L_val=10, C1_val=0.1, C2_val=0.1)
simulator = circuit.simulator(temperature=25, nominal_temperature=25)

# Лог частот от 10кГц до 100МГц
analysis = simulator.ac(start_frequency=10@u_kHz, 
                        stop_frequency=100@u_MHz, 
                        number_of_points=100,  
                        variation='dec')

# Визуализация
plt.figure(figsize=(10, 6))
# Считаем усиление (gain) в дБ относительно входного 1В
# Используем комплексные значения для получения модуля через np.abs
gain = 20 * np.log10(np.abs(analysis.n2))

plt.semilogx(analysis.frequency, gain)
plt.axhline(y=-40, color='r', linestyle='--', label='Target -40dB') # Линия цели
plt.grid(True, which="both", ls="-")
plt.title("АЧХ П-образного фильтра (Simulation)")
plt.xlabel("Частота (Гц)")
plt.ylabel("Затухание (дБ)")
plt.legend()

# Сохраняем в файл, так как мы внутри Docker
plt.savefig('/workspace/filter_response.png')
print("Симуляция завершена. График сохранен в filter_response.png")