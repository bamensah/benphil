# -*- coding: utf-8 -*-
# by khk
import time
from datetime import datetime
from odoo import fields, models, api

class optesis_dads(models.TransientModel):
    _name = 'optesis.dads.report'
    _description = 'DADS modele wizard'

    year = fields.Selection([
        ('2018', '2018'),
        ('2019', '2019'),
        ('2020', '2020'),
        ('2021', '2021'),
        ('2022', '2022')],
        'Année', required=True, #default=datetime.now().year
        )
    page = fields.Selection([('1','Etat recapitulatif des versements'),
         ('2', 'Etat récapitulatif des traitements, salaires et Rétribution')],
          default='1', string="Etat")

    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
             'ids': active_ids,
             'model': 'hr.contribution.register',
             'form': self.read()[0]
        }
        if self.page == '1':
            return self.env.ref('optipay.dads_report_1').report_action([], data=datas)
        else:
            return self.env.ref('optipay.dads_report_2').report_action([], data=datas)

