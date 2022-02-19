# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SurveyInherit(models.Model):
    _inherit = 'survey.survey'

    #@api.multi
    def action_assign_survey(self):
        local_context = dict(
            self.env.context,
            default_model='survey.survey',
            default_survey_id=self.id,
            default_manual = False
        )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'survey.assign_contact',
            'target': 'new',
            'context': local_context,
        }

class SurveyUserInputLineInherit(models.Model):
    _inherit = 'survey.user_input.line'

    answer = fields.Char(string='Answer', compute='_compute_answer', store=True)
    
    #@api.multi
    @api.depends('skipped', 'answer_type')
    def _compute_answer(self):
        for s in self:
            if not s.skipped:
                if s.answer_type == 'text':
                    s.answer = s.value_text
                elif s.answer_type == 'number':
                    s.answer = str(s.value_numerical_box) # value_number
                elif s.answer_type == 'date':
                    s.answer = str(s.value_date)
                elif s.answer_type == 'free_text':
                    s.answer = s.value_free_text
                elif s.answer_type == 'numerical_box':
                    s.answer = s.value_numerical_box   # value_number
                elif s.answer_type == 'simple_choice':
                    s.answer = s.suggested_answer_id.value  # value_suggested to suggested_answer_id
                elif s.answer_type == 'multiple_choice':
                    s.answer = s.suggested_answer_id.value
                elif s.answer_type == 'matrix':
                    s.answer = s.suggested_answer_id.value
                elif s.answer_type == 'suggestion':
                    s.answer = s.suggested_answer_id.value

class SurveyUserInputInherit(models.Model):
    _inherit = 'survey.user_input'

    #@api.multi
    def action_fill_answers(self):
        self.ensure_one()
        trail = "/%s" % self.token if self.token else ""
        
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Survey",
            'target': 'self',
            'url': self.survey_id.with_context(relative_url=True).public_url.replace('start', 'fill') + trail
        }