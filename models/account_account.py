from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    ifrs18_category_id = fields.Many2one(
        'ifrs18.category',
        string='IFRS 18 Category',
        help='Map this account to an IFRS 18 report category for dynamic financial statements.',
        ondelete='set null',
    )
    ifrs18_bs_category_id = fields.Many2one(
        'ifrs18.category',
        string='IFRS 18 Balance Sheet Category',
        domain="[('report_type', '=', 'bs')]",
        help='Map this account to a Balance Sheet category (Current/Non-current Asset/Liability/Equity).',
        ondelete='set null',
    )
    ifrs18_cf_category_id = fields.Many2one(
        'ifrs18.category',
        string='IFRS 18 Cash Flow Category',
        domain="[('report_type', '=', 'cf')]",
        help='Map this account to a Cash Flow category (Operating/Investing/Financing).',
        ondelete='set null',
    )
