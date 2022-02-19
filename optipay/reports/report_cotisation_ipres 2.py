# -*- coding:utf-8 -*-
# by khk
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, _


class CotisationIpresReport(models.AbstractModel):
    _name = 'report.optipay.report_ipres_view'
    _description = 'Rapport cotisation ipres'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        register_ids = self.env.context.get('active_ids', [])
        contrib_registers = self.env['hr.contribution.register'].browse(register_ids)
        date_from = data['form'].get('date_from', fields.Date.today())
        date_to = data['form'].get('date_to', str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])

        self.total_brut = 0.0
        self.total_ipres_rc = 0.0
        self.total_ipres_rg = 0.0
        self.total_ipres_rc_pat = 0.0
        self.total_ipres_rg_pat = 0.0
        self.total_base_rc = 0.0
        self.total_base_rg = 0.0

        dico = {}
        lines_data = []
        self.env.cr.execute("SELECT DISTINCT hr_payslip_line.id, " \
                            "hr_employee.num_chezemployeur," \
                            "hr_employee.name from " \
                            "hr_payslip_line as hr_payslip_line," \
                            "hr_employee as hr_employee," \
                            "hr_payslip as hr_payslip where " \
                            "hr_employee.id = hr_payslip_line.employee_id AND " \
                            "hr_employee.id = hr_payslip.employee_id AND " \
                            "hr_payslip_line.payslip_date_from >=  %s AND " \
                            "hr_payslip_line.payslip_date_to <= %s AND " \
                            "hr_employee.company_id = %s AND " \
                            "hr_payslip_line.code IN ('C1200','C1000','C2040','C2030','C2041','C2031') " \
                            "ORDER BY hr_employee.num_chezemployeur  ASC, hr_employee.name ASC",
                            (date_from, date_to, self.env.user.company_id.id))
        line_ids = [x[0] for x in self.env.cr.fetchall()]
        for line in self.env['hr.payslip.line'].browse(line_ids):

            if line.employee_id.id in dico:
                if line.code == 'C1200':  # brut
                    self.total_brut += line.total
                    self.line_brut += line.total
                    dico[line.employee_id.id]['Brut'] = self.line_brut
                elif line.code == 'C2040':  # ipres rc
                    self.line_ipres_rc += line.total
                    self.total_ipres_rc += line.total
                    dico[line.employee_id.id]['Ipres_rc'] = self.line_ipres_rc
                    if self.line_base_rc == 0.0:
                        self.total_base_rc += line.amount
                        dico[line.employee_id.id]['Base_rc'] = line.amount
                elif line.code == 'C2030':  # ipres_rg
                    self.total_ipres_rg += line.total
                    self.line_ipres_rg += line.total
                    dico[line.employee_id.id]['Ipres_rg'] = self.line_ipres_rg
                    if self.line_base_rg == 0.0:
                        self.total_base_rg += line.amount
                        dico[line.employee_id.id]['Base_rg'] = line.amount
                elif line.code == 'C2041':  # ipres_rc_pat
                    self.total_ipres_rc_pat += line.total
                    self.line_ipres_rc_pat += line.total
                    dico[line.employee_id.id]['Ipres_rc_pat'] = self.line_ipres_rc_pat
                elif line.code == 'C2031':  # ipres_rg_pat
                    self.total_ipres_rg_pat += line.total
                    self.line_ipres_rg_pat += line.total
                    dico[line.employee_id.id]['Ipres_rg_pat'] = self.line_ipres_rg_pat
            else:
                dico[line.employee_id.id] = {}
                employee_data = self.env['hr.employee'].browse(line.employee_id.id)

                self.line_base_rg = 0
                self.line_base_rc = 0
                self.line_brut = 0
                self.line_ipres_rc = 0
                self.line_ipres_rg = 0
                self.line_ipres_rc_pat = 0
                self.line_ipres_rg_pat = 0

                dico[line.employee_id.id]['Brut'] = 0
                dico[line.employee_id.id]['Ipres_rc'] = 0
                dico[line.employee_id.id]['Base_rc'] = 0
                dico[line.employee_id.id]['Ipres_rg'] = 0
                dico[line.employee_id.id]['Base_rg'] = 0
                dico[line.employee_id.id]['Ipres_rc_pat'] = 0
                dico[line.employee_id.id]['Ipres_rg_pat'] = 0

                if line.code == 'C1200':  # brut
                    dico[line.employee_id.id]['Brut'] = self.line_brut = self.total_brut = line.total
                elif line.code == 'C2040':  # ipres rc
                    dico[line.employee_id.id]['Ipres_rc'] = self.line_ipres_rc = self.total_ipres_rc = line.total
                    dico[line.employee_id.id]['Base_rc'] = self.total_base_rc = line.amount
                elif line.code == 'C2030':  # ipres_rg
                    dico[line.employee_id.id]['Ipres_rg'] = self.line_ipres_rg = self.total_ipres_rg = line.total
                    dico[line.employee_id.id]['Base_rg'] = self.total_base_rg = line.amount
                elif line.code == 'C2041':  # ipres_rc_pat
                    dico[line.employee_id.id]['Ipres_rc_pat'] =\
                        self.line_ipres_rc_pat = self.total_ipres_rc_pat = line.total
                elif line.code == 'C2031':  # ipres_rg_pat
                    dico[line.employee_id.id]['Ipres_rg_pat'] =\
                        self.line_ipres_rg_pat = self.total_ipres_rg_pat = line.total

                dico[line.employee_id.id]['Name'] = employee_data.name
                dico[line.employee_id.id]['Matricule'] = employee_data.num_chezemployeur

        index = 0
        for key, values in dico.items():
            index += 1
            lines_data.append({
                'index': index,
                'matricule': dico[key]['Matricule'],
                'name': dico[key]['Name'],
                'Brut': int(round(dico[key]['Brut'])),
                'Base_rg': int(round(dico[key]['Base_rg'])),
                'Base_rc': int(round(dico[key]['Base_rc'])),
                'Ipres_rc': int(round(dico[key]['Ipres_rc'])),
                'Ipres_rg': int(round(dico[key]['Ipres_rg'])),
                'Ipres_rc_pat': int(round(dico[key]['Ipres_rc_pat'])),
                'Ipres_rg_pat': int(round(dico[key]['Ipres_rg_pat'])),
                'total_rg': int(round(dico[key]['Ipres_rg'] + dico[key]['Ipres_rg_pat'])),
                'total_rc': int(round(dico[key]['Ipres_rc'] + dico[key]['Ipres_rc_pat'])),
                'Cotisation_totale': int(round((dico[key]['Ipres_rg'] + dico[key]['Ipres_rg_pat']) + (
                        dico[key]['Ipres_rc'] + dico[key]['Ipres_rc_pat']))),
            })

        total_cotisation = 0
        total_rc = 0
        total_rg = 0
        total_base_rc = 0
        total_base_rg = 0
        total_brut = 0
        total_ipres_rc = 0
        total_ipres_rg = 0
        total_ipres_rc_pat = 0
        total_ipres_rg_pat = 0

        lines_total = []
        for line in lines_data:
            total_cotisation += line.get('Cotisation_totale')
            total_rc += line.get('total_rc')
            total_rg += line.get('total_rg')
            total_base_rc += line.get('Base_rc')
            total_base_rg += line.get('Base_rg')
            total_brut += line.get('Brut')
            total_ipres_rc += line.get('Ipres_rc')
            total_ipres_rg += line.get('Ipres_rg')
            total_ipres_rc_pat += line.get('Ipres_rc_pat')
            total_ipres_rg_pat += line.get('Ipres_rg_pat')

        lines_total.append({
            'total_cotisation': int(round(total_cotisation)),
            'total_rc': int(round(total_rc)),
            'total_rg': int(round(total_rg)),
            'total_base_rc': int(round(total_base_rc)),
            'total_base_rg': int(round(total_base_rg)),
            'total_brut': int(round(total_brut)),
            'total_ipres_rc': int(round(total_ipres_rc)),
            'total_ipres_rg': int(round(total_ipres_rg)),
            'total_ipres_rc_pat': int(round(total_ipres_rc_pat)),
            'total_ipres_rg_pat': int(round(total_ipres_rg_pat)),
            'total_brut': int(round(total_brut)),
        })

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'lines_data': lines_data,
            'lines_total': lines_total
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
