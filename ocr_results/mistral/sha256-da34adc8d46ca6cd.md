# Semtech-Corporation__2312_FT-701-Product-Data-Sheet-Brief__dbefe0bc3d

- PDF: `datasheets/digikey/Semtech-Corporation__2312_FT-701-Product-Data-Sheet-Brief__dbefe0bc3d.pdf`
- SHA-256: `da34adc8d46ca6cdf4fc0b748471b0414aff373de1c22a560e72533b368012f4`
- OCR model: `mistral-ocr-latest`

## Page 1

Qorvo

# FT-701
MEMS FORCE SENSOR
PRODUCT BRIEF

Revision B

FT-701 PRODUCT BRIEF Rev B

1 | Page

## Page 2

Qorvo

# CONTENTS

1. GENERAL DESCRIPTION ...3
2. FEATURES ...3
3. APPLICATIONS ...3
4. ORDERING INFORMATION ...3
5. PIN CONFIGURATION ...4
6. PIN DESCRIPTION ...4
7. ABSOLUTE MAXIMUM RATINGS ...5
8. APPLICATION INFORMATION ...5
8.1 TYPICAL OPERATING CIRCUIT ...5
8.2 SENSOR SYSTEM STACK-UP ...6
8.3 MEMS FORCE ANALOG FRONT-END (AFE) REFERENCES ...6
9. ELECTRICAL DESIGN, SENSOR PLACEMENT, HANDLING & PACKAGING INFORMATION ...7
9.1 ELECTRICAL DESIGN ...7
9.2 SENSOR PLACEMENT ...8
9.3 FOOTPRINT AND SMT DETAILS ...9
9.4 SMT PICK & PLACE GUIDELINES ...10
9.4.1 NOZZEL CONSIDERATIONS ...10
9.4.2 PICK & PLACE OPERATION ...11
9.5 SENSOR HANDLING ...11
9.6 ASSEMBLY INSTRUCTIONS ...12
9.7 PACKAGING INFORMATION ...13
9.8 SENSOR TOP MARK CODING ...14
9.9 SENSOR TAPE-AND-REEL (T&R) DETAILS/DIMENSIONS ...14
10. RELIABILITY & ENVIRONMENTAL INFORMATION ...15
11. REVISION HISTORY ...16

FT-701 PRODUCT BRIEF Rev B

2 | Page

## Page 3

Qorvo

## 1. GENERAL DESCRIPTION

The Qorvo FT-701 MEMS Force sensor represents the World's smallest force sensor and the easiest sensor to integrate, as it only requires attachment to the under-side of a sensing surface. At 0.8mm x 1.2mm, it is designed to fit into small form factor and to serve a broad range of applications including smart surfaces, screens, buttons, and sliders. The FT-701 sensor can be used with or without capacitive touch films to enable a robust 3D touch experience.

The FT-701 MEMS Force sensor does not require a preload stack-up, such as a metal spring or rubber, to absorb mechanical tolerances. The FT-701 sensor enables sensing under OLED displays or any material such as glass, metal, plastic, ceramic, wood, leather, etc. It enables new industrial designs, provides 10x higher reliability compared to mechanical switches and is immune to radio frequencies (RF) and electro-magnetic interference (EMI).

## 2. FEATURES

- Excellent Sensitivity, Linearity and Reliability
- Easy to Install
- Tunable TCO
- Fast Response – Low Latency
- Force Range: Grams to Kilograms
- Excellent Electrical and Thermal Stability
- Differential Analog Voltage Output
- Ultra-Low Power
- Supply Voltage: 1.8 V to 3.3 V
- 6-pin CSP, 0.8 mm x 1.2 mm x 0.220 mm

## 3. APPLICATIONS

- General Purpose Solid-State Buttons
- TWS Earbuds
- Wearables
- AR/VR
- Personal Care
- Toys
- Gaming, Controllers

## 4. ORDERING INFORMATION

|  PART | OPERATING TEMP. RANGE | FEATURES | DESCRIPTION  |
| --- | --- | --- | --- |
|  FT-701Y00 | 0°C to +70°C | Consumer | 3000pc 7-inch reel  |
|  FT-701Y00SR | 0°C to +70°C | Consumer | 300pc sample reel  |
|  FT-701A00 | -20°C to +70°C | Consumer | 3000pc 7-inch reel  |
|  FT-701A00SR | -20°C to +70°C | Consumer | 300pc sample reel  |

Table 1: Ordering Information

FT-701 PRODUCT BRIEF Rev B

3 | Page

## Page 4

Qorvo

# 5. PIN CONFIGURATION



Top View
Laser Mark



Bottom View
Bump Side

Figure 1: Pin Configuration

# 6. PIN DESCRIPTION

|  BUMP | PIN NAME | PIN DESCRIPTION  |
| --- | --- | --- |
|  1 | SPOS | Sensor Positive Output Terminal  |
|  2 | GNDP | Sensor Ground for Positive Bridge. Must connect to GNDN. Can also be used as sensor enable pin.  |
|  3 | VCCP | Sensor Supply Voltage for Positive Bridge. Connect to a stable, low noise power supply (e.g. LDO source or DRV from Qorvo AF-301) for best performance.  |
|  4 | VCCN | Sensor Supply Voltage for Negative Bridge. Connect to a stable, low noise power supply (e.g. LDO source or DRV from Qorvo AF-301) for best performance.  |
|  5 | GNDN | Sensor Ground for Negative Bridge. Must connect to GNDP. Can also be used as sensor enable pin.  |
|  6 | SNEG | Sensor Negative Output Terminal  |

Table 2: Pin Description

FT-701 PRODUCT BRIEF Rev B

4 | Page

## Page 5

Qorvo

## 7. ABSOLUTE MAXIMUM RATINGS

|  VCCP/VCCN to GNDP/GNDN | -0.3 V to +6 V  |
| --- | --- |
|  Applied Force (directly applied on top of the sensor) | 15 N  |
|  Operating Temperature Range | See Ordering Information  |
|  Storage Temperature | -65°C to +150°C  |
|  Lead Temperature (soldering 10s) | +260°C  |
|  Electrostatic Discharge Protection (ESD) | 1000 V (HBM), 500 V (CDM)  |

Stresses beyond those listed under “Absolute Maximum Ratings” may cause permanent damage to the device. These are stress ratings only, and functional operation of the device at these or any other conditions beyond those indicated in the operational sections of the specifications is not implied. Exposure to absolute maximum rating conditions for extended periods may affect device reliability.

## 8. APPLICATION INFORMATION

The FT-701 MEMS Force sensor is an extremely small force sensor. The sensor is designed to detect forces with mN resolution, as determined by the bit-depth of an analog-to-digital converter (ADC). By placing an FT-701 sensor individually or in arrays attached to a touch surface, designers can create novel three-dimensional force sensing human-machine interfaces (HMI).

### 8.1 TYPICAL OPERATING CIRCUIT

Typical applications for the FT-701 MEMS Force sensor include single or multi-sensor solutions. Figure 2 demonstrates a reference circuit utilizing one FT-701 sensor in combination with Qorvo’s ultra-low power analog-front-end (AFE) AF-301 with I²C interface for a button application.

Note that this configuration can communicate with any I²C compatible host.

The DRV pin is duty-cycled to minimize the power consumption of the MEMS Force sensor solution.



Figure 2: Reference Circuit

FT-701 PRODUCT BRIEF Rev B

5 | Page

## Page 6

qorvo

# 8.2 SENSOR SYSTEM STACK-UP

The FT-701 MEMS Force sensor does not require a point-load for actuation. Instead, the sensor may be pressed upon through a glass, metal, plastic, or any other surface material. The device is soldered onto a PCB, which is then bonded to the back of the touch surface where the force is to be detected. The FT-70 sensor can detect forces as light as a few grams up to tens of kilograms depending on the surface deflection. Figure 3 shows the stack-up for a single button application utilizing one MEMS Force sensor mounted to an PCB.

For detailed FPCB stack-up and recommended adhesives, please contact Qorvo, Inc. for Stack-Up application note.



Figure 3: Stack-Up

# 8.3 MEMS FORCE ANALOG FRONT-END (AFE) REFERENCES

Table 3 shows the Qorvo Ultra-low Power AFE with I²C Interface, the AF-301, which allows the FT-701 MEMS Force sensor to be connected to a host. For a list of recommended microcontroller reference designs contact Qorvo, Inc. More details about features, electrical characteristics, and applications information for the AF-301 can be obtained from its datasheet.

|  Vendor | Part Number | Package  |
| --- | --- | --- |
|  Qorvo | AF-301* | 9-pin CSP  |

* Qorvo's MEMS Force solution can work with any host

Table 3: MEMS Force Analog Front-End References

FT-701 PRODUCT BRIEF Rev B

6 | Page

## Page 7

qorvo

# 9. ELECTRICAL DESIGN, SENSOR PLACEMENT, HANDLING & PACKAGING INFORMATION

# 9.1 ELECTRICAL DESIGN

Although the FT-701 usually operates in a low-speed environment, it is recommended to follow best layout practices involving both sensitive sensor signal and high-speed design guidelines. This includes proper matching of sensor signal line lengths and balancing parasitic impacts on the differential sensor outputs.

The FT-701 sensor is a sensitive analog device and it is therefore recommended to reference any/all power on the sensor to a low-noise analog supply source. To achieve additional noise reduction, a differential capacitor with a value of 1 nF between SPOS and SNEG is recommended. For best noise rejection, place the differential capacitor close to the AFE and away from the sensor.

Note the digital power supply section requires two bypass capacitors, 2.2uF & 1nF to reduce noise on the power supply when using the AF-301. Ensure that both capacitors are placed as close to the AF-301 VDD pin as possible.

The GNDN and GNDP pins of the sensor must be connected via a 0 ohm resistor (R_G) directly to the grounded terminal of the bypass capacitors next to the AF-301. Resistor R_G represents a star ground connection and allows for a net name change. R_G and the bypass capacitors should be ≤ 3mm away from the AF-301.

Route high-speed digital signal traces away from the sensitive analog traces. Keep signal lines short and free of 90° turns (steep angles/corners can cause undesired acid traps during the manufacturing process). Use 45° turns or rounded-edge-turns for all signal/power lines when designing with the Qorvo force sensing solutions.

For Offset and TCO tuning using R_PV, R_PS, R_NS and R_NV, contact Qorvo, Inc.

FT-701 PRODUCT BRIEF Rev B

7 | Page

## Page 8

Qorvo

# 9.2 SENSOR PLACEMENT

- Do not use glue/epoxy under or around the sensor – MANDATORY.
- Symmetrical routing improves sensor self-alignment (Figure 4) during assembly – MANDATORY.



Figure 4: Examples of Symmetrical Routing

- Place the nearest components at least 0.3 mm away (RECOMMENDED) from the sensor.
- Place Sensor and AFE on the same PCB – RECOMMENDED.
- The FT-701 sensor center should be at least 0.25 mm from all edges of the PCB and 0.3 mm from nearest components – RECOMMENDED.
- Under-fill is not recommended. For harsh environments, please contact Qorvo for recommendations for under-fill and/or glob top.
- For additional stability consider implementing “teardrop” routing into vias, pin pads and T-junctions; this increases the copper area and avoids steep angles in areas where multiple traces meet in a common point.
- Route sensitive signal and power lines away from high-speed clock and interface lines.
- It is recommended to run the high-sensitivity FT-701 sensor from an on-board analog power supply (e.g. low-noise LDO) for lowest noise or DRV pin of a Qorvo AFE.
- Make the traces to all the six pins the same width.

FT-701 PRODUCT BRIEF Rev B

8 | Page

## Page 9

Qorvo

# 9.3 FOOTPRINT AND SMT DETAILS



Figure 5: Must-Have Footprint

Figure 5 depicts the must-have footprint drawing for the FT-701 and the details below must be followed for the SMT of the sensor onto a PCB

1. Pad dimensions and type
   a. Rounded rectangle with dimensions 7.874 mil x 7.874 mil (0.2 mm x 0.2 mm)
   b. Radius of the rounded square pad: Corner radius of 0.05mm (not a circular pad)
   c. Copper defined, not solder-mask defined
2. Solder paste stencil thickness: 4 mil (100 μm)
3. Solder mask: 2 mil (50 μm) wider on all sides of the pad
4. Solder Paste: Alpha OM 550 HRL1 (to reduce solution offset and TCO), SAC305 or SAC405 (for Alpha OM 550 use low temperature soldering profile as defined by solder paste vendor)

FT-701 PRODUCT BRIEF Rev B

9 | Page

## Page 10

Qorvo

# 9.4 SMT PICK & PLACE GUIDELINES

# 9.4.1 NOZZEL CONSIDERATIONS

SMT assembly machines typically employ a vacuum nozzle for Pick & Place (P&P) operations. Not all equipment is the same, but there are some general guidelines to follow, for optimal performance/yield.

1. Select a vacuum nozzle only.
   a. DO NOT use mechanical grippers or collets, that contact the edges/sides of a WLCSP.
   b. DO NOT handle WLCSP parts with metal tweezers.
2. Prefer softer nozzle materials.
   a. Nozzle materials can vary (metal, ceramic, plastic, rubber), and certain equipment requires certain nozzle materials. If there's a choice, try to select a softer material, to avoid potential damage from mechanical shocks.
3. Select an appropriate nozzle tip shape.
   a. Nozzle tip shape can affect the amount of pressure applied to a single point on a WLCSP part.
   b. Nozzle tips should be circular, square/rectangular, and preferably with a vertical separator.
   c. The nozzle tip surface should be a single plane; do not use a nozzle with a protruded edge

Acceptable



NOT Acceptable



Figure 6: Acceptable vs. NOT Acceptable Tip Shapes

4. Select an appropriate nozzle tip size, for the part being placed.
   a. The largest tip dimension should be smaller than the size of the WLCSP part.
   b. The tip should account for the tolerance of the pick accuracy, so that it's not possible for the nozzle tip to contact the edge or the corner of a part.
   c. The tip size should be as large as possible, while satisfying the above 2 points.

FT-701 PRODUCT BRIEF Rev B

10 | Page

## Page 11

Qorvo

### 9.4.2 PICK & PLACE OPERATION

The P&P operation consists of two key steps: picking a part out of the carrier tape pocket, and placement of that part onto a circuit board. Both operations are performed with some alignment tolerance: nozzle-to-part tolerance during the pick, and part-to-board alignment during the placement. Additionally, the placement should occur with as little force as possible, to press the die into place on the board.

WLCSP parts are shipped to customers in standard carrier tape & reel packaging. Parts sit in a pocket that is slightly larger than the size of the part. A part can move laterally inside the pocket, typically by less than 0.1 mm, but this varies by product.

1. If available, the P&P equipment should use a vision detection system to align the P&P nozzle to the center of the die, for every part picked.
2. If a vision alignment system isn't available, the nozzle size selection should account for the positional tolerance of the WLCSP part in the carrier tape pocket.

The die placement operation should be performed with a placement accuracy of better than 0.1 mm, but accuracies smaller than 0.05 mm are typical. The placement force should be as small as possible to make contact of the WLCSP solder bumps with the solder paste on the board.

1. A force contactless pickup is preferred, using only light physical contact, and allowing the vacuum to pick the part.
2. Prefer to use a "air-ejection" placement over a contact placement. A typical air-ejection pressure is 150 mbar.
3. If air placement isn't available, use a contact mode for the part placement. Ensure that both the pick and placement force is not larger than 2 N (200 gram). Placement forces should be measured periodically using a calibrated load, to ensure parts aren't placed with a force over this specification.

### 9.5 SENSOR HANDLING

- Do not pick up the device with metal tweezers. Use vacuum pickup head – MANDATORY.
- Do not "snap" panelized, assembled PCBs
- Follow ESD-safe handling recommendations
  - Store sensors in ESD sensitive containers (e.g. T&R, moisture-sealed)
  - Handle devices only in ESD-safe work areas
  - Persons /machines handling sensor must be grounded to avoid potential ESD damage
- Contact Qorvo on SMT guidelines and recommendations

FT-701 PRODUCT BRIEF Rev B

11 | Page

## Page 12

Qorvo

# 9.6 ASSEMBLY INSTRUCTIONS

The FT-701 MEMS Force sensor can be reflow-soldered using direct-chip-attachment (DCA) techniques to the circuit substrate. When using SAC305 or SAC405 solder paste, the sensors should be soldered at normal reflow (Table 4) temperatures designed to support RoHS and Pb-free compliance (Figure 7). Reflow assembly houses should follow this profile closely but can choose more conservative ramp-up/down rates. To avoid damage to the force sensor do not exceed the specified maximum ratings of the qualification profile (e.g. TPMAX = 260°C @ the top side of the CSP). Customers should consult with their assembly vendor for the appropriate reflow soldering profile. When using ALPHA low temperature solder paste, use the solder paste reflow profile from the solder paste vendor.



Figure 7: Pb-Free Soldering Profile for Reflow Assembly

|  Step | Parameter | Temperature [°C] | Time [s] | Maximum Rate [°C/s]  |
| --- | --- | --- | --- | --- |
|  A | TROOM | 25 |  |   |
|  B | TSMIN | 150 |  |   |
|  C | TSMAX | 200 | 60 < tBC < 120 |   |
|  D | TLIQUIDUS | 217 |  | r(TLIQUIDUS - TPMAX) < 3  |
|  E | TPMIN [255°C, 260°] | 255 |  | r(TLIQUIDUS - TPMAX) < 3  |
|  F | TPMAX [260°C, 265°C] | 260 | tAF < 480 | r(TLIQUIDUS - TPMAX) < 3  |
|  G | TPMIN [255°C, 260°] | 255 | 10 < tEG < 30 | r(TPMAX-TLIQUIDUS) < 2  |
|  H | TLIQUIDUS | 217 | 60 < tDH < 120 |   |
|  I | TROOM | 25 |  |   |

Table 4: Reflow Assembly Temperature Profile

FT-701 PRODUCT BRIEF Rev B

12 | Page

## Page 13

Qorvo

# 9.7 PACKAGING INFORMATION







Figure 8: Package Dimensions

|  Info for 0.77 mm x 1.17 mm x 0.220 mm (Nominal) CSP  |   |   |   |   |
| --- | --- | --- | --- | --- |
|  Symbol | Min. | Nom. | Max. | Notes  |
|  A | 0.190 | 0.220 | 0.250 | Overall height (including solder bump)  |
|  A1 | 0.055 | 0.070 | 0.085 | Solder bump height  |
|  A2 | 0.135 | 0.150 | 0.165 | Body thickness  |
|  D | 1.120 | 1.170 | 1.220 | Body size, Y  |
|  D1 | 0.790 | 0.800 | 0.810 | Solder bump footprint, Y  |
|  E | 0.720 | 0.770 | 0.820 | Body size, X  |
|  E1 | 0.390 | 0.400 | 0.410 | Solder bump footprint, X  |
|  6 |   |   |   | Number of solder bumps  |
|  a | 0.185 | 0.200 | 0.215 | Solder bump diameter; measured at the maximum solder bump diameter, Y  |
|  b | 0.185 | 0.200 | 0.215 | Solder bump diameter; measured at the maximum solder bump diameter, X  |
|  d | 0.390 | 0.400 | 0.410 | Solder bump pitch, Y  |
|  e | 0.390 | 0.400 | 0.410 | Solder bump pitch, X  |
|  f | 0.160 | 0.185 | 0.210 | Package edge to solder bump center  |

All dimensions are in mm unless otherwise specified; dimensions and tolerances conform to ANSI Y14.5M-1982.

Table 5: Package Dimensions

FT-701 PRODUCT BRIEF Rev B

13 | Page

## Page 14

Qorvo

### 9.8 SENSOR TOP MARK CODING

The FT-701 sensor top mark coding consists of 2 rows of letters and numbers printed on the top of the CSP package (Figure 9).



Figure 9: Top Laser Mark

### 9.9 SENSOR TAPE-AND-REEL (T&R) DETAILS/DIMENSIONS



Figure 10: Sensor Tape-and-Reel Dimensions

Note that all dimensions and tolerances in this tape-and-reel diagram (Figure 10) are specified in mm.

FT-701 PRODUCT BRIEF Rev B

14 | Page

## Page 15

Qorvo

Figures 11 depicts a tape reel sealed in an ESD-protective bag. The diameter of the sensor reel measures 7 inches (Radius = 3.5 inches) with reel thickness of 0.25 inches to comfortably host the tape. Each reel is stamped with the company logo, part number, lot number, and date code.



Figure 11: Example of Packaged Reel

## 10. RELIABILITY & ENVIRONMENTAL INFORMATION

The Qorvo FT-701 sensor meets Level 1 (unlimited) Moisture Sensitivity Level (MSL) specifications.

Reliability and Environmental reports are furnished upon request.

FT-701 PRODUCT BRIEF Rev B

15 | Page

## Page 16

## 11. REVISION HISTORY

|  REVISION NUMBER | REVISION DATE | DESCRIPTION/CHANGES | PAGES CHANGED  |
| --- | --- | --- | --- |
|  A | 11/18/2020 | New Release | N/A  |
|  B | 05/18/2022 | Added FT-701Y00 ordering part number. Removed references to deprecated NextInput branding, added pick & place guidelines | 1-15  |

FT-701 PRODUCT BRIEF Rev B

16 | Page
