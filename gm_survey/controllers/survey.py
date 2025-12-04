from odoo import http, fields
from odoo.http import request
import logging

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.addons.survey.controllers.main import Survey
from odoo.tools import format_datetime, format_date, is_html_empty
import json

_logger = logging.getLogger(__name__)


class GmSurvey(Survey):

    def _ensure_device_token(self):
        device_token = request.httprequest.cookies.get('device_token')
        if not device_token:
            import secrets
            device_token = secrets.token_urlsafe(32)
        # Buat response dummy untuk set cookie
        response = request.make_response('')
        response.set_cookie(
            'device_token',
            device_token,
            max_age=31536000,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        return device_token

    @http.route('/survey/submit/<string:survey_token>/<string:answer_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, answer_token, **post):

        _logger.info("post = %s", post)
        """ Submit a page from the survey.
        This will take into account the validation errors and store the answers to the questions.
        If the time limit is reached, errors will be skipped, answers will be ignored and
        survey state will be forced to 'done'.
        Also returns the correct answers if the scoring type is 'scoring_with_answers_after_page'."""
        # Survey Validation
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return {}, {'error': access_data['validity_code']}
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']

        if answer_sudo.state == 'done':
            return {}, {'error': 'unauthorized'}

        questions, page_or_question_id = survey_sudo._get_survey_questions(answer=answer_sudo,
                                                                           page_id=post.get('page_id'),
                                                                           question_id=post.get('question_id'))

        if not answer_sudo.test_entry and not survey_sudo._has_attempts_left(answer_sudo.partner_id, answer_sudo.email, answer_sudo.invite_token):
            # prevent cheating with users creating multiple 'user_input' before their last attempt
            return {}, {'error': 'unauthorized'}

        if answer_sudo.survey_time_limit_reached or answer_sudo.question_time_limit_reached:
            if answer_sudo.question_time_limit_reached:
                time_limit = survey_sudo.session_question_start_time + relativedelta(
                    seconds=survey_sudo.session_question_id.time_limit
                )
                time_limit += timedelta(seconds=3)
            else:
                time_limit = answer_sudo.start_datetime + timedelta(minutes=survey_sudo.time_limit)
                time_limit += timedelta(seconds=10)
            if fields.Datetime.now() > time_limit:
                # prevent cheating with users blocking the JS timer and taking all their time to answer
                return {}, {'error': 'unauthorized'}

        errors = {}
        # Prepare answers / comment by question, validate and save answers
        for question in questions:
            inactive_questions = request.env['survey.question'] if answer_sudo.is_session_answer else answer_sudo._get_inactive_conditional_questions()
            if question in inactive_questions:  # if question is inactive, skip validation and save
                continue
            answer, comment = self._extract_comment_from_answers(question, post.get(str(question.id)))
            _logger.info("===============================")
            _logger.info("question = %s", question)
            _logger.info("answer = %s", answer)

            errors.update(question.validate_question(answer, comment))
            if not errors.get(question.id):
                answer_sudo._save_lines(question, answer, comment, overwrite_existing=survey_sudo.users_can_go_back or question.save_as_nickname or question.save_as_email)

        if errors and not (answer_sudo.survey_time_limit_reached or answer_sudo.question_time_limit_reached):
            return {}, {'error': 'validation', 'fields': errors}

        if not answer_sudo.is_session_answer:
            answer_sudo._clear_inactive_conditional_answers()

        # Get the page questions correct answers if scoring type is scoring after page
        correct_answers = {}
        if survey_sudo.scoring_type == 'scoring_with_answers_after_page':
            scorable_questions = (questions - answer_sudo._get_inactive_conditional_questions()).filtered('is_scored_question')
            correct_answers = scorable_questions._get_correct_answers()

        if answer_sudo.survey_time_limit_reached or survey_sudo.questions_layout == 'one_page':
            answer_sudo._mark_done()
        elif 'previous_page_id' in post:
            # when going back, save the last displayed to reload the survey where the user left it.
            answer_sudo.last_displayed_page_id = post['previous_page_id']
            # Go back to specific page using the breadcrumb. Lines are saved and survey continues
            return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo, **post)
        elif 'next_skipped_page_or_question' in post:
            answer_sudo.last_displayed_page_id = page_or_question_id
            return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo, next_skipped_page=True)
        else:
            if not answer_sudo.is_session_answer:
                page_or_question = request.env['survey.question'].sudo().browse(page_or_question_id)
                if answer_sudo.survey_first_submitted and answer_sudo._is_last_skipped_page_or_question(page_or_question):
                    next_page = request.env['survey.question']
                else:
                    next_page = survey_sudo._get_next_page_or_question(answer_sudo, page_or_question_id)
                if not next_page:
                    if survey_sudo.users_can_go_back and answer_sudo.user_input_line_ids.filtered(
                            lambda a: a.skipped and a.question_id.constr_mandatory):
                        answer_sudo.write({
                            'last_displayed_page_id': page_or_question_id,
                            'survey_first_submitted': True,
                        })
                        return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo, next_skipped_page=True)
                    else:
                        answer_sudo._mark_done()

            answer_sudo.last_displayed_page_id = page_or_question_id
        return correct_answers, self._prepare_question_html(survey_sudo, answer_sudo)
    
    @http.route('/survey/<string:survey_token>/<string:answer_token>', type='http', auth='public', website=True)
    def survey_display_page(self, survey_token, answer_token, **post):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        device_token = self._ensure_device_token()
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        answer_sudo = access_data['answer_sudo']
        if answer_sudo.state != 'done' and answer_sudo.survey_time_limit_reached:
            answer_sudo._mark_done()
        template = "survey.survey_page_fill"
        if access_data['survey_sudo'].theme_survey == "custom":
            template="gm_survey.survey_page_fill_custom"

        rendered = request.render(template,
            self._prepare_survey_data(access_data['survey_sudo'], answer_sudo, **post))
        # Set device_token di cookie pada response
        rendered.set_cookie(
            'device_token',
            device_token,
            max_age=31536000,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        return rendered

    def _prepare_question_html(self, survey_sudo, answer_sudo, **post):
        """ Survey page navigation is done in AJAX. This function prepare the 'next page' to display in html
        and send back this html to the survey_form widget that will inject it into the page.
        Background url must be given to the caller in order to process its refresh as we don't have the next question
        object at frontend side."""
        survey_data = self._prepare_survey_data(survey_sudo, answer_sudo, **post)

        if answer_sudo.state == 'done':
            if survey_sudo.theme_survey == "custom":
                template = 'gm_survey.survey_fill_form_done_custom'
            else:
                template = 'survey.survey_fill_form_done'
            survey_content = request.env['ir.qweb']._render(template, survey_data)
        else:
            if survey_sudo.theme_survey == "custom":
                template = 'gm_survey.survey_fill_form_in_progress_custom'
            else:
                template = 'survey.survey_fill_form_in_progress'
            survey_content = request.env['ir.qweb']._render(template, survey_data)

        survey_progress = False
        if answer_sudo.state == 'in_progress' and not survey_data.get('question', request.env['survey.question']).is_page:
            if survey_sudo.theme_survey == "custom":
                template = 'gm_survey.survey_progression_custom'
            else:
                template = 'survey.survey_progression'
            if survey_sudo.questions_layout == 'page_per_section':
                page_ids = survey_sudo.page_ids.ids

                survey_progress = request.env['ir.qweb']._render(template, {
                    'survey': survey_sudo,
                    'page_ids': page_ids,
                    'page_number': page_ids.index(survey_data['page'].id) + (1 if survey_sudo.progression_mode == 'number' else 0)
                })
            elif survey_sudo.questions_layout == 'page_per_question':
                page_ids = (answer_sudo.predefined_question_ids.ids
                            if not answer_sudo.is_session_answer and survey_sudo.questions_selection == 'random'
                            else survey_sudo.question_ids.ids)
                survey_progress = request.env['ir.qweb']._render(template, {
                    'survey': survey_sudo,
                    'page_ids': page_ids,
                    'page_number': page_ids.index(survey_data['question'].id)
                })

        background_image_url = survey_sudo.background_image_url
        if 'question' in survey_data:
            background_image_url = survey_data['question'].background_image_url
        elif 'page' in survey_data:
            background_image_url = survey_data['page'].background_image_url

        return {
            'has_skipped_questions': any(answer_sudo._get_skipped_questions()),
            'survey_content': survey_content,
            'survey_progress': survey_progress,
            'survey_navigation': request.env['ir.qweb']._render('survey.survey_navigation', survey_data),
            'background_image_url': background_image_url
        }

    @http.route('/survey/print/<string:survey_token>', type='http', auth='public', website=True, sitemap=False)
    def survey_print(self, survey_token, review=False, answer_token=None, **post):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        '''Display an survey in printable view; if <answer_token> is set, it will
        grab the answers of the user_input_id that has <answer_token>.'''
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False, check_partner=False)
        if access_data['validity_code'] is not True and (
                not access_data['has_survey_access'] or
                access_data['validity_code'] not in ['token_required', 'survey_closed', 'survey_void', 'answer_deadline']):
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        data = {}
        if access_data['survey_sudo'].theme_survey == "custom":
            question_data = answer_sudo.user_input_line_ids.filtered(lambda x: not x.question_id.fixed_question)
            _logger.info(question_data)
            _logger.info(len(question_data))
            fragrance_family = request.env['fragrance.family'].sudo().search([])
            data = {
                fragrance.name: {
                    'value': int(answer_sudo.fragrance_value_ids.filtered(lambda x: x.fragrance_family_id.id == fragrance.id).value),
                    'description': fragrance.description,
                    'color': fragrance.color or '#FFFFFF'  # Default color if not found
                } for fragrance in fragrance_family
            }
            _logger.info("data = %s", data)
            template="gm_survey.survey_page_print_custom"
        return request.render(template, {
            'is_html_empty': is_html_empty,
            'review': review,
            'survey': survey_sudo,
            'answer': answer_sudo if survey_sudo.scoring_type != 'scoring_without_answers' else answer_sudo.browse(),
            'questions_to_display': answer_sudo._get_print_questions(),
            'scoring_display_correction': survey_sudo.scoring_type in ['scoring_with_answers', 'scoring_with_answers_after_page'] and answer_sudo,
            'format_datetime': lambda dt: format_datetime(request.env, dt, dt_format=False),
            'format_date': lambda date: format_date(request.env, date),
            'graph_data': json.dumps(answer_sudo._prepare_statistics()[answer_sudo])
                              if answer_sudo and survey_sudo.scoring_type in ['scoring_with_answers', 'scoring_with_answers_after_page'] else False,
            'data': data,
        })