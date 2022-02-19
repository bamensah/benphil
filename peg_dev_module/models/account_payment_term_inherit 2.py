# -*- coding: utf-8 -*-
from odoo import models


class AccountPaymentTermInherit(models.Model):
    _inherit = 'account.payment.term'
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  'You can not have two payment term with the same name !')
    ]