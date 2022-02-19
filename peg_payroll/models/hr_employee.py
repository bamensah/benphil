# -*- coding: utf-8 -*-

from odoo import models, fields, api

class hr_employee_inherited(models.Model):
    _inherit = 'hr.employee'

    shares = fields.Float(string='Number of Shares', default=1, help='Shares used in CI calculate of General Tax', compute='_compute_shares', store=True)
    part_case_a = fields.Boolean(string='Particular Case A', help='Without dependent children as a worker with Children of Maturity Age, Deceased children or Allowance of 40% at least for war or work disability')
    part_case_b = fields.Boolean(string='Particular Case B', help='Married Woman taxed independently from the chief of family')
    has_independent_children_only = fields.Boolean(string='Has Independent Children Only')
    ci_employee = fields.Boolean(compute='_ci_employee')
    
    @api.depends('company_id')
    def _ci_employee(self):
        for rec in self:
            if rec.company_id.name == "PEG Côte d'Ivoire":
                rec.ci_employee = True
            else:
                rec.ci_employee = False

    @api.depends('marital','children')
    def _compute_shares(self):
        for rec in self:
            total_shares = 0
            has_children = rec.children > 0
            if rec.marital == 'single' or rec.marital == 'divorced':
                if has_children:
                    total_shares = 1.5 + (0.5 * rec.children)
                else:
                    if rec.part_case_a:
                        total_shares = 1.5
                    else:
                        total_shares = 1
                        
            elif rec.marital == 'windower':
                if rec.has_independent_children_only:
                    if rec.part_case_b:
                        total_shares = 1
                    else:
                        total_shares = 2
                else:
                    if has_children:
                        total_shares = 2 + (0.5 * rec.children)
                    else:
                        if rec.part_case_a:
                            total_shares = 1.5
                        else:
                            total_shares = 1
            
            elif rec.marital == 'married':
                if has_children:
                    total_shares = 2 + (0.5 * rec.children)
                else:
                    if rec.part_case_b:
                            total_shares = 1
                    else:
                        total_shares = 2
        
        rec.shares = total_shares
