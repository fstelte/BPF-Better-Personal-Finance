# Docker Production Deployment

This guide covers everything needed to deploy **Better Personal Finance** on a Linux server using Docker Compose — from provisioning a server through day-two operations such as updates, backups, and incident response.

Two deployment modes are supported:

| Mode | When to use | Entry point |
|------|-------------|-------------|
| **Standalone** | You want a self-contained stack with automatic HTTPS | Bundled Caddy on ports 80 & 443 |
| **Behind external proxy** | You already run nginx, Traefik, Caddy, etc. | Your existing proxy forwards to the web container |

---

## Table of contents

1. [Server requirements](#1-server-requirements)
2. [Install Docker](#2-install-docker)
3. [Configure the firewall](#3-configure-the-firewall)
4. [Get the source code](#4-get-the-source-code)
5. [Configure environment variables](#5-configure-environment-variables)
6. [Standalone deployment (bundled Caddy)](#6-standalone-deployment-bundled-caddy)
7. [Behind an external reverse proxy](#7-behind-an-external-reverse-proxy)
8. [First run and onboarding](#8-first-run-and-onboarding)
9. [Health checks](#9-health-checks)
10. [Logs](#10-logs)
11. [Updating to a new version](#11-updating-to-a-new-version)
12. [Rollback](#12-rollback)
13. [Backups](#13-backups)
14. [Admin operations](#14-admin-operations)
15. [Networking architecture](#15-networking-architecture)
16. [Security hardening checklist](#16-security-hardening-checklist)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Server requirements

### Minimum hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPUs |
| RAM | 1 GB | 2 GB |
| Disk | 10 GB SSD | 20 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

> **Note:** RAM is the most common bottleneck. Next.js server-side rendering and PostgreSQL both benefit from additional memory. Budget 2 GB for comfortable operation.

### Domain and DNS (standalone mode only)

- A registered domain name (e.g. `finance.example.com`)
- An **A record** pointing to the server's public IP address
- DNS propagation must complete before Caddy can obtain a TLS certificate

Verify with:

```bash
dig +short finance.example.com
# Should return your server's IP
```

### Port requirements

| Port | Protocol | Required for |
|------|----------|-------------|
| 22 | TCP | SSH access |
| 80 | TCP | Caddy HTTP challenge (Let's Encrypt) — standalone only |
| 443 | TCP | HTTPS traffic — standalone only |
| `WEB_PORT` | TCP | External proxy mode only (default 3000, internal only) |

In external proxy mode, `WEB_PORT` must **not** be reachable from the public internet — only from your proxy host. See [section 3](#3-configure-the-firewall).

---

## 2. Install Docker

If Docker is not already installed:

```bash
# Install using the official convenience script
curl -fsSL https://get.docker.com | sh

# Add your user to the docker group (avoids running docker as root)
sudo usermod -aG docker $USER

# Activate the new group without logging out
newgrp docker

# Verify
docker version
docker compose version
```

Docker Compose v2 is bundled with Docker Engine 24+. Legacy `docker-compose` (v1) is not supported.

---

## 3. Configure the firewall

### Standalone mode (UFW example)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # Caddy HTTP challenge
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
sudo ufw status verbose
```

### External proxy mode

Allow SSH and the web port only from your proxy host's IP (`<PROXY_IP>`):

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow from <PROXY_IP> to any port 3000 proto tcp
sudo ufw enable
```

> **Important:** Never expose PostgreSQL (5432) or Redis (6379) to the internet. Those ports are not published by the compose file in production — this is an additional firewall defence in depth.

---

## 4. Get the source code

```bash
git clone https://github.com/your-username/better-personal-finance.git
cd better-personal-finance
```

All subsequent commands assume you are in the project root (`better-personal-finance/`).

---

## 5. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in every value. The sections below explain each variable.

### Generating secrets

Never reuse development secrets in production. Generate each one independently:

```bash
# 256-bit hex string (use for APP_SECRET, ENCRYPTION_KEY, AUTH_SECRET)
openssl rand -hex 32

# 32-character alphanumeric (use for POSTGRES_PASSWORD, REDIS_PASSWORD)
openssl rand -base64 32 | tr -d '/+=\n' | head -c 32

# Node.js alternative (no openssl required)
node -e "process.stdout.write(require('crypto').randomBytes(32).toString('hex'))"
```

Run the command **three separate times** for at minimum `APP_SECRET`, `ENCRYPTION_KEY`, and `AUTH_SECRET` — never share the same value across fields.

### Full environment variable reference

#### Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | Yes | — | Must be `production` |
| `PORT` | No | `4000` | Port the API listens on inside the container |
| `LOG_LEVEL` | No | `info` | Pino log level: `fatal` `error` `warn` `info` `debug` `trace` |
| `LOG_PRETTY` | No | — | Set to `true` for human-readable logs (not recommended in production) |

#### Deployment / routing

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOMAIN` | Standalone | — | Domain name for the bundled Caddyfile (e.g. `finance.example.com`). Not needed in external proxy mode. |
| `WEB_ORIGIN` | External proxy | — | Full public URL the browser uses: `https://finance.example.com`. Must match your proxy's public URL exactly (scheme + host, no trailing slash). In standalone mode this is derived automatically from `DOMAIN`. |
| `WEB_PORT` | External proxy | `3000` | Host port your proxy forwards to. |

#### Secrets

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_SECRET` | Yes | 256-bit hex — signs and verifies session cookies. Changing this invalidates all active sessions. |
| `ENCRYPTION_KEY` | Yes | 256-bit hex — AES-256-GCM key used to encrypt TOTP secrets at rest. Changing this makes all existing TOTP enrollments unreadable. |
| `AUTH_SECRET` | Yes | 256-bit hex — additional signing secret for the auth layer. |
| `SESSION_MAX_AGE_SECONDS` | No | `3600` | Absolute session lifetime in seconds. Sessions are sliding by default; this is the maximum age. |

#### PostgreSQL

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_DB` | Yes | Database name (e.g. `finance`) |
| `POSTGRES_USER` | Yes | Database user (e.g. `finance_user`) |
| `POSTGRES_PASSWORD` | Yes | Database password — generate with `openssl rand -base64 32 \| tr -d '/+=\n' \| head -c 32` |
| `POSTGRES_HOST` | No | `postgres` (Docker service name — do not change unless connecting externally) |
| `POSTGRES_PORT` | No | `5432` |
| `DATABASE_URL` | No | Auto-composed by Docker Compose from the `POSTGRES_*` variables. Only set manually if connecting from outside Docker (e.g. running Prisma Studio locally). |

#### Redis

| Variable | Required | Description |
|----------|----------|-------------|
| `REDIS_PASSWORD` | Yes | Redis password — generate with `openssl rand -base64 32 \| tr -d '/+=\n' \| head -c 32` |
| `REDIS_HOST` | No | `redis` (Docker service name) |
| `REDIS_PORT` | No | `6379` |
| `REDIS_URL` | No | Auto-composed by Docker Compose. Only set manually for external connections. |

#### Email (optional)

Email is not required for core functionality today but is used by future password-reset flows.

| Variable | Required | Description |
|----------|----------|-------------|
| `SMTP_HOST` | No | SMTP server hostname |
| `SMTP_PORT` | No | SMTP port (typically 587 for STARTTLS) |
| `SMTP_USER` | No | SMTP login username |
| `SMTP_PASS` | No | SMTP password |

### Example minimal `.env` for standalone mode

```bash
NODE_ENV=production
DOMAIN=finance.example.com

APP_SECRET=<output of openssl rand -hex 32>
ENCRYPTION_KEY=<output of openssl rand -hex 32>
AUTH_SECRET=<output of openssl rand -hex 32>

POSTGRES_DB=finance
POSTGRES_USER=finance_user
POSTGRES_PASSWORD=<output of openssl rand -base64 32 | tr -d /+=\n | head -c 32>

REDIS_PASSWORD=<output of openssl rand -base64 32 | tr -d /+=\n | head -c 32>
```

---

## 6. Standalone deployment (bundled Caddy)

This mode is the simplest path to production. Caddy handles TLS automatically via Let's Encrypt — no certificate management required.

### Prerequisites

- `.env` is filled in with `DOMAIN` set
- DNS A record for your domain points to this server
- Ports 80 and 443 are open in the firewall

### Start the stack

```bash
docker compose up -d --build
```

Docker Compose will:

1. Build the API and web Docker images from source
2. Pull the PostgreSQL 16 and Redis 7 images
3. Start PostgreSQL and wait for it to pass its health check
4. Run `prisma migrate deploy` in the `migrate` service (exits after completion)
5. Start the Fastify API (waits for `migrate` to succeed)
6. Start the Next.js web app (waits for the API)
7. Start Caddy, which obtains a TLS certificate from Let's Encrypt and begins serving HTTPS traffic

The first startup may take 2–4 minutes to build images and obtain the certificate.

### Verify the stack

```bash
# All services should show "running" (migrate will show "exited 0")
docker compose ps

# Follow all logs in real time
docker compose logs -f

# Follow a specific service
docker compose logs -f api
docker compose logs -f web
docker compose logs -f caddy
```

Once running, open `https://finance.example.com` in your browser. You should see the login page.

---

## 7. Behind an external reverse proxy

Use this mode when you already operate a reverse proxy (nginx, Traefik, Caddy instance, etc.) on the same host or a separate gateway.

### What changes

- The bundled Caddy service is disabled (it is assigned a profile that is never activated)
- The `web` container exposes a port on the Docker host (`WEB_PORT`)
- Your external proxy forwards requests to `http://<docker-host>:<WEB_PORT>`
- You set `WEB_ORIGIN` instead of `DOMAIN`

### Start the stack

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.external-proxy.yml \
  up -d --build
```

### Required additions to `.env`

```bash
# Full public URL the browser uses (scheme + host, no trailing slash)
WEB_ORIGIN=https://finance.example.com

# Port the web container exposes on the Docker host
WEB_PORT=3000
```

### nginx configuration example

```nginx
server {
    listen 443 ssl http2;
    server_name finance.example.com;

    ssl_certificate     /etc/letsencrypt/live/finance.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/finance.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options    "nosniff"                                      always;
    add_header X-Frame-Options           "DENY"                                         always;
    add_header Referrer-Policy           "strict-origin-when-cross-origin"              always;

    location / {
        proxy_pass         http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host       $host;
        proxy_set_header   X-Real-IP  $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name finance.example.com;
    return 301 https://$host$request_uri;
}
```

### Traefik configuration example

Add labels to the `web` service in a `docker-compose.override.yml`:

```yaml
services:
  web:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.finance.rule=Host(`finance.example.com`)"
      - "traefik.http.routers.finance.entrypoints=websecure"
      - "traefik.http.routers.finance.tls.certresolver=letsencrypt"
      - "traefik.http.services.finance.loadbalancer.server.port=3000"
```

---

## 8. First run and onboarding

On first visit, the application detects that no users exist and redirects to the onboarding wizard at `/onboarding`.

1. **Create your account** — enter your name, email address, and a password (minimum 12 characters).
2. **Add your first account** — e.g. "Main Checking" with your current bank balance as the opening balance.
3. The wizard completes and you land on the dashboard.

Registration is one-time: only the first user can create an account through the UI. Subsequent registrations are blocked. Each member of a household should run a separate instance.

> **Tip:** After creating your account, set up MFA immediately. See the [MFA setup guide](./mfa-setup.md).
>
> **Tip:** To let yourself (or others) sign in via Entra ID or another OIDC provider instead of just a password, see the [OIDC login setup guide](./oidc-setup.md).

---

## 9. Health checks

The API exposes a health endpoint used by Docker's own health check and by your monitoring system:

```
GET /health
```

Expected response (HTTP 200):

```json
{ "status": "ok" }
```

Check it from the host:

```bash
# Via the internal Docker network (preferred — does not require Caddy to be up)
docker compose exec api wget -qO- http://localhost:4000/health

# Via the public URL
curl -sf https://finance.example.com/health
```

### Watching Docker health status

```bash
docker inspect --format='{{.State.Health.Status}}' better-personal-finance-api-1
```

Possible values: `starting`, `healthy`, `unhealthy`.

### Monitoring integration

Point any HTTP monitor (UptimeRobot, Uptime Kuma, Healthchecks.io, etc.) at your `/health` URL with a 30-second check interval. Alert on non-200 responses or latency > 5 s.

If you run Prometheus, the API logs structured JSON which can be scraped via a log-based exporter (e.g. promtail + Loki).

---

## 10. Logs

All services write structured JSON logs to stdout, captured by Docker's log driver.

### View logs

```bash
# All services, last 100 lines
docker compose logs --tail 100

# Follow a specific service in real time
docker compose logs -f api
docker compose logs -f web
docker compose logs -f postgres
docker compose logs -f caddy

# Filter API logs to errors only
docker compose logs api 2>&1 | grep '"level":50'
```

Log levels in the Pino JSON format: `10`=trace, `20`=debug, `30`=info, `40`=warn, `50`=error, `60`=fatal.

### Log rotation

Docker's default `json-file` driver accumulates logs indefinitely. Configure rotation in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
```

Restart the Docker daemon to apply:

```bash
sudo systemctl restart docker
```

Alternatively, configure per-service in `docker-compose.yml` using the `logging:` key.

---

## 11. Updating to a new version

### Standalone

```bash
# Pull latest source
git pull

# Rebuild images and restart updated services
docker compose up -d --build
```

### External proxy

```bash
git pull
docker compose \
  -f docker-compose.yml \
  -f docker-compose.external-proxy.yml \
  up -d --build
```

### What happens on update

1. Docker builds new images from the updated source
2. The `migrate` service runs `prisma migrate deploy` — any new schema migrations are applied automatically before the API starts
3. Services restart one by one with zero manual intervention required

> **Best practice:** Take a database backup before upgrading:
> ```bash
> docker compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB \
>   > backup-before-upgrade-$(date +%Y%m%d-%H%M%S).sql
> ```

---

## 12. Rollback

If an update introduces a regression, roll back to the previous commit and restart:

```bash
# Find the previous good commit
git log --oneline -10

# Reset to it (replace <sha> with the commit hash)
git checkout <sha>

# Rebuild and restart
docker compose up -d --build
```

### Database rollback

Prisma does not support automatic migration rollback. If a migration must be reversed:

1. Restore the pre-upgrade database dump (see [section 13](#13-backups)):
   ```bash
   docker compose exec -T postgres psql \
     -U $POSTGRES_USER $POSTGRES_DB \
     < backup-before-upgrade-20260101-120000.sql
   ```
2. Return to the previous code version as above.

> **Important:** Restoring a database dump is destructive. It replaces all current data. Only restore if you are certain the migration cannot be fixed forward.

---

## 13. Backups

See the full [Data Backup guide](./data-backup.md) for automated backups, off-site storage, and recovery procedures.

### Quick manual database dump

```bash
docker compose exec postgres pg_dump \
  -U $POSTGRES_USER $POSTGRES_DB \
  > backup-$(date +%Y%m%d-%H%M%S).sql
```

### Restore from a dump

```bash
docker compose exec -T postgres psql \
  -U $POSTGRES_USER $POSTGRES_DB \
  < backup-20260101-120000.sql
```

### Minimum backup schedule

| What | How often | Where |
|------|-----------|-------|
| PostgreSQL dump | Daily | Local + off-site (S3, B2, etc.) |
| `redis_data` volume | Weekly | Local + off-site |
| `.env` file | On change | Off-site (encrypted) |

> **Never store `.env` unencrypted alongside your backups.** Use `gpg --symmetric` or your secret manager.

---

## 14. Admin operations

### Access the PostgreSQL shell

```bash
docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB
```

### Reset a user's password

Generate a new bcrypt hash and update the database:

```bash
# Generate hash (cost factor 12)
docker compose exec api node -e \
  "const b=require('bcryptjs');b.hash('NewPassword123!',12).then(h=>console.log(h));"

# Apply it
docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB -c \
  "UPDATE \"User\" SET \"passwordHash\" = '<hash>' WHERE email = 'user@example.com';"
```

### Reset MFA for a user who has lost all factors

```bash
docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB <<'SQL'
UPDATE "User"
SET "totpSecret" = NULL,
    "totpEnabled" = false
WHERE email = 'user@example.com';

DELETE FROM "Passkey"
WHERE "userId" = (SELECT id FROM "User" WHERE email = 'user@example.com');
SQL
```

The user can then log in with their password alone and re-enroll MFA.

### Invalidate all active sessions (forced re-login)

```bash
docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB -c \
  'TRUNCATE "Session";'
```

Use this if `APP_SECRET` has been rotated or a security incident has occurred.

### Run a one-off database migration

```bash
docker compose run --rm migrate
```

### Open Prisma Studio (from your workstation)

Requires a local pnpm install and `DATABASE_URL` set in your local environment pointing at the server (tunnel or direct access):

```bash
DATABASE_URL="postgresql://finance_user:password@<server-ip>:5432/finance" \
  pnpm --filter @finance/db db:studio
```

---

## 15. Networking architecture

### Standalone (bundled Caddy)

```
Internet
   │
   ▼ TCP :80 / :443
[Caddy :443]  ← TLS termination (Let's Encrypt), security headers
   │
   ▼ Docker frontend network (internal)
[Next.js :3000]
   │
   ▼ Docker backend network (internal: true — isolated from host and internet)
[Fastify API :4000]
   │
   ├─▶ [PostgreSQL :5432]
   └─▶ [Redis :6379]
```

### Behind an external reverse proxy

```
Internet
   │
   ▼ TCP :443
[nginx / Traefik / Caddy]  ← TLS termination (your certificate)
   │
   ▼ host TCP :WEB_PORT (e.g. 3000) — exposed only to proxy
[Next.js :3000]
   │
   ▼ Docker backend network (internal: true)
[Fastify API :4000]
   │
   ├─▶ [PostgreSQL :5432]
   └─▶ [Redis :6379]
```

### Key isolation properties

- The `backend` Docker network has `internal: true` — it has no route to the host or internet.
- The API container is never accessible from outside Docker; all external requests go through the Next.js server, which proxies `/api/*` internally.
- PostgreSQL and Redis have no published host ports in production (the compose file only exposes them in the dev variants).
- All containers run as non-root user `finance` inside the image and have `security_opt: no-new-privileges: true` and read-only root filesystems.

---

## 16. Security hardening checklist

Complete this before going live and after every significant configuration change.

### Secrets

- [ ] `APP_SECRET` is a fresh 256-bit random hex value (not a default or dev value)
- [ ] `ENCRYPTION_KEY` is a fresh 256-bit random hex value
- [ ] `AUTH_SECRET` is a fresh 256-bit random hex value
- [ ] `POSTGRES_PASSWORD` is at least 24 random characters
- [ ] `REDIS_PASSWORD` is at least 24 random characters
- [ ] `.env` file permissions are `600` (`chmod 600 .env`)
- [ ] `.env` is not committed to version control (verify with `git status`)

### Network

- [ ] PostgreSQL port 5432 is not exposed to the host (`docker compose ps` shows no `0.0.0.0:5432` binding)
- [ ] Redis port 6379 is not exposed to the host
- [ ] Firewall allows only 22, 80, 443 (standalone) or 22 + `WEB_PORT` from proxy only (external proxy)
- [ ] `WEB_PORT` is not reachable from the public internet in external proxy mode

### TLS

- [ ] HTTPS is enforced — HTTP redirects to HTTPS
- [ ] TLS certificate is valid (check with `curl -vI https://finance.example.com`)
- [ ] `Strict-Transport-Security` header is present with `max-age` ≥ 31536000

### Application

- [ ] `NODE_ENV=production` in `.env`
- [ ] `LOG_LEVEL` is `info` or higher (not `debug` or `trace`) — debug logs may contain sensitive data
- [ ] MFA (TOTP or passkey) has been enabled on the admin account
- [ ] Swagger UI (`/api/docs`) is only accessible over HTTPS

### Docker

- [ ] Docker Engine is up to date (`docker version`)
- [ ] Containers run as non-root (`docker compose exec api whoami` returns `finance`)
- [ ] `restart: unless-stopped` is set on all long-running services

### Backups

- [ ] At least one successful database backup has been created and verified restorable
- [ ] Backup schedule is automated (cron or the built-in BullMQ backup job)
- [ ] Backups are stored off-site (S3, B2, etc.)
- [ ] `.env` backup is encrypted

---

## 17. Troubleshooting

### Container fails to start — check logs first

```bash
docker compose logs <service-name> --tail 50
```

### `migrate` service exits with non-zero code

The API waits for `migrate` to complete successfully. If it fails:

```bash
docker compose logs migrate
```

Common causes:
- `DATABASE_URL` is incorrect — verify `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` match the values in the `postgres` service
- PostgreSQL is still starting up — wait 30 seconds and run `docker compose up -d` again
- A migration was previously applied to a newer database version — check for version skew

### Caddy fails to obtain a certificate

```bash
docker compose logs caddy
```

Common causes:
- DNS A record has not propagated yet — wait and retry (`dig +short $DOMAIN`)
- Port 80 is blocked by the firewall — Let's Encrypt HTTP challenge requires port 80 to be reachable
- Rate limit from Let's Encrypt — you have requested too many certificates for this domain in the past week. Check [crt.sh](https://crt.sh) for existing certificates

### Sessions expire immediately / "authentication required" on every page

- Verify `APP_SECRET` has not changed since the last deployment. Rotating this secret invalidates all existing sessions.
- Confirm `SESSION_MAX_AGE_SECONDS` is set to a reasonable value (e.g. `86400` for 24 hours).

### API returns 500 errors

```bash
docker compose logs api | grep '"level":50'
```

The structured JSON log will contain `err.message` and `err.stack`. Common causes:
- `DATABASE_URL` is malformed or the database is unreachable
- `ENCRYPTION_KEY` is incorrect length (must be exactly 64 hex characters / 32 bytes)
- Redis is unreachable — BullMQ workers will fail to start

### Web app cannot reach the API (network errors in browser)

The Next.js app proxies `/api/*` to the internal Fastify service. If this fails:

```bash
# Verify the API is healthy from inside the web container
docker compose exec web wget -qO- http://api:4000/health
```

If this fails, the `backend` Docker network is misconfigured or the API has crashed.

### Out of disk space

```bash
# Check Docker disk usage
docker system df

# Remove unused images, stopped containers, and dangling build cache
docker system prune -f

# Remove unused volumes (WARNING: check before running)
docker volume ls
docker volume prune -f
```

### Database is slow / high CPU on PostgreSQL

```bash
# Connect and run ANALYZE to refresh planner statistics
docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB -c 'ANALYZE;'

# Check for long-running queries
docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB -c \
  "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds';"
```
