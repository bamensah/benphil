from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class PaymentTermInherit(models.Model):
    _inherit = "account.payment.term"

    rate_amount = fields.Float(
        string="Rate Amount", help="Fixed amount to be paid on a Rate Type basis")

    seasonal_rate_amount = fields.Float(string="Seasonal Rate Amount")

    rate_type = fields.Many2one(
        comodel_name="account.payment.term.rate_type",
        string="Rate Type"
    )

    is_seasonal_rate = fields.Boolean(compute='_check_seasonal_rate_type')
    seasonal_period = fields.Integer(string="Seasonal Period", help="Days")
    
    penalty_value =  fields.Float(
        string='Penalty Value'
    )

    loan_period = fields.Integer("Loan Period")

    cash_price = fields.Float("Cash Price")

    financed_price = fields.Float("Financed Price")

    deposit_amount = fields.Float("Deposit Amount")

    free_days = fields.Integer("Free Days")

    loan_type = fields.Selection([('loan', 'Loan'), ('cash', 'Cash')], string="Loan Type", required=True)
    
    @api.depends('rate_type')
    def _check_seasonal_rate_type(self):
        if self.rate_type:
            if 'seasonal' in self.rate_type.name.lower():
                self.is_seasonal_rate = True
            else:
                self.is_seasonal_rate = False
                self.seasonal_rate_amount = None
        else:
            self.is_seasonal_rate = False


class PaymentTermRateType(models.Model):
    _name = "account.payment.term.rate_type"
    _description = "Rate Types for Payment Term"

    name = fields.Char("Name")
