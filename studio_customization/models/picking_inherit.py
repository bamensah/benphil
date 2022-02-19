from odoo import api, fields, models


class StockPickingTypeInherit(models.Model):
    _inherit = 'stock.picking.type'

    field_oS0P2 = fields.Many2one('res.company', string='Sociétés')
