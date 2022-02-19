# -*- coding: utf-8 -*-
# by khk
import xlwt
import base64
from io import StringIO
import time
from datetime import datetime
from dateutil import relativedelta
from odoo import fields, models, api
from odoo.exceptions import Warning

class optesis_payslip_lines_securite_sociale(models.TransientModel):
    _name = 'optesis.payslip.lines.securite.sociale'
    _description = 'css modele wizard'

    date_from = fields.Date('Date de debut', required=True,
     default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date de fin', required=True,
     default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    print_format = fields.Selection([('pdf', 'PDF'),
                                     ('xls', 'Excel'), ],
                                    default='pdf', string="Format", required=True)
    css_data = fields.Char('Name', )
    file_name = fields.Binary('Cotisation IPRES Excel Report', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')

    # @api.multi
    def print_report_css(self):
        if self.print_format == 'pdf':
            active_ids = self.env.context.get('active_ids', [])
            datas = {
                 'ids': active_ids,
                 'model': 'hr.contribution.register',
                 'form': self.read()[0]
            }
            return self.env.ref('optipay.securite_sociale').report_action([], data=datas)
        else:
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
                                (self.date_from, self.date_to, self.env.user.company_id.id))
            line_ids = [x[0] for x in self.env.cr.fetchall()]
            if len(line_ids) > 0:
                dico = {}
                total_brut = 0.0
                total_base = 0.0
                total_prestfam = 0.0
                total_acw = 0.0
                total_cotisation = 0.0
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
            else:
                raise Warning("Pas de données pour cette période")

            file = StringIO()
            workbook = xlwt.Workbook()
            format0 = xlwt.easyxf(
                'font:height 500,bold True;pattern: pattern solid, fore_colour pale_blue;align: horiz center')
            format1 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour pale_blue;align: '
                                  'vert center, horiz center')
            format3 = xlwt.easyxf('align: vert center, horiz center')

            sheet = workbook.add_sheet('Caisse de Sécurité Sociale du ' + str(
                self.date_from.strftime(" %d %b %Y")) + ' au ' + str(
                self.date_to.strftime(" %d %b %Y")))
            sheet.col(0).width = int(5 * 260)
            sheet.col(1).width = int(15 * 260)
            sheet.col(2).width = int(15 * 260)
            sheet.col(3).width = int(18 * 260)
            sheet.col(4).width = int(18 * 260)
            sheet.col(5).width = int(18 * 260)
            sheet.col(6).width = int(18 * 260)
            sheet.col(7).width = int(18 * 260)
            sheet.write_merge(0, 2, 0, 7, 'Caisse de Sécurité Sociale ', format0)
            sheet.write_merge(4, 5, 3, 5, 'Période du ' + str(self.date_from.strftime(" %d %b %Y")) + ' au ' + str(
                self.date_to.strftime(" %d %b %Y")), format1)
            sheet.write_merge(7, 8, 0, 0, 'N', format1)
            sheet.write_merge(7, 8, 1, 2, 'Identification Employée', format1)
            sheet.write_merge(7, 8, 3, 3, 'Brut Imposable', format1)
            sheet.write_merge(7, 8, 4, 4, 'Base', format1)
            sheet.write_merge(7, 8, 5, 5, 'Allocation Familiales', format1)
            sheet.write_merge(7, 8, 6, 6, 'Accident de Travail', format1)
            sheet.write_merge(7, 8, 7, 7, 'Cotisation Total', format1)
            row = 9
            index = 1
            for key, value in dico.items():
                sheet.write(row, 0, str(index), format3)
                sheet.write(row, 1, dico[key]['Matricule'], format3)
                sheet.write(row, 2, dico[key]['Name'], format3)
                sheet.write(row, 3, dico[key]['Brut'], format3)
                sheet.write(row, 4, dico[key]['Base'], format3)
                sheet.write(row, 5, dico[key]['Prestfam'], format3)
                sheet.write(row, 6, dico[key]['Acw'], format3)
                sheet.write(row, 7, dico[key]['Prestfam'] + dico[key]['Acw'], format3)
                row += 1
                index += 1

            sheet.write_merge(row, row, 0, 2, 'Total', format1)
            sheet.write(row, 3, total_brut, format3)
            sheet.write(row, 4, total_base, format3)
            sheet.write(row, 5, total_prestfam, format3)
            sheet.write(row, 6, total_acw, format3)
            sheet.write(row, 7, total_cotisation, format3)

            filename = ('/tmp/Caisse de Sécurité Report' + '.xls')
            workbook.save(filename)
            file = open(filename, "rb")
            file_data = file.read()
            out = base64.encodestring(file_data)
            self.write({'state': 'get', 'file_name': out, 'css_data': 'Caisse de Sécurité Report.xls'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'optesis.payslip.lines.securite.sociale',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
            }
