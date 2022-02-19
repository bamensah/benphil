# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class StockRuleInherit(models.Model):
    _inherit = 'stock.rule'

#    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        """update the stock move record by recovering the analytic account """
        res = super(StockRuleInherit, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, 
                                                            origin, company_id, values)
        _logger.info('THE NUMBER OF ORIGIN ' + str(values.get('number', False)))
        res['analytic_account_id'] = values.get('analytic_account_id', False)
        res['number'] = values.get('number', False)
        return res
