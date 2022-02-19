from operator import mod
from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    date = fields.Datetime('Date', default=fields.Datetime.now, related="move_id.date")

    remarks_for_purchase = fields.Text(string = "Remarks for Purchase",related="move_id.remarks_for_purchase")
    is_remarks_for_purchase = fields.Boolean(related="company_id.remark_for_purchase_order",string = "Is Remarks for Purchase")
