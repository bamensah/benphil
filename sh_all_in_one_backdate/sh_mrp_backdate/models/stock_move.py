from odoo import fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    remarks_for_mrp = fields.Text(string = "Remarks for MRP",)
    is_remarks_for_mrp = fields.Boolean(related="company_id.remark_for_mrp_production",string = "Is Remarks for MRP")

    def write(self,vals):
        for rec in self:
            if rec.company_id.enable_backdate_for_mrp:
                if rec.raw_material_production_id:
                    vals['date'] =  rec.raw_material_production_id.date_planned_start
                    vals['remarks_for_mrp'] = rec.raw_material_production_id.remarks

                if rec.production_id: 
                    vals['date'] =  rec.production_id.date_planned_start
                    vals['remarks_for_mrp'] = rec.production_id.remarks
                
                if rec.created_production_id:
                    vals['date'] = rec.created_production_id.date_planned_start
                    vals['remarks_for_mrp'] = rec.created_production_id.remarks

             
            return super(StockMove,self).write(vals)
    
    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': self.date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()