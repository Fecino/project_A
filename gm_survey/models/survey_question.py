from odoo import models, fields, api
import logging
import random

_logger = logging.getLogger(__name__)


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    question_type = fields.Selection(
        selection_add=[('video', 'Video')])
    video_url = fields.Char(string="Video Embedd URL", help="Embbedd URL of the video to be displayed in the question")
    fixed_question = fields.Boolean(string='Fixed Question', default=False, help="If checked, this question will not be removed from the survey even if it is not answered by the user.")

    def _get_correct_answers(self):
        """ Return a dictionary linking the scorable question ids to their correct answers.
        The questions without correct answers are not considered.
        """
        correct_answers = {}

        # Simple and multiple choice
        choices_questions = self.filtered(lambda q: q.question_type in ['simple_choice', 'multiple_choice', 'video'])
        if choices_questions:
            suggested_answers_data = self.env['survey.question.answer'].search_read(
                [('question_id', 'in', choices_questions.ids), ('is_correct', '=', True)],
                ['question_id', 'id'],
                load='', # prevent computing display_names
            )
            for data in suggested_answers_data:
                if not data.get('id'):
                    continue
                correct_answers.setdefault(data['question_id'], []).append(data['id'])

        # Numerical box, date, datetime
        for question in self - choices_questions:
            if question.question_type not in ['numerical_box', 'date', 'datetime']:
                continue
            answer = question[f'answer_{question.question_type}']
            if question.question_type == 'date':
                answer = tools.format_date(self.env, answer)
            elif question.question_type == 'datetime':
                answer = tools.format_datetime(self.env, answer, tz='UTC', dt_format=False)
            correct_answers[question.id] = answer

        return correct_answers
    

    @api.depends('question_type', 'scoring_type', 'answer_date', 'answer_datetime', 'answer_numerical_box', 'suggested_answer_ids.is_correct')
    def _compute_is_scored_question(self):
        """ Computes whether a question "is scored" or not. Handles following cases:
          - inconsistent Boolean=None edge case that breaks tests => False
          - survey is not scored => False
          - 'date'/'datetime'/'numerical_box' question types w/correct answer => True
            (implied without user having to activate, except for numerical whose correct value is 0.0)
          - 'simple_choice / multiple_choice': set to True if any of suggested answers are marked as correct
          - question_type isn't scoreable (note: choice questions scoring logic handled separately) => False
        """
        for question in self:
            if question.is_scored_question is None or question.scoring_type == 'no_scoring':
                question.is_scored_question = False
            elif question.question_type == 'date':
                question.is_scored_question = bool(question.answer_date)
            elif question.question_type == 'datetime':
                question.is_scored_question = bool(question.answer_datetime)
            elif question.question_type == 'numerical_box' and question.answer_numerical_box:
                question.is_scored_question = True
            elif question.question_type in ['simple_choice', 'multiple_choice', 'video']:
                question.is_scored_question = any(question.suggested_answer_ids.mapped('is_correct'))
            else:
                question.is_scored_question = False

    def random_options(self, options):
        _logger.info("Before %s", options )
        lines = options  # recordset
        lines_list = list(lines)  # convert ke list
        random.shuffle(lines_list)
        _logger.info("After %s", lines_list )
        return lines_list
