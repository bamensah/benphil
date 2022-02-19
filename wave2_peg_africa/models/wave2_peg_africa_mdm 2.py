# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ContractStatus(models.Model):
    _name = 'sale.contract.status'
    _order = 'order_of_account'

    name = fields.Char(string='Contract Status', required=True)
    order_of_account = fields.Integer(string='Order of Account', required=True)

    _sql_constraints = [
        ('sale_contract_status_order_account_uniq', 'UNIQUE (order_of_account)',  'You can not have two contract statuses with the same order of account number!'),
        ('sale_contract_status_name_unique', 'UNIQUE (name)', "This Contract Status already exists!")
    ]

class StockAction(models.Model):
    _name = 'sale.stock.action'
    _order = 'order_of_account'

    name = fields.Char(string='Stock Action', required=True)
    order_of_account = fields.Integer(string='Order of Account', required=True)

    _sql_constraints = [
        ('sale_stock_action_order_account_uniq', 'UNIQUE (order_of_account)',  'You can not have two stock actions with the same order of account number!'),
        ('sale_stock_action_name_uniq', 'UNIQUE (name)', "This Stock Action already exists!")
    ]

class SuspensionReason(models.Model):
    _name = 'suspension.reason'

    name = fields.Char(string='Reason', required=True)
    sub_reasons = fields.One2many('sub.suspension.reason', 'reason_id', string='Sub Reasons')

    _sql_constraints = [
        ('suspension_reason_name_uniq', 'UNIQUE (name)', "This Suspension Reason already exists!")
    ]

class SubSuspensionReason(models.Model):
    _name = 'sub.suspension.reason'

    name = fields.Char(string='Sub Reason', required=True)
    reason_id = fields.Many2one('suspension.reason', string='Suspension Reason')

class DepositStatus(models.Model):
    _name = 'deposit.status'

    name = fields.Char(string='Status', required=True)

class DeviceStatus(models.Model):
    _name = 'device.status'

    name = fields.Char(string='Status', required=True)