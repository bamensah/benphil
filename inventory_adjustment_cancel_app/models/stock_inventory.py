# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class AccountMove(models.Model):
    _inherit = "account.move"
    
    def unlink(self):
        if self.env.user.has_group('inventory_adjustment_cancel_app.group_cancel_inventory'):
            self.line_ids.unlink()
        else:
            res = super(AccountMove, self).unlink()
            return res



class Inventory_Inherit(models.Model):
    _inherit = "stock.inventory"

    def cancel_stock_inventory(self):
        for move in self.move_ids :

            lot_id = False
            for lot in move.move_line_ids :
                lot_id = lot.lot_id
            
            if move.location_dest_id.usage == 'inventory' :
                
                if move.product_id.tracking == 'none':

                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id),('lot_id','=',lot_id.id)],limit=1)
                    quant._update_available_quantity(move.product_id,move.location_id,move.quantity_done)
                else :
                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id)],limit=1)
                    quant._update_available_quantity(move.product_id,move.location_id,move.quantity_done,lot_id)
            else :
                if move.product_id.tracking == 'none':
                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id),('lot_id','=',lot_id.id)],limit=1)
                    quant._update_available_quantity(move.product_id,move.location_dest_id,-move.quantity_done)
                else :
                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id)],limit=1)
                    
                    quant._update_available_quantity(move.product_id,move.location_dest_id,-move.quantity_done,lot_id)


            move.sudo()._action_cancel()
            journal_rec = self.env['account.move'].sudo().search([('stock_move_id','=',move.id)],order="id desc", limit=1)
            
            journal_rec.button_draft()
            journal_rec.button_cancel()
            journal_rec.update({'name':'/'})

            journal_rec.sudo().unlink()
            move.sudo().unlink()

        self.write({'state':'cancel'})
        return

class stock_move_line(models.Model):
    _inherit= "stock.move.line"

    def unlink(self):
        #custom code
        flag = True
        
        if not any(line.move_id.inventory_id for line in self):
            flag = False
            

        if flag == False :

            
            for ml in self:
                if ml.state in ('done', 'cancel'):
                    raise UserError(_('You can not delete product moves if the picking is done. You can only correct the done quantities.'))
        #custom code
        
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for ml in self:
            # Unlinking a move line should unreserve.
            if ml.product_id.type == 'product' and not ml.location_id.should_bypass_reservation() and not float_is_zero(ml.product_qty, precision_digits=precision):
                try:
                    self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                except UserError:
                    if ml.lot_id:
                        self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    else:
                        raise
        moves = self.mapped('move_id')
        if flag == False :
            if moves:
                moves._recompute_state()
            res = super(stock_move_line, self).unlink()
            return res
        if moves:
            moves._recompute_state()

        return

class stock_move_inherit(models.Model):
    _inherit = "stock.move"


    def _action_cancel(self):
        flag = True
        if not any(move.inventory_id for move in self):
            flag = False

        if flag == False :
            if any(move.state == 'done' for move in self):
                raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))

        for move in self:
            if move.state == 'cancel':
                continue
            move._do_unreserve()
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            if move.propagate_cancel:
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
        return True

    def _do_unreserve(self):

        #custom code
        flag = True
        if not any(move.inventory_id for move in self):
            flag = False

        if flag == False :
            if any(move.state == 'done' for move in self):
                raise UserError(_('You cannot unreserve a stock move that has been set to \'Done\'.'))
        #custom code

        moves_to_unreserve = self.env['stock.move']
        for move in self:
            if move.state == 'cancel':
                # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
                continue
            if move.state == 'done':
                if move.scrapped:
                    # We may have done move in an open picking in a scrap scenario.
                    continue
                
            moves_to_unreserve |= move
        moves_to_unreserve.mapped('move_line_ids').unlink()
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: