# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError
from psycopg2 import OperationalError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from collections import Counter
import ast
from datetime import datetime, timedelta, date
from unicodedata import normalize
import requests
import json

import logging

_logger = logging.getLogger(__name__)

WO_FLAGS = [
    ('None', 'None'),
    ('NA', 'NA'),
    ('Blocked (DWOL>156)', 'Blocked (DWOL>156)'),
    ('Client was terminated', 'Client was terminated')
]

WASTED_SALES = [
    ('wasted_sale', 'Wasted Sale')
]

class SaleOrderStockDelivery(models.Model):
    _inherit = 'sale.order'

    deposit_invoice_fully_paid = fields.Boolean(string='Deposit fully paid', default=False)
    paygops_id = fields.Many2one('peg.africa.paygops', 'PaygOps ID', readonly=True)
    contract_status = fields.Many2one('sale.contract.status', string='Contract Status')
    status_name = fields.Char(related='contract_status.name', string='Status')
    dwol = fields.Integer(string='Days Without Light', readonly=True)
    dol = fields.Integer(string='Days of light available', readonly=True)
    credit_end_date = fields.Datetime(string='Credit End Date', readonly=True, store=True)
    outstanding_balance = fields.Monetary(string='Outstanding balance', readonly=True)
    amount_pending = fields.Monetary(string='Amount Pending', readonly=True)
    arrears = fields.Monetary(string='Arrears', readonly=True, store=True)
    rank = fields.Integer(string='Rank', store=True)
    invoice_id = fields.Many2one('account.move', 'Invoice number', readonly=True, compute='_compute_invoice_number')  #
    free_days_taken = fields.Integer(string='Free days taken',
                                     compute="_calculate_freedaystaken")
    discount_given = fields.Monetary(string='Discount Given', readonly=True,
                                     compute="_calculate_discount_given")  # migrate later in v14
    stored_discount_given = fields.Monetary()
    free_days_ids = fields.One2many("free.days.discount", "sale_order", readonly=True)  # migrate later in v14
    expected_amount_due = fields.Monetary(string='Expected amount due', compute="_calculate_amount_due")
    amount_paid = fields.Monetary(string='Amount paid (excl. deposit)', compute="_calculate_amount_paid")
    amount_to_be_paid = fields.Monetary(string='Amount to be paid this month', compute="_calculate_amount_to_be_paid")
    arrears = fields.Monetary(string='Arrears', compute="_calculate_arrears")  #
    stored_expected_amount_due = fields.Monetary()
    stored_amount_paid = fields.Monetary()
    stored_arrears = fields.Monetary()
    stored_amount_to_be_paid = fields.Monetary()
    deposit_invoice_fully_paid_date = fields.Datetime()
    stock_action = fields.Many2one('sale.stock.action', 'Stock Action')
    written_off_flag = fields.Selection(WO_FLAGS, 'Written off flag', default=None, readonly=True)
    suspension_reason = fields.Many2one('suspension.reason', 'Suspension Reason')
    sub_suspension_reason = fields.Many2one('sub.suspension.reason', 'Sub Reason')
    device_status = fields.Many2one('device.status', 'Device Status')
    deposit_status = fields.Many2one('deposit.status', 'Deposit Status')
    wasted_sales = fields.Selection(WASTED_SALES, 'Wasted Sales', default=None)
    total_amount_paid = fields.Monetary(string='Total Amount Paid', readonly=True, compute="_calculate_amount_paid")  #
    stored_total_amount_paid = fields.Monetary()
    # Remove in production
    token_ids = fields.One2many("credit.token", "loan_id")

    @api.onchange('sale_order_template_id')
    def _onchange_template(self):
        if self.sale_order_template_id:
            self.analytic_account_id = self.sale_order_template_id.sale_order_template_line_ids[
                0].account_analytic_id.id

    def _calculate_freedaystaken(self):
        for order in self:
            free_days_taken = order.payment_term_id.free_days
            for freeday in order.free_days_ids:
                if all(tag.exclude_from_metrics == False for tag in freeday.tag_ids):
                    free_days_taken += freeday.delayed_days
            order.free_days_taken = free_days_taken
            

    def _calculate_discount_given(self):
        for order in self:
            credit_notes = self.env['account.move'].search([
                ('sale_order_id', '=', order.id),
                ('company_id', '=', order.company_id.id),
                ('move_type', '=', 'out_refund'),
                ('state', '!=', 'cancel')
            ])
            total_discount = 0
            if credit_notes:
                total_discount = sum(credit_notes.mapped('amount_total'))
            order.discount_given = total_discount

    def _get_all_amount(self):
        options = {
            'partner_id': self.partner_id.id,
        }
        expected_amount_due = 0
        lines = self.env['account.followup.report']._get_lines(options)
        for line in lines:
            if line['name'] and line["columns"][2]['name'] == self.name:
                normalized_str = normalize("NFKD", line['columns'][6]['name'])
                if normalized_str.find('CFA') != -1:
                    total_due = float(
                        normalized_str.replace('CFA', '').replace(' ', '').replace(',', '')) if normalized_str else 0
                    date_due = datetime.strptime(line['columns'][1]['name'], '%d/%m/%Y').date() if line['columns'][1][
                        'name'] else False
                else:
                    total_due = float(
                        normalized_str.replace('GH¢', '').replace(' ', '').replace(',', '')) if normalized_str else 0
                    date_due = datetime.strptime(line['columns'][1]['name'], '%m/%d/%Y').date() if line['columns'][1][
                        'name'] else False

                communication = line['columns'][3]['name']
                if total_due > 0 and date_due and date_due <= fields.Date.today():
                    expected_amount_due += total_due

        if expected_amount_due > 0:
            expected_amount_due -= self.payment_term_id.deposit_amount

        return {
            'expected_amount_due': expected_amount_due if expected_amount_due > 0 else 0
        }

    def last_day_of_month(self):
        current_date = datetime.utcnow()

        next_month = current_date.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)

        return last_day_of_month

    def _get_amount_to_be_paid(self):
        options = {
            'partner_id': self.partner_id.id,
        }
        amount_to_be_paid = 0
        lines = self.env['account.followup.report']._get_lines(options)
        end_date = self.last_day_of_month()
        for line in lines:
            if line['name'] and line["columns"][2]['name'] == self.name:
                normalized_str = normalize("NFKD", line['columns'][6]['name'])
                if normalized_str.find('CFA') != -1:
                    date_due = datetime.strptime(line['columns'][1]['name'], '%d/%m/%Y').date() if line['columns'][1][
                        'name'] else False
                    total_due = float(
                        normalized_str.replace('CFA', '').replace(' ', '').replace(',', '')) if normalized_str else 0
                else:
                    date_due = datetime.strptime(line['columns'][1]['name'], '%m/%d/%Y').date() if line['columns'][1][
                        'name'] else False
                    total_due = float(
                        normalized_str.replace('GH¢', '').replace(' ', '').replace(',', '')) if normalized_str else 0
                communication = line['columns'][3]['name']
                if total_due > 0 and date_due and date_due <= end_date.date():
                    amount_to_be_paid += total_due

        if amount_to_be_paid > 0:
            difference = self.payment_term_id.deposit_amount + self.amount_paid
            amount_to_be_paid -= difference

        return {
            'amount_to_be_paid': amount_to_be_paid if amount_to_be_paid > 0 else 0
        }

    def _calculate_with_method1(self, order):
        if not isinstance(order.deposit_invoice_fully_paid_date,
                          bool) and order.deposit_invoice_fully_paid_date is not None:
            days_since_activation = (datetime.utcnow() - order.deposit_invoice_fully_paid_date).days + 1
            expected_amount_due = (days_since_activation - order.free_days_taken) * order.payment_term_id.rate_daily
            order.expected_amount_due = expected_amount_due if expected_amount_due >= 0 else 0
        else:
            order.expected_amount_due = 0

    def _calculate_amount_due(self):
        for order in self:
            if order.payment_term_id.calculation_expected_amount_method == 'method1':
                self._calculate_with_method1(order)
            else:
                order.expected_amount_due = order._get_all_amount()['expected_amount_due']

    def _calculate_amount_to_be_paid(self):
        for order in self:
            if order.payment_term_id.calculation_expected_amount_method == 'method1':
                if not isinstance(order.deposit_invoice_fully_paid_date,
                                  bool) and order.deposit_invoice_fully_paid_date is not None:
                    end_date = self.last_day_of_month()
                    days_till_month_end = (end_date - order.deposit_invoice_fully_paid_date).days + 1
                    order.amount_to_be_paid = ((
                                                           days_till_month_end - order.free_days_taken) * order.payment_term_id.rate_daily) - order.amount_paid
                else:
                    order.amount_to_be_paid = 0
            else:
                order.amount_to_be_paid = order._get_amount_to_be_paid()['amount_to_be_paid']

    def _calculate_amount_paid(self):
        for order in self:
            payments = self.env['account.payment'].search([('sale_order', '=', order.id)])
            payment_sum = 0
            for payment in payments:
                if payment.confirmed or payment.state == 'posted':
                    payment_sum += payment.amount
            order.total_amount_paid = payment_sum
            order.amount_paid = payment_sum - order.payment_term_id.deposit_amount

    @api.depends('expected_amount_due', 'amount_paid')
    def _calculate_arrears(self):
        for order in self:
            arrears = order.expected_amount_due - order.amount_paid
            order.arrears = arrears if arrears > 0 else 0

    @api.model
    def create(self, vals):
        vals['contract_status'] = self.env['sale.contract.status'].search(
            [('name', '=', 'Lead')], limit=1).id
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'sale.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist
                                                   and partner.property_product_pricelist.id)

        result = super(SaleOrderStockDelivery, self).create(vals)
        partner_id = self.env['res.partner'].sudo().browse(vals['partner_id'])
        # calculate contract and client status
        result.calculate_status()
        return result

    def calculate_status(self):
        dates_to_compare = []
        if self.paygops_id:
            current_token = self.env['credit.token'].search([('loan_id', '=', self.id)], order="id desc", limit=1)
            if current_token:
                if current_token.credit_end_date:
                    dwol = int((datetime.today() - current_token.credit_end_date).days)
                    self.write({'dwol': dwol,
                                'dol': -dwol,
                                'credit_end_date': current_token.credit_end_date})
                else:
                    if current_token.token_type == 'DISABLE_PAYG':
                        self.write({'dwol': -1,
                                    'dol': 1,
                                    'credit_end_date': None})

    def update_client_status(self):
        if len(self.partner_id.sale_order_ids) > 0:
            ranks_to_compare = []
            contracts = self.env['sale.order'].search([('partner_id', '=', self.partner_id.id), ('state', '!=', 'cancel')])
            for contract in contracts:
                if contract.contract_status:
                    ranks_to_compare.append(contract.contract_status.order_of_account)
            if len(ranks_to_compare) > 0:
                max_ranking = max(ranks_to_compare)
                max_contract_status = self.env['sale.contract.status'].search(
                    [('order_of_account', '=', max_ranking)]).id
                self.partner_id.write({'client_status': max_contract_status})

    @api.depends('invoice_ids', 'contract_status', 'partner_id')
    def _compute_invoice_number(self):
        for rec in self:
            if rec.invoice_ids:
                # Invoice number related to the sale
                if len(rec.invoice_ids) > 0:
                    rec.invoice_id = self.env['account.move'].search(
                        [('invoice_origin', '=', rec.name), ('partner_id', '=', rec.partner_id.id),
                         ('state', '!=', 'cancel')], order='create_date desc', limit=1)
                else:
                    rec.invoice_id = rec.invoice_ids[0]
                return rec
            else:
                rec.invoice_id = False
                return rec

    def update_stock_action(self):
        stock_action = self.env['invoice.stock.action'].search(
            [('invoice_id', '=', self.invoice_id.id)], limit=1)

        ranks_to_compare = []
        for stock_line in stock_action.stock_action_lines:
            if stock_line.status:
                ranks_to_compare.append(stock_line.status.order_of_account)
        if len(ranks_to_compare) > 0:
            max_ranking = max(ranks_to_compare)
            max_stock_action = self.env['sale.stock.action'].search([('order_of_account', '=', max_ranking)]).id
            self.write({'stock_action': max_stock_action})

    # # CRON Update DWOL
    def sheduler_update_dwol(self):
        all_loans = self.env['sale.order'].search([('paygops_id', '!=', False)])
        for loan in all_loans:
            loan.calculate_status()

    def prev_sale_stock_actions(self):
        all_loans = self.env['sale.order'].search([('paygops_id', '!=', False), ('stock_action', '=', None)], limit=400)
        for loan in all_loans:
            if loan.invoice_id:
                result = self.env['invoice.stock.action'].search(
                    [('invoice_id', '=', loan.invoice_id.id)],
                    limit=1)

                if result:
                    if not result.stock_action_lines:
                        result.get_stock_action_lines()
                else:
                    result = self.env['invoice.stock.action'].create({'invoice_id': loan.invoice_id.id})

    def action_validate_status(self):
        if self.deposit_invoice_fully_paid and self.deposit_invoice_fully_paid_date:
            days_since_activation = (datetime.utcnow() - self.deposit_invoice_fully_paid_date).days + 1
            if days_since_activation <= 45:
                self.write({'contract_status': self.env.ref('wave2_peg_africa.contract_status_written_off').id,
                            'written_off_flag': 'Client was terminated', 'wasted_sales': 'wasted_sale'})
            else:
                self.write({'contract_status': self.env.ref('wave2_peg_africa.contract_status_written_off').id,
                            'written_off_flag': 'Client was terminated'})
        else:
            self.write({'contract_status': self.env.ref('wave2_peg_africa.contract_status_written_off').id,
                        'written_off_flag': 'Client was terminated'})
        return self.invoice_id.invoice_stock_action()

    def calculate_stored_metrics(self):
        metrics_query = """update sale_order
        set stored_expected_amount_due = credit_metrics.expected_amount_due,
        stored_amount_paid = credit_metrics.amount_paid,
        stored_arrears = credit_metrics.arrears,
        stored_amount_to_be_paid = credit_metrics.amount_to_be_paid
        from
        (
        with initial_metrics as (Select ead.id, expected_amount_due,
                                case when amount_to_be_paid > 0 then amount_to_be_paid
                                else 0
                                end amt_incl_payments,
                                case when amount_paid is null then 0
                                else amount_paid
                                end amount_paid
        from
        (
            (with free_days as
        (select sale.id, sum(discount.delayed_days) delayed_days
        from free_days_discount discount
        join sale_order sale on sale.id = discount.sale_order
        where discount.id not in (
            select discount.id
            from free_days_discount discount
            join free_day_tag_free_days_discount_rel discount_tag
                on discount.id = discount_tag.free_days_discount_id
            join free_day_tag tags on tags.id = discount_tag.free_day_tag_id
            where tags.exclude_from_metrics = True
        )
        group by sale.id
        ),
        last_day as (
            SELECT (date_trunc('month', CURRENT_DATE::date) + interval '1 month' - interval '1 day')::date
        AS end_of_month
        )
        Select so.id,
            ((date_part('day',CURRENT_DATE::timestamp - so.deposit_invoice_fully_paid_date::timestamp) -
            COALESCE(delayed_days, 0) - COALESCE(apt.free_days,0) + 1) *
            CASE WHEN apt_type.value is not null then apt.rate_amount / apt_type.value
            else 0
            end) expected_amount_due,
            ((date_part('day',(Select end_of_month from last_day)::timestamp - so.deposit_invoice_fully_paid_date::timestamp) -
            COALESCE(delayed_days, 0) - COALESCE(apt.free_days,0) + 1) *
            CASE WHEN apt_type.value is not null then apt.rate_amount / apt_type.value
            else 0
            end) amount_to_be_paid
        FROM sale_order so
        left join account_payment_term apt on apt.id = so.payment_term_id
        left join account_payment_term_rate_type apt_type on apt.rate_type = apt_type.id
        left join free_days on so.id = free_days.id
        where apt.calculation_expected_amount_method = 'method1'
        and so.deposit_invoice_fully_paid_date is not null)
        UNION ALL
        (
            with move_lines as (
            SELECT so.id,
                CASE
                WHEN aml.currency_id is not null then aml.amount_residual_currency
                ELSE aml.amount_residual
                end amount,
                CASE
                WHEN aml.date_maturity is not null THEN aml.date_maturity
                ELSE aml.date
                end due_date
            FROM sale_order so
            JOIN account_invoice aci ON so.name = aci.origin
            JOIN account_move_line aml on aml.invoice_id = aci.id
            LEFT JOIN account_payment_term apt on so.payment_term_id = apt.id
            where apt.calculation_expected_amount_method != 'method1'
        ),
        deposit_amount as (
            Select so.id so_id, deposit_amount
            from sale_order so
            left join account_payment_term pt on so.payment_term_id = pt.id
        ),
        last_day as (
            SELECT (date_trunc('month', CURRENT_DATE::date) + interval '1 month' - interval '1 day')::date
        AS end_of_month
        )

        SELECT id, (sum(
            CASE WHEN due_date <= CURRENT_DATE  and amount > 0 THEN amount
            ELSE 0
            end
            ) - deposit_amount) expected_amount_due,
            (sum(
            CASE WHEN due_date <= (Select end_of_month from last_day)  and amount > 0 THEN amount
            ELSE 0
            end
            ) - deposit_amount) amount_to_be_paid
        FROM move_lines ml
        LEFT JOIN deposit_amount da on da.so_id = ml.id
        group by id, da.deposit_amount
        )
        ) ead
        left join
        (
            Select so.id, abs((sum(ap.amount) - deposit_amount)) amount_paid
        from sale_order so
        left join account_payment ap on so.id = ap.sale_order
        left join (
            Select so.id so_id, deposit_amount
            from sale_order so
            left join account_payment_term pt on so.payment_term_id = pt.id
        ) sale_deposit_amount on so_id = so.id
        where ap.state = 'confirmed' or ap.state = 'posted'
        group by so.id, deposit_amount
        ) ap
        on ap.id = ead.id
        ),
        currency_details as (
            SELECT res_company.id, res_currency.decimal_places
            FROM res_company
            JOIN res_currency on currency_id = res_currency.id
        )
        Select sale_order.id,
            round(case when expected_amount_due > 0 then expected_amount_due::numeric
            else 0
            end, decimal_places) expected_amount_due,
            round(CASE WHEN amount_paid is not null then amount_paid::numeric
            ELSE 0
            END, decimal_places)amount_paid,
            round(CASE WHEN amount_paid is not null and expected_amount_due > amount_paid THEN (expected_amount_due - amount_paid)::numeric
            ELSE 0
            END, decimal_places) arrears,
            round(CASE WHEN amount_paid is not null and (amt_incl_payments - amount_paid) > 0 then (amt_incl_payments - amount_paid)::numeric
            else 0
            end, decimal_places) amount_to_be_paid,
            company_id
        FROM sale_order
        left join initial_metrics on sale_order.id = initial_metrics.id
        left join currency_details on company_id = currency_details.id
        ) credit_metrics
        where sale_order.id = credit_metrics.id
        """
        self.env.cr.execute(metrics_query)

        payment_metrics_query = """with update_values as (
            select * from (
                select sale_order.id,
                    coalesce(total_paid, 0) total_paid,
                    coalesce(total_discount, 0) total_discount
                from sale_order
                left join
                (
                select sale_order,
                    sum(amount) total_paid
                from account_payment payment
                where payment.state = 'confirmed' or payment.state = 'posted' group by payment.sale_order
                ) total_payments on sale_order.id = total_payments.sale_order
                --left join account_payment_term pt on sale_order.payment_term_id = pt.id
                left join
                (
                Select origin,
                    company_id,
                    sum(amount_total) total_discount
                from account_invoice where type = 'out_refund' group by origin, company_id
                ) discounts on sale_order.name = discounts.origin and sale_order.company_id = discounts.company_id
		    ) metrics where total_paid > 0 or total_discount > 0
            )
            update sale_order
                set stored_total_amount_paid = update_values.total_paid,
                stored_discount_given = update_values.total_discount
                from update_values
                where sale_order.id in (select id from update_values)
                and sale_order.id = update_values.id"""

        self.env.cr.execute(payment_metrics_query)

    def calculate_initial_metrics(self):
        metrics_query = """with update_values as (
            select * from (
                select sale_order.id,
                    (coalesce(pt.financed_price, 0) - coalesce(total_paid, 0) - coalesce(total_discount, 0)) outstanding_balance,
                    coalesce(total_paid, 0) total_paid,
                    coalesce(total_discount, 0) total_discount
                from sale_order
                left join
                (
                select sale_order,
                    sum(amount) total_paid
                from account_payment payment
                where payment.state = 'confirmed' or payment.state = 'posted' group by payment.sale_order
                ) total_payments on sale_order.id = total_payments.sale_order
                left join account_payment_term pt on sale_order.payment_term_id = pt.id
                left join
                (
                Select origin,
                    company_id,
                    sum(amount_total) total_discount
                from account_invoice where type = 'out_refund' group by origin, company_id
                ) discounts on sale_order.name = discounts.origin and sale_order.company_id = discounts.company_id
		    ) metrics where outstanding_balance > 0 or total_paid > 0 or total_discount > 0
            )
            update sale_order
                set stored_total_amount_paid = update_values.total_paid,
                stored_discount_given = update_values.total_discount,
                outstanding_balance = update_values.outstanding_balance
                from update_values
                where sale_order.id in (select id from update_values)
                and sale_order.id = update_values.id"""
        self.env.cr.execute(metrics_query)

    def get_country(self):
        return self.env.user.company_id.country_id.code.lower()

    def register_unlocking_payment(self):
        if self.payment_term_id.paygops_offer_id == 0:
            return True

        wallet_name = self.partner_id.name + '_' + self.name
        transaction_id = self.name + '_paid_off_token'
        wallet_msisdn = self.partner_id.phone if self.partner_id.phone else ''
        amount = self.payment_term_id.financed_price

        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }

        URL = API_GATEWAY_URL + "/api/v1/" + self.get_country() + "/payments"
        data = {"wallet_name": wallet_name, "transaction_id": transaction_id, "wallet_msisdn": wallet_msisdn,
                "amount": amount}
        resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
        response = resp.json()

        response_code = resp.status_code

        if str(response_code) == '200' or str(response_code) == '201':
            if 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            elif 'warning' in response:
                raise exceptions.Warning(_('PaygOps : ' + response["warning"]))
            else:
                return True
        else:
            if 'msg' in response:
                raise exceptions.Warning(_(response["msg"]))
            elif 'error' in response:
                raise exceptions.Warning(_(response["error_message"]))

    def get_unlock_token(self):
        current_token = self.env['credit.token'].search([('loan_id', '=', self.id)], order="id desc", limit=1)
        if current_token and current_token.token_type == 'DISABLE_PAYG':
            view = self.env.ref('wave2_peg_africa.view_credit_token_code_form')
            context = self._context.copy()
            return {
                'name': _('Unlock Token'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'credit.token',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': current_token.id,
                'context': context,
            }
        else:
            view = self.env.ref('wave2_peg_africa.sale_order_unlock_token_confirmation_view')
            context = self._context.copy()
            return {
                'name': _('Unlock Token Confirmation'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': context,
            }

    def generate_unlock_token(self):
        if self.paygops_id:
            response = self.register_unlocking_payment()
            if response:
                transaction_id = self.name + '_paid_off_token'
                amount = self.payment_term_id.financed_price
                self.env['paygops.tokens'].last_token_generated(self.paygops_id.device_id, transaction_id, 0,
                                                                self.partner_id.id, amount, self.user_id.id, self.id,
                                                                self.partner_id.phone, self.partner_id.phone, self)
                current_token = self.env['credit.token'].search([('loan_id', '=', self.id)], order="id desc", limit=1)
                if current_token and current_token.token_type == 'DISABLE_PAYG':
                    view = self.env.ref('wave2_peg_africa.view_credit_token_code_form')
                    context = self._context.copy()
                    return {
                        'name': _('Unlock Token'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'credit.token',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': current_token.id,
                        'context': context,
                    }


class StockPickingStockDelivery(models.Model):
    _inherit = 'stock.picking'

    deposit_invoice_fully_paid = fields.Boolean(string='Deposit fully paid')
    from_sale = fields.Boolean(string='Created from sale', compute='_compute_from_sale')  #
    token_generated = fields.Boolean(string='Token generated')
    location_dest_id = fields.Many2one(states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]})
    source_individual_id = fields.Many2one(string='Source Individual', comodel_name='res.partner')
    source_location_individual = fields.Boolean(compute='_compute_source_individual')  #
    destination_individual_id = fields.Many2one(string='Destination Individual', comodel_name='res.partner')
    destination_location_individual = fields.Boolean(compute='_compute_dest_individual')  #

    @api.depends('location_id')
    def _compute_source_individual(self):
        if self.location_id:
            self.source_location_individual = self.location_id.individual_location
        else:
            self.source_location_individual = False

    @api.depends('location_dest_id')
    def _compute_dest_individual(self):
        if self.location_dest_id:
            self.destination_location_individual = self.location_dest_id.individual_location
        else:
            self.destination_location_individual = False

    @api.onchange('destination_individual_id')
    def _onchange_dest_individual(self):
        if self.partner_id:
            return
        else:
            self.partner_id = self.destination_individual_id.id

    @api.depends('origin')
    def _compute_from_sale(self):
        for rec in self:
            print('---rec ...', rec, rec.origin)
            if rec.origin and 'S' in rec.origin:
                rec.from_sale = True
                sale_order = self.env['sale.order'].search(
                    [('name', '=', rec.origin), ('partner_id', '=', rec.partner_id.id)], limit=1)
                if sale_order:
                    rec.deposit_invoice_fully_paid = sale_order.deposit_invoice_fully_paid
                    rec.write({'deposit_invoice_fully_paid': sale_order.deposit_invoice_fully_paid})
            else:
                rec.from_sale = False

    @api.model
    def create(self, values):
        picking = super(StockPickingStockDelivery, self).create(values)
        if picking.picking_type_id.code == 'outgoing' and picking.from_sale and not picking.destination_individual_id and picking.location_dest_id.individual_location:
            picking.destination_individual_id = picking.partner_id.id

        if picking.picking_type_id.code == 'incoming' and not picking.source_individual_id and picking.location_id.individual_location:
            picking.source_individual_id = picking.partner_id.id

        if picking.from_sale:
            sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
            picking.source_individual_id = sale_order.install_user_id.partner_id
        return picking


class AccountInvoiceExtension(models.Model):
    _inherit = 'account.move'

    paygops_id = fields.Many2one('peg.africa.paygops', 'PaygOps ID', compute='default_paygops_id')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', states={'draft': [('readonly', False)], 'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    contract_status = fields.Char("Contract Status", related='sale_order_id.contract_status.name')
    written_off_flag = fields.Selection("WO Flag", related='sale_order_id.written_off_flag')
    financed_price_value = fields.Float('Financed price', compute='default_financed_price_value')
    type_of_product_id = fields.Many2one(string='Type of Product', comodel_name='wave2.peg.africa.type.of.product',
                                         compute='default_sale_id', store=True)
    analytical_account = fields.Char(store=True, compute='_compute_analytical_account')

    def action_wave_peg_africa_discount_views(self):
        action_context = {
            'invoice_id': self.id
        }
        return {
            'name': 'wave.peg.africa.discount.form',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'wave.peg.africa.discount',
            'context': action_context,
            'type': 'ir.actions.act_window',
            'nodestroy': False,
            'target': 'new',
        }

    def default_financed_price_value(self):
        order = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)], limit=1)
        self.financed_price_value = order.payment_term_id.financed_price

    def default_paygops_id(self):
        for s in self:
            order = self.env['sale.order'].search([('name', '=', s.invoice_origin), ('company_id', '=', s.company_id.id)],
                                                  limit=1)
            s.paygops_id = order.paygops_id.id

    def default_sale_id(self):
        for s in self:
            order = s.env['sale.order'].search([('name', '=', s.invoice_origin),
                                                ('company_id', '=', s.company_id.id)], limit=1)
            s.sale_order_id = order.id
            if order:
                s.type_of_product_id = order.type_of_product_id

    def set_writtenoff(self):
        sale_order = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)],
            limit=1
        )
        if sale_order:
            sale_order.write({
                'contract_status': self.env['sale.contract.status'].search(
                    [('name', '=', 'Written Off')], limit=1),
                'stock_action': self.env['sale.stock.action'].search(
                    [('name', '=', 'To be repossessed')], limit=1),
                'written_off_flag': 'Client was suspended/cancelled'
            })

    @api.depends('invoice_line_ids')
    def _compute_analytical_account(self):
        for record in self:
            if len(record.invoice_line_ids) > 0:
                record.analytical_account = record.invoice_line_ids[0].analytic_account_id.sudo().complete_name

    def _is_kit_returned(self, sale_order):
        product_order_line = []
        product_picking_id = []
        for line in sale_order.order_line:
            product_order_line.append(line.product_id.name)
            source = 'Return of '
            picking = self.env['stock.picking'].search([('origin', '=', sale_order.name)])
            stock_picking = self.env['stock.picking'].search([('origin', '=', source + picking.name)])
            for reference in stock_picking:
                if line.product_id.name == reference.move_line_ids_without_package.product_id.name:
                    product_picking_id.append(line.product_id.name)
        if len(product_order_line) == len(product_picking_id):
            return True
        else:
            return False

    def set_writtenoff_retrieved(self):
        sale_order = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)],
            limit=1
        )
        if sale_order and self._is_kit_returned(sale_order):
            sale_order.write({
                'contract_status': self.env['sale.contract.status'].search(
                    [('name', '=', 'Written Off')], limit=1),
                'stock_action': self.env['sale.stock.action'].search(
                    [('name', '=', 'Repossessed')], limit=1),
                'written_off_flag': 'Client was suspended/cancelled'
            })
        else:
            sale_order.write({
                'contract_status': self.env['sale.contract.status'].search(
                    [('name', '=', 'Written Off')], limit=1),
                'stock_action': self.env['sale.stock.action'].search(
                    [('name', '=', 'To be repossessed')], limit=1),
                'written_off_flag': 'Client was suspended/cancelled'
            })

    def set_writtenoff_lost(self):
        sale_order = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)],
            limit=1
        )
        if sale_order:
            sale_order.write({
                'contract_status': self.env['sale.contract.status'].search(
                    [('name', '=', 'Written Off')], limit=1),
                'stock_action': self.env['sale.stock.action'].search(
                    [('name', '=', 'Lost/Stolen')], limit=1),
                'written_off_flag': 'Client was suspended/cancelled'
            })

    @api.model
    def create(self, vals):
        result = super(AccountInvoiceExtension, self).create(vals)
        if result.paygops_id:
            self.env['invoice.stock.action'].create({'invoice_id': result.id})
        return result

    # def action_invoice_cancel(self): #method change --- in v14
    def button_cancel(self):
        result = super(AccountInvoiceExtension, self).button_cancel()
        # result = super(AccountInvoiceExtension, self).action_invoice_cancel()
        for record in self:
            order = record.env['sale.order'].search([('name', '=', record.invoice_origin),
                                                     ('company_id', '=', record.company_id.id)], limit=1)
            if order:
                order.write({
                    'outstanding_balance': order.payment_term_id.financed_price - order.total_amount_paid - order.discount_given
                })
        return result

    def invoice_stock_action(self):
        # self.ensure_one()
        view = self.env.ref('wave2_peg_africa.view_invoice_stock_action_form')
        context = self._context.copy()
        sale_order = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)], limit=1)
        if sale_order:
            sale_order.calculate_status()

        result = self.env['invoice.stock.action'].search(
            [('invoice_id', '=', self.id)],
            limit=1)

        if result:
            if not result.stock_action_lines:
                result.get_stock_action_lines()
        else:
            result = self.env['invoice.stock.action'].create({'invoice_id': self.id})

        return {
            'name': _('Stock Actions'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.stock.action',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': result.id,
            'context': context,
        }

    def terminate_contract(self):
        # self.ensure_one()
        view = self.env.ref('wave2_peg_africa.view_terminate_form')
        context = self._context.copy()

        result = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)], limit=1)
        return {
            'name': _('Terminate Contract'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': result.id,
            'context': context,
        }

    def reactivate_contract(self):
        for s in self:
            sale_order = self.env['sale.order'].search(
                [('name', '=', s.invoice_origin), ('company_id', '=', s.company_id.id)], limit=1)
            if sale_order:
                sale_order.write({
                    'written_off_flag': 'NA'
                })
                sale_order.calculate_status()

    def get_unlock_token(self):
        sale_order = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)], limit=1)
        current_token = self.env['credit.token'].search([('loan_id', '=', sale_order.id)], order="id desc", limit=1)
        if current_token and current_token.token_type == 'DISABLE_PAYG':
            view = self.env.ref('wave2_peg_africa.view_credit_token_code_form')
            context = self._context.copy()
            return {
                'name': _('Unlock Token'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'credit.token',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': current_token.id,
                'context': context,
            }
        else:
            view = self.env.ref('wave2_peg_africa.unlock_token_confirmation_view')
            context = self._context.copy()
            return {
                'name': _('Unlock Token Confirmation'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': context,
            }

    #     #

    # def _post(self, soft=True):
    #     """Post/Validate the documents.
    #
    #     Posting the documents will give it a number, and check that the document is
    #     complete (some fields might not be required if not posted but are required
    #     otherwise).
    #     If the journal is locked with a hash table, it will be impossible to change
    #     some fields afterwards.
    #
    #     :param soft (bool): if True, future documents are not immediately posted,
    #         but are set to be auto posted automatically at the set accounting date.
    #         Nothing will be performed on those documents before the accounting date.
    #     :return Model<account.move>: the documents that have been posted
    #     """
    #     if not self._context.get('is_from_wave2_payment'):
    #         return super(AccountInvoiceExtension, self)._post()
    #
    #     if soft:
    #         future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
    #         future_moves.auto_post = True
    #         for move in future_moves:
    #             msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
    #             move.message_post(body=msg)
    #         to_post = self - future_moves
    #     else:
    #         to_post = self
    #
    #     # `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
    #     if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
    #         raise AccessError(_("You don't have the access rights to post an invoice."))
    #     for move in to_post:
    #         if not move.line_ids.filtered(lambda line: not line.display_type):
    #             raise UserError(_('You need to add a line before posting.'))
    #         if move.auto_post and move.date > fields.Date.context_today(self):
    #             date_msg = move.date.strftime(get_lang(self.env).date_format)
    #             raise UserError(_("This move is configured to be auto-posted on %s", date_msg))
    #
    #         if not move.partner_id:
    #             if move.is_sale_document():
    #                 raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
    #             elif move.is_purchase_document():
    #                 raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))
    #
    #         if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
    #             raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))
    #
    #         # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
    #         # lines are recomputed accordingly.
    #         # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
    #         # environment.
    #         if not move.invoice_date and move.is_invoice(include_receipts=True):
    #             move.invoice_date = fields.Date.context_today(self)
    #             move.with_context(check_move_validity=False)._onchange_invoice_date()
    #
    #         # When the accounting date is prior to the tax lock date, move it automatically to the next available date.
    #         # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
    #         # environment.
    #         if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tax_tag_ids):
    #             move.date = move.company_id.tax_lock_date + timedelta(days=1)
    #             move.with_context(check_move_validity=False)._onchange_currency()
    #
    #     # Create the analytic lines in batch is faster as it leads to less cache invalidation.
    #     to_post.mapped('line_ids').create_analytic_lines()
    #     to_post.write({
    #         'state': 'posted',
    #         'posted_before': True,
    #     })
    #
    #     for move in to_post:
    #         move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])
    #
    #         # Compute 'ref' for 'out_invoice'.
    #         if move._auto_compute_invoice_reference():
    #             to_write = {
    #                 'payment_reference': move._get_invoice_computed_reference(),
    #                 'line_ids': []
    #             }
    #             for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
    #                 to_write['line_ids'].append((1, line.id, {'name': to_write['payment_reference']}))
    #             move.write(to_write)
    #
    #     for move in to_post:
    #         if move.is_sale_document() \
    #                 and move.journal_id.sale_activity_type_id \
    #                 and (move.journal_id.sale_activity_user_id or move.invoice_user_id).id not in (self.env.ref('base.user_root').id, False):
    #             move.activity_schedule(
    #                 date_deadline=min((date for date in move.line_ids.mapped('date_maturity') if date), default=move.date),
    #                 activity_type_id=move.journal_id.sale_activity_type_id.id,
    #                 summary=move.journal_id.sale_activity_note,
    #                 user_id=move.journal_id.sale_activity_user_id.id or move.invoice_user_id.id,
    #             )
    #
    #     customer_count, supplier_count = defaultdict(int), defaultdict(int)
    #     for move in to_post:
    #         if move.is_sale_document():
    #             customer_count[move.partner_id] += 1
    #         elif move.is_purchase_document():
    #             supplier_count[move.partner_id] += 1
    #     for partner, count in customer_count.items():
    #         (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
    #     for partner, count in supplier_count.items():
    #         (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)
    #
    #     # Trigger action for paid invoices in amount is zero
    #     to_post.filtered(
    #         lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
    #     ).action_invoice_paid()
    #
    #     # Force balance check since nothing prevents another module to create an incorrect entry.
    #     # This is performed at the very end to avoid flushing fields before the whole processing.
    #     to_post._check_balanced()
    #     return to_post

    def generate_unlock_token(self):
        sale_order = self.env['sale.order'].search(
            [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)], limit=1)

        if sale_order.paygops_id:
            response = sale_order.register_unlocking_payment()
            if response:
                transaction_id = sale_order.name + '_paid_off_token'
                amount = sale_order.payment_term_id.financed_price
                self.env['paygops.tokens'].last_token_generated(sale_order.paygops_id.device_id, transaction_id, 0,
                                                                sale_order.partner_id.id, amount, sale_order.user_id.id,
                                                                sale_order.id, sale_order.partner_id.phone,
                                                                sale_order.partner_id.phone, sale_order)
                current_token = self.env['credit.token'].search([('loan_id', '=', sale_order.id)], order="id desc",
                                                                limit=1)
                if current_token and current_token.token_type == 'DISABLE_PAYG':
                    view = self.env.ref('wave2_peg_africa.view_credit_token_code_form')
                    context = self._context.copy()
                    return {
                        'name': _('Unlock Token'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'credit.token',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': current_token.id,
                        'context': context,
                    }

    # Deprecated Function from V14
    def action_credit_note_draft(self):
        self.write({'state': 'draft'})
        # Delete former printed invoice
        try:
            report_invoice = self.env['ir.actions.report']._get_report_from_name('account.report_invoice')
        except IndexError:
            report_invoice = False
        if report_invoice and report_invoice.attachment:
            for invoice in self:
                with invoice.env.do_in_draft():
                    invoice.number, invoice.state = invoice.move_name, 'open'
                    attachment = self.env.ref('account.account_invoices').retrieve_attachment(invoice)
                if attachment:
                    attachment.unlink()
        return True
    

class StockLocationInherit(models.Model):
    _inherit = 'stock.location'

    individual_location = fields.Boolean(string='Is Individual Location', default=False)
