# -*- coding: utf-8 -*-
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class hr_payslip(models.Model):
    _inherit = "hr.payslip"

    # @api.multi
    def compute_total_paid_loan(self):
        total = 0.00
        for line in self.loan_ids:
            if line.paid == True:
                total += line.paid_amount
        self.total_loan_amount_paid = total

    loan_ids = fields.One2many('hr.loan.line', 'payroll_id', string="Prêts", readonly=True)
    total_loan_amount_paid = fields.Float(string="Total Prêt", compute='compute_total_paid_loan', readonly=True)

    @api.depends('loan_ids')
    def compute_total_paid_loan(self):
        for slip in self:
            self.total_loan_amount_paid = sum(loan.paid_amount for loan in slip.loan_ids)

    @api.model
    def action_payslip_done(self):
        for line in self.loan_ids:
            if line.paid is not True:
                line.action_paid_amount()
        super(hr_payslip, self).action_payslip_done()
