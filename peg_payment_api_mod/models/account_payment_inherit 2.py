from odoo import models, fields, api

class account_payment_inhert(models.Model):
    _inherit = 'account.payment'

    auto_validate = fields.Boolean(string='Auto Validate', default=False)
        