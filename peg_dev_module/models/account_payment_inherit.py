from odoo import models, fields, api


class account_payment_inhert(models.Model):
    _inherit = 'account.payment'
    
    _sql_constraints = [
        ('uniq_transaction_id', 'unique(transaction_id)', "Transaction ID already exists. It must be unique!"),
    ]

    payment_class = fields.Selection(string='Class of Payment', selection=[
        ('deposit', 'Deposit'), ('daily_repayment', 'Daily Repayment'), ('weekly_repayment', 'Weekly Repayment'), ('monthly_repayment', 'Monthly Repayment'), ('seasonal_payment', 'Seasonal Payment'), ('cash', 'Cash')])
    
    transaction_id = fields.Char(string="Transaction ID",
                                 # unique=True
                                 )
    
    original_amount = fields.Float(string='Original Amount')
    
    withhold_amount = fields.Float(string='Withheld Amount')
    
    withhold_payment_id = fields.Many2one(string='Withheld Payment', comodel_name='account.payment')
    
    parent_payment_id = fields.Many2one(string='Original Payment', comodel_name='account.payment')
    
    withhold_rate = fields.Float(string='Withheld Rate', default=0)
    
    withhold_check = fields.Boolean(string='Withheld', default=False)
    
    draft_withhold_rate = fields.Float(string="Withhold Rate", compute='_compute_draft_wth_rate')
    
    @api.depends('partner_id')
    def _compute_draft_wth_rate(self):
        if self.state == 'draft' and self.partner_id:
            rate, arr = self.get_withhold_rate()
            self.draft_withhold_rate = rate
        else:
            self.draft_withhold_rate = 0