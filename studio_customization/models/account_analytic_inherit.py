from odoo import api, fields, models


class AccountAnalyticAccountInherit(models.Model):
    _inherit = 'account.analytic.account'

    type = fields.Selection([("Normal", "Normal"), ("Vue", "Vue")])
    field_7poS3 = fields.Many2one('res.country', string='Pays')
    pays = fields.Selection([
        ("Sénégal", "Sénégal"),
        ("Cote_d'ivoire", "Cote d'ivoire"),
        ("Ghana", "Ghana"),
        ("Maurice", "Maurice"),
        ("Mali", "Mali"),
        ("PEG Africa", "PEG Africa")], sting='Pays')


class AccountAnalyticLineInherit(models.Model):
    _inherit = 'account.analytic.line'

    dpartement = fields.Many2one('account.analytic.account', string='Département')


