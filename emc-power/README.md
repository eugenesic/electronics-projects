# AI-Driven EMC Filter Optimizer ⚡🛡️

A professional tool for automatic design and optimization of power Electromagnetic Compatibility (EMC) filters using SPICE simulation and numerical optimization algorithms.

## 📌 Overview

This project automates the selection of optimal component values for a Pi-filter () to suppress differential mode noise. Unlike basic online calculators, this optimizer accounts for real-world physical constraints and varying operational conditions.

### Key Features (V4 Final):

* **SPICE-Driven:** Powered by the `NgSpice` engine via the `PySpice` library for high-fidelity circuit analysis.
* **Realistic Modeling:** Includes parasitic parameters: **ESR** (Equivalent Series Resistance), **ESL** (Equivalent Series Inductance), and coil **DCR** (DC Resistance).
* **Smart Optimization:** Utilizes the Nelder-Mead algorithm (`SciPy`) with a custom penalty function to minimize physical footprint.
* **Stability Check:** Guarantees target attenuation (e.g., -60 dB) across different load impedances: from no-load (50 Ohm) to heavy-load (10 Ohm) scenarios.
* **Design for Manufacturing (DFM):** Automatically snaps calculated values to standard industrial **E24** series components.

---

## 🛠️ How It Works

The optimization process follows three main stages:

1. **Mathematical Search:** The algorithm finds "ideal"  and  values, minimizing size while maintaining the attenuation threshold.
2. **Stability Verification:** Simulation is repeated for low-impedance loads to ensure no resonance peaks amplify the noise.
3. **Quantization:** The program selects the nearest real-world components and performs a final verification to ensure rounding didn't violate the specs.

---

## 🚀 Quick Start

### Requirements

* Docker (Recommended) or local `NgSpice` installation.
* Python 3.10+
* Libraries: `pyspice`, `scipy`, `numpy`, `matplotlib`.

### Execution

Run the optimizer:

```bash
python emc_optimizer_v4.py

```

---

## 📊 Sample Output

The program generates a console report and an Frequency Response (Bode plot):

| Component | Calculated Value | Selected E24 Value |
| --- | --- | --- |
| **L (Inductance)** | 4.534 uH | **4.700 uH** |
| **C1 (Capacitor)** | 1.696 uF | **1.600 uF** |
| **C2 (Capacitor)** | 1.074 uF | **1.100 uF** |

**Final Status:** `SPEC MET ✅`

**Attenuation (10 Ohm):** `-60.44 dB`

---

# AI-Driven EMC Filter Optimizer (RU) ⚡🛡️

Профессиональный инструмент для автоматического проектирования и оптимизации силовых фильтров электромагнитной совместимости (ЭМС) с использованием SPICE-моделирования и алгоритмов численной оптимизации.

## 📌 Описание

Проект решает задачу подбора оптимальных номиналов компонентов П-фильтра () для подавления дифференциальных помех. В отличие от простых калькуляторов, данный оптимизатор учитывает реальные физические ограничения и условия эксплуатации.

### Ключевые особенности (V4 Final):

* **SPICE-Driven:** Использование движка `NgSpice` через библиотеку `PySpice` для точного анализа цепей.
* **Realistic Modeling:** Учет паразитных параметров компонентов: **ESR** (последовательное сопротивление), **ESL** (индуктивность выводов) и **DCR** катушки.
* **Smart Optimization:** Алгоритм Нелдера-Мида (`SciPy`) с функцией штрафа за габариты компонентов.
* **Stability Check:** Гарантированное затухание (напр. -60 дБ) в разных режимах нагрузки: от холостого хода (50 Ом) до сильно нагруженной линии (10 Ом).
* **Design for Manufacturing (DFM):** Автоматическое приведение расчетных значений к стандартному промышленному ряду номиналов **E24**.

---

## 🛠️ Как это работает

Процесс оптимизации разделен на три этапа:

1. **Математический поиск:** Алгоритм ищет идеальные значения  и , минимизируя габариты при соблюдении порога затухания.
2. **Проверка стабильности:** Симуляция повторяется для низкого импеданса нагрузки, чтобы исключить возникновение резонансных пиков, усиливающих помеху.
3. **Квантование:** Программа подбирает ближайшие реальные компоненты и делает финальную верификацию, чтобы убедиться, что округление не нарушило требования ТЗ.

---

## 🚀 Быстрый запуск

### Требования

* Docker (рекомендуется) или установленный `NgSpice`.
* Python 3.10+
* Библиотеки: `pyspice`, `scipy`, `numpy`, `matplotlib`.

### Запуск

```bash
python emc_optimizer_v4.py

```

---

## 📈 Планы развития

* [x] Оптимизация П-фильтра дифференциальных помех.
* [x] Автоподбор номиналов ряда E24.
* [ ] Добавление модели синфазного дросселя (Common Mode Choke).
* [ ] Расчет тепловых потерь на DCR катушки.

---

**Developed for emc-power project**

---