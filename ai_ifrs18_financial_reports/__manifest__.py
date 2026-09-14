{
    'name': 'IFRS 18 Financial Reports Suite',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Financial Reports',
    'images': ['static/description/cover.png'],
    'summary': 'Dynamic IFRS 18 financial statements for Odoo Community: P&L, Balance Sheet, Cash Flow, Changes in Equity, Trial Balance, Partner Ledgers.',
    'description': """
IFRS 18 Financial Reports Suite
================================
Six dynamic financial statements compliant with IFRS 18 presentation
requirements, built for Odoo Community Edition:

1. Profit & Loss — Operating, Investing, Financing categories with subtotals
2. Balance Sheet — Current / Non-current classification
3. Cash Flow Statement — Direct and Indirect methods
4. Statement of Changes in Equity
5. Trial Balance
6. Partner Ledgers

Features:
- Drill-down from summary figures to individual journal entries
- Dynamic date filtering and period comparisons
- Export to PDF, Excel, CSV, and Email
- IFRS 18 category mapping on the Chart of Accounts
- Works with Odoo Community Edition (no Enterprise required)
    """,
    'author': 'SoftaiDev',
    'website': 'https://softaidev.pages.dev',
    'license': 'LGPL-3',
    'price': 100.00,
    'currency': 'USD',
    'depends': ['account', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/ifrs18_category_views.xml',
        'views/ifrs18_report_views.xml',
        'views/menu.xml',
        'wizard/ifrs18_report_wizard_views.xml',
        'reports/profit_loss_report.xml',
        'reports/balance_sheet_report.xml',
        'reports/cash_flow_report.xml',
        'reports/changes_equity_report.xml',
        'reports/trial_balance_report.xml',
        'reports/partner_ledger_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': '_post_init_hook',
}
