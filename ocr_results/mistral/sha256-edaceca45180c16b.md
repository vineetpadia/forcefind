# FLX-Datasheet-A301-RevJ

- PDF: `datasheets/tekscan/FLX-Datasheet-A301-RevJ.pdf`
- SHA-256: `edaceca45180c16bcd8a06e3a623d2ef16ab4d2c02a8fd44f8dfa57fddc5f28e`
- OCR model: `mistral-ocr-latest`

## Page 1

Tekscan

# FlexiForce™ Standard Model A301

Actual size of sensor



The A301 is optimized for high volume manufacturing and is ideal for embedding into products and applications. This sensor is available off-the-shelf, ideal for an easy proof of concept. The A301 can be used with our test & measurement, prototyping, and embedding electronics, including the FlexiForce Sensor Characterization Kit, FlexiForce Prototyping Kit, FlexiForce Quickstart Board, and the ELF™ System®. You can also use your own electronics, or multimeter.

Benefits

- Small size is ideal for prototyping and integration
- Available with Enhanced Stability Series (ESS) pressure sensitive ink for high-temperature and high-humidity environments
- Thin and Flexible
Easily integrates into tight spaces for non-intrusive force measurement between mating surfaces.
- Easy to Use
Compatible with a variety of electronics and ready-to-use for testing, prototyping, or embedding.

Physical Properties

|  **Thickness** | 0.203 mm (0.008 in.) | **Connector** | 2-pin Male Square Pin  |
| --- | --- | --- | --- |
|  **Length** | 25.4 mm (1 in.)** | **Substrate** | Polyester  |
|  **Width** | 14 mm (0.55 in.) | **Pin Spacing** | 2.54 mm (0.1 in.)  |
|  **Sensing Area** | 9.53 mm (0.375 in.) diameter |  |   |

* Sensor will require an adapter/extender to connect to the ELF System. Contact your Tekscan representative for assistance.

** Length does not include pins. Please add approximately 6 mm (0.25 in.) for pin length for a total length of approximately 32 mm (1.25 in.).

|   | Typical Performance | Evaluation Conditions  |
| --- | --- | --- |
|  Linearity (Error) | < ±3% of full scale | Line drawn from 0 to 50% load  |
|  Repeatability | < ±2.5% | Conditioned sensor, 80% of full force applied  |
|  Hysteresis | < 4.5% of full scale | Conditioned sensor, 80% of full force applied  |
|  Drift | < 5% per logarithmic time scale | Constant load of 111 N (25 lb)  |
|  Response Time | < 5μsec | Impact load, output recorded on oscilloscope  |
|  Operating Temperature | -40°C - 60°C (-40°F - 140°F) | Convection and conduction heat sources  |
|  Durability | ≥ 3 million actuations | Perpendicular load, room temperature, 22 N (5 lb)  |
|  Temperature Sensitivity | 0.36%/°C (± 0.2%/°F) | Conductive heating  |

All data above was collected utilizing an Op Amp Circuit (shown on the next page).

If your application cannot allow an Op Amp Circuit, visit www.tekscan.com/flexiforce-integration-guides, or contact a FlexiForce Applications Engineer.

SD_Rev_J_121724

ROHS COMPLIANT

ISO 9001:2008 Compliant & 13485:2016 Registered

## Page 2

## Typical Performance

### Standard Force Ranges as Tested with Inverting Op-Amp Circuit

4.4 N (0 - 1 lb)

111 N (0 - 25 lb)

445 N (0 - 100 lb) †

†This sensor can measure up to 4,448 N (1,000 lb). To measure higher forces, apply a lower drive voltage (-0.5 V, -0.25 V, etc.) and reduce the resistance of the feedback resistor (1kΩ min.). To measure lower forces, apply a higher drive voltage and increase the resistance of the feedback resistor.

Sensor output is a function of many variables, including interface materials. Calibration is recommended. See FlexiForce Best Practices for details.

## Recommended Circuit

$$V_{OUT} = -V_{REF} * (R_F / R_S)$$



$$R_{FEEDBACK}(R_F) = 100k\Omega$$
$$C_1 = 47 \text{ pF}$$



100K potentiometer and 47 pF are general recommendations; your specific sensor may be best suited with a different potentiometer and capacitor. Testing should be performed to determine this.

- • Polarity of $V_{REF}$ must be opposite the polarity of $V_{SUPPLY}$
- • Sensor Resistance $R_S$ at no load is typically >1MΩ
- • Max recommended current is 2.5mA

617.464.4500

1.800.248.3669

info@tekscan.com

tekscan.com

Sensor Datasheet
SD_Rev_J_121724

©Tekscan Inc., 2024. All rights reserved. Tekscan, the Tekscan logo, and FlexiForce are trademarks or registered trademarks of Tekscan, Inc.

Contact us
for more information.
Volume discounts available.
