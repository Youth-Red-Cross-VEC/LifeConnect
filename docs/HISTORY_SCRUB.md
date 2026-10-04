# Scrubbing personal data from git history

`source_db.sql` (a MySQL dump with real donor/admin names, emails, phone numbers, addresses,
dates of birth, Aadhaar numbers and password hashes) was committed in the past. Older versions of
`docs/initial_data.sql` and `docs/SyntheticData.sql` also contained a real admin email and password hash.
Removing the files from the current tree does **not** remove them from history, forks or clones.

The repo-side fix (synthetic seed data, `.gitignore` entries) is already committed. The steps below
rewrite history and must be run **manually, by you**, because they are destructive and force-push.

## 0. Before you start
- Tell all teammates to push or stash their work; everything they have locally will diverge.
- Make a backup: `git clone --mirror <remote-url> lifeconnect-backup.git`
- Install git-filter-repo: `pip install git-filter-repo`

## 1. Fresh mirror clone (filter-repo refuses to run on a used clone)
```bash
git clone --mirror https://github.com/Youth-Red-Cross-VEC/LifeConnect.git lifeconnect-scrub.git
cd lifeconnect-scrub.git
```

## 2. Remove the dump from every commit
```bash
git filter-repo --path source_db.sql --invert-paths
```

## 3. Redact real values that appear in older revisions of the docs SQL files
Build `replacements.txt` from the OLD dump / old docs files (one literal per line, then `==>REDACTED`).
Include every real email, phone number and password hash that was ever committed. Example format:
```
siddharthmagesh007@gmail.com==>redacted@example.com
siddha2234@gmail.com==>redacted2@example.com
regex:scrypt:32768:8:1\$[A-Za-z0-9]+\$[0-9a-f]+==>REDACTED_HASH
```
Then:
```bash
git filter-repo --replace-text replacements.txt
```
(Do not commit `replacements.txt`; it contains the real values.)

## 4. Verify
```bash
git log --all --oneline -- source_db.sql        # must print nothing
git grep -I -n -E "scrypt:32768|siddharthmagesh007|siddha2234" $(git rev-list --all) | head   # must print nothing
```

## 5. Push the rewritten history (this is the force-push; only you should run it)
```bash
git remote add origin https://github.com/Youth-Red-Cross-VEC/LifeConnect.git
git push --force --all
git push --force --tags
```
Branches affected: `main`, `development`, `fullstack-merge`, `old-copy` and any others.

## 6. After the force-push - checklist
- [ ] Ask GitHub Support to purge cached views / dangling commits and PR refs (`refs/pull/*`) that still hold the old blobs.
- [ ] **Rotate the exposed admin password** and any account whose password hash was in the dump (the legacy scrypt hashes can be brute-forced offline). Reset the affected users' passwords.
- [ ] **Invalidate all sessions**: change `SECRET_KEY` in every environment (all issued JWTs become invalid), and once refresh sessions exist (P1-13) revoke them all.
- [ ] Rotate any other secret that ever appeared in history (SMTP password, Google Maps key, reCAPTCHA secret). Check with `gitleaks detect` or `trufflehog git file://.`.
- [ ] Tell every teammate to **delete their old clones and re-clone**. Do not merge or rebase old branches into the new history (that reintroduces the data).
- [ ] Anyone who forked the repo still has the old history; ask them to delete the fork or treat the data as public.
- [ ] Decide whether affected donors must be notified (privacy/legal obligation: personal data, Aadhaar numbers, health data).
- [ ] Delete the local `source_db.sql` copy and any backups on shared drives.
