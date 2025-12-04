from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from ..tools.chart import radar_factory
import matplotlib.pyplot as plt
import base64
import io
import numpy as np
from pypdf import PdfReader, PdfWriter

_logger = logging.getLogger(__name__)

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    avatar_id = fields.Many2one('scentopia.avatar', string="Avatar", compute='_compute_avatar_id')
    device_token = fields.Char(string='Device Token', readonly=True)
    personality_citrus = fields.Integer(string='Citrus', readonly=True, compute='_compute_personality_scores',store=True)
    personality_fresh = fields.Integer(string='Fresh', readonly=True, compute='_compute_personality_scores',store=True)
    personality_floral = fields.Integer(string='Floral', readonly=True, compute='_compute_personality_scores',store=True)
    personality_woody = fields.Integer(string='Woody', readonly=True, compute='_compute_personality_scores',store=True)
    personality_oriental = fields.Integer(string='Oriental', readonly=True, compute='_compute_personality_scores',store=True)
    device_token = fields.Char('Device Token', index=True)
    fragrance_value_ids = fields.One2many('survey.user_input.fragrance_value', 'user_input_id', string="Fragrance Values")

    def set_avatar_name(self, name=False):
        for rec in self:
            if rec.avatar_id and name:
                first_letter = name[0].upper()
                matching_titles = rec.avatar_id.title.filtered(
                    lambda t: t.name and t.name[0].upper() == first_letter
                )
                if matching_titles:
                    return f"{matching_titles[0].name} {name}"
                else:
                    return name
            else:
                return ''

    def render_radar_chart(self):
        for record in self:
            data = {x.fragrance_family_id.name: x.value for x in record.fragrance_value_ids}
            labels = list(data.keys())
            values = list(data.values())
            N = len(values)
            theta = radar_factory(N, frame='polygon')

            fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(projection='radar'))
            ax.plot(theta, values, color='#EEC3C3')
            ax.fill(theta, values, color='#EEC3C3', alpha=0.9)
            ax.set_varlabels(labels)
            ax.set_rmax(max(values) + 1)
            # ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1) 
            ax.set_title("")
            ax.yaxis.grid(True, linestyle="--", linewidth=0.8, color="gray")  # lingkaran
            ax.xaxis.grid(True, linestyle=":", linewidth=0.8, color="gray") 

            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', transparent=True)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            return image_base64

    @api.depends('user_input_line_ids.suggested_answer_id.fragrance_family_id')
    def _compute_personality_scores(self):
        for rec in self:
            scores = {
                'Citrus': 0,
                'Fresh': 0,
                'Floral': 0,
                'Woody': 0,
                'Oriental': 0,
            }
            for line in rec.user_input_line_ids:
                family = line.suggested_answer_id.fragrance_family_id.name
                if family in scores:
                    scores[family] += 1

            rec.personality_citrus = scores['Citrus']
            rec.personality_fresh = scores['Fresh']
            rec.personality_floral = scores['Floral']
            rec.personality_woody = scores['Woody']
            rec.personality_oriental = scores['Oriental']

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.opportunity_id:
            res._create_personality_mapping()
        return res

    def write(self, vals):
        self.ensure_one()
        
        # Calculate fragrance values in one pass
        fragrance_data = self.env['fragrance.family'].sudo().search([])
        divisor = 2 if len(self.user_input_line_ids) > 27 else 1
        
        # Calculate raw values
        raw_values = {}
        for fragrance in fragrance_data:
            raw_value = sum(1 for line in self.user_input_line_ids 
                   if line.fragrance_family_id.id == fragrance.id 
                   and not line.question_id.fixed_question) / divisor
            raw_values[fragrance.id] = raw_value
        
        # Convert to integers with total target of 20
        if raw_values:
            # Step 1: round to int
            int_values = {k: int(round(v)) for k, v in raw_values.items()}
            
            # Step 2: check difference from target total (20)
            target = 20
            current_sum = sum(int_values.values())
            diff = target - current_sum
            
            # Step 3: adjust to item with largest value
            if diff != 0:
                key_max = max(int_values, key=int_values.get)
                int_values[key_max] += diff
            
            # Calculate for target 10
            int_values_10 = {}
            if raw_values:
                # Scale down to target 10
                scale_factor = 10 / sum(raw_values.values()) if sum(raw_values.values()) > 0 else 0
                int_values_10 = {k: int(round(v * scale_factor)) for k, v in raw_values.items()}
                
                # Adjust to exact target 10
                current_sum_10 = sum(int_values_10.values())
                diff_10 = 10 - current_sum_10
                if diff_10 != 0:
                    key_max_10 = max(int_values_10, key=int_values_10.get)
                    int_values_10[key_max_10] += diff_10
            
            # Calculate for target 6
            int_values_6 = {}
            if raw_values:
                # Scale down to target 6
                scale_factor = 6 / sum(raw_values.values()) if sum(raw_values.values()) > 0 else 0
                int_values_6 = {k: int(round(v * scale_factor)) for k, v in raw_values.items()}
                
                # Adjust to exact target 6
                current_sum_6 = sum(int_values_6.values())
                diff_6 = 6 - current_sum_6
                if diff_6 != 0:
                    key_max_6 = max(int_values_6, key=int_values_6.get)
                    int_values_6[key_max_6] += diff_6
        else:
            int_values = {}
        
        
        vals['fragrance_value_ids'] = [(5, 0, 0)] + [
            (0, 0, {
                'user_input_id': self.id,
                'fragrance_family_id': fragrance.id,
                'value': int_values.get(fragrance.id, 0),
                'value_50': int_values_10.get(fragrance.id, 0),
                'value_30': int_values_6.get(fragrance.id, 0),
            }) for fragrance in fragrance_data
        ]

        res = super().write(vals)
        for record in self:
            if record.opportunity_id:
                record._create_personality_mapping()
        return res



    def _create_personality_mapping(self):
        for rec in self:
            if not rec.opportunity_id:
                continue
            existing_mappings = self.env['crm.lead.personality.mapping'].search([
                ('lead_id', '=', rec.opportunity_id.id)
            ])
            crm_lead = self.env['crm.lead'].search([
                ('id', '=', rec.opportunity_id.id)
            ], limit=1)
            existing_mappings.unlink()
            self.env['crm.lead.personality.mapping'].create({
                'lead_id': rec.opportunity_id.id,
                'survey_user_input_id': rec.id,
            })
            crm_lead.write({
                'partner_id': rec.partner_id.id,
                'gender': rec.partner_id.gender,
            })

    def _save_lines(self, question, answer, comment=None, overwrite_existing=True):
        """ Extend to add support for video question type """
        # Get old answers
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', self.id),
            ('question_id', '=', question.id)
        ])
        if old_answers and not overwrite_existing:
            raise UserError(_("This answer cannot be overwritten."))

        # Handle video question type like simple_choice
        if question.question_type == 'video':
            return self._save_line_choice(question, old_answers, answer, comment)
        
        # For all other question types, use the original method
        return super()._save_lines(question, answer, comment, overwrite_existing)

    def _save_line_choice(self, question, old_answers, answers, comment):
        """ Extend to handle video question type """
        if not (isinstance(answers, list)):
            answers = [answers]

        if not answers:
            answers = [False]

        vals_list = []

        # Handle simple_choice, multiple_choice, and video the same way
        if question.question_type in ['simple_choice', 'video']:
            if not question.comment_count_as_answer or not question.comments_allowed or not comment:
                vals_list = [self._get_line_answer_values(question, answer, 'suggestion') for answer in answers]
        elif question.question_type == 'multiple_choice':
            vals_list = [self._get_line_answer_values(question, answer, 'suggestion') for answer in answers]

        if comment:
            vals_list.append(self._get_line_comment_values(question, comment))
        old_answers.sudo().unlink()
        return self.env['survey.user_input.line'].create(vals_list)
    
    def _get_line_answer_values(self, question, answer, answer_type):
        _logger.info("Getting line answer values for question: %s, answer: %s, answer_type: %s", question, answer, answer_type)
        answer_id = self.env['survey.question.answer'].sudo().search([('question_id', '=', question.id), ('id', '=', answer)])
        vals = {
            'user_input_id': self.id,
            'question_id': question.id,
            'skipped': False,
            'answer_type': answer_type,
            'fragrance_family_id': answer_id.fragrance_family_id.id if not answer_id.question_id.fixed_question else False,
        }
        if not answer or (isinstance(answer, str) and not answer.strip()):
            vals.update(answer_type=None, skipped=True)
            return vals

        if answer_type == 'suggestion':
            vals['suggested_answer_id'] = int(answer)
        elif answer_type == 'numerical_box':
            vals['value_numerical_box'] = float(answer)
        elif answer_type == 'scale':
            vals['value_scale'] = int(answer)
        else:
            vals['value_%s' % answer_type] = answer
        return vals

    @api.depends('user_input_line_ids.fragrance_family_id')
    def _compute_avatar_id(self):
        """Compute the avatar_id based on exact match of fragrance_family_ids"""
        Avatar = self.env['scentopia.avatar']
        for record in self:
            # Get all records that have this max value
            max_value_records = record.fragrance_value_ids.filtered(lambda r: r.value >= r.fragrance_family_id.threshold)
            # Get the fragrance family ids from these records
            families = max_value_records.mapped('fragrance_family_id.id')
            target_set = set(families)
            record.avatar_id = Avatar.search([
                ('fragrance_family_ids', '!=', False),
            ]).filtered(lambda a: set(a.fragrance_family_ids.ids) == target_set)[:1].id or False

    @api.onchange('device_token')
    def _onchange_device_token(self):
        for record in self:
            if record.device_token:
                user = self.env['res.users'].sudo().search([
                    ('last_survey_device_token', '=', record.device_token)
                ], limit=1)
                if user and user.partner_id:
                    record.partner_id = user.partner_id.id
                    record.value_test = str(user.partner_id.id)
                else:
                    record.partner_id = False
                    record.value_test = 'Nope'
            else:
                record.partner_id = False
                record.value_test = 'Nope'


    @api.model
    def send_email_report(self, answer_token, selected_reports=False):
        _logger.info("================calling======================")
        generate_reports = self.generate_report(answer_token, selected_reports)
        answer = self.env['survey.user_input'].sudo().search(
            [('access_token', '=', answer_token)], limit=1
        )
        report_map = {
            "love_match": answer.avatar_id.love_match_report,
            "career_match": answer.avatar_id.career_match_report,
            "soulfulness": answer.avatar_id.soulfulness_report,
            "five_elements": answer.avatar_id.five_elements_report,
            "thirty_one_types": answer.avatar_id.thirty_one_types_report,
            "tcm": answer.avatar_id.tcm_report,
            "ayurvedic_dosha": answer.avatar_id.ayurvedic_report,
        }

        if not answer or not answer.partner_id.email:
            return False
        report_list = [(0, 0, {
                'name': 'Scentzania Report.pdf',
                'type': 'binary',
                'datas': generate_reports,
                'mimetype': 'application/pdf',
            })]
        for report in selected_reports:
            if report in report_map and report_map[report]:
                report_list.append((0, 0, {
                    'name': f'{report.replace("_", " ").title()} Report.pdf',
                    'type': 'binary',
                    'datas': report_map[report],
                    'mimetype': 'application/pdf',
                }))
        mail = self.env['mail.mail'].sudo().create({
            'subject': 'Your Personality Test Report from Scentzania',
            'email_to': answer.partner_id.email,
            'body_html': f'''
                <p>Hi {answer.partner_id.name},<br/>
                Thank you for taking the test on Scentzania!<br/>
                We're excited to share your personalized report.<br/><br/>
                Warm regards,<br/><b>The Scentzania Team</b></p>
            ''',
            'attachment_ids': report_list,
        })
        mail.send()
        return True

    @api.model
    def generate_report(self, answer_token, selected_reports=None):
        answer = self.env['survey.user_input'].sudo().search(
            [('access_token', '=', answer_token)], limit=1
        )
        if not answer:
            return False

        writer = PdfWriter()
        selected_reports = selected_reports or []

        for report in selected_reports:
            if report == "perfume_personality":
                personality = answer.avatar_id.perfume_personality_report
                if personality:
                    page_1 = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'gm_survey.avatar_report_page_1', [answer.opportunity_id.id])[0]
                    page_5 = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'gm_survey.avatar_report_page_5', [answer.opportunity_id.id])[0]
                    page_6 = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'gm_survey.avatar_report_page_6', [answer.opportunity_id.id])[0]
                    page_9 = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'gm_survey.avatar_report_page_9', [answer.opportunity_id.id])[0]
                    intensity_index = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'gm_survey.avatar_report_intensity_index', [answer.opportunity_id.id])[0]
                    intensity_table = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        'gm_survey.avatar_report_intensity_table', [answer.opportunity_id.id])[0]
                    merged = self.process_report_personality(
                        personality, page_1, page_5, page_6, page_9, intensity_index, intensity_table
                    )
                    if merged:
                        pdf = PdfReader(io.BytesIO(base64.b64decode(merged)))
                        for page in pdf.pages:
                            writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        return base64.b64encode(output.getvalue())

    @api.model
    def process_report_personality(self, perfume_personality, page_1, page_5, page_6, page_9, intensity_index, intensity_table):
        writer = PdfWriter()

        writer.append(io.BytesIO(page_1))
        pdf = PdfReader(io.BytesIO(base64.b64decode(perfume_personality)))
        for page in pdf.pages[:3]:
            writer.add_page(page)

        pdf1 = PdfReader(io.BytesIO(page_5))
        for page in pdf1.pages:
            writer.add_page(page)

        writer.append(io.BytesIO(page_6))
        for page in pdf.pages[3:5]:
            writer.add_page(page)

        writer.append(io.BytesIO(page_9))
        for page in pdf.pages[5:7]:
            writer.add_page(page)

        pdf_intensity_index = PdfReader(io.BytesIO(intensity_index))
        for page in pdf_intensity_index.pages:
            writer.add_page(page)
        writer.append(io.BytesIO(intensity_table))
        for page in pdf.pages[7:]:
            writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        return base64.b64encode(output.getvalue())

class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    # Only extend the selection field, no new value field needed
    answer_type = fields.Selection(
        selection_add=[('video', 'Video')],
        ondelete={'video': 'cascade'}
    )
    fragrance_family_id = fields.Many2one(
        'fragrance.family',
        string="Fragrance Family",
        help="Select the fragrance family for this answer"
    )

class SurveyUserInputFragranceValue(models.Model):
    _name = 'survey.user_input.fragrance_value'
    _description = 'Survey User Input Fragrance Value'
    _rec_name = "fragrance_family_id"

    user_input_id = fields.Many2one('survey.user_input', string='User Input', ondelete='cascade')
    fragrance_family_id = fields.Many2one('fragrance.family', string='Fragrance Family')
    value = fields.Float(string='Value Original')
    value_manual = fields.Float(string='Value Manual')
    value_50 = fields.Float(string='Value 50ml')
    value_30 = fields.Float(string='Value 30ml')
