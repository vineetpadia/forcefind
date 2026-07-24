# Datasheet text extraction

- Document ID: `sha256-edaceca45180c16b`
- PDF: `datasheets/digikey/Tekscan__FLX-Datasheet-A301-RevJ__1d838b0c20.pdf`
- SHA-256: `edaceca45180c16bcd8a06e3a623d2ef16ab4d2c02a8fd44f8dfa57fddc5f28e`
- Manufacturers: Tekscan
- Indexed MPNs: 3
- Pages: 2
- Extraction method: `pymupdf_native_text`
- Native-text quality: `native_text_available`
- Mistral OCR status: `blocked_unauthorized` (API returned HTTP 401 on 2026-07-24)

This artifact contains native PDF text extraction. It is not represented as Mistral OCR output. Re-run with valid Mistral credentials to OCR page images and replace or supplement this text.

## Page 1

FlexiForce™Standard Model A301


      Actual size of sensor
                      14 mm
                          (.55 in.)                  The A301 is optimized for high volume manufacturing and is ideal for embedding
                                             into products and applications. This sensor is available off-the-shelf, ideal for
Sensing                            an easy proof of concept. The A301 can be used with our test & measurement,
 Area                                         prototyping, and embedding electronics, including the FlexiForce Sensor                                      25.4 mm
                                                (1 in.)          Characterization Kit, FlexiForce Prototyping Kit, FlexiForce Quickstart Board,
                                 and the ELF™ System*. You can also use your own electronics, or multimeter.


         6 mm
            (.25 in.)


 Benefits


  • Small size is ideal for    • Available with Enhanced        • Thin and Flexible              • Easy to Use
   prototyping and          Stability Series (ESS)             Easily integrates into tight      Compatible with a variety of
   integration             pressure sensitive ink for       spaces for non-intrusive         electronics and ready-to-use
                         high-temperature and high-    force measurement              for testing, prototyping, or
                                                        between mating surfaces.      embedding.                         humidity environments

 Physical Properties


 Thickness     0.203 mm (0.008 in.)                          Connector     2-pin Male Square Pin

 Length        25.4 mm (1 in.)**                               Substrate     Polyester

 Width         14 mm (0.55 in.)                                 Pin Spacing   2.54 mm (0.1 in.)

 Sensing Area  9.53 mm (0.375 in.) diameter


                                         *  Sensor will require an adapter/extender to connect to the ELF System. Contact your Tekscan representative for assistance.
                                        ** Length does not include pins. Please add approximately 6 mm (0.25 in.) for pin length for a total length of approximately
                                 32 mm (1.25 in).



                                                     Typical Performance                        Evaluation Conditions

                      Linearity (Error)                     < ±3% of full scale                        Line drawn from 0 to 50% load

                     Repeatability                            < ±2.5%                     Conditioned sensor, 80% of full force applied

                     Hysteresis                          < 4.5% of full scale                Conditioned sensor, 80% of full force applied

                        Drift                         < 5% per logarithmic time scale                 Constant load of 111 N (25 lb)

                  Response Time                           < 5µsec                  Impact load, output recorded on oscilloscope

                   Operating Temperature        -40°C - 60°C (-40°F - 140°F)             Convection and conduction heat sources

                      Durability                    ≥ 3 million actuations             Perpendicular load, room temperature, 22 N (5 lb)

                  Temperature Sensitivity           0.36%/°C (± 0.2%/°F)                          Conductive heating


                                           All data above was collected utilizing an Op Amp Circuit (shown on the next page).
                                       If your application cannot allow an Op Amp Circuit, visit www.tekscan.com/flexiforce-integration-guides,
                                                           or contact a FlexiForce Applications Engineer.


 SD_Rev J_121724                         ROHS COMPLIANT            ISO 9001:2008 Compliant & 13485:2016 Registered

## Page 2

Typical Performance


Standard Force Ranges                    † This sensor can measure up to 4,448 N (1,000 lb). To measure higher forces,
as Tested with Inverting             apply a lower drive voltage (-0.5 V, -0.25 V, etc.) and reduce the resistance of
Op-Amp Circuit                       the feedback resistor (1kΩ min.). To measure lower forces, apply a higher drive
4.4 N (0 - 1 lb)                        voltage and increase the resistance of the feedback resistor.
111 N (0 - 25 lb)                       Sensor output is a function of many variables, including interface materials.
445 N (0 - 100 lb) †                     Calibration is recommended. See FlexiForce Best Practices for details.



Recommended Circuit

       VOUT = -VREF * (RF / RS)
                             VDD = VSUPPLY         VREF
      Options   UpSquareto 5V,Wave50%    0.25VDC- 1.25V
                  Max Duty Cycle                        MCP6004
                                            VOUT

        RS                              -VREF
                                 VSS = Ground
      RFEEDBACK(RF) = 100kΩ
                         POTENTIOMETER                                 RFEEDBACK
     C1 = 47 pF
                                   C1
         100K potentiometer and 47 pF are
            general recommendations; your
                                               • Polarity of VREF must be opposite the polarity of VSUPPLY           speciﬁc sensor may be best suited
                                               • Sensor Resistance RS at no load is typically >1MΩ           with a different potentiometer and
                                               • Max recommended current is 2.5mA
                capacitor. Testing should be
            performed to determine this.





617.464.4500     1.800.248.3669     info@tekscan.com     tekscan.com                                                                             Contact us
                                                                                   for more information.
Sensor      Datasheet                      ©Tekscan                                           Inc., 2024.                                                            All rights                                                        reserved. Tekscan,                                                                       the Tekscan                                                                                          logo, and FlexiForce          Volume discounts available.SD_Rev       J_121724                        are trademarks                                         or registered                                                trademarks                                                                  of Tekscan,                                                                                    Inc.
