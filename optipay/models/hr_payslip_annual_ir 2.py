import time
from datetime import datetime
from odoo import models, api

class HrPayslipInheritIr(models.Model):
    _inherit = 'hr.payslip'

    brut_of_current_payslip = 0.0

    # @api.multi
    def get_brut_annual(self):
        self.ensure_one()
        for payslip in self:
            cumul_brut = 0.0
            for line in self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id), ('year', '=', payslip.date_from.year)], limit=11):
                if line.date_from.year == payslip.date_from.year:
                    cumul_brut += sum(payslip_line.total for payslip_line in line.line_ids if payslip_line.code == "C1200")
            return cumul_brut+self.brut_of_current_payslip

    # @api.multi
    def get_base_fiscal_apres_abattement_annuel(self):
        self.ensure_one()
        abbatement = min(self.get_brut_annual()*0.3,900000)
        return self.get_brut_annual() - abbatement

    # @api.multi
    def get_second_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if base_fisc < 1500000 and base_fisc > 630000:
            return round((base_fisc - 630000)*0.2)
        else:
            if base_fisc > 1500000:
                return 174000
        return 0

    # @api.multi
    def get_third_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if base_fisc < 3999996 and base_fisc > 1500000:
            return round((base_fisc - 1500000)*0.3)
        else:
            if base_fisc > 3999996:
                return 750000
        return 0

    # @api.multi
    def get_fourth_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if base_fisc < 8000004 and base_fisc > 3999996:
            return round((base_fisc - 3999996)*0.35)
        else:
            if base_fisc > 8000004:
                return 1400004
        return 0

    # @api.multi
    def get_fifth_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if base_fisc < 13500000 and base_fisc > 8000004:
            return round((base_fisc - 8000004)*0.37)
        else:
            if base_fisc > 13500000:
                return 2034996
        return 0


    # @api.multi
    def get_sixth_tranch(self):
        self.ensure_one()
        base_fisc = self.get_base_fiscal_apres_abattement_annuel()
        if base_fisc > 13500000 :
            return round((base_fisc - 13500000)*0.4)
        return 0

    # @api.multi
    def get_cumul_tranche(self):
        self.ensure_one()
        cumul = 0.0
        cumul += self.get_second_tranch()
        cumul += self.get_third_tranch()
        cumul += self.get_fourth_tranch()
        cumul += self.get_fifth_tranch()
        cumul += self.get_sixth_tranch()
        return round(cumul)

    # @api.multi
    def get_one_part(self):
        self.ensure_one()
        if self.employee_id.ir == 1.5:
            if self.get_cumul_tranche() * 0.1 < 100000:
                return 100000
            elif self.get_cumul_tranche() * 0.1 > 300000:
                return 300000
            else:
                return round(self.get_cumul_tranche() * 0.1)
        return 0

    # @api.multi
    def get_two_part(self):
        self.ensure_one()
        val = 0.0
        if self.employee_id.ir == 2:
            if self.get_cumul_tranche() * 0.15 < 200000:
                val += 200000
            elif self.get_cumul_tranche() * 0.15 > 650000:
                val += 650000
            else:
                val += self.get_cumul_tranche() * 0.15

        if self.employee_id.ir == 2.5:
            if self.get_cumul_tranche() * 0.2 < 300000:
                val += 300000
            elif self.get_cumul_tranche() * 0.2 > 1100000:
                val += 1100000
            else:
                val += self.get_cumul_tranche() * 0.2
        return round(val)

    # @api.multi
    def get_third_part(self):
        self.ensure_one()
        val = 0.0
        if self.employee_id.ir == 3:
            if self.get_cumul_tranche() * 0.25 < 400000:
                val += 400000
            elif self.get_cumul_tranche() * 0.25 > 1650000:
                val += 1650000
            else:
                val += self.get_cumul_tranche() * 0.25

        if self.employee_id.ir == 3.5:
            if self.get_cumul_tranche() * 0.3 < 500000:
                val += 500000
            elif self.get_cumul_tranche() * 0.3 > 2030000:
                val += 2030000
            else:
                val += self.get_cumul_tranche() * 0.3
        return round(val)

    # @api.multi
    def get_fourth_part(self):
        self.ensure_one()
        val = 0.0
        if self.employee_id.ir == 4:
            if self.get_cumul_tranche() * 0.35 < 600000:
                val += 600000
            elif self.get_cumul_tranche() * 0.35 > 2490000:
                val += 2490000
            else:
                val += self.get_cumul_tranche() * 0.35

        if self.employee_id.ir == 4.5:
            if self.get_cumul_tranche() * 0.4 < 700000:
                val += 700000
            elif self.get_cumul_tranche() * 0.4 > 2755000:
                val += 2755000
            else:
                val += self.get_cumul_tranche() * 0.4
        return round(val)

    # @api.multi
    def get_fifth_part(self):
        self.ensure_one()
        val = 0.0
        if self.employee_id.ir == 5:
            if self.get_cumul_tranche() * 0.45 < 800000:
                val += 800000
            elif self.get_cumul_tranche() * 0.45 > 3180000:
                val += 3180000
            else:
                val += self.get_cumul_tranche() * 0.45
        return round(val)

    # @api.multi
    def get_ir_annuel(self, brut_imposable):
        self.brut_of_current_payslip = brut_imposable
        self.ensure_one()
        deduction = 0.0
        deduction += self.get_one_part()
        deduction += self.get_two_part()
        deduction += self.get_third_part()
        deduction += self.get_fourth_part()
        deduction += self.get_fifth_part()
        return round(self.get_cumul_tranche() - deduction)

    # @api.multi
    def get_cumul_ir(self, ir_of_current_payslip):
        self.ensure_one()
        for payslip in self:
            cumul_ir = 0.0
            for line in self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id), ('year', '=', payslip.date_from.year)], limit=11):
                if line.date_from.year == payslip.date_from.year:
                    cumul_ir += sum(payslip_line.total for payslip_line in line.line_ids if payslip_line.code == "C2170")
            cumul_ir += ir_of_current_payslip
            return cumul_ir