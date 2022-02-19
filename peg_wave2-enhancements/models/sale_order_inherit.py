# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class sale_order_inherit(models.Model):
    _inherit = 'sale.order'
    
    account_number = fields.Char(string="Stored Account Number", store=True )
    
    origin = fields.Char(string='Account Number')
   
    @api.onchange('product_template_id')
    def onchange_product_template(self):
        for s in self:
            if s.product_template_id:
                s.payment_term_id = s.product_template_id.payment_term_id.id
                if s.product_template_id.type_of_product_id:
                    s.type_of_product_id = s.product_template_id.type_of_product_id.id
                    
                    
    @api.onchange('user_id')
    def onchange_salesperson_set_team(self):
        for s in self:
            if s.user_id:
                salesperson_team = self.env['crm.team'].search([
                    ('member_ids', 'in', s.user_id.id)
                    ], limit=1)
                
                s.team_id = salesperson_team.id