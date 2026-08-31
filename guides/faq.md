# Frequently Asked Questions

---

## Account & Login

### I forgot my password — how do I reset it?

Better Personal Finance is a self-hosted app with no email reset flow by default. A server administrator can reset it directly:

```bash
docker compose exec api node -e "
const bcrypt = require('bcryptjs');
bcrypt.hash('newpassword123', 12).then(h => console.log(h));
"
```

Then update the hash in the database:

```sql
UPDATE "User"
SET "passwordHash" = '\$2a\$12\$...'
WHERE email = 'your@email.com';
```

Run SQL via: `docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB`

---

### I can't log in — the page just reloads

1. Check that cookies are enabled in the browser.
2. Verify the session secret has not changed — changing `APP_SECRET` invalidates all sessions.
3. Check API logs: `docker compose logs api --tail 50`
4. Confirm the API is healthy: `curl -s http://localhost:3001/health`

---

### How do I reset my MFA (TOTP)?

If you have a backup code, enter it on the MFA prompt to get in. Then disable TOTP in **Settings → Security**.

If you have lost all factors, a server admin can clear MFA from the database:

```sql
UPDATE "User"
SET "totpSecret" = NULL, "totpEnabled" = false
WHERE email = 'your@email.com';
```

---

### Can multiple users share one installation?

Registration is one-time: only the first user can register. Multi-user support is not on the current roadmap. Each person in a household should run their own instance.

---

## Transactions & Import

### My CSV import fails — "Invalid date"

Ensure dates are in `YYYY-MM-DD` format. Open the file in a spreadsheet, format the date column as ISO 8601, and re-save as CSV.

### Imported transactions are not being categorised

1. Check that payee rules exist under **Payee Rules**.
2. Check the BullMQ job queue in the API logs: `docker compose logs api | grep auto-categoris`
3. Auto-categorisation runs asynchronously. Wait a few seconds and refresh the Transactions page.

### A transaction shows the wrong amount sign

Positive amounts are credits (money coming in); negative are debits (money going out). If your bank exports expenses as positive numbers, multiply the amount column by `-1` before importing.

---

## Budgets & Reports

### The CSV export is empty

Ensure the date range and account filter on the Reports page include the transactions you want. The export respects the active filters.

### "Copy from last month" does nothing

If no budget exists for the previous month, there is nothing to copy. Create the previous month's budget first, then use copy on the current month.

---

## Performance

### The app is slow to load

1. Verify at least 512 MB RAM is available to the Docker containers.
2. Check CPU: Next.js server-side rendering can spike CPU on first load in low-resource environments.
3. Run `ANALYZE` on the PostgreSQL database to refresh query planner statistics:
   ```sql
   ANALYZE;
   ```

### Transactions page hangs with thousands of rows

Use the date range and account filters to reduce the result set. The API paginates at 100 rows per page, so the issue is usually that many filtered pages are being loaded simultaneously.

---

## Deployment

### How do I update to a new version?

```bash
git pull
docker compose build
docker compose up -d
docker compose exec api pnpm db:migrate
```

### How do I back up my data?

See the [Data Backup guide](./data-backup.md).

### Can I run this without Docker?

Yes — see the [Getting Started guide](./getting-started.md) which covers running in development mode. For production without Docker, configure PostgreSQL and Redis externally and use a process manager like PM2 to run the API.

---

## Security

### Is my data encrypted at rest?

Database encryption at rest depends on your host OS / disk encryption (e.g. LUKS, FileVault, BitLocker). The application encrypts sensitive fields (encrypted notes, future OTP backup codes) using AES-256-GCM with the `ENCRYPTION_KEY` secret.

### Can the app be exposed directly to the internet?

The recommended topology is Caddy → Next.js → Fastify, with the API never directly exposed. Caddy handles TLS termination and provides automatic HTTPS certificates via Let's Encrypt.

### Where are session tokens stored?

Sessions are stored server-side in the PostgreSQL database. The browser receives a signed, HttpOnly cookie that contains only the session ID. There are no JWTs stored in localStorage.
