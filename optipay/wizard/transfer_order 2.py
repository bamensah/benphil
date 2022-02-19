# -*- coding: utf-8 -*-
# by khk
import xlwt
import base64
from io import StringIO
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import fields, models, api
from odoo.exceptions import Warning

class optesis_transfer_order(models.TransientModel):
    _name = 'optesis.transfer.order'
    _description = 'order de virement'

    date_from = fields.Date('Date de la paie', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    print_format = fields.Selection([('pdf', 'PDF'),
                                     ('xls', 'Excel'), ],
                                    default='pdf', string="Format", required=True)
    transfer_data = fields.Char('Name', )
    file_name = fields.Binary('Transfer order', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')

    def print_report_transfer_order(self):
        if self.print_format == 'pdf':
            active_ids = self.env.context.get('active_ids', [])
            datas = {
                'ids': active_ids,
                'model': 'hr.contribution.register',
                'form': self.read()[0]
            }
            return self.env.ref('optipay.transfer_order').report_action([], data=datas)
        else:
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
            server_dt = DEFAULT_SERVER_DATE_FORMAT
            month = datetime.strptime(str(self.date_from), server_dt).month
            year = datetime.strptime(str(self.date_from), server_dt).year
            self.env.cr.execute("SELECT hr_payslip_line.total,hr_employee.name,res_partner_bank.acc_number,"
                                "hr_employee.bank_account_id AS hr_employee_bank_account_id,"
                                "res_bank.id AS res_bank_id,res_bank.name AS res_bank_name,"
                                "res_partner_bank.bank_id AS res_partner_bank_bank_id FROM "
                                "hr_payslip_line hr_payslip_line INNER JOIN hr_payslip hr_payslip ON "
                                "hr_payslip_line.slip_id = hr_payslip.id "
                                "INNER JOIN hr_employee hr_employee ON hr_payslip_line.employee_id = hr_employee.id "
                                "INNER JOIN res_partner_bank res_partner_bank ON "
                                "hr_employee.bank_account_id = res_partner_bank.id "
                                "INNER JOIN public.res_bank res_bank ON res_partner_bank.bank_id = res_bank.id WHERE "
                                "date_part('month',hr_payslip.date_from) = %s "
                                "AND hr_payslip_line.code = %s "
                                "AND hr_payslip_line.year = %s "
                                "AND hr_employee.company_id = %s ",
                                (month, 'C5000', str(year), self.env.user.company_id.id))
            line_ids = [x for x in self.env.cr.fetchall()]
            if len(line_ids) > 0:
                file = StringIO()
                workbook = xlwt.Workbook()
                format0 = xlwt.easyxf(
                    'font:height 300,bold True;pattern: pattern solid, fore_colour pale_blue;align: horiz center')
                format1 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour pale_blue;align: '
                                      'vert center, horiz center')
                format2 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour pale_blue;align: horiz left')
                format3 = xlwt.easyxf('align: vert center, horiz center')

                sheet = workbook.add_sheet('Ordre de virement')
                sheet.col(0).width = int(15 * 260)
                sheet.col(1).width = int(15 * 260)
                sheet.col(2).width = int(15 * 260)
                sheet.col(3).width = int(18 * 260)
                sheet.col(4).width = int(18 * 260)
                sheet.write_merge(0, 2, 0, 4, 'Ordre de virement ', format0)

                sheet.write(5, 3, 'Banque:', format2)
                sheet.write(5, 4, self.env.user.company_id.bank_journal_ids[0].bank_id.name)
                sheet.write(6, 3, 'Rue:', format2)
                sheet.write(6, 4, self.env.user.company_id.bank_journal_ids[0].bank_id.street)
                sheet.write(7, 3, 'Code Postal:', format2)
                sheet.write(7, 4, self.env.user.company_id.bank_journal_ids[0].bank_id.zip)
                sheet.write(8, 3, 'Ville:', format2)
                sheet.write(8, 4, self.env.user.company_id.bank_journal_ids[0].bank_id.city)
                sheet.write(9, 3, 'Date:', format2)
                sheet.write(9, 4, now.strftime("%d/%m/%Y"))

                sheet.write(11, 0, 'Objet:')
                sheet.write(11, 1, 'Ordre de Virement')

                account_number = ''
                if self.env.user.company_id.bank_journal_ids:
                    account_number = self.env.user.company_id.bank_journal_ids[0].bank_acc_number

                sheet.write_merge(13, 13, 0, 4, 'Par le débit de notre compte n° '
                                  + str(account_number) +
                                  ' ouvert dans vos livres, nous vous prions de vouloir ')
                sheet.write_merge(14, 14, 0, 4, 'efféctuer les virements  pour les titulaires de compteci-dessous'
                                  ' en réglement de leur ')
                sheet.write_merge(15, 15, 0, 4, 'rénumérations du mois de mai.')

                sheet.write(17, 0, 'N°', format1)
                sheet.write(17, 1, 'Prénom-Nom', format1)
                sheet.write(17, 2, 'Domiciliation', format1)
                sheet.write(17, 3, 'N° Compte', format1)
                sheet.write(17, 4, 'MontantFCFA', format1)
                row = 18
                index = 0
                total = 0
                for line in line_ids:
                    index += 1
                    sheet.write(row, 0, index, format3)
                    sheet.write(row, 1, line[1], format3)
                    sheet.write(row, 2, line[5], format3)
                    sheet.write(row, 3, line[2], format3)
                    sheet.write(row, 4, line[0], format3)
                    total += line[0]
                    row += 1
                sheet.write_merge(row, row, 0, 3, 'Total ' + str(index), format1)
                sheet.write(row, 4, total, format3)
                sheet.write_merge(row+2, row+2, 0, 7, 'Veuillez agréer, Monsieur, l\'expression'
                                                      ' de notre parfaiteconsidération.')
                filename = ('/tmp/Ordre de virement Report' + '.xls')
                workbook.save(filename)
                file = open(filename, "rb")
                file_data = file.read()
                out = base64.encodestring(file_data)
                self.write({'state': 'get', 'file_name': out, 'transfer_data': 'Ordre de virement Report.xls'})
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'optesis.transfer.order',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': self.id,
                    'target': 'new',
                }
            else:
                raise Warning("Pas de données pour cette période")
