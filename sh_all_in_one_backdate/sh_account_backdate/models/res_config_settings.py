from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_backdate_for_move = fields.Boolean("Enable Backdate for Invoice")
    remark_for_move = fields.Boolean("Enable Remark for Invoice")
    remark_mandatory_move = fields.Boolean("Remark Mandatory for Invoice")

    enable_backdate_for_payment = fields.Boolean("Enable Backdate for Payment")
    remark_for_payment = fields.Boolean("Enable Remark for Payment")
    remark_mandatory_payment = fields.Boolean("Remark Mandatory for Payment")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_backdate_for_move = fields.Boolean("Enable Backdate for Invoice",related="company_id.enable_backdate_for_move",readonly=False)
    remark_for_move = fields.Boolean("Enable Remark for Invoice",related="company_id.remark_for_move",readonly = False)
    remark_mandatory_move = fields.Boolean("Remark Mandatory for Invoice",related="company_id.remark_mandatory_move",readonly = False)

    enable_backdate_for_payment = fields.Boolean("Enable Backdate for Payment",related="company_id.enable_backdate_for_payment",readonly=False)
    remark_for_payment = fields.Boolean("Enable Remark for Payment",related="company_id.remark_for_payment",readonly = False)
    remark_mandatory_payment = fields.Boolean("Remark Mandatory for Payment",related="company_id.remark_mandatory_payment",readonly = False)
