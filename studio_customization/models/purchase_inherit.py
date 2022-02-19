from odoo import api, fields, models


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    field_uQVgD = fields.Char('Ref PEG')
