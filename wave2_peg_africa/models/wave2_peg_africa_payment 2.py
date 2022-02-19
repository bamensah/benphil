# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError
import requests
import json
import phonenumbers
import re 
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

def format_date(date):
    timestamp = ""
    try:
        timestamp = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        timestamp = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d %H:%M:%S')

    return timestamp

class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    _sql_constraints = [
        ('transaction_id_uniq', 'UNIQUE (mno_ref_number)',  'You can not have two payments with the same MNO Ref number !')
    ]

    # state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancel', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    mno_ref_number = fields.Char(string='MNO ref number')
    sale_order= fields.Many2one('sale.order', string='Sale Order')
    mobile_number = fields.Char(string='Mobile Number used for payment')
    picking_id= fields.Many2one('stock.picking', string='Picking', readonly=True)
    sale_order_ids_list = fields.Many2many('sale.order',store=True,invisible=True)
    primary_mobile_number_partner = fields.Char(string='Partner primary mobile number',compute='_compute_primary_mobile_number_partner', store=True)
    confirmed = fields.Boolean(string='Confirmed', default=False)
    
    #Fields related to W2E-58 Block Tokens
    block_status = fields.Selection(string='Block Status', selection=[('none', 'None'), ('blocked','Blocked'), ('unblocked', 'Unblocked'), ('paid', 'Released')], default='none')

    @api.depends('partner_id')
    def _compute_primary_mobile_number_partner(self):
        for rec in self:
            if rec.partner_id:
                rec.primary_mobile_number_partner = rec.partner_id.phone if rec.partner_id.phone else ''
            else:
                rec.primary_mobile_number_partner = ''
                return rec


    # migrate later v14 ------------------------------
    # @api.model
    def default_get(self,default_fields):
        res = super(AccountPaymentInherit, self).default_get(default_fields)
        if 'picking_id' in res and res['picking_id']:
            picking_id = self.env['stock.picking'].search([('id', '=', res['picking_id'])])
            res['sale_order'] = self.env['sale.order'].search([('name', '=', picking_id.origin)]).id
            res['partner_id'] = self.env['res.partner'].search([('id', '=', picking_id.partner_id.id)]).id
        return res
    #
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.sale_order_ids_list = []
        sale_order_list=[]
        domain = self.env['sale.order'].search([('partner_id', '=', self.partner_id.id), ('state', '!=', 'cancel')])
        if domain:
            for sale_order in domain:
                sale_order_list.append(sale_order.id)
            self.sale_order_ids_list = sale_order_list

    # #PHONE VALIDATION E164 format
    @api.onchange('mobile_number')
    def _onchange_mobile_number(self):
        if self.mobile_number and self.mobile_number != '':
            try:
                original_num = phonenumbers.parse(self.mobile_number)
                format = phonenumbers.PhoneNumberFormat.E164
                self.mobile_number = phonenumbers.format_number(original_num, format)
            except Exception as e:
                raise ValidationError("Phone number format is not valid")
    #
    # @api.one
    @api.constrains('mobile_number')
    def _check_phonenumber(self):
        if self.mobile_number:
            original_num = phonenumbers.parse(self.mobile_number)
            if not phonenumbers.is_possible_number(original_num):
                raise ValidationError("Phone number format is not valid")
    #
    @api.onchange('payment_class')
    def _onchange_payment_class(self):
        if self.payment_class:
            if self.state == 'draft':
                if self.payment_class == 'deposit':
                    self.withhold_check = True
                else:
                    self.withhold_check = False
        else:
            if self.state == 'draft':
                self.withhold_check = False
    #
    # @api.multi
    def get_country(self):
        return self.sale_order.company_id.country_id.code.lower()
    # end ---------------------------

    # migrate later v14 ---------------
    # @api.multi
    def register_customer(self):
        name = self.partner_id.name + '_' + self.sale_order.name
        surname = self.partner_id.name + '_' + self.sale_order.name
        #village = self.sale_order.team_id.id
        #lead_generator = self.sale_order.user_id.id
        if self.sale_order.payment_term_id.paygops_offer_id:
            offer = self.sale_order.payment_term_id.paygops_offer_id
        else:
            return True #raise exceptions.Warning(_('Please specify the ID of the offer in PaygOps for this payment term'))
        #Dummy data
        #Get village and lead_generator in system parameter
        parameters = self.env['ir.config_parameter'].sudo()
        village = int(parameters.get_param('peg_village'))
        lead_generator = int(parameters.get_param('peg_lead_generator'))
        phone_numbers=[]
        #wallet_msisdn = self.mobile_number
        #Use partner's primary mobile number instead of number used for payment to match payments in PaygOps
        wallet_msisdn = self.primary_mobile_number_partner.replace(' ', '')
        phone_numbers.append(wallet_msisdn)

        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }

        URL = API_GATEWAY_URL + "/api/v1/" + self.get_country() + "/leads"
        data = {"name": name, "surname": surname, "village": village, "generator": lead_generator,"offer": offer, "phone_numbers": phone_numbers}
        resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
        response = resp.json()

        response_code = resp.status_code

        #TODO REPLACE BY TRY CATCH
        if str(response_code) == '200' or str(response_code)=='201':
            if 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            else:
                lead_id = response["id"]
                register_date = response["generation_date"]
                paygops_id = self.env['peg.africa.paygops'].create({'lead_id': lead_id, 'register_date': format_date(register_date), 'partner_id': self.partner_id.id, 'loan_id':self.sale_order.id})
                self.sale_order.update({'paygops_id': paygops_id.id})
                if self.sale_order.invoice_id:
                    stock_action = self.env['invoice.stock.action'].search(
                        [('invoice_id', '=', self.sale_order.invoice_id.id)],limit=1)
                    if not stock_action:
                        self.env['invoice.stock.action'].create({'invoice_id': self.sale_order.invoice_id.id})
                return response["status"]
        else :
            if 'msg' in response:
                raise exceptions.Warning(_(response["msg"]))
            elif 'error' in response:
                raise exceptions.Warning(_(response["error_message"]))
    #
    # @api.multi
    def register_payment(self):

        #Call Payments API HERE, send wallet_name, transaction_id, wallet_msisdn and amount

        if self.sale_order.payment_term_id.paygops_offer_id == 0:
            return True

        wallet_name = self.partner_id.name + '_' + self.sale_order.name
        transaction_id = self.mno_ref_number
        #wallet_msisdn = self.mobile_number
        #Use partner's primary mobile number instead of number used for payment to match payments in PaygOps
        wallet_msisdn = self.primary_mobile_number_partner
        amount = self.amount

        #TESTS API GATEWAY
        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }

        URL = API_GATEWAY_URL + "/api/v1/" + self.get_country() + "/payments"
        data = {"wallet_name": wallet_name, "transaction_id": transaction_id, "wallet_msisdn": wallet_msisdn, "amount": amount}
        resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
        response = resp.json()

        response_code = resp.status_code
        #TODO REPLACE BY TRY CATCH
        if str(response_code) == '200' or str(response_code)=='201':
            if 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            elif 'warning' in response:
                raise exceptions.Warning(_('PaygOps : ' + response["warning"]))
            else:
                #Payment sent to PaygOps
                return True
        else :
            if 'msg' in response:
                raise exceptions.Warning(_(response["msg"]))
            elif 'error' in response:
                raise exceptions.Warning(_(response["error_message"]))

    def _get_duration(self, day, month, year):
        return (datetime(year, month, day) - datetime.today()).days
    #
    # @api.multi
    def register_device(self, device_serial):

        #Call REGISTER DEVICE API HERE, send lead_id, device_serial
        if self.sale_order.payment_term_id.paygops_offer_id == 0:
            return True

        lead_id = self.sale_order.paygops_id.lead_id

        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }

        URL = API_GATEWAY_URL + "/api/v1/" + self.get_country() + "/device/register"
        data = {"lead_id": lead_id, "device_serial": device_serial}
        resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
        response = resp.json()

        response_code = resp.status_code
        #REPLACE BY TRY CATCH
        if str(response_code) == '200' or str(response_code)=='201':
            if 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            elif 'answer_data' in response:
                if len(response["answer_data"]) > 1:
                    if 'activation_answer_code' in response["answer_data"][1]:
                        token_code = response["answer_data"][1]["activation_answer_code"]
                        credit_end_date = response["answer_data"][1]["expiration_time_year"] + '-' + response["answer_data"][1]["expiration_time_month"] + '-' + response["answer_data"][1]["expiration_time_day"]
                        token_id = response["uuid"]
                        duration = self._get_duration(int(response["answer_data"][1]["expiration_time_day"]), int(response["answer_data"][1]["expiration_time_month"]), int(response["answer_data"][1]["expiration_time_year"]))
                        generated_date=response["time"]
                        token_type = response["type"]
                        client_id= response["answer_data"][0]["client_id"]
                        device_id = self.env['stock.production.lot'].search([('name', '=', device_serial)],limit=1)
                        registration_answer_code = response["answer_data"][0]["registration_answer_code"]

                        token = self.env['credit.token'].create({'code': token_code, 'token_id': token_id, 'duration': duration, 'token_type': token_type, 'credit_end_date': datetime.strptime(credit_end_date, '%Y-%m-%d'), 'generated_date': format_date(generated_date),
                            'inventory_id': device_id.id, 'transaction_id': self.mno_ref_number if self.mno_ref_number else '', 'payment_id':self.id, 'partner_id': self.partner_id.id, 'amount': self.amount, 'device_serial': device_serial,
                            'salesperson': self.sale_order.user_id.id, 'loan_id': self.sale_order.id, 'phone_number': self.mobile_number, 'phone_number_partner': self.primary_mobile_number_partner})

                        paygops_id = self.env['peg.africa.paygops'].search([('id', '=', self.sale_order.paygops_id.id)])
                        paygops_id.update({'device_id': device_serial, 'client_id':client_id, 'registration_answer_code':registration_answer_code})

                        #Send SMS
                        #content_message='Bienvenue parmi nos clients ! Vous pouvez activer votre nouvel appareil avec le code suivant: ' + token_code + '. Votre prochain paiement est dû le ' + credit_end_date + '. N\'hésitez pas à contacter le service d\'assistance en cas de problème.'
                        #TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                        #self.send_sms(content_message,self.mobile_number,'welcome_message',self.sale_order.id)

                        self.sale_order.calculate_status()
                    else:
                        client_id= response["answer_data"][0]["client_id"]
                        registration_answer_code = response["answer_data"][0]["registration_answer_code"]
                        device_id = self.env['stock.production.lot'].search([('name', '=', device_serial)],limit=1)
                        paygops_id = self.env['peg.africa.paygops'].search([('id', '=', self.sale_order.paygops_id.id)])
                        paygops_id.update({'device_id': device_serial, 'client_id':client_id, 'registration_answer_code':registration_answer_code})
                        self.env.cr.commit()
                        self.sync_device(client_id, device_serial)

                else:
                    message_no_activation=''
                    if response["answer_data"][0]["status"] == 'NO_ACTIVATION_TIME_ON_DEVICE':
                        message_no_activation = ' Please register a payment for this client and the corresponding sale order to activate the device and generate a token.'
                    raise exceptions.Warning(_('PaygOps : ' + response["answer_data"][0]["status"] + message_no_activation))
            elif 'error_message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
        else :
            if 'msg' in response:
                raise exceptions.Warning(_(response["msg"]))
            elif 'error' in response:
                raise exceptions.Warning(_(response["error_message"]))
            elif 'message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["message"]))
    #
    #CALL SYNC DEVICE IF DEVICE IS LINKED TO SELF.SALE_ORDER.PAYGOPS_ID.DEVICE_ID
    # @api.multi
    def sync_device(self, client_id, device_serial):
        if self.sale_order.payment_term_id.paygops_offer_id == 0:
            return True
        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }
        URL = API_GATEWAY_URL + "/api/v1/" + self.get_country() + "/sync_device"
        data = {"client_id": client_id, "device_serial": device_serial}
        resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
        response = resp.json()

        response_code = resp.status_code
        #TODO REPLACE BY TRY CATCH
        if str(response_code) == '200' or str(response_code)=='201':
            if 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            elif 'answer_data' in response:
                if 'activation_answer_code' in response["answer_data"][0]:
                    duration = 0
                    token_code = response["answer_data"][0]["activation_answer_code"]
                    credit_end_date = response["answer_data"][0]["expiration_time_year"] + '-' + response["answer_data"][0]["expiration_time_month"] + '-' + response["answer_data"][0]["expiration_time_day"]
                    token_id = response["uuid"]
                    duration = self._get_duration(int(response["answer_data"][0]["expiration_time_day"]), int(response["answer_data"][0]["expiration_time_month"]), int(response["answer_data"][0]["expiration_time_year"]))
                    generated_date=response["time"]
                    token_type = response["type"]
                    client_id= response["client"]
                    device_id = self.env['stock.production.lot'].search([('name', '=', device_serial)],limit=1)

                    token = self.env['credit.token'].create({'code': token_code, 'token_id': token_id, 'duration': duration, 'token_type': token_type, 'credit_end_date': datetime.strptime(credit_end_date, '%Y-%m-%d'), 'generated_date': format_date(generated_date),
                        'inventory_id': device_id.id, 'transaction_id': self.mno_ref_number if self.mno_ref_number else '', 'payment_id':self.id, 'partner_id': self.partner_id.id, 'amount': self.amount, 'device_serial': device_serial,
                        'salesperson': self.sale_order.user_id.id, 'loan_id': self.sale_order.id, 'phone_number': self.mobile_number, 'phone_number_partner': self.primary_mobile_number_partner})

                    #Send SMS : welcome_message for the first activation
                    tokens = self.env['credit.token'].search([('loan_id', '=', self.sale_order.id)])
                    #if len(tokens)==1:
                        #content_message='Bienvenue parmi nos clients ! Vous pouvez activer votre nouvel appareil avec le code suivant: ' + token_code + '. Votre prochain paiement est dû le ' + credit_end_date + '. N\'hésitez pas à contacter le service d\'assistance en cas de problème.'
                        #TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                        #self.send_sms(content_message,self.mobile_number,'welcome_message',self.sale_order.id)

                    self.sale_order.calculate_status()

                else:
                    message_no_activation=''
                    if response["answer_data"][0]["status"] == 'NO_ACTIVATION_TIME_ON_DEVICE':
                        message_no_activation = ' Please register a payment for this client and the corresponding sale order to activate the device and generate a token.'
                    raise exceptions.Warning(_('PaygOps : ' + response["answer_data"][0]["status"] + message_no_activation))
            elif 'error_message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
        else :
            if 'msg' in response:
                raise exceptions.Warning(_(response["msg"]))
            elif 'error' in response:
                raise exceptions.Warning(_(response["error_message"]))
            elif 'message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["message"]))
    #
    #CALL COLLECT CASH IF DEVICE IS LINKED TO SELF.SALE_ORDER.PAYGOPS_ID.DEVICE_ID
    # @api.multi
    def collect_cash(self, amount, device_serial, sale_order):

        if sale_order.payment_term_id.paygops_offer_id == 0:
            return True

        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }

        URL = API_GATEWAY_URL + "/api/v1/" + self.get_country() + "/collect/cash"
        data = {"amount": amount, "device_serial": device_serial}
        resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
        response = resp.json()

        response_code = resp.status_code

        if str(response_code) == '200' or str(response_code)=='201':
            if 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            elif 'answer_data' in response:
                if response["answer_data"][1]["status"] == "BALANCE_INSUFFICIENT":
                    raise exceptions.Warning(_('Minimum payment: ' + str(response["answer_data"][1]["minimum_payment"])))
                elif len(response["answer_data"]) > 1:
                    if 'activation_answer_code' in response["answer_data"][2]:
                        duration = 0
                        token_code = response["answer_data"][2]["activation_answer_code"]
                        credit_end_date = response["answer_data"][1]["expiration_time_year"] + '-' + response["answer_data"][1]["expiration_time_month"] + '-' + response["answer_data"][1]["expiration_time_day"]
                        token_id = response["uuid"]
                        duration = self._get_duration(int(response["answer_data"][1]["expiration_time_day"]), int(response["answer_data"][1]["expiration_time_month"]), int(response["answer_data"][1]["expiration_time_year"]))
                        generated_date=response["time"]
                        token_type = response["type"]
                        client_id= response["client"]
                        device_id = self.env['stock.production.lot'].search([('name', '=', device_serial)],limit=1)

                        token = self.env['credit.token'].create({'code': token_code, 'token_id': token_id, 'duration': duration, 'token_type': token_type, 'credit_end_date': datetime.strptime(credit_end_date, '%Y-%m-%d'), 'generated_date': format_date(generated_date),
                            'inventory_id': device_id.id, 'transaction_id': self.mno_ref_number if self.mno_ref_number else '', 'payment_id':self.id, 'partner_id': self.partner_id.id, 'amount': amount, 'device_serial': device_serial,
                            'salesperson': sale_order.user_id.id, 'loan_id': sale_order.id, 'phone_number': self.mobile_number if self.mobile_number else '', 'phone_number_partner':self.primary_mobile_number_partner})
                        sale_order.calculate_status()

                else:
                    message_no_activation=''
                    if response["answer_data"][0]["status"] == 'NO_ACTIVATION_TIME_ON_DEVICE':
                        message_no_activation = ' Please register a payment for this client and the corresponding sale order to activate the device and generate a token.'
                    raise exceptions.Warning(_('PaygOps : ' + response["answer_data"][0]["status"] + message_no_activation))
            elif 'error_message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
        else :
            if 'msg' in response:
                raise exceptions.Warning(_(response["msg"]))
            elif 'error' in response:
                raise exceptions.Warning(_(response["error_message"]))
            elif 'message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["message"]))

    # @api.multi
    # def send_sms(self,message,phone_number,message_type,sale_order):
    #
    #     #Call SMS API HERE, send message, phone_number
    #
    #     #TESTS API GATEWAY
    #     params = self.env['ir.config_parameter'].sudo()
    #     API_GATEWAY_URL = params.get_param('api_gateway_url')
    #     API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
    #     HEADERS = {
    #         "Content-Type": "application/json",
    #         "Authorization": "Bearer " + API_GATEWAY_TOKEN,
    #     }
    #
    #     URL = API_GATEWAY_URL + "/api/sms/send"
    #     data = {"message": message, "phonenumber": phone_number}
    #     resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
    #     response = resp.json()
    #
    #     response_code = resp.status_code
    #     #TODO REPLACE BY TRY CATCH
    #     if str(response_code) == '200':
    #         #Create SMS in corresponding table
    #         #Remove this line because we get all sms in sms api
    #         #sms = self.env['credit.sms'].create({'content': message, 'message_type': message_type, 'sent': datetime.now(),
    #         #                'partner_id': self.partner_id.id,'loan_id': sale_order, 'phone_number': phone_number})
    #         # SMS sent
    #         return True
    #     else :
    #         if 'message' in response:
    #             raise exceptions.Warning(_(response["message"]))
    #
    # # Check if payment needs to be blocked or unblocked. Should work only on PaygOps products
    # @api.multi
    def is_blocked(self):
        cs_blocked = self.env.ref('wave2_peg_africa.contract_status_blocked')
        cs_written_off = self.env.ref('wave2_peg_africa.contract_status_written_off')
        try:
            for s in self:
                if s.sale_order and s.partner_id:
                    if (s.sale_order.payment_term_id.paygops_offer_id):
                        if s.sale_order.partner_id.client_status:
                            if (s.sale_order.partner_id.client_status.id in (cs_blocked.id, cs_written_off.id)) or s.sale_order.partner_id.manual_block == True:
                                s.write({'block_status':'blocked'})
                                return True

                            #If it was just unblocked
                            if(s.block_status == 'blocked' and (s.sale_order.partner_id.client_status.id not in (cs_blocked.id, cs_written_off.id) or s.sale_order.partner_id.manual_block == False)):
                                s.write({'block_status':'unblocked'})
                        else:
                            return False
                    else:
                        return False
                elif s.partner_id:
                    invoices = self.env['account.move'].search([('name', '=', s.ref)], limit=1)
                    if any(invoices):
                        for inv in invoices:
                            sale = self.env['sale.order'].search([('name', '=' , inv.invoice_origin )], limit=1)
                            if (sale.partner_id.client_status.id in (cs_blocked.id, cs_written_off.id)) or sale.partner_id.manual_block == True:
                                s.write({'block_status':'blocked'})
                                return True
                                
                    return False
        except Exception as e:
            _logger.info(str(e))
        return False
    #
    def get_withhold_rate(self):
        if self.partner_id.manual_withhold_rate >= 0:
            return self.partner_id.manual_withhold_rate, self.partner_id.get_arrears()
        else:
            arrears = list(self.partner_id.get_arrears())
            # Global Withholding Rates
            gwr = self.env['account.withhold.payment.rate'].search([])
            arrear_age = 0
            oldest_arrear = None
            oldest_arr = []
            selected_rate = 0
            # Check Arrears with Oldest first (excluding current Sale Order)
            if any(arrears):
                arrears = list(filter(lambda x: x['credit_arrears'] > 0, arrears))
                if any(arrears):
                    oldest_arrear = max(arrears, key=lambda x: x['credit_age'])
                    arrear_age = oldest_arrear['credit_age']
                    oldest_arr.append(oldest_arrear)
                    _logger.info(oldest_arr)
            else:
                return 0, None

            # Compute the rate if oldest arrear is determined
            if oldest_arrear:
                for r in gwr:
                    if (arrear_age >= r.days_lower_limit and arrear_age <= r.days_upper_limit):
                        return r.rate, oldest_arr

            return 0, None
    #
    # @api.multi
    def confirm_withholding_payment(self):
        for rec in self:
             # Check if this payment is not a withheld payment and is not a deposit, then check age of arrears to create withheld payment
            if not rec.parent_payment_id and rec.payment_class != 'deposit':
                withhold_rate, arr_obj = rec.get_withhold_rate()
                if arr_obj == None:
                    rec.write({'withhold_check': True})

                if withhold_rate > 0:
                    # Calc withheld amound
                    if any(arr_obj):
                        withheld_amount = (withhold_rate/100) * rec.amount
                        if withheld_amount > 0:
                            rec.write({
                                'original_amount': rec.amount,
                                'amount': rec.amount - withheld_amount,
                                'withhold_amount': withheld_amount,
                                'withhold_check': True,
                                'withhold_rate': withhold_rate
                                })
                        count = 0
                        remainder = withheld_amount
                        while count < len(list(arr_obj)):
                            if withheld_amount > arr_obj[count]['credit_arrears']:
                                withheld_amount = arr_obj[count]['credit_arrears']
                            remainder = remainder - withheld_amount

                            if withheld_amount > 0:
                                # Create withheld payment and save it
                                sale = self.env['sale.order'].search(
                                    [('id', '=', arr_obj[count]['sale_order_id'])]).name
                                withheld_payment = self.env['account.payment'].create({
                                    'payment_type': 'inbound',
                                    'partner_type': 'customer',
                                    'partner_id': rec.partner_id.id,
                                    'amount': withheld_amount,
                                    'journal_id': rec.journal_id.id,
                                    'date': rec.date,
                                    'payment_class': rec.payment_class,
                                    'sale_order': arr_obj[count]['sale_order_id'],
                                    'mobile_number': rec.mobile_number,
                                    'mno_ref_number': str(rec.id) + '-wth' + sale,
                                    'parent_payment_id': rec.id,
                                    'payment_method_id': rec.payment_method_id.id,
                                    'transaction_id': str(rec.id) + '-wth',
                                    'name': str(rec.id) + '-wth-' + sale,
                                    'withhold_check': True
                                })

                                rec.write({
                                    'withhold_payment_id': withheld_payment.id
                                })

                                withheld_payment.confirm()
                            else:
                                rec.write({'withhold_check': True})
                                # return True
                            count+=1
                                # Leave Loop after first oldest arrear
                            # break
                        if remainder > 0:
                            rec.write({
                                'amount': rec.amount + remainder,
                                'withhold_amount': withheld_amount,
                            })
                    else:
                        rec.write({'withhold_check': True})
                else:
                    rec.write({'withhold_check': True})

            else:
                rec.write({'withhold_check': True})
        return True
    #
    # @api.multi
    def confirm(self):
        """ Save the payment in confirmed state
        """
        deposit_value=False
        total_paid=0.0
        for rec in self:
            is_blocked = rec.is_blocked()
            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be confirmed."))

            # rec.move_id._post(soft=False)

            #OLD
            if any(inv.state != 'draft' for inv in rec.sale_order.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not drafted!"))

            # if any(inv.state != 'confirmed' or inv.state != 'open' for inv in rec.invoice_ids):
            #     raise ValidationError(_("The payment cannot be processed because the invoice is not confirmed nor open!"))

            # keep the name in case of a payment reset to draft
            # if not rec.name:
            #     # Use the right sequence to set the name
            #     if rec.payment_type == 'transfer':
            #         sequence_code = 'account.payment.transfer'
            #     else:
            #         if rec.partner_type == 'customer':
            #             if rec.payment_type == 'inbound':
            #                 sequence_code = 'account.payment.customer.invoice'
            #             if rec.payment_type == 'outbound':
            #                 sequence_code = 'account.payment.customer.refund'
            #         if rec.partner_type == 'supplier':
            #             if rec.payment_type == 'inbound':
            #                 sequence_code = 'account.payment.supplier.refund'
            #             if rec.payment_type == 'outbound':
            #                 sequence_code = 'account.payment.supplier.invoice'
            #     rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
            #     if not rec.name and rec.payment_type != 'transfer':
            #         raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Case for withheld amounts
            if rec.name and '-wth' in rec.name:
                rec.write({'confirmed': True})
                if rec.sale_order and rec.sale_order.payment_term_id:
                    write_details = {}
                    if rec.sale_order.payment_term_id.loan_type == 'loan':
                        amount_paid = rec.sale_order.amount_paid - rec.sale_order.withheld_payment_amount
                        if rec.sale_order.payment_term_id.rate_amount != 0:
                            payment_count = int(amount_paid / rec.sale_order.payment_term_id.rate_amount)
                        else:
                            payment_count = 0
                        # payment_count = int(amount_paid / rec.sale_order.payment_term_id.rate_amount)
                        write_details['amount_pending'] = amount_paid - (payment_count * rec.sale_order.payment_term_id.rate_amount)
                    write_details['outstanding_balance'] = rec.sale_order.payment_term_id.financed_price - rec.sale_order.total_amount_paid - rec.sale_order.discount_given
                    rec.sale_order.write(write_details)

                return True

            # Confirm a payment from the delivery generated by a sale order
            if self.sale_order and self.picking_id and not is_blocked:
                if not self.sale_order.deposit_invoice_fully_paid:
                    payments = self.env['account.payment'].search([('sale_order', '=', self.sale_order.id), '|', ('state', '=', 'posted'), ('confirmed', '=', True)])
                    deposit_value = self.sale_order.payment_term_id.deposit_amount \
                    if self.sale_order.payment_term_id.rate_type else self.sale_order.payment_term_id.cash_price
                    for payment in payments:
                        total_paid+=float(payment.amount)
                    total_paid += rec.amount
                    if deposit_value:
                        #Lead already registered in PaygOps
                        if self.sale_order.paygops_id:
                            if self.register_payment():
                                rec.write({'confirmed': True})
                                # self.write({'state': 'confirmed'})
                                if rec.sale_order and rec.sale_order.payment_term_id:
                                    write_details = {}
                                    if rec.sale_order.payment_term_id.loan_type == 'loan':
                                        amount_paid = rec.sale_order.amount_paid - rec.sale_order.withheld_payment_amount
                                        if rec.sale_order.payment_term_id.rate_amount != 0:
                                            payment_count = int(
                                                amount_paid / rec.sale_order.payment_term_id.rate_amount)
                                        else:
                                            payment_count = 0
                                            write_details['amount_pending'] = amount_paid - (payment_count * rec.sale_order.payment_term_id.rate_amount)
                                    write_details['outstanding_balance'] = rec.sale_order.payment_term_id.financed_price - rec.sale_order.total_amount_paid - rec.sale_order.discount_given
                                    rec.sale_order.write(write_details)
                                self.env.cr.commit()
                                if float(total_paid)>=deposit_value:
                                    if not self.sale_order.deposit_invoice_fully_paid:
                                        self.sale_order.write({'deposit_invoice_fully_paid_date': datetime.utcnow()})
                                    #Deposit fully paid
                                    self.sale_order.write({'deposit_invoice_fully_paid': True})
                                    self.picking_id.write({'deposit_invoice_fully_paid': True})
                                    self.env.cr.commit()

                                    for move_line in self.picking_id.move_line_ids:
                                        if move_line.lot_id and move_line.base_unit:
                                            self.register_device(move_line.lot_id.name)

                                    #Send SMS
                                    #content_message='Vous avez payé avec succès l\'acompte de ' + str(deposit_value) +'. Contactez le service commercial pour convenir d\'une date de livraison.'
                                    # TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                                    #self.send_sms(content_message,self.mobile_number,'lead_deposit_success',self.sale_order.id)
                                else:
                                    #Deposit not fully paid
                                    rec.write({'confirmed': True})
                                    # self.write({'state': 'confirmed'})
                                    #Send SMS
                                    #content_message='Vous n\'avez pas encore payé suffisamment pour l\'acompte. Vous avez déjà payé ' + str(total_paid) +' sur ' + str(deposit_value) +' et il vous reste toujours ' + str(deposit_value - total_paid) + ' à payer.'
                                    #TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                                    #self.send_sms(content_message,self.mobile_number,'lead_insufficient_balance',self.sale_order.id)
                                    self.env.cr.commit()
                                    raise exceptions.Warning(_('The deposit ' + str(deposit_value) + ' has not been settled. Delivery cannot be processed. Please register another payment to complete deposit.  Please refresh the page to continue.'))


                        else:
                            if self.register_customer():

                                #if self.sale_order.paygops_id:
                                    #CALL PAYMENT API HERE
                                    if self.register_payment():
                                        rec.write({'confirmed': True})
                                        # self.write({'state': 'confirmed'})
                                        amount_paid = rec.sale_order.amount_paid - rec.sale_order.withheld_payment_amount
                                        if rec.sale_order.payment_term_id.rate_amount != 0:
                                            payment_count = int(amount_paid / rec.sale_order.payment_term_id.rate_amount)
                                        else:
                                            payment_count = 0
                                        rec.sale_order.write({
                                            'outstanding_balance': rec.sale_order.payment_term_id.financed_price - rec.sale_order.total_amount_paid - rec.sale_order.discount_given,
                                            'amount_pending': amount_paid - (payment_count * rec.sale_order.payment_term_id.rate_amount)
                                        })
                                        self.env.cr.commit()

                                        if float(total_paid)>=deposit_value:
                                            #Deposit fully paid
                                            if not self.sale_order.deposit_invoice_fully_paid:
                                                self.sale_order.write({'deposit_invoice_fully_paid_date': datetime.utcnow()})
                                            self.sale_order.write({'deposit_invoice_fully_paid': True})
                                            self.picking_id.write({'deposit_invoice_fully_paid': True})
                                            self.env.cr.commit()

                                            for move_line in self.picking_id.move_line_ids:
                                                if move_line.lot_id and move_line.base_unit:
                                                    self.register_device(move_line.lot_id.name)

                                            #Send SMS
                                            #content_message='Vous avez payé avec succès l\'acompte de ' + str(deposit_value) + '. Contactez le service commercial pour convenir d\'une date de livraison.'
                                            #TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                                            #self.send_sms(content_message,self.mobile_number,'lead_deposit_success',self.sale_order.id)
                                        else:
                                            #Deposit not fully paid
                                            rec.write({'confirmed': True})
                                            # self.write({'state': 'confirmed'})
                                            #Send SMS
                                            #content_message='Vous n\'avez pas encore payé suffisamment pour l\'acompte. Vous avez déjà payé ' + str(total_paid) +' sur ' + str(deposit_value) +' et il vous reste toujours ' + str(deposit_value - total_paid) + ' à payer.'
                                            #TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                                            #self.send_sms(content_message,self.mobile_number,'lead_insufficient_balance',self.sale_order.id)
                                            self.env.cr.commit()
                                            raise exceptions.Warning(_('The deposit ' + str(deposit_value) + ' has not been settled. Delivery cannot be processed. Please register another payment to complete deposit.  Please refresh the page to continue.'))
            # Confirm a payment to activate a device (from a sale order)
            elif self.sale_order and self.sale_order.paygops_id.device_id and not is_blocked:
                # Update done to handle outstanding payments for ones with a sale_order and a paygops_device
                if self.register_payment():
                    rec.write({'confirmed': True})
                    # self.write({'state': 'confirmed'})
                    amount_paid = rec.sale_order.amount_paid - rec.sale_order.withheld_payment_amount
                    if rec.sale_order.payment_term_id.rate_amount != 0:
                        payment_count = int(amount_paid / rec.sale_order.payment_term_id.rate_amount)
                    else:
                        payment_count = 0
                    rec.sale_order.write({
                        'outstanding_balance': rec.sale_order.payment_term_id.financed_price - rec.sale_order.total_amount_paid - rec.sale_order.discount_given,
                        'amount_pending': amount_paid - (payment_count * rec.sale_order.payment_term_id.rate_amount)
                    })
                    self.env.cr.commit()

                    # After a payment is confirmed, retrieve the last token generated by PaygOps
                    self.env['paygops.tokens'].last_token_generated(self.sale_order.paygops_id.device_id, self.mno_ref_number if self.mno_ref_number else '', self.id,self.partner_id.id ,self.amount, self.sale_order.user_id.id, self.sale_order.id, self.mobile_number, self.primary_mobile_number_partner, self.sale_order)

                    #self.collect_cash(self.amount, self.sale_order.paygops_id.device_id, self.sale_order)

                    #self.sync_device(self.sale_order.paygops_id.client_id, self.sale_order.paygops_id.device_id)

            # Confirm a payment to collect cash (from an invoice)
            elif self.ref:
                if re.search("^(VTE|FAC|INV)\/[0-9]{4}\/[0-9]+$", self.ref):
                    invoice = self.env['account.invoice'].search([('number', '=', self.ref), ('partner_id', '=', self.partner_id.id)],limit=1)
                    if invoice and invoice.origin:
                        sale_order = self.env['sale.order'].search([('name', '=', invoice.origin), ('partner_id', '=', invoice.partner_id.id)],limit=1)
                        if sale_order and sale_order.paygops_id.device_id and not is_blocked:
                            rec.write({'confirmed': True})
                            # self.write({'state': 'confirmed'})
                            self.env.cr.commit()
                            self.collect_cash(self.amount, sale_order.paygops_id.device_id, sale_order)
                        else:
                            rec.write({'confirmed': True})
                            # self.write({'state': 'confirmed'})
                            self.env.cr.commit()
                    else:
                        rec.write({'confirmed': True})
                        # self.write({'state': 'confirmed'})
                        self.env.cr.commit()
                elif self.sale_order and re.search("^SO[0-9]+$", self.sale_order.name) and self.sale_order.paygops_id.device_id and not is_blocked:
                    rec.write({'confirmed': True})
                    # self.write({'state': 'confirmed'})
                    self.env.cr.commit()
                    self.collect_cash(self.amount, self.sale_order.paygops_id.device_id, self.sale_order)
                else:
                    rec.write({'confirmed': True})
                    # self.write({'state': 'confirmed'})
                    self.env.cr.commit()
                amount_paid = rec.sale_order.amount_paid - rec.sale_order.withheld_payment_amount
                if rec.sale_order.payment_term_id.rate_amount != 0:
                    payment_count = int(amount_paid / rec.sale_order.payment_term_id.rate_amount)
                else:
                    payment_count = 0
                rec.sale_order.write({
                    'outstanding_balance': rec.sale_order.payment_term_id.financed_price - rec.sale_order.total_amount_paid - rec.sale_order.discount_given,
                    'amount_pending': amount_paid - (payment_count * rec.sale_order.payment_term_id.rate_amount)
                })
            else:
                rec.write({'confirmed': True})
                # self.write({'state': 'confirmed'})
                amount_paid = rec.sale_order.amount_paid - rec.sale_order.withheld_payment_amount
                if rec.sale_order.payment_term_id.rate_amount != 0:
                    payment_count = int(amount_paid / rec.sale_order.payment_term_id.rate_amount)
                else:
                    payment_count = 0
                rec.sale_order.write({
                    'outstanding_balance': rec.sale_order.payment_term_id.financed_price - rec.sale_order.total_amount_paid - rec.sale_order.discount_given,
                    'amount_pending': amount_paid - (payment_count * rec.sale_order.payment_term_id.rate_amount)
                })
        return True
    #
    # @api.multi
    def confirm_unblock(self):
        """ Reconfirm payment that has been unblocked by Sending to PaygOps
        """
        deposit_value=False
        total_paid=0.0
        for rec in self:
            is_blocked = rec.is_blocked()
            if rec.block_status != 'unblocked':
                raise UserError(_("Only a Unblocked Payments can be resent - {0}.".format(str(rec.id))))

            # Confirm a payment from the delivery generated by a sale order
            if self.sale_order and self.picking_id and not is_blocked:
                if not self.sale_order.deposit_invoice_fully_paid:
                    payments = self.env['account.payment'].search([('sale_order', '=', self.sale_order.id), ('state', 'in', ('confirmed', 'posted'))])
                    for line in self.sale_order.payment_term_id.line_ids:
                        if line.value =='deposit':
                            deposit_value = line.value_amount
                    for payment in payments:
                        total_paid+=float(payment.amount)
                    total_paid += self.amount
                    if deposit_value:
                        #Lead already registered in PaygOps
                        if self.sale_order.paygops_id:
                            if self.register_payment():

                                if float(total_paid)>=deposit_value:
                                    if not self.sale_order.deposit_invoice_fully_paid:
                                        self.sale_order.write({'deposit_invoice_fully_paid_date': datetime.utcnow()})
                                    #Deposit fully paid
                                    self.sale_order.write({'deposit_invoice_fully_paid': True})
                                    self.picking_id.write({'deposit_invoice_fully_paid': True})

                                    for move_line in self.picking_id.move_line_ids:
                                        if move_line.lot_id and move_line.base_unit:
                                            self.register_device(move_line.lot_id.name)

                                    #Send SMS
                                    #content_message='Vous avez payé avec succès l\'acompte de ' + str(deposit_value) +'. Contactez le service commercial pour convenir d\'une date de livraison.'
                                    # TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                                    #self.send_sms(content_message,self.mobile_number,'lead_deposit_success',self.sale_order.id)
                                else:
                                    #Send SMS
                                    #content_message='Vous n\'avez pas encore payé suffisamment pour l\'acompte. Vous avez déjà payé ' + str(total_paid) +' sur ' + str(deposit_value) +' et il vous reste toujours ' + str(deposit_value - total_paid) + ' à payer.'
                                    #TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                                    #self.send_sms(content_message,self.mobile_number,'lead_insufficient_balance',self.sale_order.id)
                                    raise exceptions.Warning(_('The deposit ' + str(deposit_value) + ' has not been settled. Delivery cannot be processed. Please register another payment to complete deposit.  Please refresh the page to continue.'))
                                rec.block_status = 'paid'

                        else:
                            if self.register_customer():

                                #if self.sale_order.paygops_id:
                                    #CALL PAYMENT API HERE
                                    if self.register_payment():

                                        if float(total_paid)>=deposit_value:
                                            #Deposit fully paid
                                            if not self.sale_order.deposit_invoice_fully_paid:
                                                self.sale_order.write({'deposit_invoice_fully_paid_date': datetime.utcnow()})
                                            self.sale_order.write({'deposit_invoice_fully_paid': True})
                                            self.picking_id.write({'deposit_invoice_fully_paid': True})
                                            self.env.cr.commit()

                                            for move_line in self.picking_id.move_line_ids:
                                                if move_line.lot_id and move_line.base_unit:
                                                    self.register_device(move_line.lot_id.name)

                                            #Send SMS
                                            #content_message='Vous avez payé avec succès l\'acompte de ' + str(deposit_value) + '. Contactez le service commercial pour convenir d\'une date de livraison.'
                                            #TODO When deploying in prod, replace self.mobile_number by self.primary_mobile_number_partner
                                            #self.send_sms(content_message,self.mobile_number,'lead_deposit_success',self.sale_order.id)
                                        else:
                                            raise exceptions.Warning(_('The deposit ' + str(deposit_value) + ' has not been settled. Delivery cannot be processed. Please register another payment to complete deposit.  Please refresh the page to continue.'))

            # Confirm a payment to activate a device (from a sale order)
            elif self.sale_order and self.sale_order.paygops_id.device_id and not is_blocked:
                # Update done to handle outstanding payments for ones with a sale_order and a paygops_device
                if self.register_payment():
                    # After a payment is confirmed, retrieve the last token generated by PaygOps
                    self.env['paygops.tokens'].last_token_generated(self.sale_order.paygops_id.device_id, self.mno_ref_number if self.mno_ref_number else '', self.id,self.partner_id.id ,self.amount, self.sale_order.user_id.id, self.sale_order.id, self.mobile_number, self.primary_mobile_number_partner, self.sale_order)
                    rec.block_status = 'paid'

            # Confirm a payment to collect cash (from an invoice)
            elif self.ref:
                if self.sale_order and re.search("^SO[0-9]+$", self.sale_order.name) and self.sale_order.paygops_id.device_id and not rec.is_blocked():
                    self.collect_cash(self.amount, self.sale_order.paygops_id.device_id, self.sale_order)
                    rec.block_status = 'paid'
            else:
                rec.block_status = 'paid'
        return True

    def action_post(self):
        return super(AccountPaymentInherit, self.with_context(is_from_wave2_payment=True)).action_post()

    # @api.multi
    # def post(self):
    #     """ Create the journal items for the validated payment and update the payment's state to 'posted'.
    #         A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
    #         and another in the destination reconcilable account (see _compute_destination_account_id).
    #         If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
    #         If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
    #     """
    #     for rec in self:
    #
    #         if rec.state != 'confirmed':
    #             raise UserError(_("Only a confirmed payment can be posted."))
    #
    #         if any(inv.state != 'open' for inv in rec.invoice_ids):
    #             raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
    #
    #         # keep the name in case of a payment reset to draft
    #         if not rec.name:
    #             # Use the right sequence to set the name
    #             if rec.payment_type == 'transfer':
    #                 sequence_code = 'account.payment.transfer'
    #             else:
    #                 if rec.partner_type == 'customer':
    #                     if rec.payment_type == 'inbound':
    #                         sequence_code = 'account.payment.customer.invoice'
    #                     if rec.payment_type == 'outbound':
    #                         sequence_code = 'account.payment.customer.refund'
    #                 if rec.partner_type == 'supplier':
    #                     if rec.payment_type == 'inbound':
    #                         sequence_code = 'account.payment.supplier.refund'
    #                     if rec.payment_type == 'outbound':
    #                         sequence_code = 'account.payment.supplier.invoice'
    #             rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
    #             if not rec.name and rec.payment_type != 'transfer':
    #                 raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
    #
    #         # Create the journal entry
    #         amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
    #         move = rec._create_payment_entry(amount)
    #
    #         # In case of a transfer, the first journal entry created debited the source liquidity account and credited
    #         # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
    #         if rec.payment_type == 'transfer':
    #             transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
    #             transfer_debit_aml = rec._create_transfer_entry(amount)
    #             (transfer_credit_aml + transfer_debit_aml).reconcile()
    #
    #         rec.write({'state': 'posted', 'move_name': move.name})
    #     return True
    #
    def action_validate_invoice_payment(self):
        """ Confirms a payment used to pay an invoice.
        It is called by the "confirm" button of the popup window
        triggered on invoice form by the "Register Payment" button.
        """
        if any(len(record.invoice_ids) != 1 for record in self):
            # For multiple invoices, there is account.register.payments wizard
            raise UserError(_("This method should only be called to process a single invoice's payment."))
        self.confirm_withholding_payment()
        return self.confirm()
    #
    # @api.multi
    def action_cancel(self):
        self.confirmed = False
        return super(AccountPaymentInherit, self).action_cancel()
    #     for rec in self:
    #         if rec.payment_class == 'deposit':
    #             rec.sale_order.write({
    #                 'deposit_invoice_fully_paid': False,
    #                 'deposit_invoice_fully_paid_date': None
    #             })

    #         if rec.withhold_payment_id:
    #             rec.withhold_payment_id.action_cancel()
    # #
    #         amount_paid = rec.sale_order.amount_paid - rec.sale_order.withheld_payment_amount
    #         if rec.sale_order.payment_term_id.rate_amount != 0:
    #             payment_count = int(amount_paid / rec.sale_order.payment_term_id.rate_amount)
    #         else:
    #             payment_count = 0
    #         rec.sale_order.write({
    #             'outstanding_balance': rec.sale_order.payment_term_id.financed_price - rec.sale_order.total_amount_paid - rec.sale_order.discount_given,
    #             'amount_pending': amount_paid - (payment_count * rec.sale_order.payment_term_id.rate_amount)
    #         })
    # end -------------------------------