import time
from datetime import datetime
from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class HrPayslipInheritTrimf(models.Model):
    _inherit = 'hr.payslip'

    # @api.multi
    def get_annual_trimf(self):
        brut_impo_annual = self.get_brut_annual()
        result = 0.0
        if brut_impo_annual < 600000:
            result = self.employee_id.trimf*900
        else:
            if brut_impo_annual < 999996:
                result = self.employee_id.trimf*3600
            else:
                if brut_impo_annual < 2000004:
                    result = self.employee_id.trimf*4800
                else:
                    if brut_impo_annual < 7000008:
                        result = self.employee_id.trimf*12000
                    else:
                        if brut_impo_annual < 12000000:
                            result = self.employee_id.trimf*18000
                        else:
                            result = self.employee_id.trimf*36000
        return result


    # @api.multi
    def get_trimf_of_current_month(self, brut_imposable):
        result = 0.0
        if brut_imposable < 50000:
            result = self.employee_id.trimf*75
        else:
            if brut_imposable < 83333:
                result = self.employee_id.trimf*300
            else:
                if brut_imposable < 166667:
                    result = self.employee_id.trimf*400
                else:
                    if brut_imposable < 583334:
                        result = self.employee_id.trimf*1000
                    else:
                        if brut_imposable < 1000000:
                            result = self.employee_id.trimf*1500
                        else:
                            result = self.employee_id.trimf*3000
        return result

    # @api.multi
    def get_cumul_trimf(self, brut_imposable_of_current_payslip):
        """ get the cumul genered by odoo """
        self.ensure_one()
        trimf_of_current_payslip = self.get_trimf_of_current_month(brut_imposable_of_current_payslip)
        for payslip in self:
            cumul_trimf = 0.0
            for line in self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id), ('year', '=', payslip.date_from.year)], limit=11):
                if line.date_from.year == payslip.date_from.year:
                    cumul_trimf += sum(payslip_line.total for payslip_line in line.line_ids if payslip_line.code == "C2050")
            cumul_trimf += trimf_of_current_payslip
            return cumul_trimf