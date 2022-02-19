# -*- coding: utf-8 -*-
from openerp import models, fields, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class CalculateGrossFromNet(models.TransientModel):
    _name = "payslip.simulation"
    _description = "model for net to gross simulation"

    desired_net_salary = fields.Float(string="Salaire net voulu", required=True)
    impacted_rule = fields.Many2one('hr.salary.rule')

    def compute_simulation(self):
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        payslip = self.env['hr.payslip'].search([('id', '=', active_id)])
        net_expected = data['desired_net_salary']
        rule_id = str(data['impacted_rule'][0])

        #check if the salary rule is in the struct
        for obj in payslip.struct_id.rule_ids:
            if rule_id == str(obj.id):
                break
        else:
            raise ValidationError(_("Veullez ajouter la régle de simulation dans la structure!"))

        # check if the salary rule is defined in element variable
        for bonus in payslip.contract_id.bonus:
            if str(bonus.salary_rule.id) == rule_id:
                if not ((bonus.date_to < payslip.date_from or bonus.date_from > payslip.date_to) or
                    (bonus.date_to <= payslip.date_from or bonus.date_from >= payslip.date_to)):
                    raise ValidationError(_("la règle salariale pour la simulation ne doit pas être défini comme élément variable dans contrat"))

        impacted_salary_rule = self.env['hr.salary.rule'].search([('id', '=', rule_id)])
        impacted_salary_rule.write({
            'amount_select':'fix'
        })
        net_computed = 0.0
        while net_computed != net_expected:
            payslip.compute_sheet()
            net_computed = 0.0
            net_computed += sum(line.total for line in payslip.line_ids if line.code == 'C5000')
            if net_computed > net_expected:
                diff = net_computed - net_expected
                if len(str(diff)) == 3:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix - 1})
                elif len(str(diff)) == 4:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix - 10})
                elif len(str(diff)) == 5:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix - (diff//10)*10})
                elif len(str(diff)) == 6:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix - (diff//1000)*1000})
                elif len(str(diff)) == 7:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix - (diff//10000)*10000})
                elif len(str(diff)) == 8:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix - (diff//100000)*100000})
                elif len(str(diff)) == 9:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix - (diff//1000000)*1000000})
                else:
                    break
            elif net_computed < net_expected:
                diff = net_expected - net_computed
                if len(str(diff)) == 3:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix + 1})
                elif len(str(diff)) == 4:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix + (diff//10)*10})
                elif len(str(diff)) == 5:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix + (diff//100)*100})
                elif len(str(str(diff))) == 6:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix + (diff//1000)*1000})
                elif len(str(str(diff))) == 7:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix + (diff//10000)*10000})
                elif len(str(str(diff))) == 8:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix + (diff//100000)*100000})
                elif len(str(str(diff))) == 9:
                    impacted_salary_rule.write({'amount_fix': impacted_salary_rule.amount_fix + (diff//1000000)*1000000})
                else:
                    break
        # on remet a zero la régle simule
        impacted_salary_rule.write({'amount_fix': 0.0})
