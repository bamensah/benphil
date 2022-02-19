# -*- coding: utf-8 -*-
from odoo import models, fields

class OptesisCovention(models.Model):
    _name = "optesis.convention"
    _description = "convention collective"

    name = fields.Char('Nom convention')
    line_ids = fields.One2many('line.optesis.convention','conv_id','Ligne de convention')

class LineOptesisConvention(models.Model):
    _name = "line.optesis.convention"
    _description = "Ligne de conventions collective"

    name = fields.Char('Libelle')
    code = fields.Char('Code Grille')
    taux_h = fields.Float('Taux horaire')
    wage = fields.Float('Salaire brut')
    conv_id = fields.Many2one('optesis.convention')
