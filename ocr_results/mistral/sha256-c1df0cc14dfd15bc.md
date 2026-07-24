# sb14_can_datasheet_en_41c21d3423__c1df0cc14d

- PDF: `datasheets/flintec/sb14_can_datasheet_en_41c21d3423__c1df0cc14d.pdf`
- SHA-256: `c1df0cc14dfd15bc1931ab9acf6c49b6e448a0237c58bbb96dd5472d846d3e56`
- OCR model: `mistral-ocr-latest`

## Page 1

# SB14 CAN beam load cell



## product description

The SB14 CAN is a high-accuracy, low-profile bending beam load cell available in capacities from 500 lb to 10,000 lb (227 kg to 4,536 kg), now with embedded CAN output functionality supporting both CANopen and J1939 protocols.

The full stainless steel construction and complete hermetic sealing ensure reliable accuracy and robustness in harsh industrial environments. The embedded CAN board transforms the SB14 into a digital load cell with direct CAN interface, ideal for modern industrial systems requiring efficient and reliable communication.

Setup is straightforward and can be performed with a terminal emulation program or the Flintec FDC application, available from flintec.com.

## applications

Industrial platform scales, on-board vehicle weighing systems, vessel and tank weighing systems, systems requiring direct CAN communication.

## accessories + options

Compatible range of hardware

Blind-hole (BH), counterbore metric (CM) or counterbore unified (CU)

Default: Plastic cable gland; Optional: stainless-steel cable gland

Default: Free leads; Optional: M12, 5-pin male code-A connector

## key features

Stainless steel construction

Hermetically sealed to IP68

Wide capacity range from 500lb to 10,000lb (227kg to 4,536kg)

High accuracy and reliability

Range of loading hole options

Embedded CAN output (user-selectable CANopen or J1939)

Software-configurable parameters

Works with Flintec FDC application for analysis & configuration

beam load cells | SB14 CAN | www.flintec.com

sb14-can-be-dat-en-v0

![Flintec logo]()

## Page 2

## load cell specifications

|  Maximum capacity (E_{max}) | klb | 0.5 / 1 / 2.5 / 5 / 10*  |   |
| --- | --- | --- | --- |
|  Metric equivalents (1 lb=0.45359 kg) | kg | 227 / 454 / 1134 / 2,268 / 4,536  |   |
|  Accuracy class |  | GP | G3  |
|  Temperature effect on minimum dead load output (TC_{d}) | %*RO/10°C | ± 0.0400 | ± 0.0122  |
|  Temperature effect on sensitivity (TC_{RO}) | %*RO/10°C | ± 0.0200 | ± 0.0100  |
|  Combined error | %*RO | ± 0.0500 | ± 0.0200  |
|  Non-linearity | %*RO | ± 0.0400 | ± 0.0166  |
|  Hysteresis | %*RO | ± 0.0400 | ± 0.0166  |
|  Creep error (30 minutes) / DR | %*RO | ± 0.0600 | ± 0.0166  |
|  Optional Temp. effect on min. dead load output (TC_{d} opt) | %*RO/10°C | n.a. | ± 0.0061  |
|  Zero balance | %*RO | ± 5  |   |
|  Safe load limit (E_{lim}) | %*E_{max} | 200  |   |
|  Ultimate load | %*E_{max} | 300  |   |
|  Safe side load | %*E_{max} | 100  |   |
|  Compensated temperature range | °C | -10...+40  |   |
|  Load cell material |  | stainless steel 17-4 PH (1.4548)  |   |
|  Sealing |  | cable entry hermetically sealed by glass to metal header  |   |
|  Protection according EN 60 529 |  | IP68 (up to 2m water depth) / IP69K  |   |
|  Pocket weight | kg | 1.2 (500-5,000lb), 2.44 (10,000lb)  |   |

The limits for Non-Linearity, Hysteresis, and TC$_{RO}$ are typical values.

* The 10klb model is only available as a GP version.

beam load cells | SB14 CAN | www.flintec.com

sb14-can-be-dat-en-v0

2

## Page 3

## embedded CAN board specifications

|  Board model | - | CED-20  |
| --- | --- | --- |
|  Supply voltage | VDC | 9-32  |
|  Supply reversal protection | - | Yes  |
|  Overvoltage protection | - | Yes  |
|  Software enabled CAN termination resistor | - | Yes  |
|  Operating temperature range | °C | -20 to +70  |
|  Storage temperature range | °C | -40 to +80  |
|  ADC type | - | 24-bit Sigma-Delta  |
|  Digital filters | - | Rolling average, IIR  |
|  CAN output cable | - | Free leads or an M12, 5-pin male Code A connector  |
|  Protocols supported | - | CANopen (default), J1939 (selectable)  |
|  Baud rates (CANopen) | bits/s | 10k, 20k, 50k, 125k, 250k, 500k, 800k, 1,000k  |
|  Baud rates (J1939) | bits/s | 250k  |
|  Update rates (CANopen) | Hz | 5 to 2,500  |
|  Update rates (J1939) | Hz | 5 to 1,600  |
|  Designed to meet | - | Regulation 10, ISO 13766:2018, ISO 14982:1998  |

The embedded CAN board includes components designed to meet standards such as Regulation 10, ISO 13766:2018, and ISO 14982:1998. However, it is not currently certified for these standards. Customers requiring compliance must confirm suitability with their regulatory requirements.

## wiring

The load cell is provided with a shielded, 4 conductor cable (AWG 24).

Cable jacket: polyurethane

Cable length: 3m for SB14-0.5klb to 5klb, 4.5 m for SB14-10klb

Cable diameter: 5mm

The shield is floating (On request the shield can be connected to the load cell body)



beam load cells | SB14 CAN | www.flintec.com

sb14-can-be-dat-en-v0

3

## Page 4

## M12 5-PIN Male Code A



|  Pin | Function | Colour  |
| --- | --- | --- |
|  1* | Shield** | Yellow  |
|  2 | + VDC | Green  |
|  3 | GND | Black  |
|  4 | CAN_{HI} | White  |
|  5 | CAN_{LO} | Red  |

* Pin 1 shield connection is optional.

** Shield connected at sensor is optional.

## product dimensions (mm)



|  Type | L1 | L2 | L3 | L4 | L5 | H1 | H2 | H3 | H4 | H5 | W | D1 | D2 | D3 | D4 | Mounting bolts | Torque *  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  500/1000 lb | 133.4 | 12.7 | 76.2 | 25.4 | 59.9 | 31 | 28.8 | 15 | 4 | 15 | 30 | 18 | 13 | 13.5 | M12 | M12 8.8 | 90 Nm  |
|  2500 lb | 133.4 | 12.7 | 76.2 | 25.4 | 59.9 | 31 | 30.5 | 15 | 4 | 15 | 30 | 18 | 13 | 13.5 | M12 | M12 8.8 | 90 Nm  |
|  5000 lb | 133.4 | 12.7 | 76.2 | 25.4 | 59.9 | 31 | 30.5 | 15 | 4 | 15 | 30 | 18 | 13 | 13.5 | M12 | M12 10.9 | 120 Nm  |
|  10,000 lb | 177.8 | 19.1 | 95.3 | 38.1 | 92.7 | 43.6 | 38.1 | 20.5 | 8 | 20.1 | 43 | 25 | 21 | 21.5 | M20 | M20 8.8 | 400 Nm  |

* Torque values assume oiled threads.

** Unified thread 1/2-20 UNF (500...5000 lb) and 3/4-16 UNF (10000 lb) is available. Type designation SB14-xx-CU.

Specifications and dimensions are subject to change without notice.

beam load cells | SB14 CAN | www.flintec.com

sb14-can-be-dat-en-v0

4
