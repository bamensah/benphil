# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models


class WkPayslipLinesContributionRegister(models.TransientModel):
    _name = 'wk.payslip.lines.contribution.register'
    _description = 'Payslip Lines by Contribution Registers'

    date_from = fields.Date(string='Date From', required=True,
        default=datetime.now().strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To', required=True,
        default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])

    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'wk.hr.contribution.register',
            'form': self.read()[0]
        }
        return self.env.ref(
            'wk_hr_payroll.action_contribution_register').report_action([], data=datas)
