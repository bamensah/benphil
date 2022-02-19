# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import float_compare, float_is_zero


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

#    @api.one
#    @api.depends('location_id', 'product_id', 'package_id',
#                 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id',
#                 'inventory_id.force_inventory_date')
#    def _compute_theoretical_qty(self):
#        if not self.inventory_id.force_inventory_date:
#            return super()._compute_theoretical_qty()
#        if not self.product_id:
#            self.theoretical_qty = 0
#            return
#        product_at_date = self.env['product.product'].with_context({
#            'to_date': self.inventory_id.date,
#            'location': self.location_id.id,
#            'compute_child': False,
#        }).browse(self.product_id.id)
#        theoretical_qty = product_at_date.qty_available
#        if theoretical_qty and self.product_uom_id and \
#                self.product_id.uom_id != self.product_uom_id:
#            theoretical_qty = self.product_id.uom_id._compute_quantity(
#                theoretical_qty, self.product_uom_id)
#        self.theoretical_qty = theoretical_qty
    
    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id','inventory_id.force_inventory_date')
    def _onchange_quantity_context(self):
        if self.inventory_id.force_inventory_date:
#            if self.product_id:
#                self.product_uom_id = self.product_id.uom_id
#            if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
#                product_at_date = self.env['product.product'].with_context({
#                    'to_date': self.inventory_id.date,
#                    'location': self.location_id.id,
#                    'compute_child': False,
#                }).browse(self.product_id.id)
#                theoretical_qty = product_at_date.qty_available
#            else:
#                theoretical_qty = 0
#            # Sanity check on the lot.
#            if self.prod_lot_id:
#                if self.product_id.tracking == 'none' or self.product_id != self.prod_lot_id.product_id:
#                    self.prod_lot_id = False

#            if self.prod_lot_id and self.product_id.tracking == 'serial':
#                # We force `product_qty` to 1 for SN tracked product because it's
#                # the only relevant value aside 0 for this kind of product.
#                self.product_qty = 1
#            elif self.product_id and float_compare(self.product_qty, self.theoretical_qty, precision_rounding=self.product_uom_id.rounding) == 0:
                # We update `product_qty` only if it equals to `theoretical_qty` to
                # avoid to reset quantity when user manually set it.
            product_at_date = self.env['product.product'].with_context({
                'to_date': self.inventory_id.date,
                'location': self.location_id.id,
                'compute_child': False,
            }).browse(self.product_id.id)
            theoretical_qty = product_at_date.qty_available
            
            self.product_qty = theoretical_qty
            self.theoretical_qty = theoretical_qty
        return super(StockInventoryLine, self)._onchange_quantity_context()
        
