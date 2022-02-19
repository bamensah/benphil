# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountInvoiceInherit(models.Model):
    _inherit = "account.move"
    #_inherit = "account.invoice"

    # needs to open

#    W1E-42-add product template invoice tree view
    product_template = fields.Char(compute='_compute_product_template')
    product_template_store = fields.Char(string="Product Template")

    def action_post(self):
        for invoice in self.filtered(lambda invoice: invoice.partner_id not in invoice.message_partner_ids):
            invoice.message_subscribe([invoice.partner_id.id])
   
             # Auto-compute reference, if not already existing and if configured on company
             # if not invoice.reference and invoice.type == 'in_invoice':
             #     invoice.reference = invoice._get_computed_reference()
            if not invoice.payment_reference and invoice.move_type == 'in_invoice':
                 # invoice.payment_reference = invoice._get_computed_reference()
                invoice.payment_reference = invoice._get_invoice_computed_reference()
        self._check_duplicate_supplier_reference()
    
         # add by khk
        for invoice in self:
            for invoice_line in invoice.invoice_line_ids:
                if invoice_line.landed_cost_line_origin:
                    invoice_line.landed_cost_line_origin.write({'invoiced': True})
         #self.write({'state': 'post'})
    
        return super(AccountInvoiceInherit, self).action_post()


#    W1E-42-add product template invoice tree view
    @api.depends('invoice_origin')
    def _compute_product_template(self):
        for record in self:
            record.product_template = ""
            if record.invoice_origin:
                origins = record.invoice_origin.split(",")
                for origin in origins:
                    origin = origin.strip()
                    if origin.lower().startswith("so"):
                        sale_order = self.env['sale.order'].search(['&', ('name', '=', origin), ('company_id', '=', self.env.user.company_id.id)])
                        if sale_order.sale_order_template_id:
                            if type(sale_order.sale_order_template_id.name) == str:
                                if sale_order.sale_order_template_id.name not in record.product_template:
                                    record.product_template += sale_order.sale_order_template_id.name + " "
            record.write({ "product_template_store": record.product_template })

class AccountInvoiceLoineInherit(models.Model):
    _inherit = "account.move.line"
    #_inherit = "account.invoice.line"

    landed_cost_line_origin = fields.Many2one('stock.landed.cost.lines')
