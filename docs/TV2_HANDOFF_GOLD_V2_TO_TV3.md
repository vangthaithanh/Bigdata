# TV2 Handoff - Gold v2 Feature Enrichment

## Dataset
- HDFS path: `hdfs://namenode:8020/healthcare/gold/encounter_features_v2`
- Local handoff path after export: `artifacts/handoff/encounter_features_v2/`
- Rows: `345487`
- Unique encounter_id: `345487`
- Target: `total_claim_cost`
- Size: `11.116 MB`

## Columns
- ID: `encounter_id`
- Base features: `age, gender, race, ethnicity, encounter_class, payer, condition`
- New numeric features: `condition_count, procedure_count, distinct_procedure_count, medication_count, distinct_medication_count, observation_count, encounter_duration_hours, prior_encounter_count, prior_inpatient_count, prior_emergency_count`
- Target: `total_claim_cost`

## Validation
- Status: `PASS`
- Duplicate encounter_id: `0`
- Null target: `0`
- Negative target: `0`
- Target mismatches vs Gold v1: `0`
- Null new numeric features: all zero
- Negative count/duration features: all zero

## Leakage Policy
No claim transaction financial totals or direct payment/coverage/outstanding fields were used.
Historical features use only encounters where `prior.start < current.start`.

## TV3 Notes
Use the same seed `42`, the same `70/15/15` split strategy, and compare Gold v1 vs Gold v2 using MAE, RMSE, R2, within_500_usd_rate, and within_1000_usd_rate.
