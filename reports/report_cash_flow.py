from odoo import models


class CashFlowReport(models.AbstractModel):
    _name = 'report.ifrs18_financial_reports.ifrs18_cash_flow_report'
    _description = 'IFRS 18 Cash Flow PDF Report'

    def _get_report_values(self, docids, data=None):
        wizard = self.env['ifrs18.report.wizard'].browse(docids)
        report_data = wizard._compute_report()
        return {
            'doc_ids': docids,
            'doc_model': 'ifrs18.report.wizard',
            'docs': wizard,
            'data': report_data,
        }
