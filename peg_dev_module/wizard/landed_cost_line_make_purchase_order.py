# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

import odoo.addons.decimal_precision as dp
from odoo import _, api, exceptions, fields, models
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class LandedCostLinesMakeInvoice(models.TransientModel):
    _name = "landed.cost.lines.make.invoice"
    _description = "Landed Cost Line Make Purchase Order"

    supplier_id = fields.Many2one('res.partner', string='Provider',
                                  required=False) # domain=[('category_id', 'child_of', "[(4, ref('base.res_partner_category_0'))]")]
    item_ids = fields.One2many(
        'landed.cost.lines.make.invoice.item',
        'wiz_id', string='Items')
    landed_cost_id = fields.Many2one('stock.landed.cost',
                                        string='Landed Cost',
                                        required=False,
                                        domain=[('state', '=', 'draft')])

    # needs
    # to
    # open

    @api.model
    def _prepare_item(self, line):
        """ prepare every selected landed cost line who will passed to _prepare_invoice_line function """
        return {
            'line_id': line.id,
            'request_id': line.cost_id.id,
            'product_id': line.product_id.id,
            'account_id': line.account_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            'name': line.name or line.product_id.name,
            'price_unit': line.price_unit,
            'product_qty': 1, # landed cost has no qty cuz i define 1 for the invoice line
#            'date_planned': line.cost_id.date,
            }

    @api.model
    def default_get(self, fields):
        """ recover the selected landed cost line and prepare line for the invoice"""
        res = super(LandedCostLinesMakeInvoice, self).default_get(
            fields)
        landed_cost_line_obj = self.env['stock.landed.cost.lines']
        landed_cost_line_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        if not landed_cost_line_ids:
            return res
        assert active_model == 'stock.landed.cost.lines', \
            'Bad context propagation'

        items = []
        #self._check_valid_request_line(request_line_ids)
        landed_lines = landed_cost_line_obj.browse(landed_cost_line_ids)
        for line in landed_lines:
            if not line.invoiced:
                items.append([0, 0, self._prepare_item(line)])
        res['item_ids'] = items
        return res

    # needs to open

    # @api.model
    def _prepare_invoice(self):
        """ this function prepare the invoice data"""
        if not self.supplier_id:
            raise exceptions.Warning(
                _('Enter a supplier.'))
        supplier = self.supplier_id
        data = {
            'partner_id': self.supplier_id.id,
#            'date_invoice': str(datetime.today()),
            'invoice_date': str(datetime.today()),
            'journal_id': self.env['account.journal'].search([('type', '=', 'purchase')], limit=1).id,  # by khk
#            'account_id': self.env['account.account'].search([('code', '=', '401100')], limit=1).id,  # by khk
            'state': 'draft',
            'move_type': 'in_invoice',
#            'company_id': self.env.user.company_id.id,
            }
        return data

    # needs to open

    # @api.model
    def _prepare_invoice_line(self,purchase,item):
        """ this function prepare the invoice line"""
        res = dict()
        product = item.product_id
        for record in self:
            lines = []
            for line in record.item_ids:
                _logger.info("quantité => %s",(line.product_qty))
                lines.append((0, 0, {
#                    'type': 'src',
                    'name': line.product_id.name,
#                    'invoice_id': purchase.id,
                    'move_id': purchase.id,
                    'product_id': line.product_id.id,
                    'account_id':line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
#                    'account_analytic_id': line.account_analytic_id.id,
                    'analytic_account_id': line.account_analytic_id.id,
                    'quantity': line.product_qty,
                    'price_unit': line.price_unit,
                    'product_uom_id': product.uom_po_id.id,
                    'landed_cost_line_origin': line.line_id.id,
                }))
        return lines

    def make_invoice(self):
        """ this function is called when user clic on make invoice"""
        res = []
#        invoice_obj = self.env['account.invoice']
#        invoice_line_obj = self.env['account.invoice.line']
        invoice_obj = self.env['account.move']
        invoice_line_obj = self.env['account.move.line']
        invoice = False
        for item in self.item_ids:
            line = item.line_id
#            if self.landed_cost_id:
#                invoice = self.landed_cost_id
            if not invoice:
                invoice_data = self._prepare_invoice()
                invoice = invoice_obj.create(invoice_data)
            values = self._prepare_invoice_line(invoice,item)
            if invoice:
                invoice.write({
                    'invoice_line_ids': values,
                })
#            purchase_order_line = invoice_line_obj.create(values)
            res.append(invoice.id)
            return {
                'domain': [('id', 'in', res)],
                'name': _('Invoice'),
                'view_type': 'form',
                'view_mode': 'tree,form',
#                'res_model': 'account.invoice',
                'res_model': 'account.move',
                'view_id': False,
#                'context': {'form_view_ref':'base.action_partner_supplier_form'},
                'type': 'ir.actions.act_window'
            }


class PurchaseRequestLineMakeInvoiceItem(models.TransientModel):
    _name = "landed.cost.lines.make.invoice.item"
    _description = "Landed Cost Line Make Purchase Order Item"

    wiz_id = fields.Many2one(
        'landed.cost.lines.make.invoice',
        string='Wizard', required=True, ondelete='cascade',
       )

    line_id = fields.Many2one('stock.landed.cost.lines',
                              string='Purchase Request Line',
                              )
    request_id = fields.Many2one('stock.landed.cost',
                                 related='line_id.cost_id',
                                 string='Landed Cost',
                                 )
    product_id = fields.Many2one('product.product', string='Product')

    account_id = fields.Many2one('account.account', string='Compte',
                                    required=True,
                                    domain=[('deprecated', '=', False)],
                                    help="The income or expense account related to the selected product.")

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          tracking=True)

    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(string='Quantity to invoice',
                               digits=dp.get_precision('Product UoS'),
                               )
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))

    # needs to open

    @api.onchange('product_id')
    def onchange_product_id(self):
        """this function update line when user change product """
        if self.product_id:
            name = self.product_id.name
            code = self.product_id.code
            self.account_id = self.product_id.property_account_expense_id.id or self.product_id.categ_id.property_account_expense_categ_id
            sup_info_id = self.env['product.supplierinfo'].search([
                '|', ('product_id', '=', self.product_id.id),
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('name', '=', self.wiz_id.supplier_id.id)])
            if sup_info_id:
                p_code = sup_info_id[0].product_code
                p_name = sup_info_id[0].product_name
                name = '[%s] %s' % (p_code if p_code else code,
                                    p_name if p_name else name)
            else:
                if code:
                    name = '[%s] %s' % (code, name)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
#            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1.0
            self.name = name

