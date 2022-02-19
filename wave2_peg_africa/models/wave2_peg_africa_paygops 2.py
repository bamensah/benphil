# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError
import requests
import json

class Paygops(models.Model):
    _name = 'peg.africa.paygops'
    _description = 'PaygOps'

    lead_id = fields.Integer(string='Lead ID')
    register_date = fields.Datetime(string='PaygOps register date')
    device_id = fields.Char(string= "Device")
    client_id = fields.Integer(string='Client ID')
    partner_id = fields.Many2one('res.partner', string='Partner')
    loan_id = fields.Many2one('sale.order', string='Loan')
    registration_answer_code = fields.Char(string= "Registration answer code")
    old_device_id = fields.Char(string= "Old Device")

    # migrate later v14 -----------
    # @api.multi
    def write(self, vals):
        res = super(Paygops, self).write(vals)
        return res
    #  end ---------


class ResPartnerInherit(models.Model):
    """Add fields to res.partner"""
    _inherit = 'res.partner'

    token_ids = fields.One2many('credit.token', 'partner_id', 'Tokens')