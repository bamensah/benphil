from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    backdate_for_sale_order = fields.Boolean("Enable Backdate for Sale Order")
    remark_for_sale_order = fields.Boolean("Enable Remark for Sale Order")
    remark_mandatory_for_sale_order = fields.Boolean("Remark Mandatory for Sale Order")
    backdate_for_invoice = fields.Boolean("Invoice has Same Backdate")
    backdate_for_stock_move = fields.Boolean("Delivery Order has Same Backdate ")



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    backdate_for_sale_order = fields.Boolean("Enable Backdate for Sale Order",related="company_id.backdate_for_sale_order",readonly = False)
    remark_for_sale_order = fields.Boolean("Enable Remark for Sale Order",related="company_id.remark_for_sale_order",readonly = False)
    remark_mandatory_for_sale_order = fields.Boolean("Remark Mandatory for Sale Order",related="company_id.remark_mandatory_for_sale_order",readonly = False)
    backdate_for_invoice = fields.Boolean("Invoice has Same Backdate",related="company_id.backdate_for_invoice",readonly = False)
    backdate_for_stock_move = fields.Boolean("Delivery Order has Same Backdate ",related="company_id.backdate_for_stock_move",readonly = False)