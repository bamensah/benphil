# -*- coding: utf-8 -*-
# by khk
import time
from datetime import datetime
from dateutil import relativedelta
from odoo import fields, models, api

class optesis_declaration_retenues(models.TransientModel):
    _name = 'optesis.declaration.retenues'
    _description = 'declarations des retenues a la source sur les salaires'

    date_from = fields.Date('Date de debut', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date de fin', required=True, default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])

    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
             'ids': active_ids,
             'model': 'hr.contribution.register',
             'form': self.read()[0]
        }
        return self.env.ref('optipay.declaration_retenues').report_action([], data=datas)
