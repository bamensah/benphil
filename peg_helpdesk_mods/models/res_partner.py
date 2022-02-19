from odoo import models, fields, api
import logging
import datetime
_logger = logging.getLogger(__name__)


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    
    ticket_interaction_ids = fields.One2many(
        string='Ticket Interactions',
        comodel_name='helpdesk.ticket.interaction',
        inverse_name='partner_id'
    )