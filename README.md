# Siload

**Low-cost retrofit weight sensing for existing silos.**

Siload is an open-source project for estimating the contents of a silo by measuring the strain in its existing support legs.

Instead of installing expensive load cells underneath the silo, small strain gauges are bonded directly to the structure. Siload measures these tiny deformations and converts them into an estimated silo weight.

The goal is simple:

> **Turn an existing silo into a smart weighing system without rebuilding it.**

---

## Why Siload?

Knowing how much material remains inside a silo is useful, but conventional weighing systems can be expensive and difficult to retrofit.

Traditional load-cell installations may require:

- lifting the silo;
- modifying its supports;
- installing multiple industrial load cells;
- mechanical engineering work;
- expensive instrumentation.

Siload takes a different approach.

```text
Traditional system

SILO
 │
 ▼
[ Load cell ]
 │
Foundation


Siload

SILO
 │
 │  ← strain gauges
 │
 │
Foundation
```

The silo stays where it is.

Siload measures how much its existing structure deforms under load.

---

## How it works

Steel stretches by an extremely small amount when it is loaded.

A strain gauge bonded to the silo leg changes resistance when this happens.

Siload measures that change using a Wheatstone bridge and a high-resolution ADC.

```text
Silo contents
     │
     ▼
 Mechanical load
     │
     ▼
 Silo leg strain
     │
     ▼
Strain gauges
     │
     ▼
Wheatstone bridge
     │
     ▼
  24-bit ADC
     │
     ▼
    ESP32
     │
     ▼
Filtering + calibration
     │
     ▼
Estimated silo weight
```

Measurements from multiple silo legs are combined to estimate the total load.

---

## Sensor concept

The intended configuration uses **four strain gauges per silo leg**.

```text
        SILO LEG

       Side A
        │
      [ V ]
        │
      [ H ]

        │
        │

       Side B
        │
      [ V ]
        │
      [ H ]

V = vertical strain gauge
H = transverse strain gauge
```

The gauges can be wired as a **full Wheatstone bridge**.

This configuration is intended to improve:

- temperature compensation;
- sensitivity;
- rejection of bending;
- rejection of uneven structural loading;
- long-term stability.

Each silo leg can be measured independently before the loads are combined in software.

---

## Prototype hardware

A basic four-leg Siload system can be built using inexpensive off-the-shelf components.

| Component | Quantity |
|---|---:|
| 350 Ω strain gauges | 16 |
| 24-bit ADC / HX711 | 4 |
| ESP32-C3 | 1 |
| Temperature sensors | 4 |
| Precision resistors | Several |
| Shielded sensor cable | As required |
| IP-rated enclosure | 1 |
| Power supply | 1 |

The first prototypes are intentionally based on readily available components.

Future versions may use a dedicated Siload PCB.

---

## System architecture

```text
             SILO

       ┌──────┴──────┐
       │             │
    Leg 1          Leg 2
       │             │
   Strain          Strain
   bridge          bridge
       │             │
     ADC             ADC
       │             │
       └──────┬──────┘
              │
            ESP32
              │
       ┌──────┴───────┐
       │              │
      Wi-Fi          BLE
       │
       ▼
 Dashboard / API
```

Four-leg installations simply extend the same architecture with two additional measurement channels.

---

## Calibration

Accurate absolute weight measurement requires calibration because every silo is different.

Variables include:

- silo geometry;
- leg dimensions;
- steel properties;
- welds and brackets;
- foundation stiffness;
- gauge placement;
- load distribution;
- temperature.

Siload therefore focuses heavily on software-assisted calibration.

### Initial calibration

The simplest method is to record the sensor output at one or more known silo weights.

```text
ADC / strain
     │
     │           ● known load
     │        /
     │     /
     │  ●
     │/
     └──────────────────
             kg
```

More calibration points allow the system to compensate for structural nonlinearities.

### Shunt calibration

Future hardware may include electronically switched precision resistors for **shunt calibration**.

This allows the controller to inject a known electrical change into the Wheatstone bridge.

It can be used to verify the complete measurement chain:

```text
strain gauge
    ↓
wiring
    ↓
bridge
    ↓
ADC
    ↓
firmware
```

without physically loading the silo.

---

## Temperature compensation

Outdoor silos can experience large temperature changes.

Because the measured strains are extremely small, temperature effects cannot simply be ignored.

Siload aims to compensate for them using a combination of:

- full-bridge strain measurement;
- matched strain gauges;
- temperature sensing at each leg;
- software correction;
- long-term baseline tracking.

---

## Signal processing

Raw strain measurements are not directly converted into kilograms.

The firmware can process measurements using techniques such as:

```text
raw ADC
   ↓
outlier rejection
   ↓
low-pass filtering
   ↓
temperature compensation
   ↓
per-leg calibration
   ↓
load distribution correction
   ↓
total estimated weight
```

Slow-changing silo inventory is especially suitable for aggressive noise filtering because millisecond response times are unnecessary.

---

## Possible features

The long-term goal is more than simply displaying a number.

Siload could provide:

- real-time silo weight;
- estimated fill percentage;
- kilograms or tonnes remaining;
- consumption rate;
- refill detection;
- low-level alerts;
- historical inventory graphs;
- abnormal load-distribution detection;
- individual leg diagnostics;
- temperature compensation;
- automatic drift correction;
- sensor health monitoring;
- Wi-Fi connectivity;
- local web interface;
- MQTT / REST integration.

---

## Example dashboard

```text
Siload
────────────────────────

Feed Silo 01

████████████████░░░░  78%

        18,420 kg

Consumption
   612 kg / day

Estimated remaining
   30.1 days

Leg load
A   4,580 kg
B   4,710 kg
C   4,490 kg
D   4,640 kg

System
● Sensors OK
● Temperature compensated
● Connected
```

---

## Design goals

Siload is being designed around several principles.

**Low cost**

The sensing hardware should cost a fraction of a traditional industrial silo weighing retrofit.

**Retrofit-friendly**

Installation should require minimal changes to the existing silo.

**Non-invasive**

The silo should not need to be lifted simply to install weighing hardware.

**Smart**

Software should handle as much calibration, filtering, diagnostics and compensation as possible.

**Repairable**

The hardware and firmware should use accessible components and an open design.

**Scalable**

The same principle should eventually work with different silo sizes, geometries and numbers of support legs.

---

## Project status

> **Early development / experimental**

Siload is currently a research and prototype project.

Current focus:

- strain-gauge configuration;
- mechanical mounting;
- Wheatstone bridge design;
- low-noise acquisition;
- temperature compensation;
- calibration methods;
- long-term drift;
- ESP32 firmware;
- validation against known loads.

Absolute weighing accuracy has **not yet been established**.

---

## Roadmap

### Phase 1 — Bench testing

- [ ] Test BF350 / 350 Ω strain gauges
- [ ] Build full Wheatstone bridge
- [ ] Evaluate HX711 noise and stability
- [ ] Test temperature drift
- [ ] Develop ESP32 acquisition firmware

### Phase 2 — Structural prototype

- [ ] Instrument a steel test structure
- [ ] Compare strain against known loads
- [ ] Test bending rejection
- [ ] Develop multi-point calibration
- [ ] Evaluate long-term creep and drift

### Phase 3 — Silo prototype

- [ ] Install sensors on a real silo
- [ ] Instrument all support legs
- [ ] Compare against known filling events
- [ ] Implement temperature compensation
- [ ] Develop automatic health checks

### Phase 4 — Siload hardware

- [ ] Dedicated PCB
- [ ] Industrial enclosure
- [ ] Improved ADC architecture
- [ ] Protected sensor connections
- [ ] Shunt calibration
- [ ] Local dashboard
- [ ] MQTT / API support

---

## Important

Siload is an experimental measurement system.

It must **not** be used as a safety-critical structural monitoring system or as a certified/legal-for-trade weighing instrument.

Installing strain gauges on load-bearing structures must also be performed carefully to avoid damaging protective coatings or structural components.

---

## Contributing

Siload is in an early stage and experimentation is welcome.

Useful areas of research include:

- strain gauge layouts;
- bridge circuits;
- low-noise ADCs;
- temperature compensation;
- structural mechanics;
- calibration algorithms;
- enclosure design;
- ESP32 firmware;
- field testing.

Issues, test data and hardware experiments are welcome.

---

## Name

**Siload** combines:

**Silo + Load**

A simple description of what the project measures.

---

## License

License to be determined.

---

**Siload — weigh the silo, not rebuild it.**
