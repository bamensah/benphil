from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class warehouse_inherited(models.Model):
    _inherit = "stock.warehouse"

    code = fields.Char(size=7)
