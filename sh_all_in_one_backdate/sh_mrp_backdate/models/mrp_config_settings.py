from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_backdate_for_mrp = fields.Boolean("Enable Backdate for MRP")
    remark_for_mrp_production = fields.Boolean("Enable Remark for MRP Production")
    remark_mandatory_for_mrp_production = fields.Boolean("Remark Mandatory for MRP Production")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_backdate_for_mrp = fields.Boolean("Enable Backdate for MRP",related="company_id.enable_backdate_for_mrp",readonly=False)
    remark_for_mrp_production = fields.Boolean("Enable Remark for MRP Production",related="company_id.remark_for_mrp_production",readonly = False)
    remark_mandatory_for_mrp_production = fields.Boolean("Remark Mandatory for MRP Production",related="company_id.remark_mandatory_for_mrp_production",readonly = False)
