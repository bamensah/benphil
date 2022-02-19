from odoo import api, fields, models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    field_AVLMt = fields.Many2one('res.users', string='Utilisateurs')
    payment_recovery_agent = fields.Many2one('res.partner', string='Payment recovery agent')
    field_vguST = fields.Many2one('res.partner', string='Contact')
    technician = fields.Many2one('res.partner', string='Technician')

