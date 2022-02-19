from odoo import models, fields


class HrPaySlipInherit(models.Model):
    _inherit = 'hr.payslip.run'

    journal_id = fields.Many2one('account.journal', 'Salary Journal', states={'draft': [('readonly', False)]}, readonly=True,
        required=True, default=lambda self: self._default_account_journal())

    def _default_account_journal(self):
        company_name = self.env.user.company_id.name
        query = None
        query = 'salary' if company_name == 'PEG Ghana' else 'salaire'
        return self.env['account.journal'].search([('name', 'ilike', query)], limit=1)