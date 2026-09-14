from odoo import models


class TrialBalanceReport(models.AbstractModel):
    _name = 'report.ifrs18_financial_reports.ifrs18_trial_balance_report'
    _description = 'IFRS 18 Trial Balance PDF Report'

    def _get_report_values(self, docids, data=None):
        wizard = self.env['ifrs18.report.wizard'].browse(docids)
        report_data = wizard._compute_report()
        return {
            'doc_ids': docids,
            'doc_model': 'ifrs18.report.wizard',
            'docs': wizard,
            'data': report_data,
        }
