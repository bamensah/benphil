from odoo import fields, models,_,api
from datetime import date,datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    remarks_for_purchase = fields.Text(string = "Remarks for Purchase")
    is_remarks_for_purchase = fields.Boolean(related="company_id.remark_for_purchase_order",string = "Is Remarks for Purchase")