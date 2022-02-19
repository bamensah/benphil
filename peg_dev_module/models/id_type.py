from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class id_type (models.Model):
    _description = 'ID Types of Contacts'
    _name = 'id.type'

    name = fields.Char(string='Name', translate=True)

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.user.company_id,
        # visible=False,
        readonly=True
    )
