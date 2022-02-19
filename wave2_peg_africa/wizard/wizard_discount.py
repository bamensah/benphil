from datetime import datetime
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

TYPE = [
    ('free_days', 'Free days'),
    ('amount', 'Amount'),
]


class WizardFreeDay(models.TransientModel):
    _name = 'wave.peg.africa.discount'
    _description = 'Discount'

    # @api.onchange('type')
    # def _reset_days_or_amount(self):
    #     if not self.type:
    #         self.days = 0
    #         self.amount = 0.0
    #     elif self.type == 'free_days':
    #         self.amount = 0.0
    #     else:
    #         self.days = 0
    #     return

    invoice_id = fields.Many2one('account.move', string='Invoice')
    type = fields.Selection(TYPE, required=True)
    days = fields.Integer('Free days', store=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self._default_company_id())
    tag_id = fields.Many2one('discount.tag', string='Discount Tags', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, \
                                  default=lambda self: self.env.user.company_id.currency_id.id, store=True)
    amount = fields.Monetary('Amount')

    def _default_company_id(self):
        invoice_id = self.env.context.get('invoice_id', False)
        invoice = self.env["account.move"].search([('id', '=', invoice_id)], limit=1)
        return invoice.company_id.id

    def action_confirm(self):
        invoice_id = self.env.context.get('invoice_id', False)
        if not invoice_id:
            raise UserError("This invoice doesn't exist!")
        self.invoice_id = self.env["account.move"].browse(invoice_id)
        if (not self.invoice_id.paygops_id) and (self.type == 'free_days'):
            raise UserError("You can just choose Amount")
        sale_order = self.invoice_id.sale_order_id
        ref_pricing_amount = 0
        account_analytic_id = False
    
        if self.days:
            minimum_amount_days = sale_order.payment_term_id.rate_type.value
            minimum_amount_value = sale_order.payment_term_id.rate_amount
            if minimum_amount_days:
                ref_pricing_amount = self.days * (minimum_amount_value / minimum_amount_days)
        elif self.amount:
            ref_pricing_amount = self.amount
        else:
            pass
        if ref_pricing_amount:
            product = self.tag_id.product_id
            account_id = self.tag_id.account_id.id
            journal_id = self.tag_id.journal_id.id
            discount_tax_id = self.tag_id.tax_id.id if self.tag_id.tax_id else self.env['account.tax'].search([
                ('name', '=', 'TVA Discount'),
                ('company_id', '=', self.invoice_id.company_id.id)
            ], limit=1).id
            account_analytic_id = self.invoice_id.invoice_line_ids[0].analytic_account_id
            credit_note = self.env['account.move'].create({
                'move_type': 'out_refund',
                'partner_id': sale_order.partner_id.id,
                'sale_order_id': sale_order.id,
                'invoice_date': fields.Date.context_today(self),
                'date': datetime.now(),
                'journal_id': journal_id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'account_id': account_id,
                    'analytic_account_id': account_analytic_id.id if account_analytic_id else False,
                    'price_unit': ref_pricing_amount,
                    'tax_ids': [(4, discount_tax_id)],
                })]
            })
    
            sale_order.write({
                'outstanding_balance': sale_order.payment_term_id.financed_price - sale_order.total_amount_paid - sale_order.discount_given
            })
    
        return True
