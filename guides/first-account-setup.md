# First Account Setup

After installing Better Personal Finance, the onboarding wizard walks you through initial configuration.

---

## Step 1: Create your account

Navigate to your installation URL (e.g. `https://finance.example.com`).

You will be redirected to the registration page. Enter:

- **Email address** — used for login
- **Password** — minimum 12 characters; use a password manager
- **Display name** (optional) — shown in the UI

Click **Create account**. Registration is only available when no users exist — after this it is permanently closed.

---

## Step 2: Create your first account

After registering you land on the Accounts page. Click **New account** and fill in:

| Field | Description |
|-------|-------------|
| Name | E.g. "Main Checking", "Savings" |
| Type | Checking, Savings, Credit Card, Investment, Cash, Loan, Asset |
| Currency | 3-letter ISO code (default: USD) |
| Opening balance | Your current balance as of today |
| Note | Optional description |

Click **Create**. Repeat for each bank account or card you want to track.

---

## Step 3: Add your first transactions

Go to **Transactions → New transaction**.

| Field | Description |
|-------|-------------|
| Date | Transaction date |
| Amount | Positive for income, negative for expense |
| Type | Expense / Income / Transfer |
| Account | Source account |
| Category | Optional — assign a category |
| Payee | Merchant / payer name |
| Notes | Free text |

### CSV Import

If you have existing transaction history, use **Import CSV** on the Transactions page. The importer expects columns: `date, amount, description` (and optionally `payee, category`).

---

## Step 4: Set up categories

Go to **Categories** to create a hierarchy:

- Top-level categories (e.g. "Food & Drink", "Housing", "Transport")
- Subcategories nested under them (e.g. "Groceries" under "Food & Drink")

Categories can have an icon (Lucide icon name) and a colour (hex).

---

## Step 5: Create a budget (optional)

Go to **Budgets** and click **Edit budget** for the current month. Enter spending limits for each category. The budget page shows actual vs. planned in progress bars.

---

## Step 6: Set up payee rules (optional)

Go to **Payee Rules** to create auto-categorisation rules. When a new transaction has a matching payee, it is automatically assigned the configured category.

---

## Step 7: Enable two-factor authentication (recommended)

Go to **Settings → Two-factor authentication** and click **Set up TOTP**. Scan the QR code with an authenticator app (Google Authenticator, Authy, 1Password, etc.) and enter the 6-digit code to activate. Save the backup codes in a secure place.
