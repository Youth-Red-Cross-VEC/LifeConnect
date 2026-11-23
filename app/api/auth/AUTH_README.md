# Authentication implementation notes

Authentication is implemented in `app/api/auth/` and uses HS256 JWTs through PyJWT. Decoding explicitly
allows only HS256 and requires `exp`. Access tokens include the user ID, email, user type, token version,
and expiration. The current account's token version and active status are checked against the database on
every protected request.

Passwords use the `bcrypt` package directly. Existing `$2b$` bcrypt hashes remain verifiable. New password
schemas reject passwords longer than 72 UTF-8 bytes before hashing; legacy scrypt hashes are upgraded after
a successful login.

Login responses return the access token in JSON and set the refresh token in an HttpOnly, SameSite=Strict
cookie. Development uses `lc_refresh_token` scoped to `/api/v1/auth`. HTTPS environments use
`__Host-lc_refresh_token` with Secure, Path=/ and no Domain attribute. After upgrading, existing
HTTPS browser sessions need a fresh login to obtain the host-bound cookie. Send an exact trusted
Origin or Content-Type: application/json on cookie-bearing refresh and logout calls. Refresh rotates its server-side
`refresh_tokens` row and cookie. Reuse revokes all sessions for that account. `POST /auth/logout` revokes
the presented cookie, and `POST /auth/logout-all` also increments the account token version.

Donor enrollment starts with `POST /api/v1/donors/register/code` and a JSON body containing
`email`. This operation sends a registration code without checking account membership. Submit the
code as `enrollment_code` alongside the donor details at `POST /api/v1/donors/register`. A valid
mailbox proof is required before the API reports an address conflict. Successful creation and
consumption of that proof commit together. Existing donors can continue to sign in normally.

A change of administrator role revokes existing access and refresh credentials. Sign in again
after promotion or demotion. Administrator management operations recheck the actor under a
database lock and protect the last active super administrator.

One-time codes are generated with `secrets.randbelow`, stored as an HMAC-SHA256 in `otp_codes`, and limited
to five attempts per active window by default. Failed password-reset and admin-invite confirmations also count against an hourly per-email budget in
`otp_failure_windows`. The nightly cleanup removes expired OTPs, expired or revoked refresh tokens, old OTP
failure windows, and certificates beyond their configured retention.

Runtime package versions are pinned in the root `requirements.txt`; install local test tools from
`requirements-dev.txt`.
