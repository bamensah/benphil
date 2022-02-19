from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)


class payment_api_partner(models.Model):
    _name = 'payment_api_partner'
    _description = 'Payment API Partners'
    
    name = fields.Char(string='Partner', required=True)
    username = fields.Char(string='Username', unique=True, index=True)
    account_journal_id = fields.Many2one(
        string='Account Journal',
        comodel_name='account.journal'
    )
    
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.user.company_id
    )
    
    