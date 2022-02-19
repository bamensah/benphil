from odoo import models, fields, api, _
from datetime import date,datetime

class PaymentBackdateWizard(models.TransientModel):

    _name = 'sh.payment.backdate.wizard'

    account_payment_ids = fields.Many2many('account.payment')
    date = fields.Datetime(string = "Date",required=True,default = fields.Date.today)
    company_id = fields.Many2one('res.company',default=lambda self:self.env.company)
    remarks = fields.Text(string = "Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_payment")
    is_remarks_mandatory = fields.Boolean(related="company_id.remark_mandatory_payment")
    is_boolean = fields.Boolean()

    @api.onchange('date')
    def onchange_date(self):
        if str(self.date) < str(date.today()):
           self.is_boolean = True
        else:
            self.is_boolean = False
    
    def open_payment_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')
        
        return{
                'name': 'Assign Backdate',
                'res_model': 'sh.payment.backdate.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('sh_all_in_one_backdate.payment_backdate_wizard_view_form').id,
                'context': {
                    'default_account_payment_ids': [(6, 0, active_ids)],
                },
                'target': 'new',
                'type': 'ir.actions.act_window'
            }
    
    def assign_backdate(self):
        
        if self.company_id.enable_backdate_for_payment:

            for payment in self.account_payment_ids:

                if payment.state == 'posted':

                    payment.action_draft()
                    payment.name = False

                    payment.write({
                        'date' : self.date,
                        'remarks' : self.remarks
                    })

                    payment.action_post()

                    payment.move_id.write({
                        'remarks' : self.remarks
                    })

                elif payment.state == 'cancel':

                    payment.action_draft()
                    payment.name = False

                    payment.write({
                        'date' : self.date,
                        'remarks' : self.remarks
                    })

                    payment.action_cancel()
                
                else:

                    payment.name = False

                    payment.write({
                        'date' : self.date,
                        'remarks' : self.remarks
                    })