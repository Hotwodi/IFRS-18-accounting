from odoo import models, fields, api, _
from collections import OrderedDict


class ReportCashFlow(models.AbstractModel):
    _name = 'ifrs18.report.cash_flow'
    _description = 'IFRS 18 Cash Flow Statement'

    @api.model
    def _get_lines(self, date_from, date_to, method='indirect',
                   comparison_date_from=None, comparison_date_to=None,
                   target_move='posted', company_id=None):
        """Compute Cash Flow Statement (Direct or Indirect method)."""
        company = self.env['res.company'].browse(company_id) if company_id else self.env.company
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
        ]
        if target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))

        lines = self.env['account.move.line'].search(domain)

        if method == 'direct':
            return self._compute_direct(lines, company, date_from, date_to,
                                         comparison_date_from, comparison_date_to)
        return self._compute_indirect(lines, company, date_from, date_to,
                                       comparison_date_from, comparison_date_to)

    @api.model
    def _compute_indirect(self, lines, company, date_from, date_to,
                          comp_from, comp_to):
        """Indirect method: start from net profit, adjust for non-cash items."""
        # Net profit from P&L accounts
        pl_domain = [('account_id.account_type', 'in',
                      ('income', 'income_other', 'expense', 'expense_direct_cost',
                       'expense_depreciation'))]
        pl_lines = lines.filtered(lambda l: l.account_id.account_type in
                                   ('income', 'income_other', 'expense',
                                    'expense_direct_cost', 'expense_depreciation'))
        net_profit = sum(l.balance for l in pl_lines)

        # Depreciation / non-cash adjustments
        dep_lines = lines.filtered(lambda l: l.account_id.account_type == 'expense_depreciation')
        depreciation = sum(l.balance for l in dep_lines)

        # Working capital changes
        ar_lines = lines.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
        ar_change = sum(l.balance for l in ar_lines)

        ap_lines = lines.filtered(lambda l: l.account_id.account_type == 'payable')
        ap_change = sum(l.balance for l in ap_lines)

        inv_lines = lines.filtered(lambda l: l.account_id.account_type in
                                    ('asset_non_current', 'asset_fixed'))
        inv_change = sum(l.balance for l in inv_lines)

        # Cash from operations
        cash_from_ops = net_profit + depreciation - ar_change + ap_change - inv_change

        # Investing: cash flows from non-current asset acquisitions/disposals
        investing_lines = lines.filtered(
            lambda l: l.account_id.ifrs18_cf_category_id and
            l.account_id.ifrs18_cf_category_id.section == 'investing')
        cash_investing = -sum(l.balance for l in investing_lines) if investing_lines else -inv_change

        # Financing: cash flows from debt/equity
        financing_lines = lines.filtered(
            lambda l: l.account_id.ifrs18_cf_category_id and
            l.account_id.ifrs18_cf_category_id.section == 'financing')
        cash_financing = -sum(l.balance for l in financing_lines)

        # Net change in cash
        cash_lines = lines.filtered(lambda l: l.account_id.account_type == 'asset_cash')
        net_cash_change = sum(l.balance for l in cash_lines)

        sections = OrderedDict()
        sections['operating'] = {
            'label': _('Cash from Operating Activities'),
            'lines': [
                {'name': _('Net Profit'), 'amount': net_profit},
                {'name': _('Adjustments for Depreciation'), 'amount': depreciation},
                {'name': _('Changes in Accounts Receivable'), 'amount': -ar_change},
                {'name': _('Changes in Accounts Payable'), 'amount': ap_change},
                {'name': _('Changes in Inventory'), 'amount': -inv_change},
            ],
            'subtotal': cash_from_ops,
        }
        sections['investing'] = {
            'label': _('Cash from Investing Activities'),
            'lines': [{'name': _('Investing Cash Flows'), 'amount': cash_investing}],
            'subtotal': cash_investing,
        }
        sections['financing'] = {
            'label': _('Cash from Financing Activities'),
            'lines': [{'name': _('Financing Cash Flows'), 'amount': cash_financing}],
            'subtotal': cash_financing,
        }

        return {
            'method': 'indirect',
            'sections': sections,
            'net_cash_change': net_cash_change,
            'date_from': date_from,
            'date_to': date_to,
            'company': company,
        }

    @api.model
    def _compute_direct(self, lines, company, date_from, date_to,
                         comp_from, comp_to):
        """Direct method: cash receipts and payments by category."""
        cat_data = OrderedDict()
        for line in lines:
            cat = line.account_id.ifrs18_cf_category_id
            if not cat:
                # Auto-classify by account type
                atype = line.account_id.account_type
                if atype == 'asset_cash':
                    continue  # Cash itself is the result, not a line
                Cat = self.env['ifrs18.category']
                if atype in ('income', 'income_other', 'asset_receivable'):
                    cat = Cat.search([('code', '=', 'CF_OP')], limit=1)
                elif atype in ('expense', 'expense_direct_cost', 'payable'):
                    cat = Cat.search([('code', '=', 'CF_OP')], limit=1)
                elif atype in ('asset_non_current', 'asset_fixed'):
                    cat = Cat.search([('code', '=', 'CF_INV')], limit=1)
                elif atype in ('liability_non_current', 'equity'):
                    cat = Cat.search([('code', '=', 'CF_FIN')], limit=1)
            if not cat:
                continue
            key = cat.id
            if key not in cat_data:
                cat_data[key] = {'category': cat, 'section': cat.section,
                                'name': cat.name, 'amount': 0.0}
            cat_data[key]['amount'] += line.balance

        sections = OrderedDict()
        section_labels = {
            'operating': _('Cash from Operating Activities'),
            'investing': _('Cash from Investing Activities'),
            'financing': _('Cash from Financing Activities'),
        }
        for sid, slabel in section_labels.items():
            section_lines = [v for v in cat_data.values() if v['section'] == sid]
            subtotal = sum(l['amount'] for l in section_lines)
            sections[sid] = {'label': slabel, 'lines': section_lines, 'subtotal': subtotal}

        cash_lines = lines.filtered(lambda l: l.account_id.account_type == 'asset_cash')
        net_cash_change = sum(l.balance for l in cash_lines)

        return {
            'method': 'direct',
            'sections': sections,
            'net_cash_change': net_cash_change,
            'date_from': date_from,
            'date_to': date_to,
            'company': company,
        }
