from operator import mod
from odoo import fields, models,_,api
from datetime import date,datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks_for_purchase = fields.Text(string = "Remarks for Purchase",related="purchase_id.remarks")
    is_remarks_for_purchase = fields.Boolean(related="company_id.remark_for_purchase_order",string = "Is Remarks for Purchase")

    @api.depends('move_lines.state', 'move_lines.date', 'move_type')
    def _compute_scheduled_date(self):
        for picking in self:
            moves_dates = picking.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')).mapped('date')
            if picking.move_type == 'direct':
                picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
            else:
                picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())

            if picking.company_id.backdate_for_stock_move:
                if picking.purchase_id.date_approve:
                    picking.scheduled_date = picking.purchase_id.date_approve

    def write(self,vals):
        for rec in self:
            if rec.purchase_id and 'date_done' in vals:
                vals['date_done'] =  rec.purchase_id.date_approve
            
            return super(StockPicking,self).write(vals)
             
    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_lines.write({'date': picking.scheduled_date})