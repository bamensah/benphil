## -*- coding: utf-8 -*-
#from odoo import models, fields, api, _
#from odoo.addons import decimal_precision as dp
#from odoo.exceptions import ValidationError


#class SaleProductTemplateLineInherit(models.Model):
#    _inherit = 'sale.product.template.line'
#    _description = 'Sale Product Template Line Inherit'

#    _order = 'sequence,id'

#    tax_id = fields.Many2many('account.tax', string='Taxes',
#                              domain=['|', ('active', '=', False), ('active', '=', True)])
#    account_analytic = fields.Many2one('account.analytic.account', string="Compte Analytique")
#    unit_price = fields.Float(digits=dp.get_precision('Product Template Line'))
#    sequence = fields.Integer(string="Sequence")
#    total = fields.Float(compute='_compute_total', store=True)
#    taxed_total = fields.Float(compute='_compute_total', store=True)
#    price_tax = fields.Float(compute='_compute_total', store=True)

#    @api.depends('unit_price', 'ordered_qty', 'tax_id')
#    def _compute_total(self):
#        for line in self:
#            price = line.unit_price * (1 - (line.discount or 0.0) / 100.0)
#            taxes = line.tax_id.compute_all(price, quantity=line.ordered_qty, product=line.name)
#            line.update({
#                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
#                'taxed_total': taxes['total_included'],
#                'total': taxes['total_excluded'],
#            })


#class SaleProductTemplateInherit(models.Model):
#    _inherit = 'sale.product.template'

#    _sql_constraints = [
#        ('name_uniq', 'UNIQUE (name)',  'You can not have two product template with the same name !')
#    ]

#    # needs to open
#    # @api.model
#    # def create(self, vals):
#    #     for line in self.sale_product_template_ids:
#    #         if not line.account_analytic:
#    #             raise ValidationError(_("You cannot create Custom product template with missing analytic account in line"))
#    #     return super(SaleProductTemplateInherit, self).create(vals)


#    amount_untaxed = fields.Float(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all')
#    amount_tax = fields.Float(string='Taxes', store=True, readonly=True, compute='_amount_all')
#    amount_total = fields.Float(string='Total', store=True, readonly=True, compute='_amount_all', tracking=True,
#                                # track_sequence=6
#                                )

#    @api.depends('sale_product_template_ids.total')
#    def _amount_all(self):
#        """
#        Compute the total amounts of the SO.
#        """
#        for s in self:
#            amount_untaxed = amount_tax = 0.0
#            for line in s.sale_product_template_ids:
#                amount_untaxed += line.total
#                amount_tax += line.price_tax
#            s.update({
#                'amount_untaxed': amount_untaxed,
#                'amount_tax': amount_tax,
#                'amount_total': amount_untaxed + amount_tax,
#            })
