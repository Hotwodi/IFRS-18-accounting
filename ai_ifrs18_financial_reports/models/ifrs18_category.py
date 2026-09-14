from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Ifrs18Category(models.Model):
    _name = 'ifrs18.category'
    _description = 'IFRS 18 Report Category'
    _order = 'report_type, sequence, id'

    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, help='Short code, e.g. OP_REV, OP_EXP, INV, FIN')
    report_type = fields.Selection([
        ('pl', 'Profit & Loss'),
        ('bs', 'Balance Sheet'),
        ('cf', 'Cash Flow'),
        ('equity', 'Changes in Equity'),
    ], string='Report', required=True, default='pl')
    section = fields.Selection([
        ('operating', 'Operating'),
        ('investing', 'Investing'),
        ('financing', 'Financing'),
        ('current_asset', 'Current Asset'),
        ('noncurrent_asset', 'Non-Current Asset'),
        ('current_liability', 'Current Liability'),
        ('noncurrent_liability', 'Non-Current Liability'),
        ('equity', 'Equity'),
        ('comprehensive', 'Comprehensive Income'),
        ('owner_transaction', 'Transaction with Owners'),
    ], string='Section', required=True)
    sequence = fields.Integer(default=10)
    sign = fields.Selection([
        ('positive', 'Positive (add)'),
        ('negative', 'Negative (subtract)'),
    ], string='Sign Convention', default='positive',
        help='Whether amounts in this category are added or subtracted in the report total.')
    is_subtotal = fields.Boolean(string='Subtotal Line', default=False,
        help='If checked, this category is a subtotal header, not a detail line.')
    parent_id = fields.Many2one('ifrs18.category', string='Parent Category',
        help='Parent category for nested subtotals.')
    child_ids = fields.One2many('ifrs18.category', 'parent_id', string='Child Categories')
    account_ids = fields.One2many('account.account', 'ifrs18_category_id', string='Mapped Accounts')
    active = fields.Boolean(default=True)
    note = fields.Text(string='Notes')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Category code must be unique.'),
    ]

    @api.constrains('report_type', 'section')
    def _check_section_report(self):
        valid = {
            'pl': ['operating', 'investing', 'financing'],
            'bs': ['current_asset', 'noncurrent_asset', 'current_liability', 'noncurrent_liability', 'equity'],
            'cf': ['operating', 'investing', 'financing'],
            'equity': ['comprehensive', 'owner_transaction', 'equity'],
        }
        for rec in self:
            if rec.section not in valid.get(rec.report_type, []):
                raise ValidationError(_(
                    'Section "%s" is not valid for report type "%s".'
                ) % (rec.section, rec.report_type))

    @api.model
    def _bootstrap_categories(self):
        """Seed default IFRS 18 categories on install."""
        existing = self.search_count([])
        if existing:
            return
        pl_cats = [
            ('OP_REV', 'Revenue from Operations', 'operating', 'positive', 10),
            ('OP_COGS', 'Cost of Operations', 'operating', 'negative', 20),
            ('OP_OE', 'Other Operating Expenses', 'operating', 'negative', 30),
            ('OP_OI', 'Other Operating Income', 'operating', 'positive', 40),
            ('INV_INC', 'Investing Income', 'investing', 'positive', 50),
            ('INV_EXP', 'Investing Expenses', 'investing', 'negative', 60),
            ('FIN_INC', 'Financing Income', 'financing', 'positive', 70),
            ('FIN_EXP', 'Financing Expenses', 'financing', 'negative', 80),
        ]
        bs_cats = [
            ('CA', 'Current Assets', 'current_asset', 'positive', 10),
            ('NCA', 'Non-Current Assets', 'noncurrent_asset', 'positive', 20),
            ('CL', 'Current Liabilities', 'current_liability', 'negative', 30),
            ('NCL', 'Non-Current Liabilities', 'noncurrent_liability', 'negative', 40),
            ('EQ', 'Equity', 'equity', 'negative', 50),
        ]
        cf_cats = [
            ('CF_OP', 'Cash from Operating Activities', 'operating', 'positive', 10),
            ('CF_INV', 'Cash from Investing Activities', 'investing', 'positive', 20),
            ('CF_FIN', 'Cash from Financing Activities', 'financing', 'positive', 30),
        ]
        eq_cats = [
            ('EQ_OPEN', 'Opening Equity Balance', 'equity', 'positive', 10),
            ('EQ_CI', 'Comprehensive Income', 'comprehensive', 'positive', 20),
            ('EQ_OWNER', 'Transactions with Owners', 'owner_transaction', 'positive', 30),
            ('EQ_CLOSE', 'Closing Equity Balance', 'equity', 'positive', 40),
        ]
        for code, name, section, sign, seq in pl_cats:
            self.create({'name': name, 'code': code, 'report_type': 'pl',
                         'section': section, 'sign': sign, 'sequence': seq})
        for code, name, section, sign, seq in bs_cats:
            self.create({'name': name, 'code': code, 'report_type': 'bs',
                         'section': section, 'sign': sign, 'sequence': seq})
        for code, name, section, sign, seq in cf_cats:
            self.create({'name': name, 'code': code, 'report_type': 'cf',
                         'section': section, 'sign': sign, 'sequence': seq})
        for code, name, section, sign, seq in eq_cats:
            self.create({'name': name, 'code': code, 'report_type': 'equity',
                         'section': section, 'sign': sign, 'sequence': seq})
