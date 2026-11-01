# Data Retention

**Status: DRAFT.** The "Proposed" periods below are recommendations that the YRC / college data owner
must approve (they may have legal or institutional requirements). Only the rows marked **Enforced** are
implemented in code today.

## What is stored

| Data | Table(s) | Personal / sensitive? | Retention today | Proposed |
| ---- | -------- | --------------------- | --------------- | -------- |
| Donor profile, contact, address, health notes | `donor_details`, `personal_details`, `address_details`, `disease_details` | Yes (health-adjacent) | Kept until manually deleted | Keep while the donor is registered; erase on request or after 3 years of inactivity |
| Donor login history | `authentication_details_donor` | Yes | Kept indefinitely | 12 months |
| Admin accounts and login history | `admin_details`, `authentication_details_admin` | Yes | Kept indefinitely | Keep while the admin is active; delete 12 months after deactivation |
| Blood requests (patient name, age, contact) | `blood_request_details`, `response_details` | Yes (patient data) | Kept indefinitely | Anonymize patient name, age and contact 12 months after the request is closed, declined or expired |
| Support queries | `query_table` | Yes (name, email; `donor_id` links a query to the donor who filed it while signed in, NULL for anonymous and pre-ownership rows) | Kept until an admin deletes them | 24 months after resolution |
| Admin audit trail | `admin_audit_log` | Identifiers only | Kept indefinitely (append-only) | 24 months |
| One-time codes | `otp_codes` | Hashed codes + email | **Enforced:** expire after `OTP_TTL_SECONDS` (default 10 min) and are purged daily | n/a |
| Refresh sessions | `refresh_sessions` | User id only | **Enforced:** expired rows purged daily (`purge_expired_auth_records`) | n/a |
| Generated certificates | files under `app/static` | Yes (donor name) | Kept until an admin deletes the file | Delete 12 months after generation; donors can be re-issued one |
| Logs | stdout | Masked emails, no exception text (see P1-28) | Set by the log platform | 90 days |

## Gaps to close once periods are approved

1. **Erasure on request**: there is no endpoint or script that deletes a donor and their related rows.
   Until one exists, an admin must delete them in the database by hand.
2. **Scheduled anonymization/purge** for the "Proposed" rows above. The scheduler (`SCHEDULER_ENABLED=true`
   on the dedicated process) is the place to run them; `purge_expired_auth_records` in
   `app/tasks/scheduled_jobs.py` is the pattern to follow. Make each period a setting, not a literal.
3. **Backups** keep deleted data until they rotate: state the backup retention next to the periods above.
4. **Legacy exposure**: real personal data from the old dump remains in git history until
   `docs/HISTORY_SCRUB.md` is carried out.

## Decisions needed from the data owner

- Are the proposed periods acceptable, or does a rule (hospital, state, college policy) require different ones?
- Who handles erasure requests, and what is the response deadline?
- Who may read `admin_audit_log`, and how often is it reviewed?
