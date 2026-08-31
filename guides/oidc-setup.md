# OIDC Login Setup Guide

Better Personal Finance supports signing in via an external identity provider (OIDC) in addition to email/password. This is an additional login method, not a replacement — every account still has a local password, and OIDC identities are linked to that account rather than replacing it.

Two providers are supported out of the box:

- **Entra ID** (Microsoft) — `OIDC_ENTRA_*` env vars
- **A second, generic OIDC-compliant provider** — `OIDC_COSMOS_*` env vars (any standards-compliant OIDC issuer works here, not a specific product)

Either or both can be configured independently. Leave a provider's variables unset (or only partially set) and it's simply not offered — no code changes needed to add or remove a provider.

---

## How account linking works

This app never creates a new account from an OIDC login alone — you always need a local account (email + password) first. From there, an OIDC identity gets attached to it in one of two ways:

1. **Explicit** — while logged in, go to **Settings → Connected accounts** and click **Connect** next to a provider. This is the safest path: no ambiguity, no password re-entry needed since you're already authenticated.
2. **Automatic on first OIDC login** — if you sign in via OIDC and the identity provider's email matches an existing local account that isn't linked yet, you're taken to a **Confirm it's you** screen and asked for your local password once. Entering it correctly links the OIDC identity and signs you in; entering it incorrectly counts as a failed login attempt against your account's normal lockout policy, same as a wrong password on the regular login form.

Once linked, MFA (TOTP/passkey) is skipped for that OIDC login — the identity provider's own authentication is trusted as sufficient. Local password login still enforces MFA as usual.

---

## Setting up Entra ID (Microsoft)

### 1. Create an App Registration

1. In the [Azure Portal](https://portal.azure.com), go to **Microsoft Entra ID → App registrations → New registration**.
2. Name it (e.g. "Better Personal Finance").
3. Under **Redirect URI**, choose platform **Web** and enter:
   ```
   https://your-domain.example.com/api/auth/oidc/entra/callback
   ```
   Replace `your-domain.example.com` with your instance's public domain (the same value as your `DOMAIN`/`WEB_ORIGIN` setting). For local development this would be `http://localhost:3001/api/auth/oidc/entra/callback` (or whatever port your web app runs on).
4. Click **Register**.

### 2. Create a client secret

1. In the new App Registration, go to **Certificates & secrets → Client secrets → New client secret**.
2. Copy the secret **value** immediately — it's only shown once.

### 3. Note the tenant ID and client ID

Both are shown on the App Registration's **Overview** page: **Application (client) ID** and **Directory (tenant) ID**.

### 4. Set the environment variables

Add to your `.env` (see `.env.example`):

```
OIDC_ENTRA_ISSUER_URL=https://login.microsoftonline.com/<tenant-id>/v2.0
OIDC_ENTRA_CLIENT_ID=<application-client-id>
OIDC_ENTRA_CLIENT_SECRET=<client-secret-value>
OIDC_ENTRA_DISPLAY_NAME=Microsoft Entra ID
```

`OIDC_ENTRA_DISPLAY_NAME` is just the label shown on the "Sign in with ..." button and in Settings — change it to whatever you like (e.g. your company name).

### 5. Restart the API

Provider discovery happens once, the first time it's needed after the API process starts — it is not re-checked per request. After adding or changing any `OIDC_ENTRA_*` variable, restart the API container (`docker compose restart api`, or just redeploy) for the change to take effect.

---

## Setting up the second provider

The steps are the same shape for any standards-compliant OIDC provider — Authentik, Keycloak, Authelia, Zitadel, Auth0, Okta, or similar all work the same way:

1. Register a new OIDC client/application with your provider.
2. Set its redirect URI to:
   ```
   https://your-domain.example.com/api/auth/oidc/cosmos/callback
   ```
3. Note the issuer URL (often shown as the "discovery URL" minus the trailing `/.well-known/openid-configuration`), client ID, and client secret.
4. Set the environment variables:
   ```
   OIDC_COSMOS_ISSUER_URL=https://your-provider.example.com
   OIDC_COSMOS_CLIENT_ID=<client-id>
   OIDC_COSMOS_CLIENT_SECRET=<client-secret>
   OIDC_COSMOS_DISPLAY_NAME=<whatever you want the button to say>
   ```
5. Restart the API.

---

## Verifying it worked

1. Open the login page. A "Sign in with {provider}" button (or buttons, if both are configured) should appear below the password form. If it doesn't appear, double-check all three required variables (`_ISSUER_URL`, `_CLIENT_ID`, `_CLIENT_SECRET`) are set for that provider and that the API was restarted after setting them.
2. Log in with your local account, then go to **Settings → Connected accounts** and click **Connect** next to the provider to link it explicitly.
3. Log out, then click the "Sign in with {provider}" button on the login page — it should sign you straight back in.

---

## Disconnecting a provider

1. Go to **Settings → Connected accounts**.
2. Click **Disconnect** next to the linked provider.
3. Enter your local password to confirm.

This is always available and never locks you out, since every account keeps its local password regardless of how many OIDC identities are linked to it.

---

## Troubleshooting

If an OIDC sign-in attempt fails, you're returned to the login page with a message. The underlying causes:

- **"Your sign-in attempt expired or was invalid"** (`state_invalid`) — the sign-in took too long (over 5 minutes) or was retried from a stale link. Just try again.
- **"The sign-in provider could not complete the request"** (`provider_failed`) — the API couldn't reach the provider, or the provider rejected the client ID/secret. Check the API logs for the real cause (it's logged server-side but not shown to the browser) and re-verify the client ID/secret/issuer URL.
- **"No account found for this sign-in"** (`no_account`) — the OIDC identity isn't linked to any local account, and its email doesn't match an existing one either. Register a local account first (or ask an administrator to), then use **Settings → Connected accounts → Connect**.

If discovery fails at API startup for a fully-configured provider (e.g. the issuer URL is wrong or unreachable), that provider is silently excluded from the login page until the next restart — it is not retried automatically. Check the API's startup logs for a `[oidc] discovery failed for provider "..."` message.
