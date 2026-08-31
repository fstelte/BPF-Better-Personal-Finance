# Data Backup & Recovery

Your financial data lives in the PostgreSQL database managed by Docker. Back it up regularly.

---

## Manual backup

### Export a database dump

```bash
docker compose exec postgres pg_dump \
  -U $POSTGRES_USER \
  $POSTGRES_DB \
  > backup-$(date +%Y%m%d-%H%M%S).sql
```

This creates a timestamped `.sql` file in your current directory containing the full database schema and data.

### Restore from a dump

```bash
docker compose exec -T postgres psql \
  -U $POSTGRES_USER \
  $POSTGRES_DB \
  < backup-20240115-143000.sql
```

> Run the API container with migrations disabled before restoring an older dump, or restore to a fresh database.

---

## Automated scheduled backup

The API includes a BullMQ backup job that can run on a schedule. Configure it in your `.env` file:

```env
BACKUP_CRON="0 3 * * *"        # Run at 03:00 every night
BACKUP_RETENTION_DAYS=30        # Keep the last 30 days of dumps
BACKUP_DEST=/data/backups       # Path inside the container
```

Mount a host directory for persistent storage in `docker-compose.yml`:

```yaml
services:
  api:
    volumes:
      - ./backups:/data/backups
```

The backup job writes compressed `.sql.gz` files and removes files older than `BACKUP_RETENTION_DAYS`.

---

## Off-site backup

For production use, ship backup files to an object store:

### AWS S3 example

```bash
aws s3 cp backup-$(date +%Y%m%d).sql s3://my-bucket/finance-backups/
```

Add this to a cron job on the host or in a CI pipeline.

### Rclone (Backblaze B2, Storj, etc.)

```bash
rclone copy ./backups remote:finance-backups
```

---

## Redis persistence

The Redis container is configured with append-only persistence (`--appendonly yes`). If the container restarts, the BullMQ job queue state is restored automatically from the AOF file.

Redis data is stored in the `redis_data` Docker volume. Back it up alongside the database using:

```bash
docker run --rm \
  -v better-personal-finance_redis_data:/data \
  -v $(pwd)/backups:/backup \
  alpine \
  tar czf /backup/redis-$(date +%Y%m%d).tar.gz /data
```

---

## GDPR / personal data export

To export all personal data stored for your account:

1. Go to **Settings → Data & Privacy**.
2. Click **Export my data**.
3. A JSON file is downloaded containing your profile, accounts, transactions, categories, budgets, and payee rules.

This is for personal use only and cannot be re-imported directly.

---

## Delete account

To permanently delete your account and all associated data:

1. Go to **Settings → Data & Privacy**.
2. Click **Delete my account**.
3. Confirm by typing your email address.

This action is irreversible and immediately removes all data from the database.

---

## Recovery checklist

If you need to restore to a new server:

1. Start dependency containers: `docker compose up -d postgres redis`
2. Restore the database dump (see above)
3. Start the API: `docker compose up -d api`
4. Run any pending migrations: `docker compose exec api pnpm db:migrate`
5. Start the web container: `docker compose up -d web caddy`
6. Verify the app loads and transactions are intact
