# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PickingTypeInherit(models.Model):
    _inherit = 'stock.picking.type'
    
    use_import_lots = fields.Boolean(
        'Recover Lots/Serial Numbers from imports', default=True,
        help="If this is checked only, it will suppose you want to recover Lots/Serial Numbers from import, so you can provide them in a text field. ")