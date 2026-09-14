import base64
import io
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Ifrs18ReportWizard(models.TransientModel):
    _name = 'ifrs18.report.wizard'
    _description = 'IFRS 18 Report Wizard'

    report_type = fields.Selection([
        ('pl', 'Profit & Loss'),
        ('bs', 'Balance Sheet'),
        ('cf', 'Cash Flow Statement'),
        ('equity', 'Statement of Changes in Equity'),
        ('tb', 'Trial Balance'),
        ('partner', 'Partner Ledger'),
    ], string='Report', required=True, default='pl')
    date_from = fields.Date(string='From Date', required=True,
                            default=lambda self: fields.Date.context_today(self).replace(month=1, day=1))
    date_to = fields.Date(string='To Date', required=True,
                          default=lambda self: fields.Date.context_today(self))
    comparison_date_from = fields.Date(string='Comparison From')
    comparison_date_to = fields.Date(string='Comparison To')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries'),
    ], string='Target Moves', required=True, default='posted')
    cash_flow_method = fields.Selection([
        ('indirect', 'Indirect Method'),
        ('direct', 'Direct Method'),
    ], string='Cash Flow Method', default='indirect')
    partner_id = fields.Many2one('res.partner', string='Partner (for Partner Ledger)')
    export_format = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('email', 'Email'),
    ], string='Export Format', required=True, default='pdf')
    email_to = fields.Char(string='Email To')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company, required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise ValidationError(_('From Date cannot be after To Date.'))

    def action_generate_report(self):
        self.ensure_one()
        report_data = self._compute_report()
        if self.export_format == 'pdf':
            return self._export_pdf(report_data)
        elif self.export_format == 'excel':
            return self._export_excel(report_data)
        elif self.export_format == 'csv':
            return self._export_csv(report_data)
        elif self.export_format == 'email':
            return self._export_email(report_data)
        return None

    def _compute_report(self):
        self.ensure_one()
        kwargs = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
        }
        if self.report_type == 'pl':
            kwargs['comparison_date_from'] = self.comparison_date_from
            kwargs['comparison_date_to'] = self.comparison_date_to
            return self.env['ifrs18.report.profit_loss']._get_lines(**kwargs)
        elif self.report_type == 'bs':
            kwargs.pop('date_from')
            kwargs['date_to'] = self.date_to
            kwargs['comparison_date_to'] = self.comparison_date_to
            return self.env['ifrs18.report.balance_sheet']._get_lines(**kwargs)
        elif self.report_type == 'cf':
            kwargs['method'] = self.cash_flow_method
            kwargs['comparison_date_from'] = self.comparison_date_from
            kwargs['comparison_date_to'] = self.comparison_date_to
            return self.env['ifrs18.report.cash_flow']._get_lines(**kwargs)
        elif self.report_type == 'equity':
            return self.env['ifrs18.report.changes_equity']._get_lines(**kwargs)
        elif self.report_type == 'tb':
            kwargs['comparison_date_from'] = self.comparison_date_from
            kwargs['comparison_date_to'] = self.comparison_date_to
            return self.env['ifrs18.report.trial_balance']._get_lines(**kwargs)
        elif self.report_type == 'partner':
            kwargs['partner_id'] = self.partner_id.id if self.partner_id else None
            return self.env['ifrs18.report.partner_ledger']._get_lines(**kwargs)
        return {}

    def _export_pdf(self, data):
        report_name_map = {
            'pl': 'ifrs18_financial_reports.ifrs18_profit_loss_report',
            'bs': 'ifrs18_financial_reports.ifrs18_balance_sheet_report',
            'cf': 'ifrs18_financial_reports.ifrs18_cash_flow_report',
            'equity': 'ifrs18_financial_reports.ifrs18_changes_equity_report',
            'tb': 'ifrs18_financial_reports.ifrs18_trial_balance_report',
            'partner': 'ifrs18_financial_reports.ifrs18_partner_ledger_report',
        }
        report_name = report_name_map.get(self.report_type)
        if not report_name:
            raise ValidationError(_('Unknown report type for PDF export.'))
        return self.env.ref(report_name).report_action(self, data=data)

    def _export_csv(self, data):
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['IFRS 18 Financial Report'])
        writer.writerow(['Company', data.get('company', '').name if hasattr(data.get('company', ''), 'name') else ''])
        writer.writerow(['Period', str(data.get('date_from', '')), 'to', str(data.get('date_to', ''))])
        writer.writerow([])
        if 'sections' in data:
            for sid, section in data['sections'].items():
                writer.writerow([section.get('label', sid)])
                for line in section.get('lines', []):
                    if 'account_lines' in line:
                        for acc_key, acc_val in line['account_lines'].items():
                            writer.writerow(['  ', acc_val['account'].code, acc_val['account'].name, acc_val['amount']])
                    else:
                        writer.writerow(['  ', line.get('name', ''), line.get('amount', 0)])
                writer.writerow(['  Subtotal', section.get('subtotal', 0)])
                writer.writerow([])
        elif 'lines' in data:
            writer.writerow(['Code', 'Name', 'Debit', 'Credit', 'Balance'])
            for line in data['lines']:
                writer.writerow([line['code'], line['name'], line['debit'], line['credit'], line['balance']])
            writer.writerow(['', 'Total', data.get('total_debit', 0), data.get('total_credit', 0), data.get('total_balance', 0)])
        elif 'partners' in data:
            for partner in data['partners']:
                writer.writerow([partner['name'], 'Opening', partner['opening_balance']])
                for tx in partner['transactions']:
                    writer.writerow(['  ', str(tx['date']), tx['ref'], tx['debit'], tx['credit']])
                writer.writerow([partner['name'], 'Closing', partner['closing_balance']])
                writer.writerow([])

        csv_bytes = output.getvalue().encode('utf-8')
        attachment = self.env['ir.attachment'].create({
            'name': f'ifrs18_{self.report_type}_{self.date_to}.csv',
            'datas': base64.b64encode(csv_bytes),
            'mimetype': 'text/csv',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _export_excel(self, data):
        try:
            import openpyxl
        except ImportError:
            raise ValidationError(_('openpyxl library is required for Excel export.'))
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'IFRS 18 Report'
        ws.append(['IFRS 18 Financial Report'])
        ws.append([f'Company: {data.get("company", "")}'])
        ws.append([f'Period: {data.get("date_from", "")} to {data.get("date_to", "")}'])
        ws.append([])
        if 'sections' in data:
            for sid, section in data['sections'].items():
                ws.append([section.get('label', sid)])
                for line in section.get('lines', []):
                    if 'account_lines' in line:
                        for acc_key, acc_val in line['account_lines'].items():
                            ws.append(['  ', acc_val['account'].code, acc_val['account'].name, acc_val['amount']])
                    else:
                        ws.append(['  ', line.get('name', ''), line.get('amount', 0)])
                ws.append(['  Subtotal', '', '', section.get('subtotal', 0)])
                ws.append([])
        elif 'lines' in data:
            ws.append(['Code', 'Name', 'Debit', 'Credit', 'Balance'])
            for line in data['lines']:
                ws.append([line['code'], line['name'], line['debit'], line['credit'], line['balance']])
            ws.append(['', 'Total', data.get('total_debit', 0), data.get('total_credit', 0), data.get('total_balance', 0)])
        elif 'partners' in data:
            for partner in data['partners']:
                ws.append([partner['name'], 'Opening Balance', partner['opening_balance']])
                for tx in partner['transactions']:
                    ws.append(['', str(tx['date']), tx['ref'], tx['debit'], tx['credit']])
                ws.append([partner['name'], 'Closing Balance', partner['closing_balance']])
                ws.append([])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': f'ifrs18_{self.report_type}_{self.date_to}.xlsx',
            'datas': base64.b64encode(buf.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _export_email(self, data):
        if not self.email_to:
            raise ValidationError(_('Email recipient is required for Email export.'))
        pdf_report = self._export_pdf(data)
        if not pdf_report:
            return None
        mail_template = self.env.ref('ifrs18_financial_reports.email_template_ifrs18_report', False)
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)
        return {'type': 'ir.actions.act_window_close'}
