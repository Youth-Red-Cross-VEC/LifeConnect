# Data Retention

**Status: DRAFT.** The "Proposed" periods below are recommendations that the YRC / college data owner
must approve (they may have legal or institutional requirements). Only the rows marked **Enforced** are
implemented in code today.

## What is stored

| Data | Table(s) | Personal / sensitive? | Retention today | Proposed |
| ---- | -------- | --------------------- | --------------- | -------- |
| Donor profile, contact, address, health notes | `donor_details`, `personal_details`, `address_details`, `disease_details` | Yes (health-adjacent) | Removed on approved erasure when solely linked to that donor | Keep while registered; review inactivity after 3 years |
| Donor login history | `authentication_details_donor` | Yes | Removed with approved donor erasure | 12 months |
| Admin accounts and login history | `admin_details`, `authentication_details_admin` | Yes | Kept indefinitely | Keep while the admin is active; delete 12 months after deactivation |
| Blood requests (patient name, age, contact) | `blood_request_details`, `response_details` | Yes (patient data) | Kept indefinitely | Anonymize patient name, age and contact 12 months after the request is closed, declined or expired |
| Support queries | `query_table` | Yes (contact and free text) | Owned queries are removed on approved donor erasure. Anonymous and legacy queries need separate identity verification. | 24 months after resolution |
| Admin audit trail | `admin_audit_log` | Admin identifiers and operational metadata. Legacy certificate filenames can contain names. | Kept indefinitely. Approved erasure redacts matching donor identifiers and certificate filenames while preserving event history. | 24 months |
| One-time codes | `otp_codes` | Hashed codes + email | **Enforced:** expire after `OTP_TTL_SECONDS` (default 10 min) and are purged daily | n/a |
| OTP failure windows | `otp_failure_windows` | Email + failed attempt count | **Enforced:** one-hour failure budget; expired windows purged daily | n/a |
| Refresh tokens | `refresh_tokens` | User id only | **Enforced:** expired rows purged daily; revoked rows retained until expiry for replay detection (`purge_expired_auth_records`) | n/a |
| Generated certificates | files under `app/static` | Yes (donor name) | **Enforced:** identified files are blocked immediately after approval and queued for the existing daily cleanup. Other files expire after `CERT_RETENTION_DAYS` (default 30 days). | n/a |
| Erasure receipts | `erasure_requests` | Pending and most recent declined receipt link to the donor. Completed receipts retain only the reference, timestamps and outcome. | Retained for case handling. | Data owner to approve |
| Certificate cleanup queue | `erasure_files` | Identified filenames may include a donor name | Removed after successful deletion or when the file is already absent | Existing scheduler retries failures |
| Logs | stdout | Masked emails, no exception text (see P1-28) | Set by the log platform | 90 days |

## Gaps to close once periods are approved

1. Donors submit requests under **Account privacy** with their current password. Super administrators review
   the request under **Review erasure requests**, check holds and independent records, and deliberately approve
   or decline. Approval removes the account and sessions and clears donor links and free text on associated
   donation responses. It preserves request outcomes, unit totals, unrelated donor IDs and patient records.
2. For patient, anonymous support, inactive donor or shared legacy records, verify identity and authority
   separately through the college's approved channel. Confirm the record and any hold before a reviewed,
   case-specific removal or anonymization. A donor ID, display name, phone or unauthenticated email match
   cannot establish ownership of these records. Unlinked historical certificates, mail already delivered,
   application logs and exported copies need separate review. Never guess ownership from a filename.
3. Scheduled purges for the proposed periods require owner approval. The workflow schedules file removal only
   when an individual erasure request has already been approved. Monitor scheduler failures and verify
   cleanup completion before representing the case as complete.
4. Legacy exposure remains in repository history until
   `docs/HISTORY_SCRUB.md` is carried out.

## Backup retention and restore proposal

Proposed backup retention is 30 days, subject to data-owner sign-off and documented exceptions for holds.
Encrypt database, certificate and export backups, limit access, and document each copy and its expiry. Delete
storage versions, snapshots, replicas and retired export media under the approved lifecycle process. Backups
subject to a hold remain isolated and restricted. Avoid creating new ad hoc copies of erased records.

Until the last recoverable backup expires, keep a separate, restricted erasure register with only the record
identifiers necessary to replay approved removals. The data owner should assign responsibility for recording
these identifiers at review and deleting the register entries after the last relevant backup expires. Restore
into an isolated environment, replay and verify the approved erasures and revoke restored sessions before
serving traffic. Record the verification date, responsible operator and outcome. Do not restore an erased
account to reverse an application rollback.

## Reliability verification

Cleanup preserves unexpired revoked refresh records so rotation replay detection can revoke successor sessions. OTP and failure-window removal uses the same inclusive expiry boundary as validation. Certificate cleanup retains unresolved removal entries and uses the existing configured cutoff for recognized private files. Repeated cleanup is safe when a file is already absent. Database job failure rolls back the transaction. PostgreSQL advisory locks serialize duplicate scheduled jobs.

## Decisions needed from the data owner

- Are the proposed periods acceptable, or does a rule (hospital, state, college policy) require different ones?
- Who handles erasure requests, and what is the response deadline?
- Who may read `admin_audit_log`, and how often is it reviewed?
