# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockMoveExt(models.Model):
    _inherit = 'stock.move'

    scrap_product_line_id = fields.Many2one('scrap.product.line', 'Scrap Line')

class ScrapProductsByQuantity(models.Model):
    _name = 'scrap.products.by.quantity'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _description ='Bulk Scrap'

    def _get_default_scrap_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        return self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id

    def _get_default_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    name = fields.Char('Reference',  default=lambda self: _('New'),
        copy=False, readonly=True, required=True,
        states={'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True,
                                 states={'done': [('readonly', True)]})
    src_location_id = fields.Many2one('stock.location', string='Source Location', domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id, check_company=True)
    dest_location_id = fields.Many2one('stock.location', string='Scrap Location', default=_get_default_scrap_location_id,
        domain="[('scrap_location', '=', True), ('company_id', 'in', [company_id, False])]", required=True, states={'done': [('readonly', True)]}, check_company=True)
    date = fields.Date(default=fields.Date.today())
    scrap_line = fields.One2many('scrap.product.line', 'scrap_id', string='Order Lines', copy=True, states={'done': [('readonly', True)]},required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], string='Status', default='draft', readonly=True, tracking=True)
    date_done = fields.Datetime('Done date', readonly=True)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
            self.location_id = warehouse.lot_stock_id
            self.scrap_location_id = self.env['stock.location'].search([
                ('scrap_location', '=', True),
                ('company_id', 'in', [self.company_id.id, False]),
            ], limit=1)
        else:
            self.location_id = False
            self.scrap_location_id = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            sequence = self.env.ref('scrap_multi_products.bulk_scrap_sequence')
            vals['name'] = sequence.next_by_id() or 'New'
        res = super(ScrapProductsByQuantity, self).create(vals)
        return res

    def unlink(self):
        if 'done' in self.mapped('state'):
            raise UserError(_('You cannot delete a scrap which is done.'))
        return super(ScrapProductsByQuantity, self).unlink()

    def action_done(self):
        self._check_company()
        StockMove = self.env['stock.move']
        for rec in self:
            for line in rec.scrap_line:
                res = StockMove.create({
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_uom.id,
                    'location_id': line.src_loc_id.id,
                    'name': line.product_id.name,
                    'location_dest_id': line.dest_loc_id.id,
                    'product_id': line.product_id.id,
                    'origin': rec.name,
                    'scrapped': True,
                    'scrap_product_line_id':line.id,
                    'move_line_ids': [(0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom.id,
                        'qty_done': line.quantity,
                        'location_id': line.src_loc_id.id,
                        'location_dest_id': line.dest_loc_id.id,
                    })],
                })
                res.with_context(is_scrap=True)._action_done()
            rec.state = 'done'
            rec.date_done = fields.Datetime.now()
        return True

    def action_get_stock_move_lines(self):
        action = self.env.ref('stock.stock_move_line_action').read([])[0]
        line_ids = self.scrap_line.ids
        moves = self.env['stock.move'].search([('scrap_product_line_id', 'in', line_ids)])
        action['domain'] = [('move_id', 'in', moves.ids)]
        return action


class ScrapProductLine(models.Model):
    _name = 'scrap.product.line'
    _description = 'Bulk Scrap Process Line'

    @api.depends('product_id', 'src_loc_id')
    def _get_available_qty(self):
        quant_obj = self.env['stock.quant']
        for rec in self:
            rec.available_qty = 0.0
            if rec.product_id and rec.src_loc_id:
                quants = quant_obj.search(
                    [('product_id', '=', rec.product_id.id), ('location_id', '=', rec.src_loc_id.id)])
                rec.available_qty = sum(quants.mapped('quantity'))

    scrap_id = fields.Many2one('scrap.products.by.quantity', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', 'Product Name', ondelete='restrict',required=True)
    quantity = fields.Float(string='Scrap Quanity',required=True)
    available_qty = fields.Float(string='Available Quanity', compute="_get_available_qty", store=True)
    src_loc_id = fields.Many2one('stock.location', string='Source Location',required=True)
    dest_loc_id = fields.Many2one('stock.location', string="Scrap Location",required=True)
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', string='Product Unit of Measure',required=True)

    _sql_constraints = [
        ('qty_gt_zero', 'CHECK (quantity>0.00)', 'Product Quantity to be scrapped needs to be greater than 0.'),
    ]

    @api.onchange('product_id', 'src_loc_id')
    def get_quantity(self):
        quant_obj = self.env['stock.quant']
        if self.product_id and self.src_loc_id:
            quants = quant_obj.search([('product_id', '=', self.product_id.id), ('location_id', '=',   self.src_loc_id.id)])
            self.quantity = sum(quants.mapped('quantity'))

        valid_product_ids = []
        products = self.env['product.product'].search([])
        for product in products:
            quants = quant_obj.search(
                [('product_id', '=', product.id), ('location_id', '=', self.src_loc_id.id)])
            available_qty = sum(quants.mapped('quantity'))
            if available_qty > 0.00:
                valid_product_ids.append(product.id)

        return {'domain':{'product_id':[
            ('id','in',valid_product_ids),
            ('type', 'in', ['product', 'consu']),
            '|', ('company_id', '=', False), ('company_id', '=', self.scrap_id.company_id.id)
        ]}}

    @api.onchange('quantity')
    def onchange_scrap_qty(self):
        if self.quantity and self.quantity > self.available_qty:
            raise UserError("You can't scrap more than available quantity.")
