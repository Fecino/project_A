import logging
from odoo import http, _
from odoo.http import request,route
from odoo.exceptions import UserError
from odoo.addons.web.controllers.home import SIGN_UP_REQUEST_PARAMS, Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.portal.controllers.web import Home
from odoo.addons.http_routing.models.ir_http import ModelConverter
from werkzeug.exceptions import NotFound
import json
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)

def link_survey_responses_to_user(user_id):
    """Helper function to link survey responses to authenticated user"""
    device_token = request.httprequest.cookies.get('device_token')
    answer_token = request.httprequest.cookies.get('answer_token')
    survey_token = request.httprequest.cookies.get('survey_token')
    
    if not device_token and not answer_token:
        _logger.info("No device_token or answer_token found for linking survey responses")
        return False
    
    # Build search domain for survey responses
    domain = [('partner_id', '=', False)]  # Only unlinked responses
    token_conditions = []
    
    if device_token:
        token_conditions.append(('device_token', '=', device_token))
    if answer_token:
        token_conditions.append(('access_token', '=', answer_token))
    
    if token_conditions:
        if len(token_conditions) > 1:
            domain = domain + ['|'] + token_conditions
        else:
            domain = domain + token_conditions
        
        survey_inputs = request.env['survey.user_input'].sudo().search(domain)
        
        if survey_inputs:
            user = request.env['res.users'].sudo().browse(user_id)
            survey_inputs.write({
                'partner_id': user.partner_id.id,
                'email': user.email
            })
            _logger.info(f"Successfully linked {len(survey_inputs)} survey responses to user {user_id}")
            return True
    
    _logger.info("No survey responses found to link")
    return False

class LangSelector(http.Controller):

    @http.route('/', type='http', auth='public', website=True)
    def landing(self):
        data = request.env['scentopia.web'].sudo().search([('id','=', request.env.ref('gm_web.scentopia_web_data').id)], limit=1)
        return request.render('gm_web.landing_page_template', {
            'data': data.with_context(bin_size=False)
        })

    @http.route(['/<string:language_code>/language-selector', '/language-selector'], type='http', auth='public', website=True)
    def language_selector(self, language_code=None):
        data = request.env['scentopia.web'].sudo().search([('id','=', request.env.ref('gm_web.scentopia_web_data').id)], limit=1)
        languages = request.env['res.lang'].sudo().search([('active', '=', True)])
        languages = sorted(languages, key=lambda l: l.code != 'en_US')
        return request.render('gm_web.language_selector_template', {
            'languages': languages,
            'data': data.with_context(bin_size=False)
        })

    @http.route('/set-language', type='http', auth='public', website=True, csrf=True)
    def set_language(self, **kwargs):
        lang_code = kwargs.get('language', 'en_US')
        request.session['temp_name'] = kwargs.get('name', '')
        gender = kwargs.get('gender', 'other')
        request.session['lang'] = lang_code
        response = request.redirect(f'/choose-test?lang={lang_code}')
        response.set_cookie('gender', gender, max_age=60*60*24*30)
        return response


    @http.route(['/<string:language_code>/choose-test','/choose-test'], type='http', auth='public', website=True)
    def choose_test(self, language_code=None):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        _logger.info(f"request sessions: {dict(request.session)}")
        return request.render('gm_web.choose_test_template', {'language_code': language_code})
    # @http.route('/', type='http', auth='public', website=True)
    # def home_redirect(self):
    #     return request.redirect('/language-selector')

class CountryPickerController(http.Controller):

    @http.route('/country/list', type='json', auth='public')
    def country_list(self):
        countries = request.env['res.country'].sudo().search([], order='name')
        return [{'id': c.id, 'name': c.name, 'flag_url': c.image_url} for c in countries]

class ErrorPageController(http.Controller):
    
    @http.route(['/<string:language_code>/404','/404', '/error', '/not-found'], type='http', auth='public', website=True)
    def error_404_page(self, **kwargs):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        """Custom 404 error page for missing pages or empty website"""
        values = {
            'page_title': 'Page Not Found - Scentzania',
            'error_code': '404',
            'error_message': 'Page not found or website is empty',
        }
        response = request.render('gm_web.error_404_template', values)
        response.status_code = 404
        return response
    
    @http.route(['/empty', '/maintenance'], type='http', auth='public', website=True)
    def maintenance_page(self, **kwargs):
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)
        """Maintenance or empty website page"""
        values = {
            'page_title': 'Website Under Maintenance - Scentzania',
            'error_code': 'MAINTENANCE',
            'error_message': 'Website is currently under maintenance',
        }
        return request.render('gm_web.error_404_template', values)

    # Catch-all route for any unmatched URLs - this must be at the end
    @http.route('/<path:path>', type='http', auth='public', website=True)
    def catch_all_404(self, path, **kwargs):
        """Catch all unmatched routes and show 404 page"""
        # Log the 404 for debugging
        _logger.info(f"404 Error - Path not found: /{path}")
        
        values = {
            'page_title': 'Page Not Found - Scentzania',
            'error_code': '404',
            'error_message': f'The page "/{path}" could not be found',
            'requested_path': f'/{path}',
        }
        response = request.render('gm_web.error_404_template', values)
        response.status_code = 404
        return response

class AuthSignupHome(Home):

    def do_signup(self, qcontext):
        name = qcontext.get('firstname', '') + ' ' + qcontext.get('lastname', '')
        qcontext['name'] = name.strip()
        """ Shared helper that creates a res.partner out of a token """
        values = {key: qcontext.get(key) for key in (
            'login', 'name', 'password', 'wk_dob', 
            'firstname', 'lastname', 'country_id', 'phone', 'gender'
        ) if qcontext.get(key) is not None}
        
        # Debug logging
        _logger.info(f"Signup values before processing: {values}")
        
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
            
        # Ensure required fields are present
        required_fields = ['login', 'password', 'firstname', 'lastname']
        for field in required_fields:
            if not values.get(field):
                raise UserError(_("Please fill in all required fields."))
        
        # Process country_id to ensure it's an integer
        if 'country_id' in values and values['country_id']:
            try:
                values['country_id'] = int(values['country_id'])
            except (ValueError, TypeError):
                _logger.warning(f"Invalid country_id format: {values['country_id']}")
                values.pop('country_id', None)
        
        # Ensure gender is one of the allowed values
        # if 'gender' in values and values['gender'] not in ['male', 'female', 'other']:
        #     _logger.warning(f"Invalid gender value: {values['gender']}")
        #     values.pop('gender', None)
        
        _logger.info(f"Processed signup values: {values}")
        
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '').split('_')[0]
        if lang in supported_lang_codes:
            values['lang'] = lang
            
        try:
            self._signup_with_values(qcontext.get('token'), values)
            request.env.cr.commit()
            _logger.info("User created successfully")
            
            # ENHANCED LINKING SURVEY TO PARTNER AFTER SIGNUP
            user = request.env['res.users'].sudo().search([('login', '=', values.get('login'))], limit=1)
            if user:
                _logger.info(f"Found user {user.id}, linking survey responses")
                link_survey_responses_to_user(user.id)
                
                # Update partner with additional fields if they exist
                partner_vals = {}
                if 'gender' in values:
                    partner_vals['gender'] = values['gender']
                # if 'bottle_size' in values:
                #     partner_vals['bottle_size'] = values['bottle_size']
                if 'wk_dob' in values:
                    partner_vals['wk_dob'] = values['wk_dob']
                if 'country_id' in values:
                    partner_vals['country_id'] = values['country_id']
                    
                if partner_vals:
                    _logger.info(f"Updating partner {user.partner_id.id} with values: {partner_vals}")
                    user.partner_id.sudo().write(partner_vals)
                    
        except Exception as e:
            _logger.error(f"Error during signup: {str(e)}", exc_info=True)
            request.env.cr.rollback()
            raise UserError(_("An error occurred during signup. Please try again or contact support if the problem persists."))

    def web_login(self, redirect=None, **kw):
        """Override web_login to link survey responses after successful login"""
        response = super().web_login(redirect=redirect, **kw)
        
        # Check if login was successful (user is authenticated)
        if request.session.uid and not request.env.user._is_public():
            _logger.info(f"User {request.session.uid} logged in successfully, checking for survey responses to link")
            link_survey_responses_to_user(request.session.uid)
        
        return response

class AuthSignup(AuthSignupHome):

    def get_auth_signup_qcontext(self):
        SIGN_UP_REQUEST_PARAMS.update({'wk_dob'})
        SIGN_UP_REQUEST_PARAMS.update({'firstname'})
        SIGN_UP_REQUEST_PARAMS.update({'lastname'})
        SIGN_UP_REQUEST_PARAMS.update({'country_id'})
        SIGN_UP_REQUEST_PARAMS.update({'gender'})
        # SIGN_UP_REQUEST_PARAMS.update({'bottle_size'})
        SIGN_UP_REQUEST_PARAMS.update({'phone'})
        return super().get_auth_signup_qcontext()
