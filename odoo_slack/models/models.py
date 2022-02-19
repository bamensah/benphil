# -*- coding: utf-8 -*-
import requests

from odoo import models, fields, api
from odoo.http import json, logging
from odoo.exceptions import Warning

# Initializing, the _logger object makes sure that the name of this file
# is carried along with the log messages.
_logger = logging.getLogger(__name__)

class OdooSlack(models.Model):
    _name = "odoo.slack"     
    name = fields.Char(string="Name", required=True)    
    description = fields.Text("Description")
    
    def slackup(self, slack_url, message):
        
        # Since this is just an extra module, most exceptions have to be handled
        # to enable other actions that may be in the pipeline to proceed
        error_msg = "Slack Notification won't be sent: "
        payload = {'text': message, 'icon_emoji': ':inbox_tray:'}
        try:
            req = requests.post(
                slack_url, data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            # Invalid slack URL will return 403 Error: Forbidden Client
            if req.status_code==403 :
                raise Warning(error_msg + "the Slack url is forbidden")
        except Exception:
            _logger.warning(Exception)
            
            
        