from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    backdate_for_purchase_order = fields.Boolean("Enable Backdate for Purchase Order")
    remark_for_purchase_order = fields.Boolean("Enable Remark for Purchase Order")
    remark_mandatory_for_purchase_order = fields.Boolean("Remark Mandatory for Purchase Order")
    backdate_for_bill = fields.Boolean("Bill has Same Backdate")
    backdate_for_stock_move = fields.Boolean("Receipts has Same Backdate ")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    backdate_for_purchase_order = fields.Boolean("Enable Backdate for Purchase Order",related="company_id.backdate_for_purchase_order",readonly = False)
    remark_for_purchase_order = fields.Boolean("Enable Remark for Purchase Order",related="company_id.remark_for_purchase_order",readonly = False)
    remark_mandatory_for_purchase_order = fields.Boolean("Remark Mandatory for Purchase Order",related="company_id.remark_mandatory_for_purchase_order",readonly = False)
    backdate_for_bill = fields.Boolean("Bill has Same Backdate",related="company_id.backdate_for_bill",readonly = False)
    backdate_for_stock_move = fields.Boolean("Receipts has Same Backdate ",related="company_id.backdate_for_stock_move",readonly = False)