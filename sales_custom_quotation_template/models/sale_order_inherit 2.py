from odoo import api, fields, models
from datetime import datetime, timedelta


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('sale_order_template_id')
    def product_template_id_changes(self):
        """ fucntion is defined in sh_sales_custom_product_template
         we override it for addinq tax_id in sale_order_line"""

        if self.sale_order_template_id:
            sale_ordr_line = []
            self.order_line = [(5, 0, 0)]

            for record in self.sale_order_template_id.sale_order_template_line_ids:

                vals = {}
                vals.update({'price_unit': record.unit_price,
                             #                             'order_id':self.id,
                             'name': record.name,
                             'product_uom_qty': record.product_uom_qty,
                             'tax_id': record.tax_id,
                             'account_analytic': record.account_analytic_id.id,
                             'discount': record.discount,
                             'product_uom': record.product_uom_id.id
                             })

                if record.name:
                    vals.update({'product_id': record.product_id.id})

                sale_ordr_line.append((0, 0, vals))

            self.order_line = sale_ordr_line

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_get_order_line_from_sale_product_template_line(self):
        """this function is define for generating sale order line from product
        template lines"""
        self.ensure_one()
        for order_line in self.order_line:
            order_line.unlink()
        self.product_template_id_changes()

    # def action_get_order_line_from_sale_product_template_line(self):
    #     """this function is define for generating sale order line from product
    #     template lines"""
    #     self.ensure_one()
    #     products = []
    #     if self.sale_order_template_id:
    #         for order_line in self.order_line:
    #             order_line.unlink()
    #         for qt in self.sale_order_template_id.sale_order_template_line_ids:
    #             products.append({
    #                 ''
    #             })
    #
    #         print('--products--', products)
    #         # current_template_id = self.sale_order_template_id
    #         self.write({
    #             # 'sale_order_template_id': current_template_id,
    #             'order_line': [(0, 0, products)]
    #         })

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):

        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return

        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        self.update({
            'type_of_product_id': template.type_of_product_id.id,
            'payment_term_id': template.payment_term_id.id
        })
        # --- first, process the list of products from the template
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)

            if line.product_id:
                price = line.product_id.lst_price
                discount = 0

                if self.pricelist_id:
                    pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(
                        line.product_id, 1, False)

                    if self.pricelist_id.discount_policy == 'without_discount' and price:
                        discount = max(0, (price - pricelist_price) * 100 / price)
                    else:
                        price = pricelist_price

                data.update({
                    'price_unit': line.unit_price,
                    'discount': line.discount,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                    'tax_id': [(6, 0, line.tax_id.ids)],
                    'account_analytic': line.account_analytic_id.id,
                })
            print('-----dataaaa', data)

            order_lines.append((0, 0, data))
            print('-----order_lines--', order_lines)
        self.order_line = order_lines
        self.order_line._compute_tax_id()

        # then, process the list of optional products from the template
        option_lines = [(5, 0, 0)]
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            option_lines.append((0, 0, data))

        self.sale_order_option_ids = option_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment

        if template.note:
            self.note = template.note


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    account_analytic = fields.Many2one('account.analytic.account', string="Analytical Account",required=True)



