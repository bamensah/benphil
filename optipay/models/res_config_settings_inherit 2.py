from odoo import models, fields

class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    nbj_alloue = fields.Float(related='company_id.nbj_alloue',string="Nombre de jour alloue", default="2.0", readonly=False)
    nbj_travail = fields.Float(related='company_id.nbj_travail', string="Nombre de jour de travail", default="30", readonly=False)