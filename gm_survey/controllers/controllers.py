import base64
import os
from odoo import http, fields
from odoo.http import request, content_disposition
import werkzeug
import logging
import json
from .token import get_device_token, ensure_device_token_in_url


_logger = logging.getLogger(__name__)

def set_survey_cookies(response, survey_token=None, answer_token=None):
    """Helper function to set survey-related cookies"""
    cookie_options = {
        'max_age': 86400,  # 24 hours
        'httponly': True,
        'secure': request.httprequest.is_secure,
        'samesite': 'Lax'
    }
    
    if survey_token:
        response.set_cookie('survey_token', survey_token, **cookie_options)
        _logger.info(f"Set survey_token cookie: {survey_token}")
    
    if answer_token:
        response.set_cookie('answer_token', answer_token, **cookie_options)
        _logger.info(f"Set answer_token cookie: {answer_token}")
    
    # Also ensure device token is set with longer expiry
    device_token = get_device_token()
    if device_token:
        device_cookie_options = {
            'max_age': 31536000,  # 1 year in seconds
            'httponly': True,
            'secure': request.httprequest.is_secure,
            'samesite': 'Lax'
        }
        response.set_cookie('device_token', device_token, **device_cookie_options)

class GmSurvey(http.Controller):
    @http.route(['/<string:language_code>/take_a_survey', '/take_a_survey'], type='http', auth='public', website=True, csrf=True)
    def take_a_survey(self, language_code=None, **kwargs):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        try:
            question = int(kwargs.get('questions', 0))
            fixed_question = int(kwargs.get('fixed_questions', 0))

        except (ValueError, TypeError):
            return werkzeug.exceptions.BadRequest("Invalid question parameter")
        survey = request.env['survey.survey'].sudo().search([('personality_test', '=', True)], limit=1)
        if not survey:
            return request.render('http_routing.404', {})
            
        domain = [('survey_id', '=', survey.id), ('is_page', '=', True)]
        pages = request.env['survey.question'].sudo().search([
            *domain,
            '|',
            ('fixed_question', '=', True),
            ('fixed_question', '=', False)
        ])
        
        for page in pages:
            page.sudo().write({
                'random_questions_count': fixed_question if page.fixed_question else question
            })

        base_url = survey.sudo().get_base_url()
        start_url = survey.sudo().get_start_url()
        
        # Ensure device token is in URL
        full_url = werkzeug.urls.url_join(base_url, start_url)
        full_url = ensure_device_token_in_url(full_url)
        
        # Create response and set cookies
        response = request.redirect(full_url)
        set_survey_cookies(response, survey_token=survey.access_token)
        
        return response
    
    @http.route(['/<string:language_code>/show_avatar/<string:answer_token>', '/show_avatar/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def show_avatar(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        gender = request.httprequest.cookies.get('gender')
        if answer.avatar_id.is_unisex:
            gender = 'other'
        response = request.render('gm_survey.avatar_view', 
            {
                'avatar': answer.avatar_id.with_context(bin_size=False),
                'answer_token': answer.access_token,
                'survey_token': answer.survey_id.access_token,
                'gender': gender
            }
        )
        # Set cookies to preserve session
        set_survey_cookies(response, 
                          survey_token=answer.survey_id.access_token, 
                          answer_token=answer_token)
        return response

    @http.route(['/<string:language_code>/show_profile/<string:answer_token>', '/show_profile/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def show_profile(self, language_code=None, answer_token=None, **kwargs):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        question_data = answer.user_input_line_ids.filtered(lambda x: not x.question_id.fixed_question)
        _logger.info(question_data)
        _logger.info(len(question_data))
        fragrance_family = request.env['fragrance.family'].sudo().search([])
        divide_by = len(question_data) / 20
        data = {
            fragrance.name: {
                'value': len(answer.user_input_line_ids.filtered(lambda x: x.fragrance_family_id == fragrance and not x.question_id.fixed_question)) / divide_by,
                'percentage': len(answer.user_input_line_ids.filtered(lambda x: x.fragrance_family_id == fragrance and not x.question_id.fixed_question)) / len(question_data) * 100,
                'description': fragrance.description,
                'color': fragrance.color or '#FFFFFF'  # Default color if not found
            } for fragrance in fragrance_family
        }
        _logger.info("data = %s", data)
        labels = list(data.keys())
        values = [data[k]['value'] for k in labels]
        gender = request.httprequest.cookies.get('gender')
        if answer.avatar_id.is_unisex:
            gender = 'other'
        _logger.info("Gender: %s", gender)
        
        response = request.render('gm_survey.avatar_detail',
            {
                'avatar': answer.avatar_id.with_context(bin_size=False),
                'crm_lead': answer.opportunity_id,
                'answer_token': answer.access_token,
                'labels': json.dumps(labels),
                'values': json.dumps(values),
                'data': data,
                'gender': gender,
                'avatar_name': answer.set_avatar_name(request.session.get('temp_name', '')),
                'from_choose_report': kwargs.get('from_choose_report', False)
            }
        )
        # Set cookies to preserve session
        set_survey_cookies(response, 
                          survey_token=answer.survey_id.access_token, 
                          answer_token=answer_token)
        return response
    
    @http.route(['/<string:language_code>/login_user/<string:answer_token>', '/login_user/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def login_user(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        """Redirect to login/signup with comprehensive survey session preservation"""
        # Find the survey answer to get survey_token
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        survey_token = answer.survey_id.access_token if answer else None
        
        response = request.redirect(f'/{language_code}/web/login' if language_code else '/web/login')
        
        # Set all necessary cookies for session preservation
        set_survey_cookies(response, 
                          survey_token=survey_token, 
                          answer_token=answer_token)
        
        _logger.info(f"Redirecting to login with answer_token: {answer_token} and survey_token: {survey_token}")
        return response

    @http.route(['/<string:language_code>/choose_report/<string:answer_token>', '/choose_report/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def choose_report(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_choose_report', {'answer_token': answer_token})

    @http.route(['/<string:language_code>/get_report_pdf/<string:type_report>/<string:answer_token>', '/get_report_pdf/<string:type_report>/<string:answer_token>'], type='http', auth='public')
    def get_pdf(self, language_code=None, type_report=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
            
        avatar = answer.opportunity_id.sudo().avatar_id.sudo()

        # Map report types to avatar fields
        report_fields = {
            'five_elements': 'five_elements_report',
            'love_match': 'love_match_report',
            'career_match': 'career_match_report',
            'soulfulness': 'soulfulness_report',
            'thirty_one_types': 'thirty_one_types_report',
            'tcm': 'tcm_report',
            'ayurvedic': 'ayurvedic_report'
        }

        # Get the appropriate PDF file
        field_name = report_fields.get(type_report)
        file_pdf = getattr(avatar, field_name, None) if avatar and field_name else None

        if avatar and file_pdf:
            pdf_data = base64.b64decode(file_pdf)
            filename = f"{avatar.name or 'document'}.pdf"
        else:
            # Fallback to dummy PDF in same folder as controller
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dummy_path = os.path.join(current_dir, 'sample-3.pdf')
            with open(dummy_path, 'rb') as f:
                pdf_data = f.read()
            filename = "sample-3.pdf"

        # Return with inline disposition to display in iframe
        return request.make_response(
            pdf_data,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{filename}"')
            ]
        )

    @http.route(['/<string:language_code>/love_match/<string:answer_token>', '/love_match/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def love_match(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_love_match_report', {'answer_token': answer_token})

    @http.route('/career_match/<string:answer_token>', type='http', auth='public', website=True, sitemap=False)
    def career_match(self, answer_token):
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_career_match_report', {'answer_token': answer_token})
    
    @http.route(['/<string:language_code>/soulfulness/<string:answer_token>', '/soulfulness/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def soulfulness(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_soulfulness_report', {'answer_token': answer_token})

    @http.route(['/<string:language_code>/five_elements/<string:answer_token>', '/five_elements/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def five_elements(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_five_elements_report', {'answer_token': answer_token})
    
    @http.route(['/<string:language_code>/thirty_one_types/<string:answer_token>', '/thirty_one_types/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def thirty_one_types(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_thirty_one_types_report', {'answer_token': answer_token})
    
    @http.route(['/<string:language_code>/tcm/<string:answer_token>', '/tcm/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def tcm(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_tcm_report', {'answer_token': answer_token})
    
    @http.route(['/<string:language_code>/ayurvedic_dosha/<string:answer_token>', '/ayurvedic_dosha/<string:answer_token>'], type='http', auth='public', website=True, sitemap=False)
    def ayurvedic_dosha(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_ayurvedic_dosha_report', {'answer_token': answer_token})
    
    @http.route(['/<string:language_code>/send_all_email/<string:answer_token>', '/send_all_email/<string:answer_token>'], type='http', auth='user', website=True, sitemap=False)
    def send_all_email(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        answer.sudo().with_delay().send_email_report(answer_token)
        return request.render('gm_web.thank_you_template', {'answer_token': answer_token})
    

    @http.route(['/<string:language_code>/send_email/<string:answer_token>', '/send_email/<string:answer_token>'], type='http', auth='user', website=True, sitemap=False)
    def send_email(self, language_code=None, answer_token=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})
        # set_survey_cookies(response, 
        #                   survey_token=answer.survey_id.access_token, 
        #                   answer_token=answer_token)
        return request.render('gm_survey.survey_page_send_email_report', {'answer_token': answer_token})

    @http.route(['/<string:language_code>/submit_selected_reports', '/submit_selected_reports'], type='http', auth="user", methods=['POST'], csrf=True, website=True)
    def submit_selected_reports(self, language_code=None, **post):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        answer_token = post.get('answer_token')
        answer = request.env['survey.user_input'].sudo().search([('access_token', '=', answer_token)], limit=1)
        if not answer:
            return request.render('http_routing.404', {})

        selected_reports = request.httprequest.form.getlist('reports')
        answer.sudo().with_delay().send_email_report(answer_token, selected_reports)
        return request.render('gm_web.thank_you_template', {'answer_token': answer_token})
