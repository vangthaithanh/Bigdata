# Full Data Dictionary

## patients

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `Id` | `id` | `string` | `false` | PK; PK; joins encounters.patient | Gold feature/target |
| `BIRTHDATE` | `birthdate` | `date` | `true` | - | Gold feature/target |
| `DEATHDATE` | `deathdate` | `date` | `true` | - | Silver analytics/queryable |
| `SSN` | `ssn` | `string` | `true` | - | Silver analytics/queryable |
| `DRIVERS` | `drivers` | `string` | `true` | - | Silver analytics/queryable |
| `PASSPORT` | `passport` | `string` | `true` | - | Silver analytics/queryable |
| `PREFIX` | `prefix` | `string` | `true` | - | Silver analytics/queryable |
| `FIRST` | `first` | `string` | `true` | - | Silver analytics/queryable |
| `MIDDLE` | `middle` | `string` | `true` | - | Silver analytics/queryable |
| `LAST` | `last` | `string` | `true` | - | Silver analytics/queryable |
| `SUFFIX` | `suffix` | `string` | `true` | - | Silver analytics/queryable |
| `MAIDEN` | `maiden` | `string` | `true` | - | Silver analytics/queryable |
| `MARITAL` | `marital` | `string` | `true` | - | Silver analytics/queryable |
| `RACE` | `race` | `string` | `true` | - | Gold feature/target |
| `ETHNICITY` | `ethnicity` | `string` | `true` | - | Gold feature/target |
| `GENDER` | `gender` | `string` | `true` | - | Gold feature/target |
| `BIRTHPLACE` | `birthplace` | `string` | `true` | - | Silver analytics/queryable |
| `ADDRESS` | `address` | `string` | `true` | - | Silver analytics/queryable |
| `CITY` | `city` | `string` | `true` | - | Silver analytics/queryable |
| `STATE` | `state` | `string` | `true` | - | Silver analytics/queryable |
| `COUNTY` | `county` | `string` | `true` | - | Silver analytics/queryable |
| `FIPS` | `fips` | `string` | `true` | - | Silver analytics/queryable |
| `ZIP` | `zip` | `string` | `true` | - | Silver analytics/queryable |
| `LAT` | `lat` | `double` | `true` | - | Silver analytics/queryable |
| `LON` | `lon` | `double` | `true` | - | Silver analytics/queryable |
| `HEALTHCARE_EXPENSES` | `healthcare_expenses` | `double` | `true` | - | Silver analytics/queryable |
| `HEALTHCARE_COVERAGE` | `healthcare_coverage` | `double` | `true` | - | Silver analytics/queryable |
| `INCOME` | `income` | `bigint` | `true` | - | Silver analytics/queryable |

## encounters

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `Id` | `id` | `string` | `false` | PK; PK; joins conditions.encounter and claims.appointment_id | Gold feature/target |
| `START` | `start` | `timestamp` | `true` | - | Silver analytics/queryable |
| `STOP` | `stop` | `timestamp` | `true` | - | Silver analytics/queryable |
| `PATIENT` | `patient` | `string` | `false` | FK to patients.id | Gold feature/target |
| `ORGANIZATION` | `organization` | `string` | `true` | - | Silver analytics/queryable |
| `PROVIDER` | `provider` | `string` | `true` | - | Silver analytics/queryable |
| `PAYER` | `payer` | `string` | `true` | FK to payers.id | Gold feature/target |
| `ENCOUNTERCLASS` | `encounter_class` | `string` | `true` | - | Gold feature/target |
| `CODE` | `code` | `string` | `true` | - | Silver analytics/queryable |
| `DESCRIPTION` | `description` | `string` | `true` | - | Gold feature/target |
| `BASE_ENCOUNTER_COST` | `base_encounter_cost` | `double` | `true` | - | Silver analytics/queryable |
| `TOTAL_CLAIM_COST` | `total_claim_cost` | `double` | `true` | - | Gold feature/target |
| `PAYER_COVERAGE` | `payer_coverage` | `double` | `true` | - | Silver analytics/queryable |
| `REASONCODE` | `reason_code` | `string` | `true` | - | Silver analytics/queryable |
| `REASONDESCRIPTION` | `reason_description` | `string` | `true` | - | Gold feature/target |

## conditions

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `START` | `start` | `date` | `true` | - | Silver analytics/queryable |
| `STOP` | `stop` | `date` | `true` | - | Silver analytics/queryable |
| `PATIENT` | `patient` | `string` | `false` | FK to patients.id | Gold feature/target |
| `ENCOUNTER` | `encounter` | `string` | `false` | FK to encounters.id | Gold feature/target |
| `SYSTEM` | `system` | `string` | `true` | - | Silver analytics/queryable |
| `CODE` | `code` | `string` | `true` | - | Silver analytics/queryable |
| `DESCRIPTION` | `description` | `string` | `true` | - | Gold feature/target |

## claims

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `Id` | `id` | `string` | `false` | PK | Silver analytics/queryable |
| `PATIENTID` | `patient_id` | `string` | `false` | FK to patients.id | Silver analytics/queryable |
| `PROVIDERID` | `provider_id` | `string` | `true` | - | Silver analytics/queryable |
| `PRIMARYPATIENTINSURANCEID` | `primary_patient_insurance_id` | `string` | `true` | - | Silver analytics/queryable |
| `SECONDARYPATIENTINSURANCEID` | `secondary_patient_insurance_id` | `string` | `true` | - | Silver analytics/queryable |
| `DEPARTMENTID` | `department_id` | `bigint` | `true` | - | Silver analytics/queryable |
| `PATIENTDEPARTMENTID` | `patient_department_id` | `bigint` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS1` | `diagnosis1` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS2` | `diagnosis2` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS3` | `diagnosis3` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS4` | `diagnosis4` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS5` | `diagnosis5` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS6` | `diagnosis6` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS7` | `diagnosis7` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSIS8` | `diagnosis8` | `string` | `true` | - | Silver analytics/queryable |
| `REFERRINGPROVIDERID` | `referring_provider_id` | `string` | `true` | - | Silver analytics/queryable |
| `APPOINTMENTID` | `appointment_id` | `string` | `false` | FK to encounters.id | Silver analytics/queryable |
| `CURRENTILLNESSDATE` | `current_illness_date` | `timestamp` | `true` | - | Silver analytics/queryable |
| `SERVICEDATE` | `service_date` | `timestamp` | `true` | - | Silver analytics/queryable |
| `SUPERVISINGPROVIDERID` | `supervising_provider_id` | `string` | `true` | - | Silver analytics/queryable |
| `STATUS1` | `status1` | `string` | `true` | - | Silver analytics/queryable |
| `STATUS2` | `status2` | `string` | `true` | - | Silver analytics/queryable |
| `STATUSP` | `status_p` | `string` | `true` | - | Silver analytics/queryable |
| `OUTSTANDING1` | `outstanding1` | `double` | `true` | - | Silver analytics/queryable |
| `OUTSTANDING2` | `outstanding2` | `double` | `true` | - | Silver analytics/queryable |
| `OUTSTANDINGP` | `outstanding_p` | `double` | `true` | - | Silver analytics/queryable |
| `LASTBILLEDDATE1` | `last_billed_date_1` | `timestamp` | `true` | - | Silver analytics/queryable |
| `LASTBILLEDDATE2` | `last_billed_date_2` | `timestamp` | `true` | - | Silver analytics/queryable |
| `LASTBILLEDDATEP` | `last_billed_date_p` | `timestamp` | `true` | - | Silver analytics/queryable |
| `HEALTHCARECLAIMTYPEID1` | `healthcare_claim_type_id_1` | `bigint` | `true` | - | Silver analytics/queryable |
| `HEALTHCARECLAIMTYPEID2` | `healthcare_claim_type_id_2` | `bigint` | `true` | - | Silver analytics/queryable |

## claims_transactions

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `ID` | `id` | `string` | `false` | PK | Silver analytics/queryable |
| `CLAIMID` | `claim_id` | `string` | `false` | FK to claims.id | Silver analytics/queryable |
| `CHARGEID` | `charge_id` | `bigint` | `true` | - | Silver analytics/queryable |
| `PATIENTID` | `patient_id` | `string` | `false` | FK to patients.id | Silver analytics/queryable |
| `TYPE` | `type` | `string` | `true` | - | Silver analytics/queryable |
| `AMOUNT` | `amount` | `double` | `true` | - | Silver analytics/queryable |
| `METHOD` | `method` | `string` | `true` | - | Silver analytics/queryable |
| `FROMDATE` | `from_date` | `timestamp` | `true` | - | Silver analytics/queryable |
| `TODATE` | `to_date` | `timestamp` | `true` | - | Silver analytics/queryable |
| `PLACEOFSERVICE` | `place_of_service` | `string` | `true` | - | Silver analytics/queryable |
| `PROCEDURECODE` | `procedure_code` | `string` | `true` | - | Silver analytics/queryable |
| `MODIFIER1` | `modifier1` | `string` | `true` | - | Silver analytics/queryable |
| `MODIFIER2` | `modifier2` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSISREF1` | `diagnosis_ref_1` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSISREF2` | `diagnosis_ref_2` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSISREF3` | `diagnosis_ref_3` | `string` | `true` | - | Silver analytics/queryable |
| `DIAGNOSISREF4` | `diagnosis_ref_4` | `string` | `true` | - | Silver analytics/queryable |
| `UNITS` | `units` | `bigint` | `true` | - | Silver analytics/queryable |
| `DEPARTMENTID` | `department_id` | `bigint` | `true` | - | Silver analytics/queryable |
| `NOTES` | `notes` | `string` | `true` | - | Silver analytics/queryable |
| `UNITAMOUNT` | `unit_amount` | `double` | `true` | - | Silver analytics/queryable |
| `TRANSFEROUTID` | `transfer_out_id` | `string` | `true` | - | Silver analytics/queryable |
| `TRANSFERTYPE` | `transfer_type` | `string` | `true` | - | Silver analytics/queryable |
| `PAYMENTS` | `payments` | `double` | `true` | - | Silver analytics/queryable |
| `ADJUSTMENTS` | `adjustments` | `double` | `true` | - | Silver analytics/queryable |
| `TRANSFERS` | `transfers` | `double` | `true` | - | Silver analytics/queryable |
| `OUTSTANDING` | `outstanding` | `double` | `true` | - | Silver analytics/queryable |
| `APPOINTMENTID` | `appointment_id` | `string` | `false` | FK to encounters.id | Silver analytics/queryable |
| `LINENOTE` | `line_note` | `string` | `true` | - | Silver analytics/queryable |
| `PATIENTINSURANCEID` | `patient_insurance_id` | `string` | `true` | - | Silver analytics/queryable |
| `FEESCHEDULEID` | `fee_schedule_id` | `bigint` | `true` | - | Silver analytics/queryable |
| `PROVIDERID` | `provider_id` | `string` | `true` | - | Silver analytics/queryable |
| `SUPERVISINGPROVIDERID` | `supervising_provider_id` | `string` | `true` | - | Silver analytics/queryable |

## payers

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `Id` | `id` | `string` | `false` | PK; PK; joins encounters.payer | Gold feature/target |
| `NAME` | `name` | `string` | `true` | - | Gold feature/target |
| `OWNERSHIP` | `ownership` | `string` | `true` | - | Silver analytics/queryable |
| `ADDRESS` | `address` | `string` | `true` | - | Silver analytics/queryable |
| `CITY` | `city` | `string` | `true` | - | Silver analytics/queryable |
| `STATE_HEADQUARTERED` | `state_headquartered` | `string` | `true` | - | Silver analytics/queryable |
| `ZIP` | `zip` | `string` | `true` | - | Silver analytics/queryable |
| `PHONE` | `phone` | `string` | `true` | - | Silver analytics/queryable |
| `AMOUNT_COVERED` | `amount_covered` | `double` | `true` | - | Silver analytics/queryable |
| `AMOUNT_UNCOVERED` | `amount_uncovered` | `double` | `true` | - | Silver analytics/queryable |
| `REVENUE` | `revenue` | `double` | `true` | - | Silver analytics/queryable |
| `COVERED_ENCOUNTERS` | `covered_encounters` | `bigint` | `true` | - | Silver analytics/queryable |
| `UNCOVERED_ENCOUNTERS` | `uncovered_encounters` | `bigint` | `true` | - | Silver analytics/queryable |
| `COVERED_MEDICATIONS` | `covered_medications` | `bigint` | `true` | - | Silver analytics/queryable |
| `UNCOVERED_MEDICATIONS` | `uncovered_medications` | `bigint` | `true` | - | Silver analytics/queryable |
| `COVERED_PROCEDURES` | `covered_procedures` | `bigint` | `true` | - | Silver analytics/queryable |
| `UNCOVERED_PROCEDURES` | `uncovered_procedures` | `bigint` | `true` | - | Silver analytics/queryable |
| `COVERED_IMMUNIZATIONS` | `covered_immunizations` | `bigint` | `true` | - | Silver analytics/queryable |
| `UNCOVERED_IMMUNIZATIONS` | `uncovered_immunizations` | `bigint` | `true` | - | Silver analytics/queryable |
| `UNIQUE_CUSTOMERS` | `unique_customers` | `bigint` | `true` | - | Silver analytics/queryable |
| `QOLS_AVG` | `qols_avg` | `double` | `true` | - | Silver analytics/queryable |
| `MEMBER_MONTHS` | `member_months` | `bigint` | `true` | - | Silver analytics/queryable |

## medications

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `START` | `start` | `timestamp` | `true` | - | Silver analytics/queryable |
| `STOP` | `stop` | `timestamp` | `true` | - | Silver analytics/queryable |
| `PATIENT` | `patient` | `string` | `false` | FK to patients.id | Silver analytics/queryable |
| `PAYER` | `payer` | `string` | `true` | FK to payers.id | Silver analytics/queryable |
| `ENCOUNTER` | `encounter` | `string` | `false` | FK to encounters.id | Silver analytics/queryable |
| `CODE` | `code` | `string` | `true` | - | Silver analytics/queryable |
| `DESCRIPTION` | `description` | `string` | `true` | - | Silver analytics/queryable |
| `BASE_COST` | `base_cost` | `double` | `true` | - | Silver analytics/queryable |
| `PAYER_COVERAGE` | `payer_coverage` | `double` | `true` | - | Silver analytics/queryable |
| `DISPENSES` | `dispenses` | `bigint` | `true` | - | Silver analytics/queryable |
| `TOTALCOST` | `total_cost` | `double` | `true` | - | Silver analytics/queryable |
| `REASONCODE` | `reason_code` | `string` | `true` | - | Silver analytics/queryable |
| `REASONDESCRIPTION` | `reason_description` | `string` | `true` | - | Silver analytics/queryable |

## procedures

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `START` | `start` | `timestamp` | `true` | - | Silver analytics/queryable |
| `STOP` | `stop` | `timestamp` | `true` | - | Silver analytics/queryable |
| `PATIENT` | `patient` | `string` | `false` | FK to patients.id | Silver analytics/queryable |
| `ENCOUNTER` | `encounter` | `string` | `false` | FK to encounters.id | Silver analytics/queryable |
| `SYSTEM` | `system` | `string` | `true` | - | Silver analytics/queryable |
| `CODE` | `code` | `string` | `true` | - | Silver analytics/queryable |
| `DESCRIPTION` | `description` | `string` | `true` | - | Silver analytics/queryable |
| `BASE_COST` | `base_cost` | `double` | `true` | - | Silver analytics/queryable |
| `REASONCODE` | `reason_code` | `string` | `true` | - | Silver analytics/queryable |
| `REASONDESCRIPTION` | `reason_description` | `string` | `true` | - | Silver analytics/queryable |

## observations

| Source column | Silver column | Datatype | Nullable | PK/FK/join role | Downstream use |
| --- | --- | --- | --- | --- | --- |
| `DATE` | `date` | `timestamp` | `false` | - | Silver analytics/queryable |
| `PATIENT` | `patient` | `string` | `false` | FK to patients.id | Silver analytics/queryable |
| `ENCOUNTER` | `encounter` | `string` | `false` | FK to encounters.id | Silver analytics/queryable |
| `CATEGORY` | `category` | `string` | `true` | - | Silver analytics/queryable |
| `CODE` | `code` | `string` | `false` | - | Silver analytics/queryable |
| `DESCRIPTION` | `description` | `string` | `true` | - | Silver analytics/queryable |
| `VALUE` | `value` | `string` | `true` | - | Silver analytics/queryable |
| `UNITS` | `units` | `string` | `true` | - | Silver analytics/queryable |
| `TYPE` | `type` | `string` | `true` | - | Silver analytics/queryable |
