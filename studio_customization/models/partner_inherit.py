from odoo import api, fields, models

class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    birthday = fields.Date('Birthday')
    genre = fields.Selection([("MALE", "MALE"), ("FEMALE", "FEMALE")], string='Genre')
    type_pice_didentit = fields.Selection([("Carte d'identité","Carte d'identité"),
                                           ("Passeport","Passeport"),
                                           ("Permis de conduite","Permis de conduite"),
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
                                           ("Carte D'Assurance","Carte D'Assurance"),
                                           ("Récépissé ONI","Récépissé ONI"),
                                           ("Certificat De Déclaration De Perte","Certificat De Déclaration De Perte"),
                                           ("Carte Etrangere","Carte Etrangere")], string='Type of ID')
    field_hXnbj = fields.Char('ID number')
    contract_id = fields.Char("Contract id")
    contract = fields.Boolean('Copy of contract')
    photo_of_id = fields.Boolean('Photo of ID')
    photo_of_place_to_install_panel = fields.Boolean('Photo of ID')
    after_sales_sc_suppor = fields.Many2one('crm.team', string='Service Center')
    number_for_mobile_payments = fields.Integer('Number for mobile payments')
    spoken_language = fields.Many2one('res.lang', string='Spoken language')
    refered_by = fields.Many2one('res.partner', string='Referred by')
    geolocation = fields.Char(string='geolocation')
    photo_of_customer = fields.Boolean('Photo of customer')
    photo_of_contract = fields.Boolean('Photo of contract')
    ninea = fields.Boolean('NINEA')

    screening_w3w = fields.Char(string="Screening W3W")
    post_installation_w3w = fields.Char(string="Post Installation W3W")
    w3w_validation = fields.Selection(string="W3W Validation",
                                      selection=[('validated', 'Validated'), ('not_validated', 'Not Validated'),
                                                 ('awaiting_document', 'Awaiting Document')])
    # type_of_product = fields.Many2many('res.partner.category', string='Type Of Product')
    contact_type = fields.Many2many(string='Contact Type', comodel_name='contact.type')

    is_customer = fields.Boolean(compute='_compute_customer_type', string='Is a Customer')
    is_vendor = fields.Boolean(compute='_compute_customer_type', string='Is a Vendor')

    def _compute_customer_type(self):
        # print('------self', self)
        # print('----self.customer_rank----', self.customer_rank)
        for s in self:
            if s.customer_rank == 1:
                s.write({
                    "is_customer": True
                })
            else:
                s.write({
                    "is_customer": False
                })
            if s.supplier_rank == 1:
                s.write({
                    "is_vendor": True
                })
            else:
                s.write({
                    "is_vendor": False
                })


