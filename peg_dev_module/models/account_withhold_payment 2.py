from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class AccountWithholdPaymentRate(models.Model):
    _name = 'account.withhold.payment.rate'
    _description = 'Withheld Payments Rates'
    _rec_name = 'rate'

    _sql_constraints = [
        ('uniq_rate', 'unique(rate)', "Rate already exists. It must be unique!"),
    ]

    days_lower_limit = fields.Integer(
        string='Days Lower Limit', required=True, default=0
    )

    days_upper_limit = fields.Integer(
        string='Days Upper Limit', required=True
    )

    rate = fields.Float(
        string='Rate (%)',
        default=0,
        # unique=True
    )

    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('rate')
    def _compute_display_name(self):
        for record in self:
            record.display_name = str(record.rate) + '%'
