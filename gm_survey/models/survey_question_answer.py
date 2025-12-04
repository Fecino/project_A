from odoo import models, fields, api, _

class surveyQuestionAnswer(models.Model):
    _inherit = 'survey.question.answer'

    fragrance_family_id = fields.Many2one(
        'fragrance.family',
        string="Fragrance Family",
        help="Select the fragrance family for this answer"
    )
