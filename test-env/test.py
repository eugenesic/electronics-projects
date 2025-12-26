import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

print("Python и библиотеки работают!")

circuit = Circuit('RC Test')

circuit.V('input', 'n1', circuit.gnd, 5@u_V)
circuit.R('s', 'n1', 'n2', 1@u_mOhm)  # крошечный для сходимости
circuit.R('load', 'n2', circuit.gnd, 10@u_kOhm)
circuit.C('1', 'n2', circuit.gnd, 1@u_uF, initial_condition=0@u_V)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=10@u_ms, end_time=10@u_s, use_initial_condition=True)

plt.figure(figsize=(10, 6))
plt.plot(analysis.time * 1e3, analysis.n2)
plt.xlabel('Time [ms]')
plt.ylabel('Voltage [V]')
plt.title('RC Charge Curve')
plt.grid(True)
plt.tight_layout()
plt.savefig('rc_curve.png')
print("График сохранён как rc_curve.png")
print("Симуляция завершена успешно!")
