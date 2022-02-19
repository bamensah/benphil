# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'
    
#    @api.multi
#    def _prepare_stock_moves(self, picking):
#        """ Prepare the stock moves data for one order line. This function returns a list of
#        dictionary ready to be used in stock.move's create()
#        """
#        self.ensure_one()
#        res = []
#        if self.product_id.type not in ['product', 'consu']:
#            return res
#        qty = 0.0
#        price_unit = self._get_stock_move_price_unit()
#        for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
#            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
#        template = {
#            'name': self.name or '',
#            'product_id': self.product_id.id,
#            'product_uom': self.product_uom.id,
#            'date': self.order_id.date_order,
#            'date_expected': self.date_planned,
#            'location_id': self.order_id.partner_id.property_stock_supplier.id,
#            'location_dest_id': self.order_id._get_destination_location(),
#            'picking_id': picking.id,
#            'partner_id': self.order_id.dest_address_id.id,
#            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
#            'state': 'draft',
#            'purchase_line_id': self.id,
#            'company_id': self.order_id.company_id.id,
#            'price_unit': price_unit,
#            'picking_type_id': self.order_id.picking_type_id.id,
#            'group_id': self.order_id.group_id.id,
#            'origin': self.order_id.name,
#            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
#            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
#            'analytic_account_id': self.account_analytic_id.id
#        }
#        diff_quantity = self.product_qty - qty
#        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
#            quant_uom = self.product_id.uom_id
#            get_param = self.env['ir.config_parameter'].sudo().get_param
#            if self.product_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
#                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
#                template['product_uom'] = quant_uom.id
#                template['product_uom_qty'] = product_qty
#            else:
#                template['product_uom_qty'] = diff_quantity
#            res.append(template)
#        return res
    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLineInherit, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        res.update({
            'analytic_account_id': self.account_analytic_id.id
        })
        return res
    
class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'
    
#    @api.multi
    def button_confirm(self):
        for line in self.order_line:
            _logger.info('Testing analytic account check')
            _logger.info(line.account_analytic_id)
            if (not line.account_analytic_id):
                _logger.info('Testing analytic account found')
                raise UserError(_('Specify Analytic Account for all products'))
    
        super(PurchaseOrderInherit, self).button_confirm()
