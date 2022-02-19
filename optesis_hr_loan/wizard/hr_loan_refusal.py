# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanRefusalMotivation(models.TransientModel):
    _name = "loan.refusal.motivation"

    # @api.one
    def _compute_loan_request(self):
        selected_object_ids = self._context.get('active_ids')
        if selected_object_ids:
            objects = self.env['hr.loan'].browse(selected_object_ids)
            self.loan_request = objects[0]


    loan_request = fields.Many2one('hr.loan', string='Loan', compute='_compute_loan_request')
    motivation = fields.Text(string='Motivation', required=True)


    # @api.multi
    def refuse(self):
        self.env['hr.loan.approver'].create({
             'loan_id': self.loan_request.id, 'comment': self.motivation,
             'user_id': self.env.uid,'date_approved': fields.Datetime.now(),'state': 'cancel'})
        self.loan_request.action_refuse()
        return

