---
name: subscription-audit
description: Finds every subscription and recurring charge in bank or credit-card CSV exports, totals the monthly and yearly cost, flags the ones likely forgotten, then walks the user to each cancel button in the browser (the user signs in and clicks cancel). Use when the user says "audit my subscriptions", "find my recurring charges", "what am I paying for every month", or "help me cancel subscriptions".
---

# Subscription audit

*"I discovered three streaming services. I do not know what streaming is." — Marcus*

The first job most Envoys should do. Works from exported files only; Claude never needs a bank login.

## Step 1: Get the exports (the user does this)

If there are no CSV files in the folder yet, tell the user:

> Sign in to your bank's website yourself and download **2 to 3 months** of transactions as a CSV file (usually under
> Activity, Statements or Transactions, behind a Download or Export button). Do the same for any credit cards. For
> yearly subscriptions, export **13 months**. Put the files in this folder. Never give me your bank password.

## Step 2: Run the helper

```
python find_recurring.py <folder or files> --out recurring.csv
```

`find_recurring.py` sits next to this file (standard-library Python, no installs). It:
- finds the header row even when the bank adds a few junk lines above it;
- understands `Date/Description/Amount`, separate `Debit/Credit` or `Withdrawal/Deposit` columns, and common
  variants (`Transaction Date`, `Posted Date`, `Payee`, `Merchant`, `Memo`...);
- works out whether charges are negative or positive (override with `--charges negative|positive`);
- groups by cleaned-up merchant name, keeps groups with a regular cadence (weekly to annual) and steady amounts;
- skips transfers, payroll, ATM and card payments;
- prints a Markdown table and monthly/annual totals, and flags price increases and small charges.

UK/EU date order: add `--dayfirst`. If it errors on a column name, open the first lines of the CSV, see the headers,
and either rename the header in a copy of the file or read the file yourself.

## Step 3: Review it like a human would

The script is a first pass. Before showing results:
1. Skim the raw CSVs yourself for things it may have missed: charges seen only once with names like
   "membership", "annual", "renewal", "premium", "plus", app stores (`APPLE.COM/BILL`, `GOOGLE *`), `PAYPAL *`
   (look at the merchant after the asterisk), and free trials that turned paid.
2. Merge rows that are clearly the same service under two names.
3. Remove things that are recurring but not subscriptions (rent, utilities, loan payments) into a separate
   "Regular bills" list, so the subscription total stays honest.

## Step 4: Present the table

| Service | How often | Amount | Last charged | Per month | Per year | Notes |
|---|---|---:|---|---:|---:|---|

Then: **total per month and per year**, and a short **"Likely forgotten"** list: small charges, services with
overlapping purpose (three streaming services, two cloud storage plans), price increases, and anything the user
doesn't recognise. Ask the user to mark each row **keep / cancel / downgrade / not sure**.

Save the final table to `subscriptions.md` (or the Envoy's notes) with today's date, so next month's audit can
compare.

## Step 5: Walk to the cancel button (needs a browser tool)

For each service marked **cancel**, one at a time (see the `browser-handoff` skill for the full pattern):
1. Open the service's account or cancellation page in the browser.
2. Say: "Please sign in. Tell me when you're in." **Wait.** Do not type passwords or codes.
3. Navigate past retention offers and "Are you sure?" screens. Decline discounts unless the user said a cheaper
   plan is acceptable.
4. **Stop on the final cancel/confirm screen.** Tell the user exactly what the button says and what the page says
   about refunds and the end date. The user clicks it.
5. After they confirm it's done, note the date and any confirmation number in `subscriptions.md`.

If a service can only be cancelled by phone or through an app store, give the user the exact steps instead
(e.g. phone Settings > your name > Subscriptions, or the Play Store > Payments & subscriptions).

## What this won't do

- It never asks for, types or stores bank or service passwords, 2FA codes or card numbers.
- It never clicks the final cancel, confirm, downgrade or purchase button. The user does.
- It never accepts a retention offer or changes a plan without the user saying so.
- It doesn't upload bank exports anywhere; the analysis runs on the user's computer. Suggest deleting the CSVs
  when the audit is done, or keep them only in a private folder.
