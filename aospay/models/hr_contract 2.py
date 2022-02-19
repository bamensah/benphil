import time
from datetime import datetime, date, time as t
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class HrContractCC(models.Model):
    _inherit = 'hr.contract'

    cat = fields.Many2one('line.aos.convention', 'Categorie')
    conv_id = fields.Many2one('aos.convention', string="Convention")
    indd = fields.Float(string='Indemnité de deplacement')
    inds73 = fields.Float('Indemnité Spécial de 73')
    inds91 = fields.Float('Indemnité Solidarité 1991')
    pcvie = fields.Float('Prime de Cherte de vie')
    presp = fields.Float('Prime de Responsabilité')
    sursal = fields.Float(string="Sur salaire")
    #salnet=fields.Float(string="Salaire Net")
    
#    @api.multi    
    @api.onchange('company_id')
    def onchange_employee(self):
        self.conv_id = self.company_id.conv
        
#    @api.multi
    @api.onchange('cat')
    def onchange_cat(self):
        self.wage = self.cat.salaire
        self.indd = self.cat.indd
        self.inds73 = self.cat.inds73
        self.inds91 = self.cat.inds91
        self.pcvie = self.cat.pcvie
        self.presp = self.cat.presp
        
    #@api.multi
    #@api.onchange('salnet')
    #def onchange_net(self):
        
        
    
