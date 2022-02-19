import time
from datetime import datetime, date, time as t
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    matricule_cnss = fields.Char('Matricule CNSS')
    ipres = fields.Char('Numero IPRES')
    mutuelle = fields.Char('Numero mutuelle')
    compte = fields.Char('Compte contribuable')
    num_chezemployeur = fields.Char('Numero chez l\'employeur')
    relation_ids = fields.One2many('optesis.relation', 'employee_id', 'Relation')
    ir = fields.Float('Nombre de parts IR', compute="get_ir_trimf", store=True, default=1)
    trimf = fields.Float('Nombre de parts TRIMF', compute="get_ir_trimf", store=True, default=1)
    ir_changed = fields.Integer(default=0)
    worked_days_per_years = fields.One2many('employee.worked.days', 'employee_id', 'Jour Travaillé')

    def process_scheduler_check_employee_child_grown(self):
        for empl_obj in self.env['hr.employee'].search([]):
            empl_obj.get_ir_trimf()

    # @api.multi
    @api.depends('relation_ids')
    def get_ir_trimf(self):
        for value in self:
            old_ir = value.ir
            value.ir = 1
            value.trimf = 1
            nbj_sup = 0
            for line in value.relation_ids:
                if line.type == 'enfant':
                    now = datetime.now()
                    dur = now - line.birth
                    if dur.days < 7670:  # check if child is grown
                        value.ir += 0.5

                    if dur.days <= 5114 and value.gender == 'female':  # get extra days for holidays
                        nbj_sup += 1

                if line.type == 'conjoint':
                    if line.salari == 0:
                        value.ir += 1
                        value.trimf += 1
                    else:
                        value.ir += 0.5
                    value.marital = 'married'

            if value.contract_id:
                old_nbj_sup = value.contract_id.nbj_sup
                if nbj_sup > old_nbj_sup:
                    value.contract_id.write({'nbj_sup': nbj_sup})
                    # create leaves line allocation
                    self.env['hr.leave.allocation'].create({
                        'name': "Extra days Allowance",
                        'number_of_days': nbj_sup,
                        'state': 'validate',
                        'employee_id': value.id
                    })

            if value.ir >= 5:
                value.ir = 5
            if value.trimf >= 5:
                value.trimf = 5


class OptesisRelation(models.Model):
    _name = 'employee.worked.days'
    _description = "historique des jours travaillé par année"

    year = fields.Char('Année')
    worked_days = fields.Integer('Jours Travaillés')
    employee_id = fields.Many2one('hr.employee')