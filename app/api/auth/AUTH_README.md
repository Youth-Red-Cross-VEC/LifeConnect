# Authentication implementation notes

Authentication is implemented in `app/api/auth/` and uses HS256 JWTs through PyJWT. Decoding explicitly
allows only HS256 and requires `exp`. Access tokens include the user ID, email, user type, token version,
and expiration. The current account's token version and active status are checked against the database on
every protected request.

Passwords use the `bcrypt` package directly. Existing `$2b$` bcrypt hashes remain verifiable. New password
schemas reject passwords longer than 72 UTF-8 bytes before hashing; legacy scrypt hashes are upgraded after
a successful login.

Login responses return the access token in JSON and set the refresh token in an HttpOnly, SameSite=Strict
cookie scoped to `/api/v1/auth`. The cookie is Secure outside development. Refresh rotates its server-side
`refresh_tokens` row and cookie. Reuse revokes all sessions for that account. `POST /auth/logout` revokes
the presented cookie, and `POST /auth/logout-all` also increments the account token version.

One-time codes are generated with `secrets.randbelow`, stored as an HMAC-SHA256 in `otp_codes`, and limited
to five checks per code. Failed confirmations also count against an hourly per-email budget in
`otp_failure_windows`. The nightly cleanup removes expired OTPs, expired or revoked refresh tokens, old OTP
failure windows, and certificates beyond their configured retention.

Runtime package versions are pinned in the root `requirements.txt`; install local test tools from
`requirements-dev.txt`.
