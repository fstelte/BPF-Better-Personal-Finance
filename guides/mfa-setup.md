# MFA Setup Guide

Better Personal Finance supports two forms of multi-factor authentication (MFA):

- **TOTP** — time-based one-time passwords via any authenticator app
- **Passkeys** — device-bound credentials (Face ID, Touch ID, security keys)

---

## TOTP Setup

TOTP adds a 6-digit code requirement on every login.

### Enable TOTP

1. Go to **Settings → Security**.
2. Click **Set up TOTP**.
3. A QR code is displayed. Open your authenticator app and scan it.
   - Compatible apps: Google Authenticator, Authy, 1Password, Bitwarden, Aegis (Android)
4. Enter the 6-digit code shown in your app and click **Verify**.
5. A one-time screen shows your **backup codes**. Copy and store them securely — they cannot be retrieved later.

After activation, every login requires your email, password, and the current TOTP code.

### Disable TOTP

1. Go to **Settings → Security**.
2. Click **Disable TOTP** and confirm.

> **Warning**: Disabling TOTP reduces account security. Re-enable it or add a passkey.

---

## Passkey Setup

Passkeys use hardware-backed cryptography (biometrics or security keys). They are phishing-resistant and do not require a shared secret.

### Enroll a passkey

1. Go to **Settings → Security → Passkeys**.
2. Click **Add passkey**.
3. Your browser prompts you to authenticate — use Face ID, Touch ID, Windows Hello, or a hardware security key (YubiKey, etc.).
4. Give the passkey a name (e.g. "MacBook Face ID", "YubiKey 5").
5. Click **Save**.

Repeat for additional devices (laptop + phone + backup key is recommended).

### Remove a passkey

1. Go to **Settings → Security → Passkeys**.
2. Click the delete icon next to the passkey name and confirm.

### Using a passkey to log in

On the login page click **Sign in with a passkey** instead of entering a password. The browser prompts for the device credential.

---

## Lost access / account recovery

If you lose your TOTP device:

1. Use one of your **backup codes** on the MFA prompt screen.
2. After logging in, immediately disable TOTP and re-enroll with your new device.

If you lose all factors (TOTP device + all passkeys + backup codes), a server administrator can reset MFA directly in the database:

```sql
UPDATE "User"
SET "totpSecret" = NULL, "totpEnabled" = false
WHERE email = 'your@email.com';

DELETE FROM "Passkey"
WHERE "userId" = (SELECT id FROM "User" WHERE email = 'your@email.com');
```

Run this with `docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB`.
