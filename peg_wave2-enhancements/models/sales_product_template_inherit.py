# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_product_template_inherit(models.Model):
    _inherit = 'sale.order.template'

    type_of_product_id = fields.Many2one('wave2.peg.africa.type.of.product', string="Type of Product", required=True)