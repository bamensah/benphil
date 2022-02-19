# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json
from requests import HTTPError
from datetime import datetime
from itertools import groupby


_logger = logging.getLogger(__name__)

def format_date(date):
    timestamp = ""
    try:
        timestamp = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        timestamp = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d %H:%M:%S')

    return timestamp

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    sales_channel = fields.Selection([("direct_sales", "Direct Sales"),("indirect_sales","Indirect Sales"),("telesales","Telesales"),("partnerships","Partnerships")], string='Sales Channel')
    sales_channel_partner = fields.Many2one('sale.channel.partner', string='Sale Channel Partner')

#    @api.model
#    @api.onchange('product_template_id')
#    def product_template_id_change(self):
#        """ fucntion is defined in sh_sales_custom_product_template
#         we override it for addinq tax_id in sale_order_line"""

#        if self.product_template_id:
#            sale_ordr_line = []
#            self.order_line = [(5, 0, 0)]

#            for record in self.product_template_id.sale_product_template_ids:

#                vals = {}
#                vals.update({'price_unit': record.unit_price,
#                             #                             'order_id':self.id,
#                             'name': record.description, 'product_uom_qty': record.ordered_qty,
#                             'tax_id': record.tax_id,
#                             'account_analytic': record.account_analytic,
#                             'discount': record.discount, 'product_uom': record.product_uom.id})

#                if record.name:
#                    vals.update({'product_id': record.name.id})

#                sale_ordr_line.append((0, 0, vals))

#            self.order_line = sale_ordr_line

#        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_get_order_line_from_sale_product_template(self):
        """this function is define for generating sale order line from product
        template lines"""
        self.ensure_one()
        for order_line in self.order_line:
            order_line.unlink()
        self.onchange_sale_order_template_id()#V14
#        self.product_template_id_change()


    def action_perform_sync_activation(self):
        """this function calls the api gateway to ask Paygops to generate a
        sync activation token. Then it stores and displays it to the user.
        """
        self.ensure_one()
        last_sync_token = None

        if self.paygops_id.device_id:
            data = self.syn_activation(self.paygops_id.device_id)

            if isinstance(data, dict):
                device_id = self.env['stock.production.lot'].search([('name', '=', self.paygops_id.device_id)],limit=1)
                token = self.env['credit.token'].create({'code': data['code'], 'token_id': data['token_id'], 'duration': False, 'token_type': data['token_type'], 'credit_end_date': datetime.strptime(data['credit_end_date'], '%Y-%m-%d'), 'generated_date': format_date(data['generated_date']),
                            'inventory_id': device_id.id, 'transaction_id': '', 'payment_id': False, 'partner_id': self.partner_id.id, 'amount': False, 'device_serial': self.paygops_id.device_id,
                            'salesperson': self.user_id.id, 'loan_id': self.id, 'phone_number': False, 'phone_number_partner': self.partner_id.phone })

                self.calculate_status()
                last_sync_token = self.env['sync.activation.wizard'].create({ 'last_sync_activated_token': token.code })
            else:
                msg = data.msg
                raise UserError(_(f'Paygops Error: {msg}'))
        else:
            raise UserError(_("No Paygops device assigned to this sale."))


        wizard_view_id = self.env.ref("peg_dev_module.sync_activation_form").id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Paygops Sync Activation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sync.activation.wizard',
            'res_id': last_sync_token.id,
            'views': [(wizard_view_id, 'form')],
            'target': 'new'
        }


    def syn_activation(self, device_serial):
        '''Make an API call to Paygops for Sync Activation and return
        the activation data or an error object.
        '''
        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }

        URL = API_GATEWAY_URL + "/api/v1/" + self.company_id.country_id.code.lower() + "/sync_device"
        data = { 'device_serial': device_serial }

        error = None
        response_data = None
        resp = None

        try:
            response = requests.post(URL, data=json.dumps(data), headers=HEADERS)
            resp = response.json()
            response_data = {}
            if 'answer_data' in resp and resp['answer_data'][0]['success']:
                response_data['code'] = resp['answer_data'][0]['activation_answer_code']
                response_data['token_id'] = resp['uuid']
                response_data['token_type'] = resp['type']
                credit_end_date = resp['answer_data'][0]['expiration_time_year'] + '-' + resp['answer_data'][0]['expiration_time_month'] + '-' + resp['answer_data'][0]['expiration_time_day']
                response_data['credit_end_date'] = credit_end_date
                response_data['generated_date'] = resp['time']
                response_data['device_serial'] = device_serial
                response_data['human_answer'] = resp['human_answer']

            if 'answer_data' in resp and not resp['answer_data'][0]['success']:
                raise exceptions.Warning(_('PaygOps ERROR : ' + resp['human_answer']))

            response.raise_for_status()
        except HTTPError as http_error:
            http_error.msg = resp['error_message']
            error = http_error
        except Exception as err:
            err.msg = "Server Error"
            error = err
        else:
            return response_data

        return error

    # needs to open

    def action_confirm(self):
        """this function is defined in sale modulle
        we override it for configuring the confirmation date like the date_order"""
        for obj in self:
            if obj.state in ['draft', 'sent']:
                if obj._get_forbidden_state_confirm() & set(obj.mapped('state')):
                    raise UserError(_(
                        'It is not allowed to confirm an order in the following states: %s'
                    ) % (', '.join(obj._get_forbidden_state_confirm())))
    
                for order in obj.filtered(lambda order: order.partner_id not in order.message_partner_ids):
                    order.message_subscribe([order.partner_id.id])
                obj.write({
                    'state': 'sale',
                    'date_order': obj.date_order
                })
                obj._action_confirm()
#                if obj.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
                if obj.env['ir.config_parameter'].sudo().get_param('sale.group_auto_done_setting'):
                    obj.action_done()
            else:
                pass
        return True

    # needs to open

#    @api.multi
#    def action_invoice_create(self, grouped=False, final=False):
#        """
#        Create the invoice associated to the SO.
#        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
#                        (partner_invoice_id, currency)
#        :param final: if True, refunds will be generated if necessary
#        :returns: list of created invoices


#        we override it for giving the invoice the same date as SO
#        """
#        
#        

#        inv_obj = self.env['account.invoice']
#        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
#        invoices = {}
#        references = {}
#        invoices_origin = {}
#        invoices_name = {}

#        for order in self:
#            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)

#            # We only want to create sections that have at least one invoiceable line
#            pending_section = None

#            for line in order.order_line:
#                if line.display_type == 'line_section':
#                    pending_section = line
#                    continue
#                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
#                    continue
#                if group_key not in invoices:
#                    inv_data = order._prepare_invoice()
#                    invoice = inv_obj.create(inv_data)
#                    # add line by khk
#                    invoice.write({
#                        'date_invoice': order.date_order,
#                        'payment_term_id': order.payment_term_id.id
#                    })
#                    # end add line
#                    references[invoice] = order
#                    invoices[group_key] = invoice
#                    invoices_origin[group_key] = [invoice.origin]
#                    invoices_name[group_key] = [invoice.name if invoice.name else '' ]
#                elif group_key in invoices:
#                    if order.name not in invoices_origin[group_key]:
#                        invoices_origin[group_key].append(order.name)
#                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
#                        invoices_name[group_key].append(order.client_order_ref)

#                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
#                    if pending_section:
#                        pending_section.invoice_line_create(invoices[group_key].id, pending_section.qty_to_invoice)
#                        pending_section = None
#                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

#            if references.get(invoices.get(group_key)):
#                if order not in references[invoices[group_key]]:
#                    references[invoices[group_key]] |= order

#        for group_key in invoices:
#            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
#                                       'origin': ', '.join(invoices_origin[group_key])})
#            sale_orders = references[invoices[group_key]]
#            if len(sale_orders) == 1:
#                invoices[group_key].reference = sale_orders.reference

#        if not invoices:
#            raise UserError(_(
#                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

#        for invoice in invoices.values():
#            if not invoice.invoice_line_ids:
#                raise UserError(_(
#                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
#            # If invoice is negative, do a refund invoice instead
#            if invoice.amount_untaxed < 0:
#                invoice.type = 'out_refund'
#                for line in invoice.invoice_line_ids:
#                    line.quantity = -line.quantity
#            # Use additional field helper function (for account extensions)
#            for line in invoice.invoice_line_ids:
#                line._set_additional_fields(invoice)
#            # Necessary to force computation of taxes. In account_invoice, they are triggered
#            # by onchanges, which are not triggered when doing a create.
#            invoice.compute_taxes()
#            # Idem for partner
#            invoice._onchange_partner_id()
#            invoice.message_post_with_view('mail.message_origin_link',
#                                           values={'self': invoice, 'origin': references[invoice]},
#                                           subtype_id=self.env.ref('mail.mt_note').id)
#            # add line by khk
#            so_origin = self.env['sale.order'].search([('name', '=', invoice.origin)])
#            invoice.write({
#                'date_invoice': so_origin.date_order,
#                'payment_term_id': so_origin.payment_term_id.id
#            })
#            # end add line
#        return [inv.id for inv in invoices.values()]
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys])
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
            order_id = move.line_ids.mapped('sale_line_ids.order_id')
            if order_id:
                move.write({
                 'invoice_date': order_id.date_order,
                 'invoice_payment_term_id': order_id.payment_term_id.id
                })
        return moves

    # needs to open
    @api.constrains('order_line')
    def _check_order_line(self):
        for record in self:
            _logger.info("ORDER LINE CHECK: {0}".format(record.order_line))
            for line in record.order_line:
                _logger.info(line)
                if not line.account_analytic:
                    raise ValidationError(_('Analytic Account not set for line {}'.format(line.name)))

class SaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

#    account_analytic = fields.Many2one('account.analytic.account', required=True, string="Analytical Account") Added on sales_custom_quotation_template module

    # def _prepare_invoice_line(self, qty):
    #     """
    #     Prepare the dict of values to create the new invoice line for a sales order line.
    #
    #     :param qty: float quantity to invoice
    #     """
    #     """ on redefinit pour que le invoice line recupere le compte analytique du order line"""
    #     self.ensure_one()
    #     res = {}
    #     account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
    #
    #     if not account and self.product_id:
    #         raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
    #             (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))
    #
    #     fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
    #     if fpos and account:
    #         account = fpos.map_account(account)
    #
    #     res = {
    #         'name': self.name,
    #         'sequence': self.sequence,
    #         'origin': self.order_id.name,
    #         'account_id': account.id,
    #         'price_unit': self.price_unit,
    #         'quantity': qty,
    #         'discount': self.discount,
    #         'uom_id': self.product_uom.id,
    #         'product_id': self.product_id.id or False,
    #         'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
    #         'account_analytic_id': self.account_analytic.id,  # ligne modifie
    #         'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
    #         'display_type': self.display_type,
    #     }
    #     return res

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLineInherit, self)._prepare_invoice_line(**optional_values)
        res.update({
            'analytic_account_id': self.account_analytic.id,
        })
        return res

    def _prepare_procurement_values(self, group_id=False):
        """get account analytic value from sale order line"""
        res = super(SaleOrderLineInherit, self)._prepare_procurement_values(group_id)
        res.update({
            'analytic_account_id': self.account_analytic.id,
            'number': self.order_id.origin
        })
        return res
