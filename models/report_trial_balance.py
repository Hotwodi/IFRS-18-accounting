from odoo import models, fields, api, _
from collections import OrderedDict


class ReportTrialBalance(models.AbstractModel):
    _name = 'ifrs18.report.trial_balance'
    _description = 'Trial Balance Report'

    @api.model
    def _get_lines(self, date_from, date_to, target_move='posted',
                   comparison_date_from=None, comparison_date_to=None, company_id=None):
        """Compute Trial Balance: all accounts with debit/credit balances."""
        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
        ]
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))

        lines = self.env['account.move.line'].search(domain)
        account_data = OrderedDict()
        for line in lines:
            acc = line.account_id
            key = acc.id
            if key not in account_data:
                account_data[key] = {
                    'account': acc,
                    'code': acc.code,
                    'name': acc.name,
                    'debit': 0.0,
                    'credit': 0.0,
                    'balance': 0.0,
                    'comparison_debit': 0.0,
                    'comparison_credit': 0.0,
                    'comparison_balance': 0.0,
                }
            account_data[key]['debit'] += line.debit
            account_data[key]['credit'] += line.credit
            account_data[key]['balance'] += line.balance

        # Comparison period
        if comparison_date_from and comparison_date_to:
            comp_domain = [
                ('date', '>=', comparison_date_from),
                ('date', '<=', comparison_date_to),
                ('company_id', '=', company.id),
            ]
            if target_move == 'posted':
                comp_domain.append(('move_id.state', '=', 'posted'))
            comp_lines = self.env['account.move.line'].search(comp_domain)
            for line in comp_lines:
                acc = line.account_id
                key = acc.id
                if key not in account_data:
                    account_data[key] = {
                        'account': acc, 'code': acc.code, 'name': acc.name,
                        'debit': 0.0, 'credit': 0.0, 'balance': 0.0,
                        'comparison_debit': 0.0, 'comparison_credit': 0.0,
                        'comparison_balance': 0.0,
                    }
                account_data[key]['comparison_debit'] += line.debit
                account_data[key]['comparison_credit'] += line.credit
                account_data[key]['comparison_balance'] += line.balance

        # Sort by account code
        sorted_lines = sorted(account_data.values(), key=lambda x: x['code'])
        total_debit = sum(l['debit'] for l in sorted_lines)
        total_credit = sum(l['credit'] for l in sorted_lines)
        total_balance = sum(l['balance'] for l in sorted_lines)
        comp_total_debit = sum(l['comparison_debit'] for l in sorted_lines)
        comp_total_credit = sum(l['comparison_credit'] for l in sorted_lines)

        return {
            'lines': sorted_lines,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'total_balance': total_balance,
            'comparison_total_debit': comp_total_debit,
            'comparison_total_credit': comp_total_credit,
            'date_from': date_from,
            'date_to': date_to,
            'company': company,
        }
