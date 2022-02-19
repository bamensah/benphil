
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class product_template_inherited(models.Model):
    _inherit = 'product.template'
    
    company_ids = fields.Many2many(
        string='Companies', required=True,
        comodel_name='res.company'
    )


class ProductSwapReason(models.Model):
    _name = "swap.reason"
    _description = "Reason for swapping a product"
    _sql_constraints = [('name_unique', 'unique(name)', "This reason already exists")]

    name = fields.Char(string="Reason", required=True)


class ProductRepairOrder(models.Model):
    _inherit = 'repair.order'

    swap_reason = fields.Many2one('swap.reason', 'Reason Category', required=True)
    detailed_reason = fields.Text("Detailed Reason")
    