from odoo import fields, models, api


class LivreDePaie(models.Model):
    _name = 'hr.payslip.book'
    _description = 'Livre de Paie'

    name = fields.Char('Reference')
    line_ids = fields.One2many("hr.payslip.book.line", "book_id", string="Lignes du livre")
    slip_batch = fields.Many2one('hr.payslip.run', string="lot", required="True")
    date_from = fields.Date(related='slip_batch.date_start')
    date_to = fields.Date(related='slip_batch.date_end')

#    @api.multi
    def create_fields(self):
        rules = self.env['hr.salary.rule'].search([('appears_on_book', '=', True)])
        champs = self.env['ir.model.fields'].search([('model', '=', 'hr.payslip.book.line')])
        modele = self.env['ir.model'].search([('model', '=', 'hr.payslip.book.line')])

        for rule in rules:
            field_name = 'x_' + rule.code
            if field_name not in champs.mapped("name"):
                self.env['ir.model.fields'].sudo().create({
                    'name': field_name,
                    'field_description': rule.name,
                    'model_id': modele.id,
                    'model': 'hr.payslip.book.line',
                    'ttype': 'float',
                })


#    @api.multi
    def generate_lines(self):
        for book in self:
            if book.line_ids:
                book.line_ids.unlink()
            for slip in book.slip_batch.slip_ids:
                line = self.env['hr.payslip.book.line'].create({
                    'employee_id': slip.employee_id.id,
                    'slip_id': slip.id,
                    'book_id': book.id})
                for rule in self.env['hr.salary.rule'].search([('appears_on_book', '=', True)]):
                    field_name = 'x_' + rule.code
                    if field_name in line:
                        line[field_name] = slip.line_ids.filtered(lambda l: l.code == rule.code).total
                    else:
                        modele = self.env['ir.model'].search([('model', '=', 'hr.payslip.book.line')])
                        self.env['ir.model.fields'].sudo().create({
                            'name': field_name,
                            'field_description': rule.name,
                            'model_id': modele.id,
                            'model': 'hr.payslip.book.line',
                            'ttype': 'float',
                        })
                        line[field_name] = slip.line_ids.filtered(lambda l: l.code == rule.code).total


class LigneLivreDePaie(models.Model):
    _name = 'hr.payslip.book.line'
    _description = 'Ligne de Livre de paie'

    employee_id = fields.Many2one("hr.employee", string="Employé")
    book_id = fields.Many2one("hr.payslip.book", string="Livre de Paie")
    slip_id = fields.Many2one("hr.payslip", string="Fiche de Paie")
    date_from = fields.Date(related='slip_id.date_from')
    date_to = fields.Date(related='slip_id.date_to')
    numero = fields.Char(related="employee_id.mobile_phone")
    matricule = fields.Char(related="employee_id.matricule")
    nom = fields.Char(related="employee_id.name")
    prenom = fields.Char()

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    appears_on_book = fields.Boolean("Apparait sur le livre de paie")
