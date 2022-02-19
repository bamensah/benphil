# -*- coding:utf-8 -*-
# by khk
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from odoo import api, fields, models, _

class TransferOrder(models.AbstractModel):
    _name = 'report.optipay.report_transfer_order_view'
    _description = 'Rapport ordre de virement'

    def _get_lines(self, month, year):
        res = []
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
        index = 0
        for line in self.env.cr.fetchall():
            index += 1
            res.append({
                'index': index,
                'mane': line[1],
                'domiciliation': line[5],
                'numero_compte': line[2],
                'total': int(round(line[0])),
            })
        return res

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
        month = datetime.strptime(str(date_from), server_dt).month
        year = datetime.strptime(str(date_from), server_dt).year
        lines_data = self._get_lines(month, year)
        total_net = 0.0
        max_index = 0
        for line in lines_data:
            max_index += 1
            total_net += line.get('total')

        account_number = ''
        name = ''
        street = ''
        city = ''
        if self.env.user.company_id.bank_journal_ids:
            bank_number = self.env.user.company_id.bank_journal_ids[0].bank_acc_number
            bank_name = self.env.user.company_id.bank_journal_ids[0].bank_id.name
            bank_street = self.env.user.company_id.bank_journal_ids[0].bank_id.street
            bank_city = self.env.user.company_id.bank_journal_ids[0].bank_id.city

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'lines_data': lines_data,
            'total_net': int(round(total_net)),
            'max_index': max_index,
            'company_bank_number': bank_number,
            'company_bank_name': bank_name,
            'company_bank_street': bank_street,
            'company_bank_city': bank_city,
            'date': now.strftime("%d/%m/%Y"),
            'month': number_month_to_word.get(str(month))
        }
