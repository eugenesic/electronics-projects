# AI-Driven EMC Filter Optimizer ⚡🛡️

Professional tool for automated synthesis and optimization of power EMI filters using SPICE-level simulation and numerical optimization.

## 📌 Overview

This project automates the design of industrial EMC filters, balancing the suppression of **Differential Mode (DM)** and **Common Mode (CM)** noise. Unlike basic models, the V5.2 optimizer uses a **Common Mode Choke (CMC)** with a realistic coupling coefficient () to utilize leakage inductance for DM filtering, significantly reducing component count.

### Key Features (V5.2 Industrial):

* **Dual-Mode Optimization:** Simultaneously optimizes DM and CM attenuation targets (default -60 dB).
* **Leakage Inductance Modeling:** Uses CMC leakage () instead of separate bulky DM inductors.
* **Safety-First Design:** Implements a strict constraint on **Leakage Current** (max 3.5 mA) by limiting Y-capacitor values () according to international safety standards (230V/50Hz).
* **Thermal Awareness:** Calculates static power losses based on real DC Resistance (**DCR**) of the windings at high load currents (up to 10A+).
* **Design for Manufacturing (DFM):** Snaps all calculated values to the standard industrial **E24** series.
* **Visual Analytics:** Generates professional Bode plots showing the performance of both noise modes from 10 kHz to 30 MHz.

---

## 🛠️ How It Works

1. **SPICE Simulation:** The tool builds a dynamic netlist in `NgSpice` for two separate test circuits (DM and CM).
2. **Constraint-Based Optimization:** The Nelder-Mead algorithm explores the parameter space () with a complex penalty function:
* **Penalty 1:** Violation of -60 dB attenuation target.
* **Penalty 2:** Exceeding 3.5 mA leakage current (Safety Limit).
* **Penalty 3:** Component physical footprint (prioritizing inductor minimization).


3. **Real-World Snap:** Rounds results to E24 and performs a final "as-built" verification.

---

## 📊 Performance Analysis

The transition from V4 to V5.2 represents a shift from theoretical Pi-filters to industrial-grade topology:

| Feature | V4 (Pi-Filter) | V5.2 (CMC-based) |
| --- | --- | --- |
| **Noise Type** | Differential Only | **DM + Common Mode** |
| **Main Component** | Separate L-inductor | **Common Mode Choke** |
| **Safety Check** | None | **Leakage Current Control** |
| **Damping** | Ideal/Generic | **Real DCR (mOhm)** |

---

# AI-Driven EMC Filter Optimizer (RU) ⚡🛡️

Инструмент профессионального уровня для автоматизированного синтеза и оптимизации силовых ЭМС-фильтров с использованием SPICE-моделирования.

## 📌 Описание

Проект автоматизирует проектирование промышленных фильтров, обеспечивая одновременное подавление **дифференциальных (DM)** и **синфазных (CM)** помех. Версия 5.2 использует модель **синфазного дросселя (CMC)** с реалистичным коэффициентом связи (), что позволяет использовать индуктивность рассеяния для фильтрации DM-помех без установки дополнительных катушек.

### Ключевые особенности (V5.2 Industrial):

* **Комплексная оптимизация:** Одновременный подбор параметров для DM и CM режимов (целевое затухание -60 дБ).
* **Модель индуктивности рассеяния:** Интеллектуальное использование паразитных параметров дросселя для экономии места на плате.
* **Контроль электробезопасности:** Жесткое ограничение **тока утечки** (макс. 3.5 мА) через лимит емкости Y-конденсаторов () для сетей 230В/50Гц.
* **Тепловой расчет:** Учет статических потерь мощности на активном сопротивлении обмоток (**DCR**) при токах до 10А и выше.
* **Готовность к производству (DFM):** Квантование номиналов по стандартному промышленному ряду **E24**.
* **Визуализация:** Автоматическая генерация графиков АЧХ в диапазоне 10 кГц — 30 МГц.

---

## 🚀 Быстрый запуск / Quick Start

### Requirements

* Python 3.10+
* `pyspice`, `scipy`, `numpy`, `matplotlib`
* `NgSpice` (or Docker with PySpice image)

### Execution

```bash
python emc_optimizer_v5.py

```

## 📈 Результаты работы (Sample Report)

| Компонент | Номинал E24 | Роль в схеме |
| --- | --- | --- |
| **Cx (X-Capacitor)** | **6.200 uF** | Подавление дифференциальной помехи |
| **Lcm (CM Choke)** | **20.000 mH** | Основной фильтр синфазной помехи |
| **Cy (Y-Capacitor)** | **27.000 nF** | Слив синфазного тока на заземление |

**Статус:** `✅ Расчет завершен успешно`
**Затухание (150 кГц):** DM: `-61.94 dB`, CM: `-59.61 dB`
**Потери мощности (10A):** `1.00 W`

---

**Developed for emc-power project. Engineering-grade EMI suppression.**

---