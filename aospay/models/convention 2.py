# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AosCovention(models.Model):
    _name = "aos.convention"
    _description = "convention collective"

    name = fields.Char('Nom convention')
    line_ids = fields.One2many('line.aos.convention','conv_id', string='Ligne de convention')

class LineAosConvention(models.Model):
    _name = "line.aos.convention"
    _description = "Ligne de conventions collective"

    name = fields.Char(string='Catégorie', required=True, copy=False, index=True)
    salaire = fields.Float('Salaire de Base Majoré')
    indd = fields.Float(string='Indemnité de deplacement')
    inds73 = fields.Float('Indemnité Spécial de 73')
    inds91 = fields.Float('Indemnité Solidarité 1991')
    pcvie = fields.Float('Prime de Cherte de vie')
    presp = fields.Float('Prime de Responsabilité')
    conv_id = fields.Many2one('aos.convention',string ="Convention")
    
    
