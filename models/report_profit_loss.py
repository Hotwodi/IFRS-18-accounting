from odoo import models, fields, api, _
from collections import OrderedDict


class ReportProfitLoss(models.AbstractModel):
    _name = 'ifrs18.report.profit_loss'
    _description = 'IFRS 18 Profit & Loss Report'

    @api.model
    def _get_lines(self, date_from, date_to, comparison_date_from=None, comparison_date_to=None,
                   target_move='posted', company_id=None):
        """Compute P&L lines grouped by IFRS 18 category (Operating/Investing/Financing)."""
        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
        ]
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))

        lines = self.env['account.move.line'].search(domain)
        # Group by IFRS 18 P&L category
        cat_data = OrderedDict()
        for line in lines:
            cat = line.account_id.ifrs18_category_id
            if not cat or cat.report_type != 'pl':
                # Auto-classify by account type if no explicit mapping
                cat = self._auto_classify_pl(line.account_id)
            if cat:
                key = cat.id
                if key not in cat_data:
                    cat_data[key] = {
                        'category': cat,
                        'section': cat.section,
                        'name': cat.name,
                        'code': cat.code,
                        'sign': cat.sign,
                        'amount': 0.0,
                        'comparison_amount': 0.0,
                        'account_lines': {},
                    }
                val = line.balance  # debit - credit
                if cat.sign == 'negative':
                    val = -val
                cat_data[key]['amount'] += val
                # Track per-account detail for drill-down
                acc_key = line.account_id.id
                if acc_key not in cat_data[key]['account_lines']:
                    cat_data[key]['account_lines'][acc_key] = {
                        'account': line.account_id,
                        'amount': 0.0,
                    }
                cat_data[key]['account_lines'][acc_key]['amount'] += val

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
                cat = line.account_id.ifrs18_category_id
                if not cat or cat.report_type != 'pl':
                    cat = self._auto_classify_pl(line.account_id)
                if cat and cat.id in cat_data:
                    val = line.balance
                    if cat.sign == 'negative':
                        val = -val
                    cat_data[cat.id]['comparison_amount'] += val

        # Build ordered output by section
        sections = OrderedDict()
        section_labels = {
            'operating': _('Operating'),
            'investing': _('Investing'),
            'financing': _('Financing'),
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

        net_profit = sum(s['subtotal'] for s in sections.values())
        comp_net = sum(s['comparison_subtotal'] for s in sections.values())
        return {
            'sections': sections,
            'net_profit': net_profit,
            'comparison_net_profit': comp_net,
            'net_variance': net_profit - comp_net,
            'date_from': date_from,
            'date_to': date_to,
            'company': company,
        }

    @api.model
    def _auto_classify_pl(self, account):
        """Auto-classify an account into a P&L category based on account type."""
        Cat = self.env['ifrs18.category']
        atype = account.account_type
        # Odoo 18 account types: asset, liability, equity, income, expense, off
        if atype in ('income', 'income_other'):
            return Cat.search([('code', '=', 'OP_REV')], limit=1)
        elif atype in ('expense', 'expense_depreciation', 'expense_direct_cost'):
            return Cat.search([('code', '=', 'OP_COGS')], limit=1)
        return None
