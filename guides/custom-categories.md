# Custom Categories

Categories let you organise every transaction into a hierarchy you control. Better Personal Finance ships with a set of default categories, but you can add, edit, or reorganise them freely.

---

## Category concepts

| Term | Meaning |
|------|---------|
| **Root category** | Top-level group, e.g. "Food & Drink" |
| **Subcategory** | Nested under a root, e.g. "Groceries" under "Food & Drink" |
| **System category** | Supplied by default; cannot be deleted (but can be renamed) |

Transactions can be assigned to any category (root or subcategory).

---

## Create a category

1. Go to **Categories** in the sidebar.
2. Click **New category**.
3. Fill in:

| Field | Required | Notes |
|-------|----------|-------|
| Name | Yes | E.g. "Restaurants" |
| Parent | No | Select a root category to create a subcategory |
| Icon | No | Any [Lucide](https://lucide.dev/icons/) icon name, e.g. `utensils` |
| Colour | No | Hex colour used in charts, e.g. `#f97316` |

4. Click **Save**.

---

## Create subcategories

A subcategory is a category with a parent selected. Example hierarchy:

```
Food & Drink
  ├── Groceries
  ├── Restaurants
  └── Coffee & Tea

Transport
  ├── Fuel
  ├── Public Transit
  └── Parking
```

To nest a category, choose the parent in the **Parent** dropdown when creating or editing.

There is no limit on depth, but two levels (root + one subcategory) are recommended for clarity.

---

## Edit a category

1. On the Categories page, find the category in the list.
2. Click the **pencil** icon.
3. Change name, icon, colour, or parent and click **Save**.

> Changing a category's parent re-nests all transactions already assigned to it.

---

## Delete a category

1. Click the **trash** icon next to a category.
2. Confirm the deletion.

Before deleting, choose what to do with assigned transactions:

- **Move to a different category** — select any other category
- **Clear category** — transactions become uncategorised

> System categories (marked with a lock icon) cannot be deleted.

---

## Using categories with payee rules

To auto-assign a category to future transactions, create a **payee rule** at **Payee Rules** in the sidebar. Map a payee name (or substring) to a category so newly imported or entered transactions are categorised automatically.
