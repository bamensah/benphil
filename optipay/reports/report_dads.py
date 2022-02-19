# -*- coding:utf-8 -*-
# by khk

from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo import api, fields, models, _


class DadsReport1(models.AbstractModel):
    _name = "report.optipay.report_dads_view_1"
    _description = 'Rapport Dads'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        register_ids = self.env.context.get('active_ids', [])
        contrib_registers = self.env['hr.contribution.register'].browse(register_ids)
        year = data['form'].get('year', fields.Date.today().year)

        self.sn_male_count = 0
        self.sn_female_count = 0
        self.other_male_count = 0
        self.other_female_count = 0

        self.total_salary_sn = 0
        self.total_salary_others = 0

        self.total_cfce_sn = 0
        self.total_cfce_others = 0

        self.total_cfce = 0
        self.total_trimf = 0
        self.total_ir = 0
        self.total_montant_verse = 0

        dico = {}
        lines_detail_versement = []

        detail_versement = self.env['optesis.detail.versement'].search([('name', '=', year),('company_id', '=', self.env.user.company_id.id)])
        for line_id in detail_versement.detail_versement_line:
            self.total_montant_verse += line_id.montant_versement
            self.total_ir += line_id.montant_ir
            self.total_trimf += line_id.montant_trimf
            self.total_cfce += line_id.montant_cfce
            lines_detail_versement.append({
                'mois': line_id.name,
                'date': line_id.date_versement,
                'montant_versement': line_id.montant_versement if line_id.montant_versement else False,
                'montant_ir': line_id.montant_ir if line_id.montant_ir else False,
                'montant_trimf': line_id.montant_trimf if line_id.montant_trimf else False,
                'montant_cfce': line_id.montant_cfce if line_id.montant_cfce else False,
                'num_quitance': line_id.numero_quitance,
                'obsevation': line_id.observation
            })

        for line in self.env['hr.payslip.line'].search([('year', '=', year), ('company_id', '=', self.env.user.company_id.id)]):
            if line.employee_id.id not in dico:
                dico[line.employee_id.id] = {}
                if line.employee_id.country_id.code == 'SN':
                    if line.employee_id.gender == 'male':
                        self.sn_male_count += 1
                    else:
                        self.sn_female_count += 1
                else:
                    if line.employee_id.gender == 'male':
                        self.other_male_count += 1
                    else:
                        self.other_female_count += 1


            if line.employee_id.country_id.code == "SN":
                if line.code == "C5000":        
                    self.total_salary_sn += line.total
                if line.code == "C2000":
                    self.total_cfce_sn += line.total
            else:
                if line.code == "C5000":        
                    self.total_salary_others += line.total
                if line.code == "C2000":
                    self.total_cfce_others += line.total

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'details_versement': lines_detail_versement,
            'year': year,
            'sn_male_count': self.sn_male_count,
            'sn_female_count': self.sn_female_count,
            'other_male_count': self.other_male_count,
            'other_female_count': self.other_female_count,
            'total_count': self.sn_male_count + self.sn_female_count + self.other_male_count + self.other_female_count,
            'total_salary_sn': self.total_salary_sn,
            'total_salary_others': self.total_salary_others,
            'total_salary': self.total_salary_others + self.total_salary_sn,
            'total_cfce_sn': self.total_cfce_sn,
            'total_cfce_others': self.total_cfce_others,
            'total_cfce': self.total_cfce,
            'total_ir': self.total_ir,
            'total_trimf': self.total_trimf,
            'total_montant_verse': self.total_montant_verse
        }


class DadsReport(models.AbstractModel):
    _name = "report.optipay.report_dads_view_2"
    _description = 'Rapport Dads'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        register_ids = self.env.context.get('active_ids', [])
        contrib_registers = self.env['hr.contribution.register'].browse(register_ids)
        year = data['form'].get('year', fields.Date.today().year)        

        server_dt = DEFAULT_SERVER_DATE_FORMAT
        number_month_to_word = {
            "1": "JAN",
            "2": "FEV",
            "3": "MARS",
            "4": "AVR",
            "5": "MAI",
            "6": "JUIN",
            "7": "JUL",
            "8": "AOUT",
            "9": "SEPT",
            "10": "OCT",
            "11": "NOV",
            "12": "DEC"
        }
        marital = {
            'single': 'C',
            'married': 'M',
            'cohabitant': '',
            'widower': 'V',
            'divorced': 'D'
        }

        self.total_brut = 0
        self.total_avn = 0
        self.total_brut_avn = 0
        self.total_impot = 0
        self.total_trimf = 0
        self.total_cfce = 0
        self.total_transport = 0

        dico = {}
        lines_data = []
        lines_total = []

        for line in self.env['hr.payslip.line'].search([('year', '=', year),('company_id', '=', self.env.user.company_id.id)]):
            if line.employee_id.id in dico:
                if line.code == 'C1148': # brut
                    dico[line.employee_id.id]['brut'] += line.total
                    dico[line.employee_id.id]['brut+avn'] += line.total
                    self.total_brut += line.total
                    self.total_brut_avn += line.total
                elif line.code == 'C1090': # avn
                    dico[line.employee_id.id]['avn'] += line.total
                    dico[line.employee_id.id]['brut+avn'] += line.total
                    self.total_avn += line.total
                    self.total_brut_avn += line.total
                elif line.code == 'C2170': # impot sur le revenu
                    dico[line.employee_id.id]['impot'] += line.total
                    self.total_impot += line.total
                elif line.code == 'C2050': # trimf
                    dico[line.employee_id.id]['trimf'] += line.total
                    self.total_trimf += line.total
                elif line.code == 'C2000': # cfce
                    dico[line.employee_id.id]['cfce'] += line.total
                    self.total_cfce += line.total
                elif line.code in ('C1125', 'C1140'): # prime transport et indm km
                    dico[line.employee_id.id]['transport'] += line.total
                    self.total_transport += line.total

                if line.slip_id.date_from < dico[line.employee_id.id]['minDate']:
                    dico[line.employee_id.id]['minDate'] = line.slip_id.date_from

                if line.slip_id.date_from > dico[line.employee_id.id]['maxDate']:
                    dico[line.employee_id.id]['maxDate'] = line.slip_id.date_from
            else:
                dico[line.employee_id.id] = {}
                dico[line.employee_id.id]['name'] = line.employee_id.name
                dico[line.employee_id.id]['matricule'] = line.employee_id.num_chezemployeur
                dico[line.employee_id.id]['employement'] = line.employee_id.job_id.name
                dico[line.employee_id.id]['address'] = line.employee_id.address_home_id.name
                dico[line.employee_id.id]['gender'] = 'M' if line.employee_id.gender == 'male' else 'F'
                dico[line.employee_id.id]['country'] = line.employee_id.country_id.name
                dico[line.employee_id.id]['marital'] = line.employee_id.marital

                nb_wife = 0
                nb_children = 0
                for family_line in line.employee_id.relation_ids:
                    if family_line.type == 'conjoint':
                        nb_wife += 1
                    elif family_line.type == 'enfant':
                        nb_children += 1
                dico[line.employee_id.id]['nb_wife'] = nb_wife
                dico[line.employee_id.id]['nb_children'] = nb_children
                dico[line.employee_id.id]['nb_part'] = line.employee_id.ir

                dico[line.employee_id.id]['brut'] = 0
                dico[line.employee_id.id]['avn'] = 0
                dico[line.employee_id.id]['brut+avn'] = 0
                dico[line.employee_id.id]['impot'] = 0
                dico[line.employee_id.id]['trimf'] = 0
                dico[line.employee_id.id]['cfce'] = 0
                dico[line.employee_id.id]['transport'] = 0
                dico[line.employee_id.id]['minDate'] = line.slip_id.date_from
                dico[line.employee_id.id]['maxDate'] = line.slip_id.date_from

                if line.code == 'C1148': # brut
                    dico[line.employee_id.id]['brut'] = self.total_brut = line.total
                    self.total_brut_avn += line.total
                elif line.code == 'C1090': #avn
                    dico[line.employee_id.id]['avn'] = self.total_avn = line.total
                    self.total_brut_avn += line.total
                elif line.code == 'C2170': # impot sur le revenu
                    dico[line.employee_id.id]['impot'] = self.total_impot = line.total
                elif line.code == 'C2050': # trimf
                    dico[line.employee_id.id]['trimf'] = self.total_trimf = line.total
                elif line.code == 'C2000': # cfce
                    dico[line.employee_id]['cfce'] = self.total_cfce = line.total
                elif line.code in ('C1125', 'C1140'): # prime transport et indm km
                    dico[line.employee_id.id]['transport'] = self.total_transport = line.total

        index = 0
        for key, value in dico.items():
            index += 1
            lines_data.append({
                'index': index,
                'name': dico[key]['name'],
                'matricule': dico[key]['matricule'],
                'employement': dico[key]['employement'],
                'address': dico[key]['address'],
                'gender': dico[key]['gender'],
                'country': dico[key]['country'],
                'marital': marital.get(dico[key]['marital']),
                'nb_children': dico[key]['nb_children'],
                'nb_wife': dico[key]['nb_wife'],
                'nb_part': dico[key]['nb_part'],
                'period': number_month_to_word.get(str(datetime.strptime(str(dico[key]['minDate']), server_dt).month)) 
                + '-' +  number_month_to_word.get(str(datetime.strptime(str(dico[key]['maxDate']), server_dt).month)),
                'brut': dico[key]['brut'],
                'avn': dico[key]['avn'],
                'brut+avn': dico[key]['brut+avn'],
                'impot': dico[key]['impot'],
                'trimf': dico[key]['trimf'],
                'cfce': dico[key]['cfce'],
                'transport': dico[key]['transport']
            })

        lines_total.append({
            'total_brut': self.total_brut,
            'total_avn': self.total_avn,
            'total_brut_avn': self.total_brut_avn,
            'total_impot': self.total_impot,
            'total_trimf': self.total_trimf,
            'total_cfce': self.total_cfce,
            'total_transport': self.total_transport
        })

        return {
            'doc_ids': register_ids,
            'doc_model': 'hr.contribution.register',
            'docs': contrib_registers,
            'data': data,
            'lines_data': lines_data,
            'lines_total': lines_total,
            'year': year
        }