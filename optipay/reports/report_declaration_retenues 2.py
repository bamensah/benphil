# -*- coding:utf-8 -*-
# by khk
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from odoo import api, fields, models, _

class DeclarationRetenues(models.AbstractModel):
    _name = 'report.optipay.report_declaration_retenues_view'
    _description = 'Rapport declaration des retenues'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        server_dt = DEFAULT_SERVER_DATE_FORMAT
        number_month_to_word = {
            "1": "janvier",
            "2": "février",
            "3": "mars",
            "4": "avril",
            "5": "mai",
            "6": "juin",
            "7": "julliet",
            "8": "aout",
            "9": "septembre",
            "10": "octobre",
            "11": "novembre",
            "12": "decembre"
        }
        now = datetime.now()
        register_ids = self.env.context.get('active_ids', [])
        contrib_registers = self.env['hr.contribution.register'].browse(register_ids)
        date_from = data['form'].get('date_from', fields.Date.today())
        date_to = data['form'].get('date_to', str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
        month_from = datetime.strptime(str(date_from), server_dt).month
        month_to = datetime.strptime(str(date_to), server_dt).month
        year_from = datetime.strptime(str(date_from), server_dt).year
        year_to = datetime.strptime(str(date_to), server_dt).year

        periode = ""
        if month_from == month_to and year_from == year_to:
            periode = number_month_to_word.get(str(month_from)) + " " + str(year_from)
        else:
            periode = number_month_to_word.get(str(month_from)) + " " + str(
                year_from) + " au " + number_month_to_word.get(str(month_to)) + " " + str(year_to)

        self.total_brut_male = 0.0
        self.total_ir_male = 0.0
        self.total_trimf_male = 0.0
        self.total_cfce_male = 0.0

        self.total_brut_female = 0.0
        self.total_ir_female = 0.0
        self.total_trimf_female = 0.0
        self.total_cfce_female = 0.0

        dict = {}
        self.env.cr.execute("SELECT hr_payslip_line.id,\
                hr_payslip_line.total,hr_payslip_line.employee_id from \
                hr_salary_rule_category as hr_salary_rule_category INNER JOIN hr_payslip_line as \
                hr_payslip_line ON hr_salary_rule_category.id = hr_payslip_line.category_id INNER JOIN \
                hr_employee as hr_employee ON hr_payslip_line.employee_id = hr_employee.id INNER JOIN \
                hr_payslip as hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id AND hr_employee.id \
                = hr_payslip.employee_id where hr_payslip.date_from >= %s  AND hr_payslip.date_to <= \
                %s AND hr_employee.company_id = %s AND hr_payslip_line.code IN ('C1200','C2170','C2050','C2000') ORDER BY \
                hr_employee.name ASC, hr_payslip_line.code ASC",
                            (date_from, date_to, self.env.user.company_id.id))
        line_ids = [x[0] for x in self.env.cr.fetchall()]
        self.nb_male = 0
        self.nb_female = 0
        for line in self.env['hr.payslip.line'].browse(line_ids):
            if line.code == 'C2170':  # ir_fin
                if line.employee_id.gender == 'male':
                    if line.employee_id.id not in dict:
                        dict[line.employee_id.id] = {}
                        self.nb_male += 1
                    self.total_ir_male += line.total
                if line.employee_id.gender == 'female':
                    if line.employee_id.id not in dict:
                        dict[line.employee_id.id] = {}
                        self.nb_female += 1
                    self.total_ir_female += line.total
            if line.code == 'C2050':  # trimf
                if line.employee_id.gender == 'male':
                    self.total_trimf_male += line.total
                if line.employee_id.gender == 'female':
                    self.total_trimf_female += line.total
            if line.code == 'C2000':  # cfce
                if line.employee_id.gender == 'male':
                    self.total_cfce_male += line.total
                if line.employee_id.gender == 'female':
                    self.total_cfce_female += line.total
            if line.code == 'C1200':  # brut imposable
                if line.employee_id.gender == 'male':
                    self.total_brut_male += line.total
                if line.employee_id.gender == 'female':
                    self.total_brut_female += line.total

        lines_total_male = [{
            'nb_male_count': self.nb_male,
            'total_brut_male': int(round(self.total_brut_male)),
            'total_ir_male': int(round(self.total_ir_male)),
            'total_trimf_male': int(round(self.total_trimf_male)),
            'total_cfce_male': int(round(self.total_cfce_male)),
            'total_total_male': int(round(self.total_ir_male +
                                          self.total_trimf_male + self.total_cfce_male)),
        }]

        lines_total_female = [{
            'nb_female_count': self.nb_female,
            'total_brut_female': int(round(self.total_brut_female)),
            'total_ir_female': int(round(self.total_ir_female)),
            'total_trimf_female': int(round(self.total_trimf_female)),
            'total_cfce_female': int(round(self.total_cfce_female)),
            'total_total_female': int(round(self.total_ir_female +
                                            self.total_trimf_female + self.total_cfce_female)),
        }]

        lines_total = [{
            'total_brut': int(round(self.total_brut_male + self.total_brut_female)),
            'total_ir': int(round(self.total_ir_male + self.total_ir_female)),
            'total_trimf': int(round(self.total_trimf_male + self.total_trimf_female)),
            'total_cfce': int(round(self.total_cfce_male + self.total_cfce_female)),
            'total_total': int(round(self.total_ir_male + self.total_trimf_male + self.total_cfce_male +
                                     self.total_ir_female + self.total_trimf_female + self.total_cfce_female)),
        }]

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'lines_male': lines_total_male,
            'lines_female': lines_total_female,
            'lines_total': lines_total,
            'current_date': now.strftime("%d/%m/%Y"),
            'periode': periode
        }
