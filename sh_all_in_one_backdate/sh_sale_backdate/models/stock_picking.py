from odoo import fields, models,_,api
from datetime import date,datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks_for_sale = fields.Text(string = "Remarks for Sale",related="sale_id.remarks")
    is_remarks_for_sale = fields.Boolean(related="company_id.remark_for_sale_order",string = "Is Remarks for Sale")

    @api.depends('move_lines.state', 'move_lines.date', 'move_type')
    def _compute_scheduled_date(self):
        for picking in self:
            moves_dates = picking.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')).mapped('date')
            if picking.move_type == 'direct':
                picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
            else:
                picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())

            if not picking.company_id.backdate_for_stock_move:
                picking.scheduled_date = datetime.now()
            
            if picking.company_id.backdate_for_stock_move and picking.sale_id:
                picking.scheduled_date = picking.sale_id.date_order
    
    def write(self,vals):
        for rec in self:
            if rec.sale_id and 'date_done' in vals:
                vals['date_done'] =  rec.sale_id.date_order
            
            return super(StockPicking,self).write(vals)
            
    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_lines.write({'date': picking.scheduled_date})