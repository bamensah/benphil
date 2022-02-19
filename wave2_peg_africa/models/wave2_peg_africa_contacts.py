# -*- coding: utf-8 -*-
from collections import Counter
import ast
import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class PartnerInformationDisplayed(models.Model):
    _inherit = 'res.partner'

    # migrate later v14
    client_status = fields.Many2one('sale.contract.status', string='Client Status', readonly=True)
    phone=fields.Char(string='Primary mobile number')
    mobile=fields.Char(string='Secondary mobile number')
    is_base_user = fields.Boolean(string="Base user", compute='get_user')
    has_paid_sale = fields.Boolean(compute='_has_paid_sale')

    #Check if user is a simple user (base user) and is not in group Master Data
    @api.depends('is_base_user')
    def get_user(self):
        res_user = self.env.user
        if res_user.has_group('base.group_user') and not res_user.has_group('__export__.res_groups_98_1ebb9fae'):
            self.is_base_user = True
        else:
            self.is_base_user = False

    @api.depends('is_base_user')
    def _has_paid_sale(self):
        for s in self:
            s.has_paid_sale = False
            if s.id:
                sales = self.env['sale.order'].search([('partner_id.id','=',s.id)])
                if any(sale.deposit_invoice_fully_paid for sale in sales):
                    self.has_paid_sale = True
                else:
                    self.has_paid_sale = False

    # migrate v14 later --------------------
    #Add Tokens sent in Contact page
    # @api.multi
    def action_get_tokens_sent_tree_views(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "credit.token",
            "views": [[False, "tree"]],
            "name": "List of tokens",
            "search_view_id" : self.env.ref('wave2_peg_africa.model_credit_token').id,
        }
    #
    #Add SMS sent in Contact page
    # @api.multi
    def action_get_sms_sent_tree_views(self):
        if self.phone:
            self._get_user_sms_sent()
        return {
            "type": "ir.actions.act_window",
            "res_model": "credit.sms",
            "views": [[False, "tree"]],
            "name": "List of SMS",
            "search_view_id" : self.env.ref('wave2_peg_africa.model_credit_sms').id,
        }

    def get_country(self):
        return self.env.user.company_id.country_id.code.lower()
    #
    #
    # def _get_user_sms_sent(self):
    #     #refresh the token by the daily cron: Make sure the cron is configured
    #     #self.env['res.config.settings'].refresh_token()
    #     parameters = self.env['ir.config_parameter'].sudo()
    #     access_token = parameters.get_param('api_gateway_access_token')
    #     API_GATEWAY_URL = parameters.get_param('api_gateway_url')
    #     country = self.get_country()
    #     phone = self.phone
    #
    #     API_GATEWAY_SMS_SENT_ENDPOINT = API_GATEWAY_URL + "/api/sms/" + country + "/list/" + phone
    #     headers = {
    #             "content-type": "application/json",
    #             'Authorization': "Bearer " + access_token
    #     }
    #
    #     try:
    #         req = requests.get(API_GATEWAY_SMS_SENT_ENDPOINT, headers=headers)
    #         req.raise_for_status()
    #         content = req.json()
    #
    #         for sms_line in content:
    #             #Check if the message is not yet saved in the database
    #             if not self.env['credit.sms'].search([ \
    #                 ('msg_id', '=', sms_line['msg_id']) \
    #             ]):
    #                 self.env['credit.sms'].create({
    #                     'msg_id':sms_line['msg_id'],
    #                     'sent': sms_line['sent_datetime'],
    #                     'partner_id': self.id,
    #                     'phone_number': sms_line['to_number'],
    #                     'content': sms_line['body'],
    #                     'status': sms_line["status"]
    #                 })
    #
    #     except IOError:
    #         # error_msg = _("An error occurred while retrieving SMS.")
    #         # raise UserError(error_msg)
    #         pass
    #
    #Add Credit tab in Contact page
    # @api.multis
    def action_get_credit_tree_views(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "tree"]],
            "views": [[self.env.ref('wave2_peg_africa.view_credit_loan_tree').id, "tree"]],
            "name": "List of credits",
            "search_view_id" : self.env.ref('sale.model_sale_order').id,
            "domain": [['state','!=', 'cancel']]
        }
    # end --------------------
