from operator import mod
from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    date = fields.Datetime('Date', default=fields.Datetime.now, related="move_id.date")

    remarks_for_mrp = fields.Text(string = "Remarks for MRP",related="move_id.remarks_for_mrp")
    is_remarks_for_mrp = fields.Boolean(related="company_id.remark_for_mrp_production",string = "Is Remarks for MRP")
