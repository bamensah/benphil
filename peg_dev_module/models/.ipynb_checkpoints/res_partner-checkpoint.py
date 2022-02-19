from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.tools import email_split
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

# def extract_email(email):
#     """ extract the email address from a user-friendly email address """
#     addresses = email_split(email)
#     return addresses[0] if addresses else ''
#
# class ContactType(models.Model):
#     _name = "contact.type"
#
#     name = fields.Char(string='Tag Name', required=True)
#
# def is_dsr(res, self):
#     contact_type_selected = res.contact_type.ids
#     # List of contact types to create users for
#     c_users = ['ABM/SFM', 'DSR', 'RBM']
#
#     dsr_id = self.sudo().env['contact.type'].search([('name', 'in', c_users)])
#     _logger.info(dsr_id)
#     if dsr_id:
#         _logger.info(list(map(lambda d: d.id, dsr_id)))
#         if bool(set(list(map(lambda d: d.id, dsr_id))).intersection(contact_type_selected)):
#             return True
#         else:
#             return False
#     else:
#         return False

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    contact_type = fields.Many2many(
        string='Contact Type',
        comodel_name='contact.type')


    @api.model
    def create(self, values):
        res = super(ResPartnerInherit, self).create(values)
        # here you can do accordingly

        if is_dsr(res, self):
            group_portal = self.env.ref('base.group_portal')
            _logger.info(res.email)
            new_email = 'user@' + str(res.id) if res.email == False or res.email is None else res.email
            
            self.sudo().env['res.users'].with_context(no_reset_password=True).create({
                'email': extract_email(new_email),
                'login': extract_email(new_email),
                'partner_id': res.id,
                'company_id': res.company_id.id,
                'company_ids': [(6, 0, [res.company_id.id])],
                'groups_id': [(4, group_portal.id)],
                'active': True
            })

        return res
 
