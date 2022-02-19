# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class PaymentTermLine(models.Model):
    _inherit = 'account.payment.term.line'

    value = fields.Selection([
        ('balance', 'Balance'),
        ('deposit', 'Deposit'),
        ('repayment', 'Repayment'),
        ('weekly repayment', 'Weekly repayment'),
        ('monthly repayment', 'Monthly repayment'),
        ('seasonal repayment', 'Seasonal repayment'),
        ('annual repayment', 'Annual repayment'),
        ('fixed', 'Fixed Amount'),
        ('other', 'Other')
    ], string='Type', required=True, default='balance',
        help="Select here the kind of valuation related to this payment terms line.")


class PaymentTermRateType(models.Model):
    _inherit = "account.payment.term.rate_type"

    value = fields.Integer("Value (days)")


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    specific = fields.Boolean(string='Specific payment term', help="Specific payment term")
    partner_id = fields.Many2one('res.partner', string='Client ID',
                                 default=lambda self: self.env.context.get('partner_id', False))
    type_of_product_id = fields.Many2one('wave2.peg.africa.type.of.product', string='Type of product')
    paygops_offer_id = fields.Integer(string='ID of the offer in PaygOps')
    minimum_amount_days = fields.Integer(string="Minimum Amount Value, Days")
    minimum_amount_value = fields.Float(string="Minimum Amount Value, Value")
    rate_daily = fields.Float(compute="_calculate_rate_daily")
    calculation_expected_amount_method = fields.Selection(
        [('method1', 'Using rate pro-rated daily'), ('method2', 'Using invoice dates on a loan')],
        string="Expected amount calculation method")

    # migrate v14 late ---------
    # @api.one
    def copy(self, default=None):
        default = dict(default or {})
        all_payment_term = self.search([])
        all_payment_term_len = str(len(all_payment_term) + 1) if all_payment_term else '1'
        if 'name' not in default:
            default.update({
                'name': all_payment_term_len + '-' + self.name + '-discount',
            })
        return super(PaymentTerm, self).copy(default)

    #
    def _calculate_rate_daily(self):
        for term in self:
            if term.rate_type:
                term.rate_daily = term.rate_amount / term.rate_type.value if term.rate_type.value else 0

    # old methof in v12 check below v14
    # @api.one
    # def compute(self, value, date_ref=False, currency=None):
    #     date_ref = date_ref or fields.Date.today()
    #     amount = value
    #     sign = value < 0 and -1 or 1
    #     result = []
    #     if self.env.context.get('currency_id'):
    #         currency = self.env['res.currency'].browse(self.env.context['currency_id'])
    #     else:
    #         currency = self.env.user.company_id.currency_id
    #     for line in self.line_ids:
    #         if line.value == 'fixed':
    #             amt = sign * currency.round(line.value_amount)
    #         elif line.value == 'percent':
    #             amt = currency.round(value * (line.value_amount / 100.0))
    #         elif line.value == 'balance':
    #             amt = currency.round(amount)
    #         else:
    #             amt = sign * currency.round(line.value_amount)
    #         if amt:
    #             next_date = fields.Date.from_string(date_ref)
    #             if line.option == 'day_after_invoice_date':
    #                 next_date += relativedelta(days=line.days)
    #                 if line.day_of_the_month > 0:
    #                     months_delta = (line.day_of_the_month < next_date.day) and 1 or 0
    #                     next_date += relativedelta(day=line.day_of_the_month, months=months_delta)
    #             elif line.option == 'after_invoice_month':
    #                 next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
    #                 next_date = next_first_date + relativedelta(days=line.days - 1)
    #             elif line.option == 'day_following_month':
    #                 next_date += relativedelta(day=line.days, months=1)
    #             elif line.option == 'day_current_month':
    #                 next_date += relativedelta(day=line.days, months=0)
    #             result.append((fields.Date.to_string(next_date), amt))
    #             amount -= amt
    #     amount = sum(amt for _, amt in result)
    #     dist = currency.round(value - amount)
    #     if dist:
    #         last_date = result and result[-1][0] or fields.Date.today()
    #         result.append((last_date, dist))
    #     print('----resulkt', result)
    #     return result

    def compute(self, value, date_ref=False, currency=None):
        self.ensure_one()
        date_ref = date_ref or fields.Date.context_today(self)
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if not currency and self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        elif not currency:
            currency = self.env.company.currency_id
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)
            else:
                amt = sign * currency.round(line.value_amount)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                    if line.day_of_the_month > 0:
                        months_delta = (line.day_of_the_month < next_date.day) and 1 or 0
                        next_date += relativedelta(day=line.day_of_the_month, months=months_delta)
                elif line.option == 'after_invoice_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'day_following_month':
                    next_date += relativedelta(day=line.days, months=1)
                elif line.option == 'day_current_month':
                    next_date += relativedelta(day=line.days, months=0)
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.context_today(self)
            result.append((last_date, dist))
        return result
    #
    # def write(self, vals):
    #     print('---vals', vals)
    #     if vals and 'specific' in vals:
    #
    #         values = self.env['account.payment.term'].search([('id', '=', self.id)]).line_ids
    #         value_ids = []
    #         self_value_ids = []
    #         for line in values:
    #             line_id_value = self.env['account.payment.term.line'].search([('id', '=', line.id)]).value
    #             line_id_value_amount = self.env['account.payment.term.line'].search([('id', '=', line.id)]).value_amount
    #             line_id_days = self.env['account.payment.term.line'].search([('id', '=', line.id)]).days
    #             line_id_day_of_the_month = self.env['account.payment.term.line'].search(
    #                 [('id', '=', line.id)]).day_of_the_month
    #             line_id_option = self.env['account.payment.term.line'].search([('id', '=', line.id)]).option
    #             if line_id_value == 'balance':
    #                 line_id_sequence = 500
    #             else:
    #                 line_id_sequence = self.env['account.payment.term.line'].search([('id', '=', line.id)]).sequence
    #             value = {'value': line_id_value, 'value_amount': line_id_value_amount, 'sequence': line_id_sequence,
    #                      'days': line_id_days, 'option': line_id_option, 'day_of_the_month': line_id_day_of_the_month}
    #             value_ids.append(value)
    #
    #         # Condition pour lever l'erreur si specific coché et pas de lignes ajoutées
    #         if 'line_ids' in vals:
    #             for line in vals['line_ids']:
    #                 self_value_ids.append(line)
    #         else:
    #             raise ValidationError(
    #                 _('You cannot save this payment term as a specific one as you have not change anything.'))
    #
    #         if 'name' in vals:
    #             name = vals['name']
    #         else:
    #             name = self.name
    #         all_payment_term = self.search([])
    #         all_payment_term_len = str(len(all_payment_term) + 1) if all_payment_term else '1'
    #         new_payment_term = self.create({
    #             'name': all_payment_term_len + "-" + vals[
    #                 'partner_id'].id + "-" + name if 'partner_id' in vals else all_payment_term_len + "-" + name + "-specific",
    #             'specific': vals['specific'] if 'specific' in vals else self.specific,
    #             'note': vals['note'] if 'note' in vals else self.note,
    #
    #             'line_ids': [value_ids]
    #         })
    #         new_payment_term['line_ids'] = self_value_ids
    #         res = super(PaymentTerm, self).write({'specific': False})
    #         self.env['account.payment.term'].search([('id', '=', self.id)]).line_ids = value_ids
    #         # res = new_payment_term
    #         res = self.env['account.payment.term'].search([('id', '=', new_payment_term.id)])
    #         if res.partner_id.id:
    #             if "-specific" in res.name:
    #                 res.write({'name': str(res.partner_id.id) + "-" + (res.name).split('-specific')[0]})
    #             else:
    #                 res.write({'name': str(res.partner_id.id) + "-" + res.name})
    #         res.write({'type_of_product_id': res.type_of_product_id.id})
    #
    #     else:
    #         res = super(PaymentTerm, self).write(vals)
    #     return res
#     end ---------------------


class CustomSaleOrder(models.Model):
    _inherit = 'sale.order'

    def default_user_id(self):
        return

    def default_team_id(self):
        return

    @api.model
    def _default_warehouse_id(self):
        # !!! Any change to the default value may have to be repercuted
        # on _init_column() below.
        return False
    
    def default_installer_user_id(self):
        return self.user_id
    

    type_of_product_id = fields.Many2one('wave2.peg.africa.type.of.product', string='Type of product')
    payment_term_modified = fields.Boolean(string='Payment term modified', default=False)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term',
                                      required=True)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
                              track_sequence=2, required=True, default=default_user_id)
    install_user_id = fields.Many2one('res.users', string='Installation Agent', index=True, track_visibility='onchange', required=True, default=default_installer_user_id)
    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, oldname='section_id', required=True,
                              default=default_team_id)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, related='warehouse_peg_id')
    warehouse_peg_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    withheld_payment_amount = fields.Float(string="Held Amount For", compute='_compute_withheld_amount' )

    # migrate later v14 ---------
    @api.onchange('user_id')
    def _onchange_field(self):
        if self.sales_channel == 'direct_sales':
            self.install_user_id = self.user_id.id
    #
    @api.onchange('sales_channel')
    def _onchange_field(self):
        if self.sales_channel == 'direct_sales':
            self.install_user_id = self.user_id.id
    # end ---------------------
    
    
    @api.depends('partner_id')
    def _compute_withheld_amount(self):
        for record in self:
            payments = self.env['account.payment'].search([('sale_order', '=', record.id), ('parent_payment_id', '!=', False), ('state', 'in', ['posted', 'confirmed'])])
            if any(payments):
                withheld_amounts = map(lambda x: x.amount, payments)
                withheld_total = sum(withheld_amounts)
                record.withheld_payment_amount = withheld_total
            else:
                record.withheld_payment_amount = 0
    
    # migrate later v14 ----------
    # # Mise à jour de la condition de paiement avec celle créée pour le client sélectionné
    # @api.multi
    @api.onchange('payment_term_id')
    def onchange_payment_term_id(self):

        if not self.payment_term_id:
            self.update({
                'payment_term_id': False,
            })
            return
        if self.partner_id and self.payment_term_id and self.type_of_product_id and not self.payment_term_modified:
            # TODO : filtrer sur le type de produit
            if self.env['account.payment.term'].search(
                    [('partner_id', '=', self.partner_id.id), ('type_of_product_id', '=', self.type_of_product_id.id)],
                    order='create_date desc', limit=1):
                values = {
                    'payment_term_id': self.env['account.payment.term'].search([('partner_id', '=', self.partner_id.id),
                                                                                ('type_of_product_id', '=',
                                                                                 self.type_of_product_id.id)],
                                                                               order='create_date desc', limit=1) and
                                       self.env['account.payment.term'].search(
                                           [('partner_id', '=', self.partner_id.id)], order='create_date desc',
                                           limit=1).id or False,
                    'payment_term_modified': False
                }
                self.update(values)
        if self.payment_term_id.specific:
            values = {'payment_term_modified': True
                      }
            self.update(values)
        else:
            values = {'payment_term_modified': False
                      }
            self.update(values)
    #
    # @api.multi
    @api.onchange('type_of_product_id')
    def onchange_type_of_product_id(self):

        return {
            'context': {'type_of_product_id': self.type_of_product_id}
        }

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery']
        }
        if self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super(CustomSaleOrder, self)._create_invoices(grouped, final)
        moves.write({'sale_order_id': self.id})
        return moves

class TypeOfProduct(models.Model):
    _name = 'wave2.peg.africa.type.of.product'
    _description = 'Type Of Product'

    name = fields.Char('Type of product', required=True)
    dashboard_button_name = fields.Char(string="Dashboard Button", compute='_compute_dashboard_button_name')

    def get_alias_model_name(self, vals):
        return 'crm.lead'

    def _compute_dashboard_button_name(self):
        opportunity_product = self
        opportunity_product.update({'dashboard_button_name': _("Pipeline")})

    # migrate later v14 ---------
    def action_primary_channel_button(self):
        action = self.env.ref('wave2_peg_africa.crm_case_form_view_products_opportunity').read()[0]
        return action
        return super(TypeOfProduct, self).action_primary_channel_button()


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    picking_type_id = fields.Many2one('stock.picking.type', string='Deliver to', required=True)
    invoiced_check = fields.Boolean(string="Invoiced", readonly=True, compute='_compute_invoiced', store=True)

    # migrate v14 -------
    @api.model
    def default_get(self, default_fields):
        res = super(PurchaseOrderInherit, self).default_get(default_fields)
        company = self.env.user.company_id.partner_id.name
        picking_type_id = self.env['stock.picking.type'].search([
            ('warehouse_id', '=like', 'HQ%'),
            ('warehouse_id.company_id.partner_id.name', '=', company),
            '|', ('name', '=', 'Receipts'), ('name', '=', 'Réceptions')
        ], limit=1)
        if picking_type_id:
            res['picking_type_id'] = picking_type_id.id
        return res
    # end ---------------

    @api.depends('state', 'order_line.qty_invoiced', 'order_line.qty_received', 'order_line.product_qty')
    def _compute_invoiced(self):
        for record in self:
            if len(record.invoice_ids.filtered(lambda invoice: invoice.state != 'cancel')) > 0 :
                record.invoiced_check = True
            else:
                record.invoiced_check = False

    # migrate later v14 --------
    def write(self, vals):
        if self.state == 'done' and vals.get('state') == 'purchase':
            vals['state'] = 'to approve'
        return super(PurchaseOrderInherit, self).write(vals)

    # @api.multi
    def button_finance_approval(self):
        if self.director_manager_id and self.state == 'finance_approval':
            director_validation_amount = self._get_director_validation_amount()
            amount_total = self.currency_id.compute(self.amount_total, self.company_id.currency_id)
            if amount_total > director_validation_amount:
                self.message_post(body="{} please review this PO".format(self.director_manager_id.name), subject='Waiting Director Approval', message_type='notification', subtype_id=self.env.ref('mail.mt_comment').id, partner_ids=[self.director_manager_id.partner_id.id])
        return super(PurchaseOrderInherit, self).button_finance_approval()
    #
    # @api.multi
    def button_approve(self):
        if self.finance_manager_id and self.state == 'to approve':
            self.message_post(body="{} please review this PO".format(self.finance_manager_id.name), subject='Waiting Finance Approval', message_type='notification', subtype_id=self.env.ref('mail.mt_comment').id, partner_ids=[self.finance_manager_id.partner_id.id])
        return super(PurchaseOrderInherit, self).button_approve()
    #
    # @api.multi
    def button_confirm(self):
        if self.dept_manager_id and self.state == 'draft':
            self.message_post(body="{} please review this PO".format(self.dept_manager_id.name), subject='Waiting Purchase Approval', message_type='notification', subtype_id=self.env.ref('mail.mt_comment').id, partner_ids=[self.dept_manager_id.partner_id.id])
        return super(PurchaseOrderInherit, self).button_confirm()
    # end ------------# end ------------


class FreeDaysTags(models.Model):
    _name = 'free.day.tag'
    _description = 'free days tags & description'
    _rec_name = 'tag'

    tag = fields.Char(string='Tag', required=True)
    description = fields.Text(string='Description')
    exclude_from_metrics = fields.Boolean('Exclude in the expected amount calculation ?')

class DiscountTags(models.Model):
    _name = 'discount.tag'
    _description = 'discount tags & description'
    _rec_name = 'tag'

    tag = fields.Char(string='Tag', required=True)
    account_id = fields.Many2one('account.account', required=True)
    journal_id = fields.Many2one('account.journal', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    product_id = fields.Many2one('product.product', required=True)
    tax_id = fields.Many2one('account.tax', required=True, string='Tax')
