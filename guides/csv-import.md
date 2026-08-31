# CSV Import

Better Personal Finance can import transactions from CSV files exported by your bank or any other source.

---

## Accessing the importer

1. Go to **Transactions** in the sidebar.
2. Click **Import CSV**.
3. Select the target **account** (the account the transactions belong to).
4. Upload your CSV file.
5. Review the preview and click **Confirm import**.

---

## Required CSV format

The importer recognises these column headers (case-insensitive):

| Column | Required | Description |
|--------|----------|-------------|
| `date` | Yes | Transaction date |
| `amount` | Yes | Decimal value; positive = credit, negative = debit |
| `description` or `payee` | Yes | Merchant / transaction description |
| `category` | No | Category name; auto-matched to existing categories |
| `notes` | No | Free text appended to the transaction |

Column order does not matter; the importer matches by header name.

### Minimal example

```csv
date,amount,description
2024-01-15,-42.50,Whole Foods Market
2024-01-16,-3.80,Costa Coffee
2024-01-17,3200.00,Salary
```

### Full example

```csv
date,amount,description,payee,category,notes
2024-01-15,-42.50,Grocery shopping,Whole Foods Market,Groceries,
2024-01-16,-3.80,Morning coffee,Costa Coffee,Coffee & Tea,
2024-01-17,3200.00,Monthly salary,,Salary,January payroll
```

---

## Supported date formats

The importer accepts these date formats:

| Format | Example |
|--------|---------|
| ISO 8601 | `2024-01-15` |
| US slash | `01/15/2024` |
| UK slash | `15/01/2024` |
| US dash | `01-15-2024` |
| Long form | `January 15, 2024` |

> If your bank uses a different format, open the CSV in a spreadsheet and change the date column to ISO 8601 (`YYYY-MM-DD`) before importing.

---

## Number format

The importer needs to know how decimal amounts are written in your bank export. By default it uses your saved preference from **Settings → Number format**, but you can override it per import using the **Number format** selector shown on the upload step.

| Format | Example | Decimal separator | Thousands separator |
|--------|---------|------------------|---------------------|
| US / UK (dot decimal) | `1,234.56` | `.` | `,` |
| European (comma decimal) | `1.234,56` | `,` | `.` |

**Choose the format your bank uses in its export file** — not your display preference in the app. If your German bank exports `1.234,56`, select **European (comma decimal)** even if you normally view amounts differently.

> The number format selected during import only affects how that import is parsed. Your display preference in Settings is not changed.

### Ambiguous values

A small number of values cannot be parsed unambiguously and will be rejected with a row-level error:

- `1.234` under US/UK — three digits after the dot looks like a decimal, not a thousands group
- `1,234` under European — same reason

If your CSV contains values like these, add `.00` or `,00` to make the intent clear (`1234.00` / `1234,00`), or convert the column in a spreadsheet before importing.

---

## Duplicate detection

The importer compares incoming rows against existing transactions using date + amount + description. If a transaction already exists it is skipped and reported in the import summary. This allows you to safely re-import overlapping exports.

---

## After import

- Imported transactions appear in the **Transactions** list with status **Pending**.
- The auto-categorisation job runs in the background and applies payee rules. Refresh the page after a few seconds to see categories assigned.
- Use **Bulk edit** to assign categories to many uncategorised transactions at once.

---

## Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Amount column not found" | Column named differently | Rename column to `amount` |
| "Invalid date on row N" | Unrecognised date format | Convert dates to `YYYY-MM-DD` |
| "No account selected" | Target account not chosen | Select an account before uploading |
| "File too large" | File exceeds 10 MB | Split the file into smaller chunks |

---

## Bank-specific tips

### Monzo
Export from the app: **Account → Export → CSV**. Column names are compatible out of the box.

### Starling Bank
Export from the web portal: **Transactions → Export → CSV**. The `Amount (GBP)` column needs renaming to `amount`.

### Chase (US)
Download from **Accounts → Download transactions → CSV**. Select the date range and use the default format.

### N26
Export from the app. The `Amount (EUR)` column needs renaming to `amount`.
