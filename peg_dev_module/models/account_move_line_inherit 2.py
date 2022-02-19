from odoo import models, fields, api


class account_move_line_inherited(models.Model):
    _inherit = 'account.move.line'

    payment_type_class = fields.Selection(string='Type of Payment', selection=[
        ('balance', 'Balance'), ('deposit', 'Deposit'), ('daily_repayment', 'Daily Repayment'), ('weekly_repayment', 'Weekly Repayment'), ('monthly_repayment', 'Monthly Repayment'), ('seasonal_repayment', 'Seasonal Repayment'), ('cash', 'Cash'), ('fixed', 'Fixed'), ('other', 'Other')])
