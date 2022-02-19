# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class Picking(models.Model):
    _inherit = "stock.picking"

    def action_custom_cancel(self):
        # For Purchase Order (Receipts)
        # For Sale Order (Delivery Order)
        Quant = self.env['stock.quant']
        if self.picking_type_code == 'outgoing' or self.picking_type_code == 'incoming':
            for move in self.move_lines:
                for ml in move.move_line_ids.filtered(
                        lambda ml: ml.move_id.state == 'done' and
                                   ml.product_id.type == 'product'):
                    qty_done_orig = ml.move_id.product_uom._compute_quantity(
                        ml.qty_done, ml.move_id.product_id.uom_id,
                        rounding_method='HALF-UP')
                    in_date = Quant._update_available_quantity(ml.product_id,
                                                               ml.location_id,
                                                               qty_done_orig,
                                                               lot_id=ml.lot_id,
                                                               package_id=ml.result_package_id,
                                                               owner_id=ml.owner_id)[1]
                    Quant._update_available_quantity(ml.product_id,
                                                     ml.location_dest_id,
                                                     -qty_done_orig,
                                                     lot_id=ml.lot_id,
                                                     package_id=ml.package_id,
                                                     owner_id=ml.owner_id,
                                                     in_date=in_date)

                    move.write({'state': 'cancel'})
                    if ml.lot_id:
                        ml.update({'lot_id': '', 'qty_done': 0.00})
                    ml.update({'qty_done': 0.00})
                    ml.write({'state': 'cancel'})
                    self.write({'state': 'cancel'})

    def action_draft(self):
        pickings = self.filtered(lambda p: p.state in ['cancel'])
        return pickings.write({'state': 'draft'})
