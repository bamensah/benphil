# -*- coding:utf-8 -*-
# by khk
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SecuriteSociale(models.AbstractModel):
    _name = 'report.optipay.report_css_view'
    _description = 'Rapport securite sociale'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        register_ids = self.env.context.get('active_ids', [])
        contrib_registers = self.env['hr.contribution.register'].browse(register_ids)
        date_from = data['form'].get('date_from', fields.Date.today())
        date_to = data['form'].get('date_to', str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])

        dico = {}
        lines_data = []
        total_brut = 0.0
        total_base = 0.0
        total_prestfam = 0.0
        total_acw = 0.0
        total_cotisation = 0.0

        self.env.cr.execute("SELECT DISTINCT hr_payslip_line.id,\
                            hr_employee.num_chezemployeur,\
                            hr_employee.name from\
                            hr_payslip_line as hr_payslip_line,\
                            hr_employee as hr_employee,\
                            hr_payslip as hr_payslip where\
                            hr_employee.id = hr_payslip_line.employee_id AND\
                            hr_employee.id = hr_payslip.employee_id AND\
                            hr_payslip_line.payslip_date_from >=  %s AND\
                            hr_payslip_line.payslip_date_to <= %s AND \
                            hr_employee.company_id = %s AND \
                            hr_payslip_line.code IN ('C1200','C1000','C2010','C2020')\
                            ORDER BY hr_employee.num_chezemployeur  ASC, hr_employee.name ASC",
                            (date_from, date_to, self.env.user.company_id.id))
        line_ids = [x[0] for x in self.env.cr.fetchall()]
        for line in self.env['hr.payslip.line'].browse(line_ids):
            if line.employee_id.id in dico:
                if line.code == 'C1200':  # brut
                    dico[line.employee_id.id]['Brut'] += line.total
                    total_brut += line.total
                elif line.code == 'C2010':  # prestfam
                    dico[line.employee_id.id]['Prestfam'] += line.total
                    dico[line.employee_id.id]['Base'] += line.amount
                    total_base += line.amount
                    total_prestfam += line.total
                    total_cotisation += line.total
                elif line.code == 'C2020':  # acw
                    dico[line.employee_id.id]['Acw'] += line.total
                    total_acw += line.total
                    total_cotisation += line.total
            else:
                dico[line.employee_id.id] = {}
                employee_data = self.env['hr.employee'].browse(line.employee_id.id)

                dico[line.employee_id.id]['Brut'] = 0
                dico[line.employee_id.id]['Prestfam'] = 0
                dico[line.employee_id.id]['Acw'] = 0
                dico[line.employee_id.id]['Base'] = 0

                if line.code == 'C1200':  # brut
                    dico[line.employee_id.id]['Brut'] = line.total
                    total_brut += line.total
                elif line.code == 'C2010':  # prestfam
                    dico[line.employee_id.id]['Prestfam'] = line.total
                    dico[line.employee_id.id]['Base'] = line.amount
                    total_base += line.amount
                    total_prestfam += line.total
                    total_cotisation += line.total
                elif line.code == 'C2020':  # acw
                    dico[line.employee_id.id]['Acw'] = line.total
                    total_acw += line.total
                    total_cotisation += line.total

                dico[line.employee_id.id]['Name'] = employee_data.name
                dico[line.employee_id.id]['Matricule'] = employee_data.num_chezemployeur

        index = 0
        for key, values in dico.items():
            index += 1
            lines_data.append({
                'index': index,
                'matricule': dico[key]['Matricule'],
                'name': dico[key]['Name'],
                'brut': int(round(dico[key]['Brut'])),
                'base': int(round(dico[key]['Base'])),
                'prestfam': int(round(dico[key]['Prestfam'])),
                'acw': int(round(dico[key]['Acw'])),
                'cotisation': int(round(dico[key]['Prestfam'] + dico[key]['Acw'])),
            })

        lines_total = [{
            'total_brut': int(round(total_brut)),
            'total_base': int(round(total_base)),
            'total_prestfam': int(round(total_prestfam)),
            'total_acw': int(round(total_acw)),
            'total_cotisation': int(round(total_cotisation)),
        }]

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'lines_data': lines_data,
            'lines_total': lines_total
        }