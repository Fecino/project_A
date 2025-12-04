from odoo import models, fields

class TriviaCard(models.Model):
    _name = "trivia.card"
    _description = "Trivia and Helpful Guides"
    _rec_name = 'name'

    name = fields.Char(string="Question/Title", required=True, help="Trivia question or helpful guide title")
    type = fields.Selection([('trivia','Trivia'),('helpfull','Helpful Guides')], string="Type", required=True)
    
    # For trivia
    answer = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Answer', help="Correct answer to the trivia question")
    
    # For helpful guides
    content = fields.Text(string="Content", help="Content for helpful guides")