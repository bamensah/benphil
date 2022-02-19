# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil import relativedelta

class BulletinPaieReport(models.AbstractModel):
    _name = "report.aospay.report_bulletin"
    _description = "Bulletin de paie"

    def get_payslip_libelle_salaire(self, payslip_lines):
        res = {}
        for line in payslip_lines:
            if line.category_id.code == 'INDM' or line.category_id.code == 'BASIC' or line.category_id.code == 'AVN' or line.category_id.code == 'HS':
                if line.total != 0.0:
                    res.setdefault(line.slip_id.id, [])
                    res[line.slip_id.id] += line
        return res

    def get_sal_brut(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            sal_brut_imp = 0.0
            for line in payslip.line_ids:
                if line.category_id.code == 'GROSS':
                    sal_brut_imp += line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(sal_brut_imp).replace(',', ' '))
        return res
        
    def get_base_inps(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'inps':
                    base_inps = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(base_inps).replace(',', ' '))
        return res
        
    def get_taux_salarie_inps(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            taux_salarie_inps = 0.0
            for line in payslip.line_ids:
                if line.code == 'inpse':
                    taux_salarie_inps = line.rate
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.2f}'.format(taux_salarie_inps).replace(',', ' '))
        return res
        
    def get_montant_salarie_inps(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'inpse':
                    montant_salarie_inps = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(montant_salarie_inps).replace(',', ' '))
        return res
    
    def get_taux_patronales_inps(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            taux_patronales_inps = 0.0
            for line in payslip.line_ids:
                if line.code == 'inpss':
                    taux_patronales_inps = line.rate
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.2f}'.format(taux_patronales_inps).replace(',', ' '))
        return res
       
    def get_montant_patronales_inps(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'inpss':
                    montant_patronales_inps = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(montant_patronales_inps).replace(',', ' '))
        return res
    
    def get_taux_salarie_amo(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            taux_salarie_amo = 0.0
            for line in payslip.line_ids:
                if line.code == 'amoe':
                    taux_salarie_amo = line.rate
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.2f}'.format(taux_salarie_amo).replace(',', ' '))
        return res
        
    def get_montant_salarie_amo(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'amoe':
                    montant_salarie_amo = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(montant_salarie_amo).replace(',', ' '))
        return res
    
    def get_taux_patronales_amo(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            taux_patronales_amo = 0.0
            for line in payslip.line_ids:
                if line.code == 'amos':
                    taux_patronales_amo = line.rate
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.2f}'.format(taux_patronales_amo).replace(',', ' '))
        return res
       
    def get_montant_patronales_amo(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'amos':
                    montant_patronales_amo = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(montant_patronales_amo).replace(',', ' '))
        return res
    
    def get_base_its(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'its':
                    base_its = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(base_its).replace(',', ' '))
        return res
    
    def get_montant_its(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'itsm':
                    montant_its = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(montant_its).replace(',', ' '))
        return res
        
    def get_total_retenues(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'ttr':
                    total_retenues = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(total_retenues).replace(',', ' '))
        return res
        
    def get_contribution_salaire(self, payslip_lines):
        res = {}
        for line in payslip_lines:
            if line.category_id.code == 'COMP' and line.code != 'amos' and line.code != 'inpss' and line.code != 'tcp':
                if line.total != 0.0:
                    res.setdefault(line.slip_id.id, [])
                    res[line.slip_id.id] += line
        return res
    
    def get_total_charges_patronales(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'tcp':
                    total_charges_patronales = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(total_charges_patronales).replace(',', ' '))
        return res
    
    def get_cout_total_employe(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'cte':
                    cout_total_employe = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(cout_total_employe).replace(',', ' '))
        return res
    
    def get_net_apayer(self, current_payslips):
        res = {}
        for payslip in self.env['hr.payslip'].browse(current_payslips):
            for line in payslip.line_ids:
                if line.code == 'nap':
                    net_apayer = line.total
            res.setdefault(payslip.id, [])
            res[payslip.id].append('{0:,.0f}'.format(net_apayer).replace(',', ' '))
        return res
        
    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['hr.payslip'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'data': data,
            'get_payslip_libelle_salaire': self.get_payslip_libelle_salaire(payslips.mapped('line_ids').filtered(
                lambda r: r.appears_on_payslip)),
            'get_sal_brut': self.get_sal_brut(payslips.mapped('id')),
            'get_base_inps': self.get_base_inps(payslips.mapped('id')),
            'get_taux_salarie_inps': self.get_taux_salarie_inps(payslips.mapped('id')),
            'get_montant_salarie_inps': self.get_montant_salarie_inps(payslips.mapped('id')),
            'get_taux_patronales_inps': self.get_taux_patronales_inps(payslips.mapped('id')),
            'get_montant_patronales_inps': self.get_montant_patronales_inps(payslips.mapped('id')),
            'get_taux_salarie_amo': self.get_taux_salarie_amo(payslips.mapped('id')),
            'get_montant_salarie_amo': self.get_montant_salarie_amo(payslips.mapped('id')),
            'get_taux_patronales_amo': self.get_taux_patronales_amo(payslips.mapped('id')),
            'get_montant_patronales_amo': self.get_montant_patronales_amo(payslips.mapped('id')),
            'get_base_its': self.get_base_its(payslips.mapped('id')),
            'get_montant_its': self.get_montant_its(payslips.mapped('id')),
            'get_total_retenues': self.get_total_retenues(payslips.mapped('id')),
            'get_contribution_salaire': self.get_contribution_salaire(payslips.mapped('line_ids').filtered(
                lambda r: r.appears_on_payslip)),
            'get_total_charges_patronales': self.get_total_charges_patronales(payslips.mapped('id')),
            'get_cout_total_employe': self.get_cout_total_employe(payslips.mapped('id')),
            'get_net_apayer': self.get_net_apayer(payslips.mapped('id')),

        }
