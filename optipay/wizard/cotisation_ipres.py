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

class optesis_payslip_lines_cotisation_ipres(models.TransientModel):
    _name = 'optesis.payslip.lines.cotisation.ipres'
    _description = 'cotisation ipres modele wizard'

    date_from = fields.Date('Date de debut', required=True,
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date de fin', required=True,
                          default=lambda *a: str(
                              datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    print_format = fields.Selection([('pdf', 'PDF'),
                                     ('xls', 'Excel'), ],
                                    default='pdf', string="Format", required=True)
    cotisation_ipres_data = fields.Char('Name', )
    file_name = fields.Binary('Cotisation IPRES Excel Report', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')

    # @api.multi
    def print_report_ipres(self):

        if self.print_format == 'pdf':
            active_ids = self.env.context.get('active_ids', [])
            datas = {
                'ids': active_ids,
                'model': 'hr.contribution.register',
                'form': self.read()[0]
            }
            return self.env.ref('optipay.cotisation_ipres').report_action([], data=datas)
        else:
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
                                (self.date_from, self.date_to, self.env.user.company_id.id))
            line_ids = [x[0] for x in self.env.cr.fetchall()]
            if len(line_ids) > 0:
                self.total_brut = 0.0
                self.total_ipres_rc = 0.0
                self.total_ipres_rg = 0.0
                self.total_ipres_rc_pat = 0.0
                self.total_ipres_rg_pat = 0.0
                self.total_base_rc = 0.0
                self.total_base_rg = 0.0

                dico = {}
                lines_data = []
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
                            dico[line.employee_id.id][
                                'Ipres_rc'] = self.line_ipres_rc = self.total_ipres_rc = line.total
                            dico[line.employee_id.id]['Base_rc'] = self.total_base_rc = line.amount
                        elif line.code == 'C2030':  # ipres_rg
                            dico[line.employee_id.id][
                                'Ipres_rg'] = self.line_ipres_rg = self.total_ipres_rg = line.total
                            dico[line.employee_id.id]['Base_rg'] = self.total_base_rg = line.amount
                        elif line.code == 'C2041':  # ipres_rc_pat
                            dico[line.employee_id.id]['Ipres_rc_pat'] = \
                                self.line_ipres_rc_pat = self.total_ipres_rc_pat = line.total
                        elif line.code == 'C2031':  # ipres_rg_pat
                            dico[line.employee_id.id]['Ipres_rg_pat'] = \
                                self.line_ipres_rg_pat = self.total_ipres_rg_pat = line.total

                        dico[line.employee_id.id]['Name'] = employee_data.name
                        dico[line.employee_id.id]['Matricule'] = employee_data.num_chezemployeur
                        dico[line.employee_id.id]['jour entree'] = employee_data.contract_id.date_start.day
                        dico[line.employee_id.id]['mois entree'] = employee_data.contract_id.date_start.month
                        dico[line.employee_id.id]['annee entree'] = employee_data.contract_id.date_start.year
                        dico[line.employee_id.id]['jour sortie'] = employee_data.contract_id.date_end.day if \
                            employee_data.contract_id.date_end else '-'
                        dico[line.employee_id.id]['mois sortie'] = employee_data.contract_id.date_end.month if \
                            employee_data.contract_id.date_end else '-'
                        dico[line.employee_id.id]['annee sortie'] = employee_data.contract_id.date_end.year if \
                            employee_data.contract_id.date_end else '-'
            else:
                raise Warning("Pas de données pour cette période")

            index = 0
            for key, values in dico.items():
                index += 1
                lines_data.append({
                    'index': index,
                    'matricule': dico[key]['Matricule'],
                    'name': dico[key]['Name'],
                    'jour entree': dico[key]['jour entree'],
                    'mois entree': dico[key]['mois entree'],
                    'annee entree': dico[key]['annee entree'],
                    'jour sortie': dico[key]['jour sortie'],
                    'mois sortie': dico[key]['mois sortie'],
                    'annee sortie': dico[key]['annee sortie'],
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

            file = StringIO()
            workbook = xlwt.Workbook()
            format0 = xlwt.easyxf(
                'font:height 500,bold True;pattern: pattern solid, fore_colour pale_blue;align: horiz center')
            format1 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour pale_blue;align: '
                                  'vert center, horiz center')
            format2 = xlwt.easyxf('font:bold True;align: vert center, horiz center')
            format3 = xlwt.easyxf('align: vert center, horiz center')

            sheet = workbook.add_sheet('Cotisation IPRES du ' + str(
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
            sheet.col(8).width = int(18 * 260)
            sheet.col(9).width = int(15 * 260)
            sheet.col(10).width = int(15 * 260)
            sheet.col(11).width = int(15 * 260)
            sheet.col(12).width = int(15 * 260)
            sheet.col(13).width = int(15 * 260)
            sheet.col(14).width = int(15 * 260)
            sheet.col(15).width = int(15 * 260)
            sheet.col(16).width = int(15 * 260)
            sheet.col(17).width = int(15 * 260)
            sheet.col(18).width = int(15 * 260)
            sheet.col(19).width = int(15 * 260)
            sheet.col(20).width = int(15 * 260)

            sheet.write_merge(0, 2, 0, 18, 'Cotisation IPRES ', format0)
            sheet.write_merge(4, 5, 8, 10, 'Période du ' + str(self.date_from.strftime(" %d %b %Y")) + ' au ' + str(
                self.date_to.strftime(" %d %b %Y")), format1)
            sheet.write_merge(7, 8, 0, 0, 'N', format1)
            sheet.write_merge(7, 8, 1, 2, 'Identification Employée', format1)
            sheet.write_merge(7, 8, 3, 8, '', format1)
            sheet.write_merge(7, 8, 9, 9, 'Brut Imposable', format1)
            sheet.write_merge(7, 8, 10, 13, 'Ipres Régime Général', format1)
            sheet.write_merge(7, 8, 14, 17, 'Ipres Régime Cadre', format1)
            sheet.write_merge(7, 8, 18, 18, 'Cotisation Totale', format1)

            sheet.write(9, 0)
            sheet.write(9, 1, 'Matricule', format2)
            sheet.write(9, 2, 'Nom et Prenom', format2)
            sheet.write(9, 3, "JOUR D'ENTREE", format2)
            sheet.write(9, 4, "MOIS D'ENTREE", format2)
            sheet.write(9, 5, "ANNEE D'ENTREE", format2)
            sheet.write(9, 6, "JOUR DE SORTIE", format2)
            sheet.write(9, 7, "MOIS DE SORTIE", format2)
            sheet.write(9, 8, "ANNEE DE SORTIE", format2)
            sheet.write(9, 10, 'BASE', format2)
            sheet.write(9, 11, 'Employée', format2)
            sheet.write(9, 12, 'Employeur', format2)
            sheet.write(9, 13, 'Total RG', format2)
            sheet.write(9, 14, 'BASE', format2)
            sheet.write(9, 15, 'Employée', format2)
            sheet.write(9, 16, 'Employeur', format2)
            sheet.write(9, 17, 'Total RC', format2)
            sheet.write(9, 18)

            row = 10
            for line in lines_data:
                sheet.write(row, 0, line.get('index'), format3)
                sheet.write(row, 1, line.get('matricule'), format3)
                sheet.write(row, 2, line.get('name'), format3)
                sheet.write(row, 3, line.get('jour entree'), format3)
                sheet.write(row, 4, line.get('mois entree'), format3)
                sheet.write(row, 5, line.get('annee entree'), format3)
                sheet.write(row, 6, line.get('jour sortie'), format3)
                sheet.write(row, 7, line.get('mois sortie'), format3)
                sheet.write(row, 8, line.get('annee sortie'), format3)
                sheet.write(row, 9, line.get('Brut'), format3)
                sheet.write(row, 10, line.get('Base_rg'), format3)
                sheet.write(row, 11, line.get('Ipres_rg'), format3)
                sheet.write(row, 12, line.get('Ipres_rg_pat'), format3)
                sheet.write(row, 13, line.get('total_rg'), format3)
                sheet.write(row, 14, line.get('Base_rc'), format3)
                sheet.write(row, 15, line.get('Ipres_rc'), format3)
                sheet.write(row, 16, line.get('Ipres_rc_pat'), format3)
                sheet.write(row, 17, line.get('total_rc'), format3)
                sheet.write(row, 18, line.get('Cotisation_totale'), format3)
                row += 1

            row += 1
            for line in lines_total:
                sheet.write_merge(row, row, 0, 2, 'Total', format1)
                sheet.write(row, 9, line.get('total_brut'), format3)
                sheet.write(row, 10, line.get('total_base_rg'), format3)
                sheet.write(row, 11, line.get('total_ipres_rg'), format3)
                sheet.write(row, 12, line.get('total_ipres_rg_pat'), format3)
                sheet.write(row, 13, line.get('total_rg'), format3)
                sheet.write(row, 14, line.get('total_base_rc'), format3)
                sheet.write(row, 15, line.get('total_ipres_rc'), format3)
                sheet.write(row, 16, line.get('total_ipres_rc_pat'), format3)
                sheet.write(row, 17, line.get('total_rc'), format3)
                sheet.write(row, 18, line.get('total_cotisation'), format3)

            filename = ('/tmp/Cotisation IPRES Report' + '.xls')
            workbook.save(filename)
            file = open(filename, "rb")
            file_data = file.read()
            out = base64.encodestring(file_data)
            self.write({'state': 'get', 'file_name': out, 'cotisation_ipres_data': 'Cotisation IPRES Report.xls'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'optesis.payslip.lines.cotisation.ipres',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'target': 'new',
            }
