# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class Site(models.Model):
    _name = "optesis.site"
    _description = "optesis site"
    _sql_constraints = [('name_unique', 'unique(name)', "ce site existe déja")]

    name = fields.Char(string="Site", required=True, size=50)
    address = fields.Char(string="Addresse")
    region = fields.Char(string="Région")
    locality = fields.Char(string="Localité")
    description = fields.Text(string="description")
    
    
class Level(models.Model):
    _name = "optesis.level"
    _description = "optesis level"

    name = fields.Char(string="Level", required=True, size=50)
    description = fields.Text(string="description")
    site_id = fields.Many2one(comodel_name="optesis.site", string="Site", required=True)
    
    
class Room(models.Model):
    _name = "optesis.room"
    _description = "optesis room"

    name = fields.Char(string="Room", required=True, size=50)
    description = fields.Text(string="description")
    level_id = fields.Many2one(comodel_name="optesis.level", string="Level", required=True)
    site_id = fields.Many2one(comodel_name="optesis.site", string="Site", required=True)
    
    @api.onchange('site_id')
    def onchange_level_id(self):
        return {'domain': {'level_id': [('site_id', '=', self.site_id.id)]}}