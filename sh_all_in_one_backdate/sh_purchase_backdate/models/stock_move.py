from odoo import fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    remarks_for_purchase = fields.Text(string = "Remarks for Purchase",related="picking_id.remarks_for_purchase")
    is_remarks_for_purchase = fields.Boolean(related="company_id.remark_for_purchase_order",string = "Is Remarks for Purchase")

    def write(self,vals):
        for rec in self:
            if rec.company_id.backdate_for_stock_move:
                if rec.picking_id:
                    vals['date'] =  rec.picking_id.scheduled_date
            
            return super(StockMove,self).write(vals)
    
    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        date = self._context.get('force_period_date', fields.Date.context_today(self))
        return {
            'journal_id': journal_id,
            'line_ids': move_lines,
            'date': self.date,
            'ref': description,
            'stock_move_id': self.id,
            'stock_valuation_layer_ids': [(6, None, [svl_id])],
            'move_type': 'entry',
        }