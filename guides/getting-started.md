# Getting Started

This guide walks you through cloning the repository, installing dependencies, and running **Better Personal Finance** locally in development mode.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 22 LTS | https://nodejs.org |
| pnpm | 9 | `npm install -g pnpm@9` |
| Docker Desktop | latest | https://www.docker.com/products/docker-desktop/ |

---

## 1. Clone the repository

```bash
git clone https://github.com/your-username/better-personal-finance.git
cd better-personal-finance
```

## 2. Install dependencies

```bash
pnpm install
```

## 3. Configure environment variables

```bash
cp .env.development .env
```

The development defaults work out of the box with the dev Docker Compose file. You can leave them as-is for local development.

## 4. Start development infrastructure

This starts PostgreSQL and Redis in Docker:

```bash
docker compose -f docker-compose.dev.yml up -d
```

Verify both containers are running:

```bash
docker compose -f docker-compose.dev.yml ps
```

## 5. Run database migrations

```bash
pnpm --filter @finance/db db:migrate:dev
```

## 6. Generate the Prisma client

```bash
pnpm --filter @finance/db db:generate
```

## 7. Start the development servers

```bash
pnpm dev
```

This starts both the API (port 4000) and the web frontend (port 3000) in watch mode.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:4000 |
| Swagger UI | http://localhost:4000/api/docs |
| Prisma Studio | Run `pnpm --filter @finance/db db:studio` |

---

## 8. First-time setup

Navigate to http://localhost:3000. The onboarding wizard will guide you through:

1. Creating your admin account (email + password)
2. Setting up your first bank account
3. Optionally enabling TOTP two-factor authentication

---

## Useful development commands

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start all apps in watch mode |
| `pnpm build` | Build all packages |
| `pnpm typecheck` | TypeScript check all packages |
| `pnpm lint` | ESLint all packages |
| `pnpm test` | Run unit tests |
| `pnpm --filter @finance/db db:migrate:dev` | Apply new migrations |
| `pnpm --filter @finance/db db:studio` | Open Prisma Studio |
| `pnpm format` | Format all files with Prettier |

---

## Next steps

- [First account setup](./first-account-setup.md)
- [Production deployment](./docker-deployment.md)
