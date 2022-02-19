from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.tools import email_split
from odoo.exceptions import UserError, ValidationError

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

import phonenumbers
import logging
import re
_logger = logging.getLogger(__name__)

# needs to open

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()
#
def extract_email(email):
    """ extract the email address from a user-friendly email address """
    addresses = email_split(email)
    return addresses[0] if addresses else ''
#


class ContactType(models.Model):
    _description = "Contact Type for Contacts (Customer, DSR, etc)"
    _name = "contact.type"

    name = fields.Char(string='Tag Name', required=True)
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.user.company_id
    )
    

def is_dsr(res, self):
    contact_type_selected = res.contact_type.ids
    # List of contact types to create users for
    c_users = ['ABM/SFM', 'DSR', 'RBM']

    dsr_id = self.sudo().env['contact.type'].search([('name', 'in', c_users)])
    _logger.info(dsr_id)
    if dsr_id:
        _logger.info(list(map(lambda d: d.id, dsr_id)))
        if bool(set(list(map(lambda d: d.id, dsr_id))).intersection(contact_type_selected)):
            return True
        else:
            return False
    else:
        return False


class ContactDistrict(models.Model):
    _description = "Coordinates for Towns/Districts of Customers"
    _name = "contact.district"

    name = fields.Char(string='District', required=True)
    name2 = fields.Char(string='Town')
    region = fields.Many2one('contact.region', 'Region')
    longitude = fields.Float(string='Longitude', digits=(12, 6))
    latitude = fields.Float(string='Latitude', digits=(12, 6))
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.user.company_id
    )


class ContactRegion(models.Model):
    _description = "Regions for Contact Districts"
    _name = "contact.region"

    name = fields.Char(string='Region', required=True)
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.user.company_id
    )
    
    ref = fields.Char(
        string='Old Customer ID',
        index=True
    )


class ResPartnerInherit(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'phone.validation.mixin']

    @api.model
    def _default_lang(self):
        if self.env.user.company_id:
            return self.env.user.company_id.partner_id.lang
        else:
            return None

    contact_type = fields.Many2many(string='Contact Type', comodel_name='contact.type')
    mobile_payment_number = fields.Char(string='Number for Mobile Payments')
    lang = fields.Selection(_lang_get, string='Language', default=_default_lang, help="All the emails and documents sent to this contact will be translated in this language.", required=True)
    id_type_id = fields.Many2one(string='ID Type', comodel_name='id.type')
    
    screening_w3w = fields.Char(string="Screening W3W")
    post_installation_w3w = fields.Char(string="Post Installation W3W")
    w3w_validation = fields.Selection(string="W3W Validation", selection=[('validated', 'Validated'), ('not_validated', 'Not Validated'), ('awaiting_document', 'Awaiting Document')])


    # needs to open

    # Modify to add more languages
    @api.constrains('lang')
    def _only_en_fr(self):
        for s in self:
            if s.lang not in ('en_US', 'fr_FR'):
                    raise ValidationError('Only English and French are allowed as a valid language')
    #
    @api.constrains('id_number')
    def _duplicate_id_number(self):
        for s in self:
            if s.ignore_duplicates == False:
                if s.id_number and s.id_type:
                    result = self.env['res.partner'].search(['&',('id_number','=',s.id_number),('id_type', '=', s.id_type)])
                    _logger.info(result)
                    if len(result) > 1:
                        raise ValidationError('Duplicate Identification Number found {}'.format(str(result)))

    # needs to open

    @api.constrains('phone', 'mobile')
    def _duplicate_phone_numbers(self):
        for s in self:
            if s.ignore_duplicates == False:
                mobile_result = None
                phone_result = None
                momo_result = None
                msg = ''
                if s.phone:
                    phone_result = self.env['res.partner'].search(['|', '|', ('phone','=',s.phone), ('mobile', '=', s.phone), ('mobile_payment_number','=', s.phone)])
                    _logger.info(phone_result)
                    if len(phone_result) > 1:
                         msg = msg + 'Duplicate Phone number found {}'.format(str(phone_result))
                if s.mobile:
                    mobile_result = self.env['res.partner'].search(['|', '|', ('phone','=',s.mobile), ('mobile', '=', s.mobile), ('mobile_payment_number','=', s.mobile)])
                    if len(mobile_result) > 1:
                        msg = msg + 'Duplicate Mobile number found {}'.format(str(mobile_result))
                if s.mobile_payment_number:
                    momo_result = self.env['res.partner'].search(['|', '|', ('phone','=',s.mobile_payment_number), ('mobile', '=', s.mobile_payment_number), ('mobile_payment_number','=', s.mobile_payment_number)])
                    if len(momo_result) > 1:
                        msg = msg + 'Duplicate Phone number found {}'.format(str(momo_result))
                if msg != '':
                    raise ValidationError(msg)
    #

    # needs to open

    @api.onchange('mobile_payment_number')
    def _onchange_mobile_money(self):
        if self.mobile_payment_number and self.mobile_payment_number != '':
            try:
                original_num = phonenumbers.parse(self.mobile_payment_number)
                format = phonenumbers.PhoneNumberFormat.INTERNATIONAL
                self.mobile_payment_number = phonenumbers.format_number(
                    original_num, format)
            except Exception as e:
                raise ValidationError(str(e))

    location_description = fields.Text(string='Location Description')
    contact_district = fields.Many2one(
        string='Town/District',
        comodel_name='contact.district'
    )
    gender = fields.Selection(
        string='Gender',
        selection=[('male', 'Male'), ('female', 'Female')]
    )

    marital_status = fields.Selection(
        string='Marital Status',
        selection=[('single', 'Single'), ('married', 'Married'),
                   ('undisclosed', 'Undisclosed (Will not tell)')]
    )

    number_of_dependents = fields.Integer(
        string='Number of Dependents'
    )

    primary_occupation_id = fields.Many2one(
        string='Primary Occupation',
        comodel_name='contact.occupation'
    )

    secondary_occupation_id = fields.Many2one(
        string='Secondary Occupation',
        comodel_name='contact.occupation'
    )

    education_level_id = fields.Many2one(
        string='Education Level',
        comodel_name='contact.education_level',
        ondelete='restrict'
    )

    crop_id = fields.Many2one(
        string='Crops',
        comodel_name='contact.crop',
        ondelete='restrict'
    )

    livestock_id = fields.Many2one(
        string='Livestock',
        comodel_name='contact.livestock',
        ondelete='restrict'
    )

    agric_occupation = fields.Boolean(
        readonly=True,
        compute='_compute_agric_selected',
        default=False
    )

    id_type = fields.Selection(string='ID Type', selection=[
        ("Carte d'identité","Carte d'identité"),
        ("Attestation D’Identité","Attestation D’Identité"),
        ("Extrait De Naissance","Extrait De Naissance"),
        ("Carte Cedeao","Carte Cedeao"),
        ("Carte Consulaire","Carte Consulaire"),
        ("Carte Professionnelle","Carte Professionnelle"),
        ("Jugement Supplétif","Jugement Supplétif"),
        ("Carte Électorale","Carte Électorale"),
        ("Carte D’Étudiant","Carte D’Étudiant"),
        ("Carte Pastorale","Carte Pastorale"),
        ("Carte Séjour","Carte Séjour"),
        ("Carte Sociale","Carte Sociale"),
        ("Carte Militaire","Carte Militaire"),
        ("Carte Scolaire","Carte Scolaire"),
        ("Carte ONG","Carte ONG"),
        ("Carte De Refugie","Carte De Refugie"),
        ("Carte De Pension","Carte De Pension"),
        ("Carte DAssurance","Carte D'Assurance"),
        ("Récépissé ONI","Récépissé ONI"),
        ("Certificat De Déclaration De Perte","Certificat De Déclaration De Perte"),
        ("Carte Etrangere","Carte Etrangere"),
        ("Carte De Pension","Carte De Pension")
    ], translate=True)

    id_number = fields.Char(string='ID Number', translate=True)

    ignore_duplicates = fields.Boolean(string='Ignore Duplicates', default=False)

    # needs to open

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self.phone_format(self.phone).replace(" ","")

    @api.depends('primary_occupation_id', 'secondary_occupation_id')
    def _compute_agric_selected(self):
        for s in self:
            if s.primary_occupation_id and s.secondary_occupation_id:
                if 'agric' in (s.primary_occupation_id.name.lower() + s.secondary_occupation_id.name.lower()) \
                        or 'farm' in (s.primary_occupation_id.name.lower() + s.secondary_occupation_id.name.lower()):
                    s.agric_occupation = True
                else:
                    s.agric_occupation = False
            else:
                s.agric_occupation = False

    @api.constrains('mobile_payment_number')
    def _check_phonenumber(self):
        if self.mobile_payment_number:
            original_num = phonenumbers.parse(self.mobile_payment_number)
            if not phonenumbers.is_possible_number(original_num):
                raise ValidationError("Phone number format is not valid")

    @api.model
    def create(self, vals):
        res = super(ResPartnerInherit, self).create(vals)
        # here you can do accordingly
    
        if is_dsr(res, self):
            group_portal = self.env.ref('base.group_portal')
            _logger.info(res.email)
            new_email = 'user@' + \
                str(res.id) if res.email == False or res.email is None else res.email
    
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

    manual_withhold_rate = fields.Float(string='Manual Withhold Rate', default=-1)
    computed_withhold_rate = fields.Float(compute='_compute_withhold_rate')

    # Function to return the arrears and age of arrears (in days)
    def get_arrears(self):
        arrears = []
        for s in self:
            today = fields.Date.today()
            # Fetch account holding debt
            client_account = s.property_account_receivable_id

            # Get the sale orders/valid non-written off loans
#            sale_orders = self.env['sale.order'].search([('partner_id', '=', s.id),
#                                                         ('contract_status', '!=', 'written_off')
#                                                         ], order='create_date asc')
#            W2E-545 modify condition for fetching sale orders to calculate arrears
#            sale_orders = self.env['sale.order'].search([('partner_id', '=', s.id),
#                                                         ('contract_status', '!=', 'written_off'),
#                                                         '|', ('state', '!=', 'cancel'), ('state', '!=', 'draft')
#                                                         ], order='create_date asc')
#            W2E-552 improve withheld payment mno ref
            sale_orders = self.env['sale.order'].search([('partner_id', '=', s.id),
                                                         ('contract_status', '!=', 'written_off'),
                                                         ('state', '!=', 'cancel'),
                                                         ('state', '!=', 'draft'),
                                                         ('paygops_id', '!=', None)], order='create_date asc')



            # For each sale, get the current arrears for Journal Items in
            for sale in sale_orders:
                lines = self.env['account.move.line'].search([('partner_id', '=', s.id), ('account_id', '=', client_account.id),
                                                              ('move_id.invoice_origin', '=', sale.name)
                                                              #('invoice_id.origin', '=', sale.name)
                                                              ])

                total_amount_overdue = 0
                total_amount_paid = 0
                overdue_age = 0

                # Get payment term and calc the days by daily rate
                term = sale.payment_term_id

                if term.rate_type:
                    rate_type = term.rate_type.name
                    rate = 0
                    if rate_type.lower() == 'daily':
                        rate = term.rate_amount
                    elif rate_type.lower() == 'weekly':
                        rate = term.rate_amount/7
                    elif rate_type.lower() == 'monthly':
                        rate = term.rate_amount/30

                    # credit_overdue_age = today - sale.create_date.date()
                    if rate != 0:
                        credit_overdue_age = sale.arrears/rate

                        # Get overdue amounts
                        for line in lines:
                            is_overdue = today > line.date_maturity if line.date_maturity else today > line.date
                            age = today - line.date_maturity
                            is_payment = line.payment_id
                            if is_overdue:
                                total_amount_overdue += line.debit
                                if (age.days > overdue_age):
                                    overdue_age = age.days
                            if is_payment:
                                total_amount_paid += line.credit

                        net_overdue = total_amount_overdue - total_amount_paid

                        arrears.append({'partner_id' : s.id, 'sale_order_id': sale.id, 'arrears': 0 if net_overdue < 0 else net_overdue, 'age': overdue_age, 'credit_arrears': sale.arrears, 'credit_age': credit_overdue_age})
            _logger.info(arrears)
        return arrears

    @api.depends('manual_withhold_rate')
    def _compute_withhold_rate(self):
        for s in self:
            if s.manual_withhold_rate and s.manual_withhold_rate >= 0:
                s.computed_withhold_rate = s.manual_withhold_rate
                return s.computed_withhold_rate
            else:
                arrears = list(s.get_arrears())
                # Global Withholding Rates
                gwr = self.env['account.withhold.payment.rate'].search([])
                arrear_age = 0
                oldest_arrear = None
                oldest_arr = []
                selected_rate = 0
                # Check Arrears with Oldest first (excluding current Sale Order)
                if any(arrears):
                    arrears = list(filter(lambda x: x['credit_arrears'] > 0, arrears))
                    if any(arrears):
                        oldest_arrear = max(arrears, key=lambda x: x['credit_age'])
                        arrear_age = oldest_arrear['credit_age']
                        oldest_arr.append(oldest_arrear)
                else:
                    s.computed_withhold_rate = 0
                    return s.computed_withhold_rate

                # Compute the rate if oldest arrear is determined
                if oldest_arrear:
                    for r in gwr:
                        if (arrear_age >= r.days_lower_limit and arrear_age <= r.days_upper_limit):
                            s.computed_withhold_rate = r.rate
                            return s.computed_withhold_rate

                s.computed_withhold_rate = 0
                return s.computed_withhold_rate


class PartnerOccupation(models.Model):
    _name = 'contact.occupation'
    _description = 'Partner Occupations'

    name = fields.Char(
        string='Name',
        required=True
    )


class PartnerCrop(models.Model):
    _name = 'contact.crop'
    _description = 'Partner Crops'

    name = fields.Char(
        string='Name',
        required=True
    )


class PartnerLivestock(models.Model):
    _name = 'contact.livestock'
    _description = 'Partner Livestock'

    name = fields.Char(
        string='Name',
        required=True
    )


class PartnerEducationLevel(models.Model):
    _name = 'contact.education_level'
    _description = 'Partner Education Levels'

    name = fields.Char(
        string='Name',
        required=True
    )


class PartnerWithholdPaymentRateWizard(models.TransientModel):
    _name = 'set.withhold_payment_rate.wizard'
    _description = 'Partner Withhold Payment Rate Selection Wizard'

    rate = fields.Selection(
        string='Rate',
        selection=[('-1', "None"),
                   ('0', '0'),
                   ('5', '5'),
                   ('10', '10'),
                   ('15', '15'),
                   ('20', '20'),
                   ('25', '25'),
                   ('30', '30'),
                   ('35', '35'),
                   ('40', '40'),
                   ('45', '45'),
                   ('50', '50'),
                   ('55', '55'),
                   ('60', '60'),
                   ('65', '65'),
                   ('70', '70'),
                   ('75', '75'),
                   ('80', '80'),
                   ('85', '85'),
                   ('90', '90'),
                   ('95', '95')]
    )

    def save_rate(self):
        if self.env.user.has_group('__export__.res_groups_108_1e0506ee') or self.env.user.has_group('wave2_peg_africa.group_credit_team'):
            clients = self.env['res.partner'].browse(
            self._context.get('active_ids', []))
            clients.write({'manual_withhold_rate' : self.rate})
        else:
            raise UserError("You do not have access to trigger this action - Credit Director or Credit Team access required")

        return clients

