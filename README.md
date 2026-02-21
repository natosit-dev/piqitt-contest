# MediLacra + PIQI Contest Prototype

Synthetic HL7 v2 message generator (ADT^A01, ORU^R01) used as the foundation
for an IRIS → FHIR → PIQI quality scoring and routing demo.

## Current scope
- Modular HL7 v2 generator
- ADT with vitals and gender identity OBXs
- ORU with radiology-style report text

## Next steps
- IRIS HL7 ingest
- HL7 → FHIR conversion
- PIQI evaluation and routing


Command to run the script:

python -m scripts.hl7_out_to_piqi `
--sam config/piqi_sam_library.yaml `
--profile config/profile_clinical_minimal.yaml `
--plausibility config/plausibility.yaml
