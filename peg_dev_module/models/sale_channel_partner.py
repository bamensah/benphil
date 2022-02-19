from odoo import models, fields


class SaleChannelPartner(models.Model):
    _name = "sale.channel.partner"
    _description = 'Sale Channel Partner'
    
    name = fields.Char(string="Partner Name")
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id)