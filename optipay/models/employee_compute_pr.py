from dateutil import relativedelta
from odoo import models, fields, api


class ProvisionRetraiteRuleInput(models.Model):
    _inherit = 'hr.payslip'

    # @api.multi
    def compute_provision_retraite(self, brut_of_current_payslip):
        """salaire_brut_val is the value of current payslip
        i use it like argument because i can not get the value of payslip line"""
        for payslip in self:
            # get last 12 payslip of employee
            payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', payslip.employee_id.id)], order='id desc',
                                                        limit=12)
            if len(payslip_ids) >= 11:
                cumul_brut = 0
                for line in payslip_ids:
                    cumul_brut += sum(line.total for line in line.line_ids if
                                      line.code == 'C1148')
#                    cumul_brut += sum(line.total for line in line.details_by_salary_rule_category if
#                                      line.code == 'C1148')  # get salary brut of previous payslip

                # after the cumulates of last salary brut i add the value of current payslip
                cumul_brut += brut_of_current_payslip

                moy_brut = cumul_brut / len(payslip_ids)
                diff = relativedelta.relativedelta(payslip.contract_id.dateAnciennete, payslip.date_to)
                if diff.years <= 5:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, -diff.years, -diff.months,
                                                                   -diff.days)  # moy_brut*(dur.days/360)*0.25

                elif 5 < diff.years <= 10:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_cinq(moy_brut, -diff.years - 5, -diff.months,
                                                                    -diff.days)  # moy_brut*(dur.days/360)*0.3

                else:
                    provision_retraite = self.compute_pr_moin_cinq(moy_brut, 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_cinq(moy_brut, -diff.years - 5, 0, 0)
                    provision_retraite += self.compute_pr_plus_dix(moy_brut, -diff.years - 10, -diff.months, -diff.days)

                return round(provision_retraite)
            return 0.0

    def compute_pr_moin_cinq(self, moyb, years, months, days):
        amount_for_year = (moyb * 0.25) * float(years)
        amount_for_month = moyb * 0.25 * (float(months) / 12)
        amount_for_days = moyb * 0.25 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    def compute_pr_plus_cinq(self, moyb, years, months, days):
        amount_for_year = (moyb * 0.3) * float(years)
        amount_for_month = moyb * 0.3 * (float(months) / 12)
        amount_for_days = moyb * 0.3 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    def compute_pr_plus_dix(self, moyb, years, months, days):
        amount_for_year = (moyb * 0.4) * float(years)
        amount_for_month = moyb * 0.4 * (float(months) / 12)
        amount_for_days = moyb * 0.4 * (float(days) / 365)
        return round(amount_for_year + amount_for_month + amount_for_days)

    # @api.multi
    def compute_retirement_balance(self, brut_of_current_payslip):
        for payslip in self:
            if payslip.contract_id.motif:
                return self.compute_provision_retraite(brut_of_current_payslip)


    # @api.multi
    def loan_balance(self):
        for payslip in self:
            amount = 0
            loan_lines = self.env['hr.loan.line'].search(
                [('employee_id', '=', payslip.employee_id.id), ('paid', '=', False)])
            for loan_line in loan_lines:
                # on ne prend pas en compte les loans du mois courant
                if not payslip.date_from <= loan_line.paid_date <= payslip.date_to:
                    amount += loan_line.paid_amount
            return round(amount)
