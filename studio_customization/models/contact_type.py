from odoo import api, fields, models


class ContactType(models.Model):
    _name = 'contact.type'

    name = fields.Char('Name')
