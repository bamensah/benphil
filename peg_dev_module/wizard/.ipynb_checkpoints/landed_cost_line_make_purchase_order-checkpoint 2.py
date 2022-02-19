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

    supplier_id = fields.Many2one('res.partner', string='Customer',
                                  required=False,
                                  domain=[('supplier', '=', True)])
    item_ids = fields.One2many(
        'landed.cost.lines.make.invoice.item',
        'wiz_id', string='Items')
    landed_cost_id = fields.Many2one('stock.landed.cost',
                                        string='Landed Cost',
                                        required=False,
                                        domain=[('state', '=', 'draft')])

    @api.model
    def _prepare_item(self, line):
        return {
            'line_id': line.id,
            'request_id': line.cost_id.id,
            'product_id': line.product_id.id,
            'account_id': line.account_id.id,
            #'account_analytic_id': line.account_analytic_id.id,
            'name': line.name or line.product_id.name,
            'price_unit': line.price_unit,
            'product_qty': 1, # landed cost has no qty
            #'product_uom_id': line.product_uom_id.id,
            'date_planned': line.cost_id.date,
            }

    #@api.model
    #def _check_valid_request_line(self, request_line_ids):
    #    location = False
    #    picking_type = False
    #    company_id = False

    #   for line in self.env['stock.landed.cost.lines'].browse(request_line_ids):
    #        if line.request_id.state != 'approved':
    #           raise exceptions.Warning(
    #                _('Purchase Request %s is not approved') %
    #                line.request_id.name)
    #        
    #        if line.purchase_state == 'done':
    #            raise exceptions.Warning(
    #                _('The purchase has already been completed.'))       
    #       line_company_id = line.company_id \
    #            and line.company_id.id or False
    #        if company_id is not False \
    #               and line_company_id != company_id:
    #            raise exceptions.Warning(
    #                _('You have to select lines '
    #                  'from the same company.'))
    #        else:
    #            company_id = line_company_id
    #        
    #        line_picking_type = line.request_id.picking_type_id or False
    #        if not line_picking_type:
    #            raise exceptions.Warning(
    #                _('You have to enter a Picking Type.'))
    #        if picking_type is not False \
    #                and line_picking_type != picking_type:
    #            raise exceptions.Warning(
    #                _('You have to select lines '
    #                  'from the same Picking Type.'))
    #        else:
    #            picking_type = line_picking_type
    #        
    #        line_location = line.procurement_id and \
    #            line.procurement_id.location_id or False
    #        
    #        if location is not False and line_location != location and \
    #                line_location:
    #            raise exceptions.Warning(
    #                _('You have to select lines '
    #                  'from the same procurement location.'))
    #        else:
    #            location = line_location

    @api.model
    def default_get(self, fields):
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
            items.append([0, 0, self._prepare_item(line)])
        res['item_ids'] = items
        #supplier_ids = request_lines.mapped('supplier_id').ids
        #if len(supplier_ids) == 1:
        #    res['supplier_id'] = supplier_ids[0]
        return res

    @api.model
    def _prepare_invoice(self):
        if not self.supplier_id:
            raise exceptions.Warning(
                _('Enter a supplier.'))
        supplier = self.supplier_id
        data = {
            'partner_id': self.supplier_id.id,
            'invoice_date': str(datetime.today()),
            }
        return data

    @api.model
    def _get_purchase_line_onchange_fields(self):
        return ['product_uom', 'price_unit', 'name',
                'taxes_id']

    @api.model
    def _execute_purchase_line_onchange(self, vals):
        cls = self.env['stock.landed.cost.lines']
        onchanges_dict = {
            'onchange_product_id': self._get_purchase_line_onchange_fields(),
        }
        for onchange_method, changed_fields in onchanges_dict.items():
            if any(f not in vals for f in changed_fields):
                obj = cls.new(vals)
                getattr(obj, onchange_method)()
                for field in changed_fields:
                    vals[field] = obj._fields[field].convert_to_write(
                        obj[field], obj)

    @api.model
    def _prepare_invoice_line(self,purchase,item):
        res = dict()
        product = item.product_id
        for record in self:
            lines = []
            for line in record.item_ids:
                _logger.info("quantité => %s",(line.product_qty))
                lines.append({
                    'name': line.product_id.name,
                    'invoice_id': purchase.id,
                    'product_id': line.product_id.id,
                    'account_id':line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'quantity': line.product_qty,
                    'price_unit': line.price_unit,
                    'uom_id': product.uom_po_id.id,
                })
        return lines

    @api.model
    def _get_purchase_line_name(self, order, line):
        product_lang = line.product_id.with_context({
            'lang': self.supplier_id.lang,
            'partner_id': self.supplier_id.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase
        return name

    @api.model
    def _get_order_line_search_domain(self, order, item):
        vals = self._prepare_invoice_line(order, item)
        name = self._get_purchase_line_name(order, item)
        order_line_data = [('order_id', '=', order.id),
                           ('name', '=', name),
                           ('product_id', '=', item.product_id.id or False),
                           ('account_id', '=', item.account_id.id or False),
                           # ('date_planned', '=', item.line_id.date_required),
                           ('product_uom', '=', vals['product_uom']),
                           ('account_analytic_id', '=',
                            item.account_analytic_id.id or False),
                           ]
        if not item.product_id:
            order_line_data.append(('name', '=', item.name))
        # if not item.line_id.procurement_id and \
        #         item.line_id.procurement_id.location_id:
        #     order_line_data.append(
        #         ('location_id', '=',
        #          item.line_id.procurement_id.location_id.id))
        return order_line_data

    @api.multi
    def make_invoice(self):
        res = []
        purchase_obj = self.env['account.invoice']
        po_line_obj = self.env['account.invoice.line']
        pr_line_obj = self.env['stock.landed.cost.lines']
        purchase = False
        for item in self.item_ids:
            line = item.line_id
            #location = line.request_id.picking_type_id.default_location_dest_id
            if self.landed_cost_id:
                purchase = self.landed_cost_id
            if not purchase:
                po_data = self._prepare_invoice()
                purchase = purchase_obj.create(po_data)
            values = self._prepare_invoice_line(purchase,item)
            purchase_order_line = po_line_obj.create(values)
            res.append(purchase.id)
            return {
                'domain': [('id', 'in', res)],
                'name': _('Invoice'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'view_id': False,
                'context': False,
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
                                          track_visibility='onchange', required=True)

    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(string='Quantity to invoice',
                               digits=dp.get_precision('Product UoS'),
                               )
    product_uom_id = fields.Many2one('uom.uom', string='UoM',
                                     readonly=True)
    keep_description = fields.Boolean(string='Copy descriptions to new PO',
                                      help='Set true if you want to keep the '
                                           'descriptions provided in the '
                                           'wizard in the new PO.',
                                      default=False)
    date_planned = fields.Date(string='Request Date',
                                track_visibility='onchange',
                                default=fields.Date.context_today)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))

    @api.onchange('product_id')
    def onchange_product_id(self):
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
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1.0
            self.name = name