# IFRS 18 Financial Reports Suite

Dynamic IFRS 18 financial statements for Odoo Community Edition.

## Price

$100.00 USD

## Features

Six financial reports compliant with IFRS 18 presentation requirements:

1. **Profit & Loss** — Operating, Investing, Financing categories with subtotals
2. **Balance Sheet** — Current / Non-current classification
3. **Cash Flow Statement** — Direct and Indirect methods
4. **Statement of Changes in Equity** — Opening, Comprehensive Income, Owner Transactions, Closing
5. **Trial Balance** — All accounts with debit/credit balances and comparison period
6. **Partner Ledgers** — Per-partner transaction listing with running balance

## Dynamic Features

- **Drill-down**: Click any summary figure to see the underlying journal entries
- **Date filtering**: Flexible date range selection
- **Period comparisons**: Compare current period to a prior period side-by-side
- **IFRS 18 category mapping**: Map Chart of Accounts to IFRS 18 categories
- **Auto-classification**: Accounts without explicit mapping are auto-classified by account type

## Export Formats

- **PDF** — Professional formatted report with company letterhead
- **Excel** — Spreadsheet export with openpyxl
- **CSV** — Raw data export for further analysis
- **Email** — Send report as PDF attachment

## Requirements

- Odoo 18 Community Edition
- `account` module (installed by default with Accounting)
- `openpyxl` Python package (for Excel export)

## Installation

1. Copy the `ai_ifrs18_financial_reports` folder to your Odoo addons directory.
2. Update the apps list in Odoo.
3. Install "IFRS 18 Financial Reports Suite".
4. Go to **Accounting > Configuration > IFRS 18 Categories** to review/adjust category mappings.
5. Go to **Accounting > Chart of Accounts** and map each account to its IFRS 18 category.
6. Go to **IFRS 18 Financial Reports > Financial Statements > Generate Report** to run any of the 6 reports.

## License

LGPL-3

## Author

SoftaiDev — https://softaidev.pages.dev
