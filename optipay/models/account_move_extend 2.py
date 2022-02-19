#-*- coding:utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    batch_id = fields.Many2one('hr.payslip.run', string="Payroll Batch")
