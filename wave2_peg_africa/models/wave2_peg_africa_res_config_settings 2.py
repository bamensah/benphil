# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    api_gateway_access_token = fields.Char(string='API Gateway Access Token', config_parameter='api_gateway_access_token')
    api_gateway_refresh_token = fields.Char(string='API Gateway Refresh Token', config_parameter='api_gateway_refresh_token')
    #Add village and lead generator fields in system parameter
    peg_village = fields.Integer(String='Village', config_parameter='peg_village')
    peg_lead_generator = fields.Integer(String='lead generator', config_parameter='peg_lead_generator')

    def refresh_token(self):
        params = self.env['ir.config_parameter'].sudo()
        refresh_token = params.get_param('api_gateway_refresh_token')
        new_access_token = self.env['api.gateway.service']._refresh_api_gateway_token(refresh_token)
        params.set_param('api_gateway_access_token', new_access_token)

    def get_access_token(self):
        self.env['api.gateway.service']._generate_access_token()