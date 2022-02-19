from operator import mod
from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    date = fields.Datetime('Date', default=fields.Datetime.now, related="move_id.date")

    remarks_for_picking = fields.Text(string = "Remarks for picking",related="move_id.remarks_for_picking")
    is_remarks_for_picking = fields.Boolean(related="company_id.remark_for_picking",string = "Is Remarks for picking")

    remarks_for_adjustment = fields.Text(string = "Remarks for adjustment",related="move_id.remarks_for_adjustment")
    is_remarks_for_adjustment = fields.Boolean(related="company_id.remark_for_adjustment",string = "Is Remarks for adjustment")

    remarks_for_scrap = fields.Text(string = "Remarks for scrap",related="move_id.remarks_for_scrap")
    is_remarks_for_scrap = fields.Boolean(related="company_id.remark_for_scrap",string = "Is Remarks for scrap")