
# -*- coding: utf-8 -*-
# by khk
from odoo import models, fields, api, _
from datetime import datetime

class optesisDetailVersement(models.Model):
    _name = "optesis.detail.versement"
    _description = "optesis detail versement"

    name = fields.Selection([ 
        ('2018', '2018'),
        ('2019', '2019'),
        ('2020', '2020'),
        ('2021', '2021'),
        ('2022', '2022')],
        'Année ', required=True, #default=datetime.now().year
        )
    detail_versement_line = fields.One2many('optesis.detail.versement.line', 'detail_versement_id', string="DETAIL DES VERSEMENTS")
    company_id = fields.Many2one('res.company', 'Société', copy=False,
                                 default=lambda self: self.env.user.company_id)
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',  'You can not have two records with the same name !')
    ]


class optesisDetailVersementLine(models.Model):
    _name = "optesis.detail.versement.line"
    _description = 'optesis detail versement line'

    name = fields.Char('Salaire du mois de')
    montant_versement = fields.Float('Montant Versement', compute="_compute_versement_amount")
    date_versement = fields.Date('Date de versement')
    montant_ir = fields.Float('IR')
    montant_trimf = fields.Float('TRIMF')
    montant_cfce = fields.Float('CFCE')
    numero_quitance = fields.Char('Numéro quittance')
    observation = fields.Char('Observation')
    detail_versement_id = fields.Many2one('optesis.detail.versement')
    year = fields.Char(string="Year")

    # @api.multi
    def create(self, value):
        res = super(optesisDetailVersementLine, self).create(value)
        for line in res:
            line.year = line.detail_versement_id.name
        return res

    @api.depends('montant_ir', 'montant_cfce', 'montant_trimf')
    def _compute_versement_amount(self):
        for line in self:
            line.montant_versement = line.montant_ir + line.montant_trimf + line.montant_cfce
