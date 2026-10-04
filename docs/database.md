# Database Structure

This document is generated from the SQLAlchemy models in `app/models/` by
`python scripts/gen_db_docs.py` (a test fails if it drifts). The schema itself is created by
Alembic migrations (`alembic upgrade head`); PostgreSQL is the supported database. SQLite is used
only by the automated test suite.

Status columns are plain strings or booleans; blood request statuses and their allowed
transitions are defined in `app/core/request_status.py`.


## `address_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| address | VARCHAR(200) | no |  |
| pincode | VARCHAR(10) | no | indexed |
| country | VARCHAR(45) | no |  |
| state | VARCHAR(45) | no |  |
| city | VARCHAR(45) | no | indexed |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

## `admin_audit_log`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | INTEGER | no | primary key |
| admin_id | VARCHAR(36) | no | indexed |
| action | VARCHAR(50) | no | indexed |
| entity_type | VARCHAR(30) | no |  |
| entity_id | VARCHAR(100) | yes |  |
| detail | VARCHAR(255) | yes |  |
| created_at | DATETIME | no | indexed |

## `admin_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| email | VARCHAR(100) | no | unique |
| password | VARCHAR(250) | no |  |
| username | VARCHAR(45) | no |  |
| authentication_id | VARCHAR(36) | no | unique |
| vec_registration_number | VARCHAR(36) | no | unique |
| date_of_birth | DATE | no |  |
| mobile_number | VARCHAR(36) | no |  |
| department | VARCHAR(50) | yes |  |
| active_status | VARCHAR(36) | no | indexed |
| last_login_date | DATETIME | yes |  |
| approved_donation_count | INTEGER | no |  |
| closed_requests_count | INTEGER | no |  |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

## `authentication_details_admin`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | INTEGER | no | primary key |
| auth_id | VARCHAR(36) | no | indexed |
| name | VARCHAR(100) | no |  |
| login_date | DATE | no |  |
| login_time | TIME | no |  |

## `authentication_details_donor`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | INTEGER | no | primary key |
| auth_id | VARCHAR(36) | no | indexed |
| name | VARCHAR(100) | no |  |
| login_date | DATE | yes |  |
| login_time | TIME | yes |  |

## `blood_request_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| patient_name | VARCHAR(100) | no |  |
| blood_group | VARCHAR(10) | no | indexed |
| hospital_name | VARCHAR(100) | no |  |
| contact_number | VARCHAR(15) | no |  |
| patient_age | INTEGER | no |  |
| due_date | DATETIME | no | indexed |
| request_reason | VARCHAR(200) | yes |  |
| status | VARCHAR(45) | no | indexed |
| units_required | INTEGER | no |  |
| attendant_name | VARCHAR(100) | yes |  |
| hospital_id | VARCHAR(36) | no | FK -> `hospital_details.id` |
| response_id | VARCHAR(36) | no | FK -> `response_details.id` |
| approved_admin_id | VARCHAR(36) | yes |  |
| closed_admin_id | VARCHAR(36) | yes |  |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

## `disease_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| name | VARCHAR(100) | no |  |
| description | VARCHAR(200) | yes |  |

## `donor_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| name | VARCHAR(100) | no |  |
| email | VARCHAR(100) | no | unique |
| password | VARCHAR(500) | no |  |
| blood_group | VARCHAR(10) | no | indexed |
| active_status | BOOLEAN | no | indexed |
| authentication_id | VARCHAR(36) | no | unique |
| last_donated_date | DATETIME | yes |  |
| number_of_times_donated | INTEGER | no |  |
| last_login_date | DATETIME | yes |  |
| personal_details_id | VARCHAR(36) | no | FK -> `personal_details.id` |
| address_id | VARCHAR(36) | no | FK -> `address_details.id` |
| disease_id | VARCHAR(36) | no | FK -> `disease_details.id` |
| terms_and_conditions_id | VARCHAR(36) | no | FK -> `terms_and_conditions.id` |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

## `hospital_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| hospital_name | VARCHAR(100) | no | indexed |
| hospital_address | VARCHAR(200) | no |  |
| pincode | VARCHAR(10) | no | indexed |
| city | VARCHAR(45) | no | indexed |
| state | VARCHAR(45) | no |  |
| country | VARCHAR(45) | no |  |
| branch | VARCHAR(45) | yes |  |
| landmark | VARCHAR(100) | yes |  |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

## `otp_codes`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | INTEGER | no | primary key |
| purpose | VARCHAR(40) | no |  |
| email | VARCHAR(100) | no |  |
| otp_hash | VARCHAR(64) | no |  |
| expires_at | DATETIME | no | indexed |
| attempts | INTEGER | no |  |
| created_at | DATETIME | no |  |

## `personal_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| first_name | VARCHAR(45) | no |  |
| last_name | VARCHAR(45) | yes |  |
| age | INTEGER | no |  |
| date_of_birth | DATE | no |  |
| contact_number | VARCHAR(15) | no |  |
| secondary_contact_number | VARCHAR(15) | yes |  |
| marital_status | VARCHAR(10) | yes |  |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

## `query_table`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | INTEGER | no | primary key |
| user_name | VARCHAR(55) | no |  |
| user_email | VARCHAR(55) | no | indexed |
| admin_id | VARCHAR(55) | no | indexed |
| admin_name | VARCHAR(55) | no |  |
| user_query | VARCHAR(555) | yes |  |
| admin_response | VARCHAR(555) | yes |  |
| user_query_date | DATE | yes |  |
| admin_response_date | DATE | yes |  |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

## `refresh_sessions`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| jti | VARCHAR(36) | no | primary key |
| user_id | VARCHAR(36) | no | indexed |
| role | VARCHAR(10) | no |  |
| expires_at | DATETIME | no |  |
| revoked_at | DATETIME | yes |  |
| replaced_by | VARCHAR(36) | yes |  |
| created_at | DATETIME | no |  |

## `response_details`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| status | VARCHAR(45) | yes |  |
| report | VARCHAR(255) | yes |  |
| units_donated | INTEGER | yes |  |
| certificate_status | VARCHAR(36) | yes |  |
| donation_date | DATE | yes |  |
| donor_ids | VARCHAR(255) | yes |  |
| created_at | DATETIME | no |  |
| updated_at | DATETIME | yes |  |

Check constraints: `ck_response_details_units_donated_nonneg`

## `terms_and_conditions`

| Column | Type | Nullable | Notes |
| ------ | ---- | -------- | ----- |
| id | VARCHAR(36) | no | primary key |
| version | VARCHAR(20) | no |  |
| effective_date | DATE | no |  |
