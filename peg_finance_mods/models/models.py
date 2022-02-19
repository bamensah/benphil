# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountDepartmentMapping(models.Model):
    _name = 'account.department_mapping'
    _description = 'Table to store department mapping for report building'

    name = fields.Char(string='Name')
    shortname = fields.Char(string='Shortname')
    groupname = fields.Char(string='Analytical Account Group Name')
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.user.company_id
    )


class AccountAccountMapping(models.Model):
    _name = 'account.account_mapping'
    _description = 'Table to store account mapping for report building'

    odoo_account = fields.Integer(string='Odoo Account')
    description = fields.Char(string='Description')
    department = fields.Char(string='Department')
    department_name = fields.Char(string='Department Name')
    account_department = fields.Char(string='Account & Department Combo')
    pl_level1 = fields.Char(string='P&L Level 1')
    pl_level2 = fields.Char(string='P&L Level 2')
    pl_level3 = fields.Char(string='P&L Level 3')
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.user.company_id
    )