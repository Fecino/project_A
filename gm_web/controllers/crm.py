import datetime
import logging
import json
import base64
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import json

_logger = logging.getLogger(__name__)


class CrmPersonalizedController(http.Controller):
    """Controller for CRM personalized data page"""

    @http.route(['/<string:language_code>/my', '/my'], type='http', auth='user', website=True)
    def portal_my_home(self, language_code=None, **kwargs):
        """Custom dashboard home page"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        request.session['crm_lead_id'] = crm_leads.id if crm_leads else None
        formula = crm_leads.purchased_formula_ids.sorted(key=lambda x: x.id, reverse=True)
        if not formula:
            return request.redirect('/perfume-journey/create')
        purchased_formula = crm_leads.purchase_history_ids.sorted(key=lambda x: x.id, reverse=True)
        values = {
            'page_name': 'home',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'purchased_formula': purchased_formula,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
        }
        return request.render('gm_web.home_page', values)

    @http.route(['/<string:language_code>/my/formula/all', '/my/formula/all'], type='http', auth='user', website=True)
    def portal_my_formula_all(self, language_code=None, **kwargs):
        """Display all formulas for logged-in users"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchased_formula_ids.sorted(key=lambda x: x.id, reverse=True)
        fragrance = {fragrance.name.lower(): fragrance.color for fragrance in request.env['fragrance.family'].sudo().search([], order='id asc')}
        _logger.info("fragrance data: %s", fragrance)
        values = {
            'page_name': 'all_formulas',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'fragrance': fragrance,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
        }
        return request.render('gm_web.formula_all_page', values)

    @http.route(['/<string:language_code>/my/formula/<int:formula_id>', '/my/formula/<int:formula_id>'] , type='http', auth='user', website=True)
    def portal_my_formula_detail(self, formula_id, language_code=None, **kwargs):
        """Display details for a specific formula"""
        # Clear formula-related session data
        for key in ['formula_id', 'all_oil']:
            request.session.pop(key, None)
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchased_formula_ids.sudo().search([('id', '=', formula_id)], limit=1)
        if not formula:
            return request.redirect('/my/formula/all')
        fragrance = {fragrance.name.lower(): fragrance.color for fragrance in request.env['fragrance.family'].sudo().search([], order='id asc')}
        _logger.info("fragrance data: %s", fragrance)
        values = {
            'page_name': 'formula_detail',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'fragrance': fragrance,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
        }
        return request.render('gm_web.formula_detail_page', values)
    
    @http.route(['/<string:language_code>/my/formula-purchased/all', '/my/formula-purchased/all'], type='http', auth='user', website=True)
    def portal_my_formula_purchased_all(self, language_code=None, **kwargs):
        """Display all purchased formulas for logged-in users"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchase_history_ids.sorted(key=lambda x: x.id, reverse=True)
        fragrance = {fragrance.name.lower(): fragrance.color for fragrance in request.env['fragrance.family'].sudo().search([], order='id asc')}
        _logger.info("fragrance data: %s", fragrance)
        values = {
            'page_name': 'all_formulas',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'fragrance': fragrance,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
        }
        return request.render('gm_web.formula_purchased_all_page', values)

    @http.route(['/<string:language_code>/my/formula-purchased/<int:formula_id>', '/my/formula-purchased/<int:formula_id>'], type='http', auth='user', website=True)
    def portal_my_formula_purchased_detail(self, formula_id, language_code=None, **kwargs):
        """Display details for a specific formula"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchase_history_ids.sudo().search([('id', '=', formula_id)], limit=1)
        if not formula:
            return request.redirect('/my/formula/all')
        fragrance = {fragrance.name.lower(): fragrance.color for fragrance in request.env['fragrance.family'].sudo().search([], order='id asc')}
        _logger.info("fragrance data: %s", fragrance)
        values = {
            'page_name': 'formula_detail',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'fragrance': fragrance,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
        }
        return request.render('gm_web.formula_purchased_detail_page', values)
    
    @http.route(['/<string:language_code>/my/formula/bottling/<int:formula_id>/access', '/my/formula/bottling/<int:formula_id>/access'], type='http', auth='user', website=True)
    def portal_my_formula_bottling_access(self, formula_id, language_code=None, **kwargs):
        """Access bottling page for a specific formula"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchased_formula_ids.sudo().search([('id', '=', formula_id)], limit=1)
        if not formula:
            return request.redirect('/my/formula/all')
        values = {
            'page_name': 'bottling_access',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
        }
        return request.render('gm_web.formula_bottling_access_page', values)
    
    @http.route(['/<string:language_code>/my/formula/bottling/check_access', '/my/formula/bottling/check_access'], type='http', auth='user', methods=['POST'], csrf=False)
    def portal_my_formula_bottling_check_access(self, language_code=None, **kwargs):
        kwargs.update(json.loads(request.httprequest.data))
        access_code = kwargs.get('access_code', '')
        check_access_code = request.env['pos.access.code'].sudo().search([('name', '=', access_code)], limit=1)
        if not check_access_code:
            return request.make_response(
                json.dumps({'success': False, 'message': 'Invalid access code'}),
                [('Content-Type', 'application/json')]
            )
        if not check_access_code.is_valid:
            return request.make_response(
                json.dumps({'success': False, 'message': 'Access code is not valid'}),
                [('Content-Type', 'application/json')]
            )
        request.session['bottling_access_code_id'] = check_access_code.id
        return request.make_response(
            json.dumps({'success': True, 'message': 'Access granted','redirect_url': f"/my/formula/bottling/{kwargs.get('formula_id')}/start"}),
            [('Content-Type', 'application/json')]
        )
    

    @http.route(['/<string:language_code>/my/formula/bottling/<int:formula_id>/start', '/my/formula/bottling/<int:formula_id>/start'], type='http', auth='user', website=True)
    def portal_my_formula_bottling_start(self, formula_id, language_code=None, **kwargs):
        """Start bottling process for a specific formula"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchased_formula_ids.sudo().search([('id', '=', formula_id)], limit=1)
        if not formula:
            return request.redirect('/my/formula/all')
        flashcard = request.env['info.card'].sudo().search([('name','=','bottling_page')], limit=1)
        values = {
            'page_name': 'bottling_start',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
            'link_video': request.env['ir.config_parameter'].sudo().get_param('gm_scentopia.bottling_video_url', ''),
            'flashcard': flashcard,
        }
        return request.render('gm_web.formula_bottling_start_page', values)
    
    @http.route(['/<string:language_code>/my/formula/bottling/<int:formula_id>/pump', '/my/formula/bottling/<int:formula_id>/pump'], type='http', auth='user', website=True)
    def portal_my_formula_bottling_pump(self, formula_id, language_code=None, **kwargs):
        """Start bottling process for a specific formula"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchased_formula_ids.sudo().search([('id', '=', formula_id)], limit=1)
        if not formula:
            return request.redirect('/my/formula/all')
        values = {
            'page_name': 'bottling_start',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
            'link_video': request.env['ir.config_parameter'].sudo().get_param('gm_scentopia.pump_video_url', ''),
        }
        return request.render('gm_web.formula_bottling_pump_page', values)
    
    @http.route(['/<string:language_code>/my/formula/bottling/<int:formula_id>/seal', '/my/formula/bottling/<int:formula_id>/seal'], type='http', auth='user', website=True)
    def portal_my_formula_bottling_seal(self, formula_id, language_code=None, **kwargs):
        """Start bottling process for a specific formula"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchased_formula_ids.sudo().search([('id', '=', formula_id)], limit=1)
        if not formula:
            return request.redirect('/my/formula/all')
        values = {
            'page_name': 'bottling_start',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
            'link_video': request.env['ir.config_parameter'].sudo().get_param('gm_scentopia.seal_video_url', ''),
        }
        return request.render('gm_web.formula_bottling_seal_page', values)
    
    @http.route(['/<string:language_code>/my/formula/bottling/<int:formula_id>/finish', '/my/formula/bottling/<int:formula_id>/finish'], type='http', auth='user', website=True)
    def portal_my_formula_bottling_finish(self, formula_id, language_code=None, **kwargs):
        """Start bottling process for a specific formula"""
        user = request.env.user
        crm_leads = request.env['crm.lead'].sudo().search([('email_from', '=', user.email)], limit=1)
        if not crm_leads:
            return request.redirect('/perfume-journey/create')
        formula = crm_leads.purchased_formula_ids.sudo().search([('id', '=', formula_id)], limit=1)
        if not formula:
            return request.redirect('/my/formula/all')
        
        request.env['crm.lead.purchase.history'].sudo().create({
            'lead_id': crm_leads.id,
            'formula_id': formula.id,
            'formula_name': formula.formula_name,
            'purchase_formula_id': formula.id,
            'access_code': request.session.get('bottling_access_code_id', False),
            'purchase_date': datetime.datetime.now(),
            'bottle_size': crm_leads.bottle_size,
            'unit_price': formula.access_code_id.booking_price,
        })
        request.env['pos.access.code'].sudo().browse(request.session.get('bottling_access_code_id', False)).use_access_code()
        values = {
            'page_name': 'bottling_start',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'formulas': formula,
            'avatar': crm_leads.avatar_id.with_context(bin_size=False) if crm_leads and crm_leads.avatar_id else None,
            'link_video': request.env['ir.config_parameter'].sudo().get_param('gm_scentopia.seal_video_url', ''),
        }
        return request.render('gm_web.formula_bottling_finish_page', values)

    @http.route(['/<string:language_code>/api/save_formula_details', '/api/save_formula_details'], type='http', auth='user', methods=['POST'], csrf=False)
    def save_formula_details(self, language_code=None, **kwargs):
        """API endpoint to save details for a formula"""
        try:
            user = request.env.user
            data = json.loads(request.httprequest.data or '{}')
            formula_id = data.get('formula_id')
            formula_name = data.get('formula_name', '')
            notes = data.get('notes', '')

            _logger.info(f"Saving details for formula {formula_id} for user {user.email}")

            # Get user's CRM lead data
            formula = request.env['crm.lead.purchased.formula'].sudo().search([
                ('id', '=', formula_id),
                ('lead_id.email_from', '=', user.email)
            ], limit=1)
            if not formula:
                return request.make_response(
                    json.dumps({'success': False, 'message': 'Formula not found'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Update formula notes
            formula.sudo().write({
                'notes': notes,
                'formula_name': formula_name
            })
            
            _logger.info(f"Notes saved successfully for formula {formula_id}")
            
            return request.make_response(
                json.dumps({'success': True, 'message': 'Notes saved successfully'}),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.error(f"Error saving formula notes: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'success': False, 'message': 'Failed to save notes'}),
                headers=[('Content-Type', 'application/json')]
            )
        
    @http.route(['/<string:language_code>/api/save_formula_purchased_notes', '/api/save_formula_purchased_notes'], type='http', auth='user', methods=['POST'], csrf=False)
    def save_formula_purchased_notes(self, language_code=None, **kwargs):
        """API endpoint to save notes for a purchased formula"""
        _logger.info("Received request to save purchased formula notes")
        try:
            user = request.env.user
            data = json.loads(request.httprequest.data or '{}')
            formula_id = data.get('formula_id')
            notes = data.get('notes', '')
            
            _logger.info(f"Saving notes for formula {formula_id} for user {user.email}")
            
            # Get user's CRM lead data
            formula = request.env['crm.lead.purchase.history'].sudo().search([
                ('id', '=', formula_id),
                ('lead_id.email_from', '=', user.email)
            ], limit=1)
            if not formula:
                return request.make_response(
                    json.dumps({'success': False, 'message': 'Formula not found'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Update formula notes
            formula.sudo().write({
                'notes': notes
            })
            
            _logger.info(f"Notes saved successfully for formula {formula_id}")
            
            return request.make_response(
                json.dumps({'success': True, 'message': 'Notes saved successfully'}),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.error(f"Error saving formula notes: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({'success': False, 'message': 'Failed to save notes'}),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route(['/<string:language_code>/api/upload_photo_profile', '/api/upload_photo_profile'], type='http', auth='user', methods=['POST'], csrf=False)
    def upload_photo(self, language_code=None, **kwargs):
        import json
        data = json.loads(request.httprequest.data or '{}')
        image = data.get('image')
        if image:
            request.env.user.sudo().image_1920 = image
            return "success"
        return "no_image"