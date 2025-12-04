from odoo import models, fields, api
import random

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    # Example: add a new field
    theme_survey = fields.Selection([('default','Default'), ('custom','Custom')])
    personality_test = fields.Boolean(string='Personality Test')

    @api.onchange('personality_test')
    def _onchange_personality_test(self):
        if self.personality_test:
            self.env['survey.survey'].search([('id','!=', self.id)]).write({'personality_test': False})

    def _prepare_user_input_predefined_questions(self):
        """ Will generate the questions for a randomized survey.
        It uses the random_questions_count of every sections of the survey to
        pick a random number of questions and returns the merged recordset """
        self.ensure_one()

        questions = self.env['survey.question']

        # First append questions without page
        for question in self.question_ids:
            if not question.page_id:
                questions |= question

        # Then, questions in sections

        for page in self.page_ids:
            if self.questions_selection == 'all':
                questions |= page.question_ids
            else:
                if 0 < page.random_questions_count < len(page.question_ids):
                    questions_fixed = questions.concat(*random.sample(page.question_ids.filtered(lambda x: x.fixed_question), 7))
                    questions_non_fixed = questions.concat(*random.sample(page.question_ids.filtered(lambda x: not x.fixed_question), page.random_questions_count))
                    questions = questions_non_fixed + questions_fixed
                else:
                    questions |= page.question_ids
        return questions