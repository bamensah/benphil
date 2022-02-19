import time, math
from datetime import datetime, date, time as t
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class HrContractBonus(models.Model):
    _inherit = 'hr.contract'

    # @api.onchange('bonus.amount')
    # def get_bonus_amount(self):
    #     current_datetime = datetime.now()
    #     for contract in self:
    #         bonus_amount = 0
    #         for bonus in contract.bonus:
    #             x = datetime.strptime(str(bonus.date_from), '%Y-%m-%d')
    #             y = datetime.strptime(str(bonus.date_to), '%Y-%m-%d')
    #             if x <= current_datetime <= y:
    #                 bonus_amount = bonus_amount + bonus.amount
    #             contract.total_bonus = bonus_amount

    total_bonus = fields.Float(string="Total Bonus", default=100.00)#compute=get_bonus_amount)
    bonus = fields.One2many('hr.employee.bonus', 'contract_id', string="Bonus",
                            domain=[('state', '=', 'active')])
    nb_days = fields.Float(string="Anciennete", compute="_get_duration")
    cumul_jour = fields.Float("Cumul jours anterieur")
    cumul_conges = fields.Float("Cumul conges anterieur")
    nbj_aquis = fields.Float("Nombre de jour acquis", default=0.0)
    convention_id = fields.Many2one('line.optesis.convention', 'Categorie')
    nbj_pris = fields.Float("Nombre de jour pris", default="0", compute='onchange_holiday_tracking', store=True)
    cumul_mensuel = fields.Float("Cumul mensuel conges")
    last_date = fields.Date("derniere date")
    alloc_conges = fields.Float("Allocation conges", compute="_get_alloc")
    motif = fields.Selection([('demission', 'Démission'), ('fin', 'Fin de contrat'), ('retraite', 'Retraite'),
                              ('licenciement', 'Licenciement'), ('deces', 'Décès'),
                              ('depart_nogicie', 'Départ négocié')], string='Motif de sortie')
    dateAnciennete = fields.Date("Date d'ancienneté", default=lambda self: fields.Date.to_string(date.today()))
    typeContract = fields.Selection([('cdi', 'CDI'), ('cdd', 'CDD'), ('others', 'Autres')], string="Type de contract")
    nbj_sup = fields.Float("Nombre de jour supplementaire")
    year_extra_day_anciennete = fields.Integer()
    holidays_tracking = fields.One2many('optipay.holidays.tracking', 'contract_id')
    cumul_provision_fin_contrat = fields.Float("Cumul mensuel Provision fin de contrat")

    @api.depends('holidays_tracking')
    def onchange_holiday_tracking(self):
        for contract in self:
            days = 0
            objs = [obj for obj in contract.holidays_tracking if obj.state == 'draft']
            if len(objs) > 1:
                raise ValidationError(_("On ne peut pas avoir plus d'une seule ligne à l'état draft"))

            for line in contract.holidays_tracking:
                domain = [('date_from', '<=', line.date_to),('date_to', '>', line.date_from),
                        ('contract_id', '=', contract.id)
                    ]
                hlds = contract.env['optipay.holidays.tracking'].search(domain)
                if len(hlds) > 1:
                    raise ValidationError(_("Vous ne pouvez pas avoir 2 congés qui se superposent sur le même jour."))

                if line.number_of_days < 0:
                    raise ValidationError(_("Le nombre de jour de congès ne doit pas être inféreur ou égal à 0."))

                if line.state == 'draft':
                    days += line.number_of_days

                if days > contract.nbj_aquis:
                    raise ValidationError(_("Le nombre de jour pris ne doit pas être supérieur au nombre de jours acquis."))

            contract.nbj_pris = days

    
    def reinit(self, contract_ids):
        for record in self.browse(contract_ids):
            record.cumul_mensuel = record.cumul_mensuel - record.alloc_conges
            record.alloc_conges = 0
            record.nbj_aquis = record.nbj_aquis - record.nbj_pris
            record.nbj_pris = 0

    @api.onchange("convention_id")
    def onchange_categ(self):
        if self.convention_id:
            self.wage = self.convention_id.wage

    # @api.multi
    def _get_droit(self, provision_conges, provision_fin_contrat):
        for record in self:

            record.cumul_mensuel += provision_conges
            record.cumul_provision_fin_contrat += provision_fin_contrat
            record.nbj_aquis += record.company_id.nbj_alloue


    # @api.multi
    @api.depends("cumul_mensuel", "nbj_pris", "nbj_aquis")
    def _get_alloc(self):
        for record in self:
            record.alloc_conges = 0
            if record.nbj_pris == 0 and record.cumul_mensuel == 0:
                return True
            if record.nbj_pris == 0 and record.cumul_mensuel != 0:
                return True
            if record.nbj_pris != 0 and record.cumul_mensuel == 0:
                return True
            if record.nbj_pris != 0 and record.cumul_mensuel != 0:
                if record.nbj_aquis == 0:
                    return True
                else:
                    record.alloc_conges = (record.cumul_mensuel * record.nbj_pris) / record.nbj_aquis

    @api.depends('dateAnciennete')
    def _get_duration(self):
        for record in self:
            server_dt = DEFAULT_SERVER_DATE_FORMAT
            today = datetime.now()
            dateAnciennete = datetime.strptime(str(record.dateAnciennete), server_dt)
            dur = today - dateAnciennete
            record.nb_days = dur.days
            # check if employee seniority is more than 10 years
            # if it is we add one day in nbj_aquis
            if dur.days >= 3653:
                if record.year_extra_day_anciennete:
                    if record.year_extra_day_anciennete != today.year:  # we must add it one time by year
                        record.year_extra_day_anciennete = today.year
                        record.write({'nbj_aquis': record.nbj_aquis + 1})
                else:
                    record.year_extra_day_anciennete = today.year
                    record.write({'nbj_aquis': record.nbj_aquis + 1})


class OptesisHolidaysTracking(models.Model):
    _name = "optipay.holidays.tracking"
    _description = "Optipay Holidays Tracking"

    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')
    number_of_days = fields.Float('Duration in days',
        help='Number of days of the leave request. Used for interface.')
    contract_id = fields.Many2one('hr.contract')
    state = fields.Selection([
        ('draft', 'draft'),
        ('done', 'done')
        ], string='Status', default='draft', required=True, readonly=True,
        help="The status is set to 'To Submit', when a leave request is created.")


    # @api.multi
    def unlink(self):
        self.ensure_one()
        if self.state == 'done':
            raise ValidationError(_("On ne peut pas supprimer une ligne de congès qui est a l'état done"))
        return super(OptesisHolidaysTracking, self).unlink()

    # @api.multi
    @api.onchange('date_from', 'date_to')
    def onchange_leave_date(self):
        for obj in self:
            if obj.date_from and obj.date_to:
                days = obj._get_number_of_days(obj.date_from, obj.date_to)
                obj.number_of_days = days
            else:
                obj.number_of_days = 0


    def _get_number_of_days(self, date_from, date_to):
        """ Returns a float equals to the timedelta between two dates given as string."""
        time_delta = date_to - date_from
        return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)



