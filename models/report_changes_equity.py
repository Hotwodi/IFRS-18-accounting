from odoo import models, fields, api, _
from collections import OrderedDict


class ReportChangesEquity(models.AbstractModel):
    _name = 'ifrs18.report.changes_equity'
    _description = 'IFRS 18 Statement of Changes in Equity'

    @api.model
    def _get_lines(self, date_from, date_to, target_move='posted', company_id=None):
        """Compute Statement of Changes in Equity."""
        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
        ]
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))

        lines = self.env['account.move.line'].search(domain)

        # Opening balance: sum of all equity account balances before date_from
        opening_domain = [
            ('date', '<', date_from),
            ('company_id', '=', company.id),
        ]
        if target_move == 'posted':
            opening_domain.append(('move_id.state', '=', 'posted'))
        opening_lines = self.env['account.move.line'].search(opening_domain)
        opening_balance = 0.0
        for line in opening_lines:
            if line.account_id.account_type in ('equity', 'equity_paid_in', 'equity_unpaid'):
                opening_balance += line.balance

        # Comprehensive income: net profit for the period
        pl_lines = lines.filtered(lambda l: l.account_id.account_type in
                                    ('income', 'income_other', 'expense',
                                     'expense_direct_cost', 'expense_depreciation'))
        comprehensive_income = sum(l.balance for l in pl_lines)

        # Transactions with owners: capital contributions, dividends, etc.
        owner_lines = lines.filtered(lambda l: l.account_id.account_type in
                                       ('equity', 'equity_paid_in', 'equity_unpaid'))
        owner_transactions = sum(l.balance for l in owner_lines)

        closing_balance = opening_balance + comprehensive_income + owner_transactions

        sections = OrderedDict()
        sections['opening'] = {
            'label': _('Opening Equity Balance'),
            'lines': [{'name': _('Balance at start of period'), 'amount': opening_balance}],
            'subtotal': opening_balance,
        }
        sections['comprehensive'] = {
            'label': _('Comprehensive Income'),
            'lines': [{'name': _('Net Profit for the Period'), 'amount': comprehensive_income}],
            'subtotal': comprehensive_income,
        }
        sections['owner'] = {
            'label': _('Transactions with Owners'),
            'lines': [{'name': _('Capital and Distribution Transactions'), 'amount': owner_transactions}],
            'subtotal': owner_transactions,
        }
        sections['closing'] = {
            'label': _('Closing Equity Balance'),
            'lines': [{'name': _('Balance at end of period'), 'amount': closing_balance}],
            'subtotal': closing_balance,
        }

        return {
            'sections': sections,
            'opening_balance': opening_balance,
            'comprehensive_income': comprehensive_income,
            'owner_transactions': owner_transactions,
            'closing_balance': closing_balance,
            'date_from': date_from,
            'date_to': date_to,
            'company': company,
        }
