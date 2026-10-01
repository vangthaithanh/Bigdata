# TV2 Handoff To TV4

TV2 completed analytics outputs for dashboard/reporting work.

## Final Dataset

- Population: `5000`
- RAW GB: `3.667`
- Silver GB: `0.412492`
- Gold MB: `8.819`

## Analytics Files

- `output/analytics/summary.json`
- `output/analytics/cost_by_encounter_class.json`
- `output/analytics/cost_by_gender.json`
- `output/analytics/top_conditions.json`

## KPI Meaning

- `total_patients`: distinct patient rows from final Silver patients.
- `total_encounters`: Gold encounter feature rows.
- `average_claim_cost`: average `total_claim_cost` in Gold.
- Cost by encounter class/gender: grouped average and total claim cost.
- Top conditions: most frequent Gold condition labels.

## Summary

- Total patients: `5715`
- Total encounters: `345487`
- Average claim cost: `2688.04622469141`
