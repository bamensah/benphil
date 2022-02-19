from odoo import api, fields, models


class SaleOrderTemplateLineInherit(models.Model):
    _inherit = 'sale.order.template.line'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Account Analytic', required=True)
    unit_price = fields.Float(string='Unit Price')
    tax_id = fields.Many2many('account.tax', string='Taxes')
    discount = fields.Float(string='Discount')
    total = fields.Float('Total', compute='_compute_total', store=True)
    taxed_total = fields.Float('Taxed Total', compute='_compute_total', store=True)
    price_tax = fields.Float(compute='_compute_total', store=True)


    @api.depends('unit_price', 'product_uom_qty', 'tax_id')
    def _compute_total(self):
        for line in self:
            price = line.unit_price * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, quantity=line.product_uom_qty)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'taxed_total': taxes['total_included'],
                'total': taxes['total_excluded'],
            })


class SaleOrderTemplateInherit(models.Model):
    _inherit = 'sale.order.template'

    payment_term_id = fields.Many2one('account.payment.term', ondelete='restrict')

