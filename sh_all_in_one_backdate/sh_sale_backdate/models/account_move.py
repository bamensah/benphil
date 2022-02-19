from odoo import fields, models,_,api
from datetime import date,datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    remarks_for_sale = fields.Text(string = "Remarks for Sale" )
    is_remarks_for_sale = fields.Boolean(related="company_id.remark_for_sale_order",string = "Is Remarks for Sale")