# TV2 Handoff To TV3

TV2 completed the data engineering handoff. TV3 receives the full Gold dataset and decides train/test split, model training, tuning, and evaluation.

## Gold Dataset

- Path: `/healthcare/gold/encounter_features`
- Rows: `345487`
- Size MB: `8.819`
- Validation: `PASS`

## Target

- `total_claim_cost`

## Features

- `age`
- `gender`
- `race`
- `ethnicity`
- `encounter_class`
- `payer`
- `condition`

## Artifacts

- `artifacts/handoff/feature_schema.json`
- `artifacts/handoff/data_profile.json`

No train/test split was created by TV2.
