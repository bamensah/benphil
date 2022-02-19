# -*- coding: utf-8 -*-

from datetime import datetime
import json
import logging

import requests
from werkzeug import urls

from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError
from odoo.http import request


_logger = logging.getLogger(__name__)


#API_GATEWAY_TOKEN_ENDPOINT = "http://52.208.202.81/auth/login"
#API_GATEWAY_TOKEN_REFRESH_ENDPOINT = "http://52.208.202.81/auth/refresh"

class ApiGatewayService(models.TransientModel):
    _name = 'api.gateway.service'
    _description = 'API Gateway Service'

    # migrate v14 later ----------
    @api.model
    def _generate_access_token(self):
        """ Call API Gateway to generate a token
            :returns the access token
        """
        Parameters = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = Parameters.get_param('api_gateway_url')
        API_GATEWAY_TOKEN_ENDPOINT = API_GATEWAY_URL + "/auth/login"
        user = self.env['res.users'].browse(self.env.user.id).read(['login', 'password'])[0]
        username = user['login']
        password = user['password']

        # Get the Access Token From API Gateway And store it in ir.config_parameter
        headers = {"Content-type": "application/json"}
        data = {
            # 'username': username,
            # 'password': password
            'username': 'odoo',
            'password': 'n2@a{+Zb'
        }
        try:
            req = requests.post(API_GATEWAY_TOKEN_ENDPOINT, data=json.dumps(data), headers=headers)
            req.raise_for_status()
            content = req.json()
            Parameters.set_param('api_gateway_access_token', content.get('access_token'))
            Parameters.set_param('api_gateway_refresh_token', content.get('refresh_token'))

        except IOError:
            error_msg = _("Something went wrong during your token generation.")
            raise self.env['res.config.settings'].get_config_warning(error_msg)
    #
    #
    # @api.model
    def _refresh_api_gateway_token(self, refresh_token):
        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN_REFRESH_ENDPOINT = API_GATEWAY_URL + "/auth/refresh"
        refresh_token = params.get_param('api_gateway_refresh_token')

        headers = {
                "content-type": "application/json",
                'Authorization': "Bearer " + refresh_token
        }

        try:
            req = requests.post(API_GATEWAY_TOKEN_REFRESH_ENDPOINT, headers=headers)
            req.raise_for_status()
            content = req.json()
            params.set_param('api_gateway_access_token', content.get('access_token'))
        except IOError:
            error_msg = _("Something went wrong during your token refresh.")
            raise self.env['res.config.settings'].get_config_warning(error_msg)

        return content.get('access_token')
    # end ----------------------------