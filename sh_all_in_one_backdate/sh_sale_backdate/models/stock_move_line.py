from operator import mod
from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    date = fields.Datetime('Date', default=fields.Datetime.now, related="move_id.date")

    remarks_for_sale = fields.Text(string = "Remarks for sale",related="move_id.remarks_for_sale")
    is_remarks_for_sale = fields.Boolean(related="company_id.remark_for_sale_order",string = "Is Remarks for sale")
