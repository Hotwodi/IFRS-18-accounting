from odoo import models, fields, api, _
from collections import OrderedDict


class ReportBalanceSheet(models.AbstractModel):
    _name = 'ifrs18.report.balance_sheet'
    _description = 'IFRS 18 Balance Sheet Report'

    @api.model
    def _get_lines(self, date_to, comparison_date_to=None, target_move='posted', company_id=None):
        """Compute Balance Sheet as of a date, grouped by Current/Non-current."""
        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        domain = [
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
        ]
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))

        lines = self.env['account.move.line'].search(domain)
        cat_data = OrderedDict()
        for line in lines:
            cat = line.account_id.ifrs18_bs_category_id
            if not cat:
                cat = self._auto_classify_bs(line.account_id)
            if cat:
                key = cat.id
                if key not in cat_data:
                    cat_data[key] = {
                        'category': cat,
                        'section': cat.section,
                        'name': cat.name,
                        'code': cat.code,
                        'amount': 0.0,
                        'comparison_amount': 0.0,
                        'account_lines': {},
                    }
                val = line.balance
                cat_data[key]['amount'] += val
                acc_key = line.account_id.id
                if acc_key not in cat_data[key]['account_lines']:
                    cat_data[key]['account_lines'][acc_key] = {
                        'account': line.account_id,
                        'amount': 0.0,
                    }
                cat_data[key]['account_lines'][acc_key]['amount'] += val

        # Comparison date
        if comparison_date_to:
            comp_domain = [
                ('date', '<=', comparison_date_to),
                ('company_id', '=', company.id),
            ]
            if target_move == 'posted':
                comp_domain.append(('move_id.state', '=', 'posted'))
            comp_lines = self.env['account.move.line'].search(comp_domain)
            for line in comp_lines:
                cat = line.account_id.ifrs18_bs_category_id
                if not cat:
                    cat = self._auto_classify_bs(line.account_id)
                if cat and cat.id in cat_data:
                    cat_data[cat.id]['comparison_amount'] += line.balance

        sections = OrderedDict()
        section_labels = {
            'current_asset': _('Current Assets'),
            'noncurrent_asset': _('Non-Current Assets'),
            'current_liability': _('Current Liabilities'),
            'noncurrent_liability': _('Non-Current Liabilities'),
            'equity': _('Equity'),
        }
        for sid, slabel in section_labels.items():
            section_lines = [v for v in cat_data.values() if v['section'] == sid]
            if not section_lines:
                continue
            subtotal = sum(l['amount'] for l in section_lines)
            comp_subtotal = sum(l['comparison_amount'] for l in section_lines)
            sections[sid] = {
                'label': slabel,
                'lines': section_lines,
                'subtotal': subtotal,
                'comparison_subtotal': comp_subtotal,
                'variance': subtotal - comp_subtotal,
            }

        total_assets = sum(s['subtotal'] for sid, s in sections.items()
                           if sid in ('current_asset', 'noncurrent_asset'))
        total_liab_eq = sum(s['subtotal'] for sid, s in sections.items()
                            if sid in ('current_liability', 'noncurrent_liability', 'equity'))
        comp_assets = sum(s['comparison_subtotal'] for sid, s in sections.items()
                         if sid in ('current_asset', 'noncurrent_asset'))
        comp_liab_eq = sum(s['comparison_subtotal'] for sid, s in sections.items()
                           if sid in ('current_liability', 'noncurrent_liability', 'equity'))
        return {
            'sections': sections,
            'total_assets': total_assets,
            'total_liabilities_equity': total_liab_eq,
            'comparison_total_assets': comp_assets,
            'comparison_total_liabilities_equity': comp_liab_eq,
            'date_to': date_to,
            'company': company,
        }

    @api.model
    def _auto_classify_bs(self, account):
        Cat = self.env['ifrs18.category']
        atype = account.account_type
        if atype in ('asset_current', 'asset_cash', 'asset_receivable'):
            return Cat.search([('code', '=', 'CA')], limit=1)
        elif atype in ('asset_non_current', 'asset_fixed'):
            return Cat.search([('code', '=', 'NCA')], limit=1)
        elif atype in ('liability_current', 'payable'):
            return Cat.search([('code', '=', 'CL')], limit=1)
        elif atype in ('liability_non_current',):
            return Cat.search([('code', '=', 'NCL')], limit=1)
        elif atype in ('equity', 'equity_paid_in', 'equity_unpaid'):
            return Cat.search([('code', '=', 'EQ')], limit=1)
        return None
