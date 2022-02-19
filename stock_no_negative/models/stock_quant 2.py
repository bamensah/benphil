# ?? 2015-2017 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare


import logging
_logger = logging.getLogger(__name__)

class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains("product_id", "quantity")
    def check_negative_qty(self):
        p = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        check_negative_qty = (
            config["test_enable"] and self.env.context.get("test_stock_no_negative")
        ) or not config["test_enable"]
        if not check_negative_qty:
            return

        for quant in self:
            disallowed_by_product = (
                not quant.product_id.allow_negative_stock
                and not quant.product_id.categ_id.allow_negative_stock
            )
            disallowed_by_location = not quant.location_id.allow_negative_stock
            _logger.info('Checks for no negative')
            _logger.info(quant.location_id)
            _logger.info(quant.quantity)
            _logger.info(float_compare(quant.quantity, 0, precision_digits=p) == -1)
            _logger.info(quant.product_id.type == "product")
            _logger.info(quant.location_id.usage in ["internal", "transit"])
            _logger.info(disallowed_by_product)
            _logger.info(disallowed_by_location)
            
            if (
                float_compare(quant.quantity, 0, precision_digits=p) == -1
                and quant.product_id.type == "product"
                and quant.location_id.usage in ["internal", "transit"]
                and disallowed_by_product
                and disallowed_by_location
            ):
                msg_add = ""
                if quant.lot_id:
                    msg_add = _(" lot '%s'") % quant.lot_id.name_get()[0][1]
                raise ValidationError(
                    _(
                        "You cannot validate this stock operation because the "
                        "stock level of the product '%s'%s would become negative "
                        "(%s) on the stock location '%s' and negative stock is "
                        "not allowed for this product and/or location."
                    )
                    % (
                        quant.product_id.display_name,
                        msg_add,
                        quant.quantity,
                        quant.location_id.complete_name,
                    )
                )