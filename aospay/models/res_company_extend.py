from odoo import models, fields

class ResCompanyExtend(models.Model):
    _inherit = "res.company"

    conv=fields.Many2one('aos.convention',string="Convention collective")
    immat=fields.Char(string="Immatriculation sociale")
    #sigle = fields.Char(string="Sigle", help="Pour les sociétés")
    #profession = fields.Char(string="Profession")
    #localite = fields.Char(string="Localité")
    #nom_adress_comptable = fields.Char("Nom et adresse du comptable")
    #nbj_alloue = fields.Float(string="Nombre de jour alloue", default="2.0")
    #nbj_travail = fields.Float(string="Nombre de jour de travail", default="30")
    #taccident_travail = fields.Float("Taux Accident du travail")
    #prestation_fam = fields.Float("Taux Prestation Familiale")
