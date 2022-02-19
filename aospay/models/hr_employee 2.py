import time
from datetime import datetime, date, time as t
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    tauxabat = fields.Float(string = "Taux d'abattement")
    sitfam = fields.Char(string = "Situation de Famille")
    matricule = fields.Char(string = "Matricule")
    secu_social = fields.Char(string = "N° Sécurité Sociale")
    section = fields.Char(string = "Section")
    #matricule=fields.Char(string="Matricule")
    #matricule_cnss = fields.Char('Matricule CNSS')
    #ipres = fields.Char('Numero IPRES')
    #mutuelle = fields.Char('Numero mutuelle')
    #compte = fields.Char('Compte contribuable')
    #num_chezemployeur = fields.Char('Numero chez l\'employeur')
    #relation_ids = fields.One2many('optesis.relation', 'employee_id', 'Relation')
    #ir = fields.Float('Nombre de parts IR', compute="get_ir_trimf", store=True, default=1)
    #trimf = fields.Float('Nombre de parts TRIMF', compute="get_ir_trimf", store=True, default=1)
    #ir_changed = fields.Integer(default=0)
    #worked_days_per_years = fields.One2many('employee.worked.days', 'employee_id', 'Jour Travaillé')

#    @api.multi  
    @api.onchange('marital', 'children')
    def onchange_marital(self):
        if self.marital == 'married':
            self.sitfam = "M"+str(self.children)
            if self.children <=10:
                self['tauxabat']=10 + (2.5*self.children)
            else:
                self['tauxabat']=35
        else:
            self.sitfam="C"+str(self.children)
            if self.children <=10:
                self['tauxabat']=2.5*self.children
            else:
                self['tauxabat']=25
