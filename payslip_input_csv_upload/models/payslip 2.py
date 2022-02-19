# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipInput(models.Model):
    _inherit = 'wk.hr.payslip.input'

    def name_get(self):
        res = []
        for record in self:
            name = "%s (%s)" %(record.contract_id.employee_id.name,record.name)
            res.append((record.id, name))
        return res
