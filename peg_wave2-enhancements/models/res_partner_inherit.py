from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.phone_validation.tools import phone_validation


import logging
_logger = logging.getLogger(__name__)

class ContactRelationship(models.Model):
    _name = "contact.relationship"
    _description = "Contact Relationship Types"
    _sql_constraints = [('name_unique', 'unique(name)', "This type of relationship already exists")]

    name = fields.Char(string="Relationship", required=True)

class PartnerContacts(models.Model):
    _name = "res.partner.contacts"
    _description = "Contacts for a partner"

    partner_id = fields.Many2one('res.partner', string='Contact', required=True)
    relationship_id = fields.Many2one('contact.relationship', string='Relationship')
    phone_number = fields.Char(string='Phone Number', required=True)
    name = fields.Char(string='Contact Name')

    def _phone_get_country(self):
        if 'country_id' in self.partner_id and self.partner_id.country_id:
            return self.partner_id.country_id
        return self.env.user.company_id.country_id

    def _phone_get_always_international(self):
        if 'company_id' in self.partner_id and self.partner_id.company_id:
            return self.partner_id.company_id.phone_international_format == 'prefix'
        return self.env.user.company_id.phone_international_format == 'prefix'

    def phone_format(self, number, country=None, company=None):
        country = country or self._phone_get_country()
        if not country:
            return number
        always_international = company.phone_international_format == 'prefix' if company else self._phone_get_always_international()
        return phone_validation.phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            always_international=always_international,
            raise_exception=False
        )

    @api.onchange('phone_number')
    def _onchange_phone_validation(self):
        if self.phone_number:
            self.phone_number = self.phone_format(self.phone_number).replace(" ","")

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    contacts = fields.One2many(string='Other Contact Details',
        comodel_name='res.partner.contacts', inverse_name='partner_id')
    
    manual_block = fields.Boolean(string='Manual Block', default=False)
    
    def block_customer(self):
        cs_blocked = self.env.ref('wave2_peg_africa.contract_status_blocked')
        for s in self:
            if s.client_status.id != cs_blocked.id or s.client_status == False or s.manual_block == False:
                s.manual_block = True
                payments = self.env['account.payment'].search([('partner_id.id','=',s.id), ('block_status','=', 'unblocked')])
                payments.write({'block_status':'blocked'})
    
        return True
    
    def unblock_customer(self):
        cs_blocked = self.env.ref('wave2_peg_africa.contract_status_blocked')
        cs_active = self.env.ref('wave2_peg_africa.contract_status_active')
        cs_written_off = self.env.ref('wave2_peg_africa.contract_status_written_off')
        for s in self:
            if s.client_status.id in (cs_blocked.id, cs_written_off.id) or s.manual_block == True:
                payments = self.env['account.payment'].search([('partner_id.id','=',s.id), ('block_status','=', 'blocked'), ('state','!=', 'cancel')])
                payments.write({'block_status':'unblocked'})
                no_withheld_payments = self.env['account.payment'].search([('partner_id.id','=',s.id), ('block_status','=', 'unblocked'), ('parent_payment_id', '=', False)])
                if s.client_status.id == cs_blocked.id:
                    s.client_status = cs_active.id
                s.manual_block = False
                for payment in no_withheld_payments:
                    payment.confirm_unblock()
    
        return True