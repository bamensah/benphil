from odoo import models, fields, api, _, exceptions
import logging 
_logger = logging.getLogger(__name__)


class StockAction(models.Model):
    _name = 'invoice.stock.action'
    _description = 'Stock Action'

    invoice_id = fields.Many2one('account.move', string='Invoice', required=True)
    stock_action_lines = fields.One2many('invoice.stock.action.line', 'stock_action_id', string='Stock Action Lines', copy=True)

    # migrate later v14 --------------
    @api.model
    def create(self, vals):
        result = super(StockAction, self).create(vals)
        if result.invoice_id:
            result.get_stock_action_lines()
        return result
    #
    def get_stock_action_lines(self):
        default_products = []
        if self.invoice_id:
            invoice_id = self.env['account.move'].browse(self.invoice_id.id)
            sale_order_ref = self.env['sale.order'].search([
            ('name', '=', self.invoice_id.invoice_origin)], limit=1)
            status = self.env.ref('wave2_peg_africa.stock_action_no_action')

            if sale_order_ref:
                if (sale_order_ref.contract_status != None) and (sale_order_ref.contract_status.name == self.env.ref('wave2_peg_africa.contract_status_written_off').name):
                    status = self.env.ref('wave2_peg_africa.stock_action_to_be_repossessed')
            picking = self.env['stock.picking'].search([
                ('origin', '=', invoice_id.invoice_origin), ('backorder_id', '=', None), ('company_id', '=', invoice_id.company_id.id)
            ], limit=1)
            for move in picking.move_ids_without_package:
                for move_line in move.move_line_ids:
                    if move_line.lot_ids:
                        default_products.append(
                            (0, 0, {
                                'product_id': move_line.product_id.id,
                                'device_serial': move_line.lot_id.id,
                                'status': status.id
                            })
                        )
            self.update({'stock_action_lines': default_products})
            self.action_validate()
    #
    def action_validate(self):
        status_list = []
        sale_order_ref = self.env['sale.order'].search([
            ('name', '=', self.invoice_id.invoice_origin)
        ], limit=1)
        sale_order_ref.update_stock_action()


class StockActionLine(models.Model):
    _name = 'invoice.stock.action.line'
    _description = 'Stock Action line'

    stock_action_id = fields.Many2one('stock.action', string='Stock Action')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    device_serial = fields.Many2one('stock.production.lot')
    status = fields.Many2one('sale.stock.action', string='Status', default=lambda self: self.env['sale.stock.action'].search(
            [('name', '=', 'No Action')], limit=1))