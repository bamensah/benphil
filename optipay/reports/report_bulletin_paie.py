# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil import relativedelta

class BulletinPaieReport(models.AbstractModel):
    _name = "report.optipay.report_bulletin"
    _description = "Bulletin de paie"

    def get_payslip_imposable(self, payslip_lines):
        res = {}
        for line in payslip_lines:
            if line.category_id.code == 'INDM' or line.category_id.code == 'BASE' or line.category_id.code == 'AVN' or line.category_id.code == 'HS':
                if line.total != 0.0:
                    res.setdefault(line.slip_id.id, [])
                    res[line.slip_id.id] += line
        return res

    def get_payslip_cotisation(self, payslip_lines):
        res = {}
        for line in payslip_lines:
            if line.category_id.code == 'COMP' or line.category_id.code == 'SALC':
                if line.total != 0.0:
                    res.setdefault(line.slip_id.id, [])
                    res[line.slip_id.id] += line
        return res

    def get_payslip_non_imposable(self, payslip_lines):
        res = {}
        for line in payslip_lines:
            if line.category_id.code == 'NOIMP':
                if line.total != 0.0:
                    res.setdefault(line.slip_id.id, [])
                    res[line.slip_id.id] += line
        return res

    def get_payslip_retenu(self, payslip_lines):
        res = {}
        for line in payslip_lines:
            if line.category_id.code == 'IR' or line.category_id.code == 'DED':
                if line.total != 0.0:
                    res.setdefault(line.slip_id.id, [])
                    res[line.slip_id.id] += line
        return res

    def get_total_gains(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            total_gain = 0.0
            for line in payslip.line_ids:
                if line.category_id.code == 'INDM' or line.category_id.code == 'BASE' or \
                        line.category_id.code == 'NOIMP' or line.category_id.code == 'HS':
                    total_gain += line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(total_gain).replace(',', ' '))
        return res

    def get_total_charg_sal(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            total_charg_sal = 0.0
            for line in payslip.line_ids:
                if line.category_id.code == 'DED' or line.category_id.code == 'SALC':
                    total_charg_sal += line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(total_charg_sal).replace(',', ' '))
        return res

    def get_total_charge_pat(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            total_charg_pat = 0.0
            for line in payslip.line_ids:
                if line.category_id.code == 'COMP':
                    total_charg_pat += line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(total_charg_pat).replace(',', ' '))
        return res

    def get_sal_brut_imp(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            sal_brut_imp = 0.0
            for line in payslip.line_ids:
                if line.category_id.code in ['BASE', 'INDM', 'AVN', 'HS']:
                    sal_brut_imp += line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(sal_brut_imp).replace(',', ' '))
        return res

    def get_sal_brut(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            total_brut = 0.0
            for line in payslip.line_ids:
                if line.category_id.code in ['NOIMP', 'INDM', 'BASE', 'AVN', 'HS']:
                    total_brut += line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(total_brut).replace(',', ' '))
        return res

    def get_sal_net(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            net = 0.0
            for line in payslip.line_ids:
                if line.category_id.code == 'NET':
                    net += line.total
                    break
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(net).replace(',', ' '))
        return res

    def get_base_conges(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            amount = 0.0
            for line in payslip.line_ids:
                if line.code == 'C1150':
                    amount += line.total
                    break
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(amount).replace(',', ' '))
        return res

    def get_val_annuel(self, payslips):
        payslipref = self.env['hr.payslip']
        server_dt = DEFAULT_SERVER_DATE_FORMAT
        res = {}
        for obj_payslip in payslipref.browse(payslips):

            year = datetime.strptime(str(obj_payslip.date_from), server_dt).year
            payslip_ids = [payslip_id for payslip_id in
                           payslipref.search([('employee_id', '=', obj_payslip.employee_id.id),
                                              ('date_from', '<=', obj_payslip.date_from)])]

            sal_brut_an = 0.0
            sal_brut_imp_an = 0.0
            charg_pat_an = 0.0
            charg_sal_an = 0.0

            for payslip in payslip_ids:
                if datetime.strptime(str(payslip.date_from), server_dt).year == year:
                    for payslip_line in payslip.line_ids:
                        if payslip_line.category_id.code == 'BASE' or payslip_line.category_id.code == 'INDM' or \
                                payslip_line.category_id.code == 'AVN':
                            sal_brut_imp_an += payslip_line.total
                        if payslip_line.category_id.code == 'BRUT':
                            sal_brut_an += payslip_line.total
                        if payslip_line.category_id.code == 'COMP':
                            charg_pat_an += payslip_line.total
                        if payslip_line.category_id.code == 'SALC' or \
                                payslip_line.category_id.code == 'DED':
                            charg_sal_an += payslip_line.total
            res.setdefault(obj_payslip.id, [])
            res[obj_payslip.id].append({
                'sal_brut_imp_an': sal_brut_imp_an,
                'sal_brut_an': sal_brut_an,
                'charg_pat_an': charg_pat_an,
                'charg_sal_an': charg_sal_an,
            })
        return res

    def get_anciennte(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            seniority = ""
            server_dt = DEFAULT_SERVER_DATE_FORMAT
            diff = relativedelta.relativedelta(datetime.strptime(str(payslip.contract_id.dateAnciennete), server_dt),
                                               datetime.strptime(str(payslip.date_to), server_dt))
            if diff.years != 0 and diff.years < 0:
                seniority += " " + str(-diff.years) + " An(s)"
            if diff.months != 0 and diff.months < 0:
                seniority += " " + str(-diff.months) + " mois"
            if diff.days != 0 and diff.days < 0:
                seniority += " " + str(-diff.days) + " jour(s)"

            res.setdefault(payslip.id, [])
            res[payslip.id].append(seniority)
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['hr.payslip'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'data': data,
            'get_payslip_imposable': self.get_payslip_imposable(payslips.mapped('line_ids').filtered(
                lambda r: r.appears_on_payslip)),
            'get_payslip_cotisation': self.get_payslip_cotisation(payslips.mapped('line_ids').filtered(
                lambda r: r.appears_on_payslip)),
            'get_payslip_non_imposable': self.get_payslip_non_imposable(payslips.mapped('line_ids').filtered(
                lambda r: r.appears_on_payslip)),
            'get_payslip_retenu': self.get_payslip_retenu(payslips.mapped('line_ids').filtered(
                lambda r: r.appears_on_payslip)),
            'get_total_gains': self.get_total_gains(payslips.mapped('id')),
            'get_total_charg_sal': self.get_total_charg_sal(payslips.mapped('id')),
            'get_total_charge_pat': self.get_total_charge_pat(payslips.mapped('id')),
            'get_sal_brut_imp': self.get_sal_brut_imp(payslips.mapped('id')),
            'get_sal_brut': self.get_sal_brut(payslips.mapped('id')),
            'get_sal_net': self.get_sal_net(payslips.mapped('id')),
            'get_base_conges': self.get_base_conges(payslips.mapped('id')),
            'get_val_annuel': self.get_val_annuel(payslips.mapped('id')),
            'get_anciennte': self.get_anciennte(payslips.mapped('id')),
        }
