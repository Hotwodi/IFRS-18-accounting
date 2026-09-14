from odoo import models, fields, api, _
from collections import OrderedDict


class ReportPartnerLedger(models.AbstractModel):
    _name = 'ifrs18.report.partner_ledger'
    _description = 'Partner Ledger Report'

    @api.model
    def _get_lines(self, date_from, date_to, partner_id=None, target_move='posted',
                   company_id=None):
        """Compute Partner Ledger: per-partner transaction listing with running balance."""
        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
            ('partner_id', '!=', False),
        ]
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        lines = self.env['account.move.line'].search(domain)

        # Opening balance per partner: sum of all moves before date_from
        opening_domain = [
            ('date', '<', date_from),
            ('company_id', '=', company.id),
            ('partner_id', '!=', False),
        ]
        if target_move == 'posted':
            opening_domain.append(('move_id.state', '=', 'posted'))
        if partner_id:
            opening_domain.append(('partner_id', '=', partner_id))
        opening_lines = self.env['account.move.line'].search(opening_domain)

        partner_data = OrderedDict()
        for line in opening_lines:
            p = line.partner_id
            key = p.id
            if key not in partner_data:
                partner_data[key] = {
                    'partner': p,
                    'name': p.name,
                    'opening_balance': 0.0,
                    'transactions': [],
                    'closing_balance': 0.0,
                    'total_debit': 0.0,
                    'total_credit': 0.0,
                }
            partner_data[key]['opening_balance'] += line.balance

        for line in lines:
            p = line.partner_id
            key = p.id
            if key not in partner_data:
                partner_data[key] = {
                    'partner': p,
                    'name': p.name,
                    'opening_balance': 0.0,
                    'transactions': [],
                    'closing_balance': 0.0,
                    'total_debit': 0.0,
                    'total_credit': 0.0,
                }
            partner_data[key]['transactions'].append({
                'date': line.date,
                'move_id': line.move_id,
                'account': line.account_id,
                'ref': line.ref or line.move_id.name,
                'debit': line.debit,
                'credit': line.credit,
                'balance': line.balance,
            })
            partner_data[key]['total_debit'] += line.debit
            partner_data[key]['total_credit'] += line.credit

        for key in partner_data:
            partner_data[key]['closing_balance'] = (
                partner_data[key]['opening_balance'] +
                partner_data[key]['total_debit'] -
                partner_data[key]['total_credit']
            )

        sorted_partners = sorted(partner_data.values(), key=lambda x: x['name'])
        return {
            'partners': sorted_partners,
            'date_from': date_from,
            'date_to': date_to,
            'company': company,
        }
