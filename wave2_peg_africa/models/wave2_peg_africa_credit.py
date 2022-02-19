# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError
from datetime import date
import uuid

class CreditToken(models.Model):
    _name = 'credit.token'
    _description = 'PaygOps Token'

    def _default_token_id(self):
        return uuid.uuid4().hex

    token_id = fields.Char(string='Token ID',required=True)
    amount = fields.Float(string='Payment amount',required=True)
    code = fields.Char(string='Token code')
    duration = fields.Float(string='Duration')
    credit_end_date = fields.Datetime(string='Credit End Date')
    token_type = fields.Char(string="Type")
    generated_date = fields.Datetime(string='PaygOps register date',required=True)
    device_serial = fields.Char(string= 'Device',required=True)
    transaction_id = fields.Char(string='Transaction ID number')
    inventory_id = fields.Many2one('stock.production.lot', string='Inventory ID')
    payment_id = fields.Many2one('account.payment', string='Payment ID')
    partner_id = fields.Many2one('res.partner', string='Contact ID')
    send_id = fields.Boolean(string='Send')
    salesperson = fields.Many2one('res.users', string='Salesperson')
    loan_id = fields.Many2one('sale.order', string='Loan ID')
    phone_number = fields.Char(string='Sent to (number used for payment)')
    phone_number_partner = fields.Char(string='Sent to (primary mobile number)')
    days_of_light = fields.Integer('Days Of Light', compute='_compute_days_of_light')
    token_index = fields.Integer(string='Token Index',compute="_compute_token_index",store=True)

    def _compute_days_of_light(self):
        for record in self:
            record.days_of_light = ((record.credit_end_date - record.generated_date).days + 1) if record.credit_end_date else 1

    @api.depends('loan_id')
    def _compute_token_index(self):
        tokens_to_compare=[]
        for record in self:
            tokens_of_loan = self.env['credit.token'].search([('loan_id', '=', record.loan_id.id)],order='create_date asc')
            if (len(tokens_of_loan)>0):
                for token in tokens_of_loan:
                    tokens_to_compare.append(token.id)
                record.token_index = tokens_to_compare.index(record.id) + 1
                tokens_to_compare.clear()


class CreditSms(models.Model):
    _name = 'credit.sms'
    _description = 'SMS'

    MESSAGE_TYPE=[
    ('lead_insufficient_balance','Lead insufficient balance'),
    ('lead_deposit_success','Lead pay deposit success'),
    ('welcome_message','Welcome message (Loan)'),
]

    msg_id = fields.Char(required=True)
    sent = fields.Datetime(string='Sent',required=True)
    partner_id = fields.Many2one('res.partner', string='Contact ID')
    #loan_id = fields.Many2one('sale.order', string='Loan ID')
    phone_number = fields.Char(string='Sent to')
    content = fields.Text(string='Content',required=True)
    status = fields.Char(string="SMS Status")