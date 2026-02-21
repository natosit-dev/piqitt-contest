# MediLacra + PIQI Contest Prototype

Synthetic HL7 v2 message generator (ADT^A01, ORU^R01) used as the foundation
for an IRIS → FHIR → PIQI quality scoring and routing demo.

Current scope
Modular HL7 v2 generator
ADT with vitals and gender identity OBXs
ORU with radiology-style report text
HL7 v2 to FHIR conversion
IRIS HL7 ingest
PIQI evaluation and routing based on PIQI score threshold


Command to run the HL7 v2 generation script:
python scripts_generate_hl7.py --n 10 --out out --per-encounter

Command to run the v2 to FHIR/PIQI conversion

python -m scripts.hl7_out_to_piqi `
--sam config/piqi_sam_library.yaml `
--profile config/profile_clinical_minimal.yaml `
--plausibility config/plausibility.yaml

Command to Summarize PIQI Scores:
python -m scripts.summarize_piqi_scores
