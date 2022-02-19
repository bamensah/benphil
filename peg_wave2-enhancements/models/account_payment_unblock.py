from odoo import models, fields, api


class comfirm_unblock_payment_wizard(models.TransientModel):
    _name = 'comfirm_unblock_payment_wizard'
    _description = 'Wizard to Confirm Unblock Payments'

    def confirm_unblock_payments(self):
        payments = self.env['account.payment'].browse(
            self._context.get('active_ids', []))
        payments.confirm_unblock()
        return payments
