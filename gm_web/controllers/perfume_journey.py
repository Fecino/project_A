import json
from odoo import http
from odoo.http import request
import inflect
from datetime import datetime
import logging

log = logging.getLogger(__name__)

p = inflect.engine()

class PerfumeJourneyController(http.Controller):
    """Controller for managing perfume journey workflow with SOLID principles"""

    def _get_crm_lead(self):
        """Get CRM lead for current user"""
        return request.env['crm.lead'].sudo().search([('email_from', '=', request.env.user.email)], limit=1)

    def _get_crm_lead_by_uuid(self, uuid):
        """Get CRM lead by UUID"""
        return request.env['crm.lead'].sudo().search([('uuid', '=', uuid)], limit=1)

    def _initialize_session(self, crm_lead):
        """Initialize session with CRM lead data"""
        request.session['crm_lead_id'] = crm_lead.id if crm_lead else None
        if crm_lead:
            request.session['uuid'] = crm_lead.uuid

    def _get_avatar(self, crm_lead):
        """Get avatar image for CRM lead"""
        return crm_lead.avatar_id.with_context(bin_size=False) if crm_lead and crm_lead.avatar_id else None

    def _get_oil_value(self, crm_lead, bottle_size):
        """Get oil value based on bottle size"""
        bottle_field_map = {
            '100ml': 'value_manual' if all(crm_lead.sudo().fragrance_value_ids.mapped('value_manual')) else 'value',
            '50ml': 'value_50',
            '30ml': 'value_30'
        }
        field_name = bottle_field_map.get(bottle_size, 'value_30')
        return {x.fragrance_family_id.name.lower(): int(getattr(x, field_name)) for x in crm_lead.fragrance_value_ids}

    def _calculate_oil_drops(self, crm_lead, bottle_size):
        value = self._get_oil_value(crm_lead, bottle_size)
        sum_value = sum(value.values()) or 1
        multiplier = int(request.env['ir.config_parameter'].sudo().get_param('gm_scentopia.scentzania_oil_drop', default=100))
        bottle_size = 100 if bottle_size == '100ml' else 50 if bottle_size == '50ml' else 30
        return {str(x).lower(): int((value[x] / sum_value) * bottle_size) * multiplier for x in value}

    def _initialize_oil_session_data(self, crm_lead, location):
        """Initialize oil-related session data"""
        bottle_size = request.session.get('bottle_size', '30ml')
        log.info("calling this function")
        oil_max = request.session.get('max_drop', {})
        if not oil_max:
            if location == 'team_building':
                oil_max = self._calculate_oil_drops(crm_lead, bottle_size)
            else:
                oil_max = self._get_oil_value(crm_lead, bottle_size)
            request.session['max_drop'] = oil_max

        oil_added = request.session.get('oil_added', {})
        if not oil_added:
            oil_added = {str(x.fragrance_family_id.name).lower(): {} for x in crm_lead.fragrance_value_ids}
            request.session['oil_added'] = oil_added

        oil_remain = request.session.get('oil_remain', {})
        if not oil_remain:
            oil_remain = {}
            for fragrance_key in oil_max.keys():
                total_added = sum(oil_added.get(fragrance_key, {}).values()) if isinstance(oil_added.get(fragrance_key), dict) else 0
                oil_remain[fragrance_key] = max(oil_max.get(fragrance_key, 0) - total_added, 0)
            request.session['oil_remain'] = oil_remain

        return oil_added, oil_remain, oil_max

    def _prepare_fragrance_values(self, crm_lead, oil_added, oil_remain, oil_max):
        """Prepare fragrance value data for template"""
        value = {}
        for x in crm_lead.fragrance_value_ids:
            fragrance_name = x.fragrance_family_id.name.lower()
            oil_codes = oil_added.get(fragrance_name, {}) if isinstance(oil_added.get(fragrance_name), dict) else {}
            total_added = sum(oil_codes.values())
            
            value[fragrance_name] = {
                'oil_added': total_added,
                'oil_remain': oil_remain.get(fragrance_name, 0),
                'oil_max': oil_max.get(fragrance_name, 0),
                'oil_codes': oil_codes,
            }
        return value

    def _validate_scent_code(self, scent_code, category):
        """Validate scent code and return perfume details"""
        if not scent_code:
            return None, 'Please enter a scent code'

        if not category:
            return None, 'Please select a fragrance category'
        
        scent_code = str(scent_code).strip().upper()
        fragrance_id = request.env['fragrance.family'].sudo().search([('name', 'ilike', category)], limit=1)
        perfume = request.env['perfume.details'].sudo().search([('name_code', '=', scent_code), ('main_category_id', '=', fragrance_id.id)], limit=1)
        
        if not perfume:
            return None, f'Invalid scent code: {scent_code}'
        
        return perfume, 'Scent code found!'

    def _get_oil_counts(self, category, location):
        """Calculate oil counts for given category and location"""
        # Count oil added in current category only
        oil_added = request.session.get('oil_added', {}).get(category.lower(), {})
        oil_added_count = sum(oil_added.values())
        
        # Count all oil added across all categories
        oil_added_all = sum(sum(rec.values()) for rec in request.session.get('oil_added', {}).values())
        
        oil_max = request.session.get('max_drop', {}).get(category.lower(), 0)
        oil_max_all = sum(request.session.get('max_drop', {}).values())
        
        return oil_added_count, oil_max, oil_max_all, oil_added_all

    def _prepare_perfume_details(self, perfume_data):
        """Prepare perfume details for template"""
        return {
            'oil_code': perfume_data.name_code or '-',
            'oil_name': perfume_data.perfume_name or '-',
            'oil_main_categ': perfume_data.main_category_id.name or '-',
            'oil_strength': perfume_data.strength or '-',
            'oil_gender': perfume_data.gender.title() if perfume_data.gender else '-',
            'oil_about': perfume_data.scent_writeup or '-',
            'oil_main_note': perfume_data.main_note or '-',
            'oil_top_note': perfume_data.top_note or '-',
            'oil_middle_note': perfume_data.middle_note or '-',
            'oil_base_note': perfume_data.base_note or '-',
            'oil_historical_significance': perfume_data.historical_significance or '-',
            'oil_health_benefits': perfume_data.health_benefits or '-',
            'oil_main_accords': perfume_data.main_accords or '-',
        }

    def _create_formula_record(self, crm_lead, oil_added):
        """Create formula record in database"""
        formula_name = "My Formula " + datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Organize oils by fragrance family
        fragrance_oils = {'citrus': [], 'fresh': [], 'floral': [], 'woody': [], 'oriental': []}
        
        for key, value in oil_added.items():
            if key in fragrance_oils:
                for oil_code, drop_count in value.items():
                    oil_record = request.env['perfume.details'].sudo().search([('name_code', '=', oil_code)], limit=1)
                    if oil_record:
                        fragrance_oils[key].append(oil_record.id)

        formula_vals = {
            'lead_id': crm_lead.id,
            'formula_name': formula_name,
            'sample_citrus': [(6, 0, fragrance_oils['citrus'])],
            'sample_fresh': [(6, 0, fragrance_oils['fresh'])],
            'sample_floral': [(6, 0, fragrance_oils['floral'])],
            'sample_woody': [(6, 0, fragrance_oils['woody'])],
            'sample_oriental': [(6, 0, fragrance_oils['oriental'])],
            'formula_purchased': False,
            'perfume_picture': False,
            'bottle_size': request.session.get('bottle_size', '30ml'),
            'access_code_id': request.session.get('access_code_id'),
            'location': request.session.get('location', ''),
        }
        
        return request.env['crm.lead.purchased.formula'].sudo().create(formula_vals)

    def _create_team_building_drops(self, formula_record, crm_lead, oil_added):
        """Create team building drop records"""
        for fragrance_type, oils in oil_added.items():
            formula_drop = request.env['crm.lead.purchased.formula.drop'].sudo().create({
                'formula_id': formula_record.id,
                'lead_id': crm_lead.id,
            })
            
            data_oil = []
            for oil_code, drop_count in oils.items():
                oil_id = request.env['perfume.details'].sudo().search([('name_code', '=', oil_code)], limit=1)
                data_oil.append({
                    'drop_count': drop_count,
                    'oil_id': oil_id.id,
                    'purchase_formula_id': formula_drop.id,
                })
            request.env['crm.lead.purchased.formula.drop.line'].sudo().create(data_oil)

    def _clean_session(self):
        """Clean up session data"""
        for key in ['oil_added', 'oil_remain', 'max_drop', 'location']:
            request.session.pop(key, None)

    def _set_language_context(self):
        """Set language context based on session"""
        lang = request.session.get('lang', 'en_US')
        request.session['context']['lang'] = lang
        request.env.context = dict(request.env.context, lang=lang)

    @http.route(['/<string:language_code>/perfume-journey/create', '/perfume-journey/create'], type='http', auth='user', website=True)
    def perfume_journey(self, language_code=None, **kwargs):
        """Main perfume journey entry point"""
        self._set_language_context()
        crm_leads = self._get_crm_lead()
        self._initialize_session(crm_leads)
        
        values = {
            'page_name': 'home',
            'user': request.env.user,
            'crm_leads': crm_leads,
            'avatar': self._get_avatar(crm_leads),
        }
        return request.render('gm_web.perfume_journey_create_page', values)

    @http.route(['/<string:language_code>/perfume-journey/access', '/perfume-journey/access'], type='http', auth='user', website=True)
    def access_page(self, language_code=None, **kwargs):
        """Display access page for user preferences"""
        self._clean_session()
        self._set_language_context()
        values = {
            'user': request.env.user,
            'page_name': 'access',
        }
        return request.render('gm_web.access_page_template', values)

    @http.route(['/<string:language_code>/perfume-journey/check-access-code', '/perfume-journey/check-access-code'], type='http', auth='user', methods=['POST'], csrf=False)
    def check_access_code(self, language_code=None, **kwargs):
        kwargs.update(json.loads(request.httprequest.data))
        access_code = kwargs.get('access_code', '')
        check_access_code = request.env['pos.access.code'].sudo().search([('name', '=', access_code), ('is_valid', '=', True)], limit=1)
        if not check_access_code:
            return request.make_response(
                json.dumps({'success': False, 'message': 'Invalid access code'}),
                [('Content-Type', 'application/json')]
            )
        return request.make_response(
            json.dumps({'success': True, 'message': 'Access granted'}),
            [('Content-Type', 'application/json')]
        )

    @http.route(['/<string:language_code>/perfume-journey/access/submit', '/perfume-journey/access/submit'], type='http', auth='user', website=True, csrf=True)
    def set_language(self, language_code=None, **kwargs):
        """Process access form submission"""
        self._clean_session()
        location = kwargs.get('location', 'scentzania')
        access_code = kwargs.get('access_code', '')
        check_access_code = request.env['pos.access.code'].sudo().search([('name', '=', access_code), ('is_valid', '=', True)], limit=1)
        bottle_size = check_access_code.bottle_size
        crm_lead_id = request.session.get('crm_lead_id') or self._get_crm_lead().id
        crm_lead = request.env['crm.lead'].sudo().browse(crm_lead_id)
        crm_lead.sudo().write({'bottle_size': bottle_size})
        
        request.session.update({
            'bottle_size': bottle_size,
            'location': location,
            'access_code_id': check_access_code.id,
        })
        return request.redirect('/perfume-journey/pre-intro')
    
    @http.route(['/<string:language_code>/perfume-journey/pre-intro', '/perfume-journey/pre-intro'], type='http', auth='user', website=True)
    def pre_intro_page(self, language_code=None, **kwargs):
        """Display pre-introduction page"""
        self._set_language_context()
        crm_lead_id = request.session.get('crm_lead_id') or self._get_crm_lead().id
        crm_lead = request.env['crm.lead'].sudo().browse(crm_lead_id)
        
        values = {
            'avatar': self._get_avatar(crm_lead),
        }
        return request.render('gm_web.pre_intro_page_template', values)

    @http.route(['/<string:language_code>/perfume-journey/intro', '/perfume-journey/intro'], type='http', auth='user', website=True)
    def intro_page(self, language_code=None, **kwargs):
        """Display introduction page"""
        self._set_language_context()
        crm_lead_id = request.session.get('crm_lead_id') or self._get_crm_lead().id
        crm_lead = request.env['crm.lead'].sudo().browse(crm_lead_id)
        flashcard_id = request.env['info.card'].sudo().search([('name', '=', 'intro_app')], limit=1)
        values = {
            'avatar': self._get_avatar(crm_lead),
            'location': request.session.get('location', ''),
            'flashcard': flashcard_id.with_context(bin_size=False),
        }
        return request.render('gm_web.intro_page_template', values)

    def _create_intro_page_values(self, card_name, page_name=None):
        """Create standardized values for introduction pages"""
        flashcard = request.env['info.card'].sudo().search([('name', '=', card_name)], limit=1)
        value = {
            'flashcard': flashcard.with_context(bin_size=False),
            'avatar': self._get_avatar(self._get_crm_lead()),
            'page_name': page_name or card_name,
            'text': flashcard.mastertext if flashcard else '',
            'subtext': flashcard.subtext if flashcard else '',
        }
        if card_name == "test_result":
            value['value_data'] = self._get_oil_value(self._get_crm_lead(), request.session.get('bottle_size', '30ml'))
        return value

    def _render_intro_page(self, card_name, template_name, page_name=None):
        """Render introduction page with standard values"""
        values = self._create_intro_page_values(card_name, page_name)
        return request.render(f'gm_web.{template_name}', values)

    @http.route(['/<string:language_code>/perfume-journey/intro/scent-paper', '/perfume-journey/intro/scent-paper'], type='http', auth='user', website=True)
    def intro_scent_paper_page(self, language_code=None, **kwargs):
        """Display scent paper introduction page"""
        self._set_language_context()
        return self._render_intro_page('scent_paper', 'intro_scent_paper_page_template')
    
    @http.route(['/<string:language_code>/perfume-journey/intro/collect-sticker', '/perfume-journey/intro/collect-sticker'], type='http', auth='user', website=True)
    def intro_collect_sticker_page(self, language_code=None, **kwargs):
        """Display collect sticker introduction page"""
        self._set_language_context()
        return self._render_intro_page('collect_sticker', 'intro_collect_sticker_page_template')
    
    @http.route(['/<string:language_code>/perfume-journey/intro/test-result', '/perfume-journey/intro/test-result'], type='http', auth='user', website=True)
    def intro_test_result_page(self, language_code=None, **kwargs):
        """Display test result introduction page"""
        self._set_language_context()
        return self._render_intro_page('test_result', 'intro_test_result_page_template')
    
    @http.route(['/<string:language_code>/perfume-journey/intro/female-wand', '/perfume-journey/intro/female-wand'], type='http', auth='user', website=True)
    def intro_female_wand_page(self, language_code=None, **kwargs):
        """Display female wand introduction page"""
        self._set_language_context()
        return self._render_intro_page('female_scent_ward', 'intro_female_wand_page_template')

    @http.route(['/<string:language_code>/perfume-journey/intro/male-wand', '/perfume-journey/intro/male-wand'], type='http', auth='user', website=True)
    def intro_male_wand_page(self, language_code=None, **kwargs):
        """Display male wand introduction page"""
        self._set_language_context()
        return self._render_intro_page('male_scent_ward', 'intro_male_wand_page_template')
    
    @http.route(['/<string:language_code>/perfume-journey/intro/unisex-wand', '/perfume-journey/intro/unisex-wand'], type='http', auth='user', website=True)
    def intro_unisex_wand_page(self, language_code=None, **kwargs):
        """Display unisex wand introduction page"""
        self._set_language_context()
        return self._render_intro_page('unisex_scent_ward', 'intro_unisex_wand_page_template')

    @http.route(['/<string:language_code>/perfume-journey/intro/smell-scent-ward', '/perfume-journey/intro/smell-scent-ward'], type='http', auth='user', website=True)
    def intro_smell_scent_ward_page(self, language_code=None, **kwargs):
        """Display smell scent ward introduction page"""
        self._set_language_context()
        return self._render_intro_page('smell_scent_ward', 'intro_smell_scent_ward_page_template')

    @http.route(['/<string:language_code>/perfume-journey/intro/marking-scent-paper', '/perfume-journey/intro/marking-scent-paper'], type='http', auth='user', website=True)
    def intro_marking_scent_paper_page(self, language_code=None, **kwargs):
        """Display marking scent paper introduction page"""
        self._set_language_context()
        return self._render_intro_page('marking_scent_paper', 'intro_marking_scent_paper_page_template')

    @http.route(['/<string:language_code>/perfume-journey/intro/part-of-plant', '/perfume-journey/intro/part-of-plant'], type="http", auth="user", website=True)
    def part_of_plant(self, language_code=None, **kwargs):
        """Display part of plant introduction page"""
        self._set_language_context()
        return self._render_intro_page('part_of_plants', 'intro_part_of_plants_page_template')

    @http.route(['/<string:language_code>/perfume-journey/formula-guide', '/perfume-journey/formula-guide'], type="http", auth="user", website=True)
    def formula_guide(self, language_code=None, **kwargs):
        """Display formula guide introduction page"""
        self._set_language_context()
        return self._render_intro_page('formula_guide', 'intro_formula_guide_page_template')

    @http.route(['/<string:language_code>/perfume-journey/fragrance-selection', '/perfume-journey/fragrance-selection'], type='http', auth="user", website=True)
    def fragrance_selection_page_drop(self, language_code=None, **kwargs):
        """Main fragrance selection interface"""
        self._set_language_context()
        location = kwargs.get('location', False) or request.session.get('location', False)
        if not location:
            return request.redirect('/perfume-journey/access')
        log.info(f"session before setting location: {dict(request.session)}")
        request.session['location'] = location
        crm_leads = self._get_crm_lead()
        self._initialize_session(crm_leads)
        
        oil_added, oil_remain, oil_max = self._initialize_oil_session_data(crm_leads, location)
        value = self._prepare_fragrance_values(crm_leads, oil_added, oil_remain, oil_max)
        is_complete = all(v['oil_remain'] == 0 for v in value.values())
        log.info(f"oil_added: {oil_added}, oil_remain: {oil_remain}, oil_max: {oil_max}")
        log.info(f"Request session data: {dict(request.session)}")
        values = {
            'page_title': 'Choose Your Fragrance',
            'user': request.env.user,
            'crm_lead': crm_leads,
            'values': value,
            'avatar': self._get_avatar(crm_leads),
            'is_complete': is_complete,
            'location': location,
            'formula_id': request.session.get('formula_id', False),
        }
        log.info(f"values prepared for rendering: {values}")
        return request.render('gm_web.fragrance_selection_drop_template', values)
    
    @http.route(['/<string:language_code>/perfume-journey/fragrance-selection/reset', '/perfume-journey/fragrance-selection/reset'], type='http', auth="user", website=True)
    def fragrance_selection_reset_page(self, language_code=None, **kwargs):
        location = request.session.get('location', False)
        self._clean_session()
        return request.redirect(f'/perfume-journey/fragrance-selection?location={location}' if location else '/perfume-journey/fragrance-selection')

    @http.route(['/<string:language_code>/perfume-journey/fragrance-selection/edit', '/perfume-journey/fragrance-selection/edit'], type='http', auth="user", website=True)
    def fragrance_selection_edit_page(self, language_code=None, **kwargs):
        self._set_language_context()
        crm_leads = self._get_crm_lead()
        self._initialize_session(crm_leads)
        location = request.session.get('location', False)
        
        oil_added, oil_remain, oil_max = self._initialize_oil_session_data(crm_leads, location)
        value = self._prepare_fragrance_values(crm_leads, oil_added, oil_remain, oil_max)
        
        values = {
            'page_title': 'Edit Your Fragrance Selection',
            'user': request.env.user,
            'crm_lead': crm_leads,
            'values': value,
            'avatar': self._get_avatar(crm_leads),
            'location': location
        }
        return request.render('gm_web.fragrance_selection_edit_drop_template', values)
    
    @http.route(['/<string:language_code>/perfume-journey/api/update-selected-oil', '/perfume-journey/api/update-selected-oil'], type='json', auth="user", website=True, csrf=False)
    def update_selected_oil(self, language_code=None, **kwargs):
        """Update selected oil data in session"""
        data = json.loads(request.httprequest.data) if request.httprequest.data else kwargs
        logging.info(f"Update Selected Oil called with parameters: {data}")
        
        try:
            location = request.session.get('location', 'scentzania')
            oil_added = request.session.get('oil_added', {})
            
            for fragrance_name, oil_codes in data.items():
                fragrance_key = fragrance_name.lower()
                
                if not oil_codes or oil_codes == [] or oil_codes is False:
                    oil_added[fragrance_key] = {}
                elif isinstance(oil_codes, list):
                    if location == "scentzania":
                        # For scentzania, always set value to 1
                        oil_added[fragrance_key] = {oil_code: 1 for oil_code in oil_codes}
                    else:  # team_building
                        # For team_building, preserve previous values or set to 1 if new
                        current_oils = oil_added.get(fragrance_key, {})
                        oil_added[fragrance_key] = {
                            oil_code: current_oils.get(oil_code, 1) for oil_code in oil_codes
                        }
            
            request.session['oil_added'] = oil_added
            
            oil_max = request.session.get('max_drop', {})
            oil_remain = {}
            for fragrance_key in oil_max.keys():
                total_added = sum(oil_added.get(fragrance_key, {}).values()) if isinstance(oil_added.get(fragrance_key), dict) else 0
                oil_remain[fragrance_key] = max(oil_max.get(fragrance_key, 0) - total_added, 0)
            
            request.session['oil_remain'] = oil_remain
            
            return {
                'success': True,
                'message': 'Oil selection updated successfully',
                'oil_added': oil_added,
                'oil_remain': oil_remain
            }
            
        except Exception as e:
            logging.error(f"Error updating selected oil: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating oil selection: {str(e)}'
            }
            
    @http.route(['/<string:language_code>/perfume-journey/api/validate-oil-code', '/perfume-journey/api/validate-oil-code'], type='json', auth="user", website=True, csrf=False)
    def validate_scent_code_api_drop(self, language_code=None, **kwargs):
        """API endpoint for scent code validation"""
        try:
            perfume, message = self._validate_scent_code(kwargs.get('scent_code', ''), kwargs.get('category', ''))
            
            if not perfume:
                return {'success': False, 'message': message}
                
            return {
                'success': True,
                'message': message,
                'redirect_url': f'/perfume-journey/oil-detail?code={perfume.name_code}&category={kwargs.get("category","")}'
            }
        except Exception as e:
            return {'success': False, 'message': f'Error validating scent code: {str(e)}'}

    @http.route(['/<string:language_code>/perfume-journey/oil-detail', '/perfume-journey/oil-detail'], type='http', auth="user", website=True)
    def perfume_start_02_page_drop(self, language_code=None, **kwargs):
        """Display detailed oil information"""
        if not kwargs.get('code') or not kwargs.get('category'):
            return request.render('http_routing.404', {})
            
        perfume_data = request.env['perfume.details'].sudo().search([('name_code', '=', kwargs.get('code'))], limit=1)
        category = kwargs.get('category')
        crm_lead = self._get_crm_lead_by_uuid(request.session.get('uuid', ''))
        fragrance_families = request.env['fragrance.family'].sudo().search([('name', 'ilike', category)], order='name asc')
        
        oil_added_count, oil_max, oil_max_all, oil_added_all = self._get_oil_counts(category, request.session.get('location'))
        oil_added_fragrance = request.session.get('oil_added', {}).get(category.lower(), {})
        oil_order = p.ordinal(len(oil_added_fragrance) + 1)
        self._set_language_context()
        values = {
            'page_title': 'Perfume Journey - Step 1',
            'category': category,
            'user': request.env.user,
            'fragrance_families': fragrance_families,
            'oil_order': oil_order,
            'oil_max': oil_max,
            'oil_added_count': oil_added_count,
            'value': self._prepare_perfume_details(perfume_data),
            'avatar': self._get_avatar(crm_lead),
            'location': request.session.get('location'),
            'oil_max_all': oil_max_all,
            'oil_added_all': oil_added_all,
        }
        return request.render('gm_web.perfume_start_02_drop_template', values)

    @http.route(['/<string:language_code>/perfume-journey/select-oil', '/perfume-journey/select-oil'], type='http', auth="user", website=True)
    def perfume_start_01_page_drop(self, language_code=None, **kwargs):
        """Oil selection input interface"""
        self._set_language_context()
        category = kwargs.get('category')
        if not category:
            return request.render('http_routing.404', {})
            
        crm_lead = self._get_crm_lead_by_uuid(request.session.get('uuid', ''))
        fragrance_families = request.env['fragrance.family'].sudo().search([('name', 'ilike', category)], order='name asc')
        
        oil_added_count, oil_max, oil_max_all, oil_added_all = self._get_oil_counts(category, request.session.get('location'))
        oil_added_fragrance = request.session.get('oil_added', {}).get(category.lower(), {})
        oil_order = p.ordinal(len(oil_added_fragrance) + 1)
        oil_percentage = int(oil_max / oil_max_all * 100)
        fragrance_text = fragrance_families.value_ids.filtered(lambda r: r.percentage_start <= oil_percentage <= r.percentage_end)
        
        values = {
            'page_title': 'Perfume Journey - Step 1',
            'category': category,
            'user': request.env.user,
            'fragrance_families': fragrance_families,
            'oil_order': oil_order,
            'oil_max': oil_max,
            'oil_added_count': oil_added_count,
            'avatar': self._get_avatar(crm_lead),
            'location': request.session.get('location'),
            'oil_max_all': oil_max_all,
            'oil_added_all': oil_added_all,
            'oil_percentage': oil_percentage,
            'fragrance_text': fragrance_text[0].label if fragrance_text else '',
        }
        return request.render('gm_web.perfume_start_01_drop_optimized_template', values)

    @http.route(['/<string:language_code>/perfume-journey/oil-drop', '/perfume-journey/oil-drop'], type='http', auth="user", website=True)
    def oil_drop_page(self, language_code=None, **kwargs):
        """Oil drop calculation interface"""
        self._set_language_context()
        fragranceName = str(kwargs.get('category', 'Citrus')).strip().lower()
        uuid = kwargs.get('uuid', '') or request.session.get('uuid')
        crm = self._get_crm_lead_by_uuid(uuid)
        
        if not crm or not uuid:
            return request.render('http_routing.404', {})
            
        request.session['uuid'] = uuid
        bottle_size = {'100ml': 100, '50ml': 50}.get(crm.sudo().bottle_size, 30)
        
        oil_added_fragrance = request.session.get('oil_added', {}).get(fragranceName, {})
        oil_added_count = sum(oil_added_fragrance.values())
        oil_order = p.ordinal(len(oil_added_fragrance) + 1)
        oil_max = request.session.get('max_drop', {}).get(fragranceName, 0)
        
        value = request.session.get('oil_remain')
        if not value:
            value = self._calculate_oil_drops(crm, bottle_size)
        else:
            try:
                value = {str(k).lower(): int(v) for k, v in value.items()}
            except Exception:
                pass
        request.session['oil_remain'] = value
        
        oil_data = request.env['perfume.details'].sudo().search([('name_code', '=', kwargs.get('oil_code'))], limit=1)
        
        values = {
            'fragrance_name': kwargs.get('category', 'Citrus'),
            'oil_code': oil_data.name_code if oil_data else '',
            'oil_name': oil_data.perfume_name if oil_data else '',
            'value': value,
            'oil_order': oil_order,
            'oil_max': oil_max,
            'oil_added_count': oil_added_count,
            'category': fragranceName,
            'avatar': self._get_avatar(crm)
        }
        return request.render('gm_web.oil_drop_template', values)

    @http.route(['/<string:language_code>/perfume-journey/api/save-formula', '/perfume-journey/api/save-formula'], type='json', auth="user", website=True, csrf=False)
    def save_formula_api_drop(self, language_code=None, **kwargs):
        """Save user formula to database"""
        self._set_language_context()
        crm_lead = self._get_crm_lead_by_uuid(request.session.get('uuid', ''))
        oil_added = request.session.get('oil_added', {})
        
        formula_record = self._create_formula_record(crm_lead, oil_added)
        request.session['formula_id'] = formula_record.id
        if request.session.get('location') == 'team_building':
            self._create_team_building_drops(formula_record, crm_lead, oil_added)
            access_code = request.env['pos.access.code'].sudo().browse(request.session.get('access_code_id'))
            access_code.sudo().use_access_code()
            history = request.env['crm.lead.purchase.history'].sudo().create({
                'lead_id': crm_lead.id,
                'formula_id': formula_record.id,
                'formula_name': formula_record.formula_name,
                'purchase_formula_id': formula_record.id,
                'access_code': access_code.id,
                'purchase_date': datetime.datetime.now(),
                'bottle_size': crm_lead.bottle_size,
                'unit_price': formula_record.access_code_id.booking_price,
            })

            request.session['purchase_history_id'] = history.id

        userFormula = {key: list(value.keys()) for key, value in oil_added.items()}
        self._clean_session()
        
        return {
            'success': True,
            'message': 'Formula saved successfully!',
            'formula_id': formula_record.id,
            'formula_name': formula_record.formula_name,
            'userFormula': userFormula
        }

    @http.route(['/<string:language_code>/perfume-journey/add-oil', '/perfume-journey/add-oil'], type='http', auth="user", website=True)
    def add_oil_page(self, language_code=None, **kwargs):
        self._set_language_context()
        location = kwargs.get('location') or request.session.get('location')
        fragranceName_raw = kwargs.get('fragranceName', '') or kwargs.get('category', '')
        fragranceName = str(fragranceName_raw).strip().lower()
        oilCode = kwargs.get('oilCode', '') or kwargs.get('oil_code', '')
        
        try:
            count = max(0, int(kwargs.get('dropCountInput', '0')))
        except Exception:
            count = 0
            
        if location == "scentzania":
            count = 1

        # Update session data
        oil_added = request.session.get('oil_added', {})
        if not isinstance(oil_added, dict):
            oil_added = {}
        if fragranceName not in oil_added or not isinstance(oil_added.get(fragranceName), dict):
            oil_added[fragranceName] = {}

        # Accumulate drops for the same oil code
        prev_count = oil_added[fragranceName].get(oilCode, 0)
        oil_added[fragranceName][oilCode] = prev_count + count
        request.session['oil_added'] = oil_added

        # Update remaining drops
        value = request.session.get('oil_remain', {})
        value = {str(k).lower(): max(0, int(v) - (count if str(k).lower() == fragranceName else 0)) for k, v in value.items()}
        request.session['oil_remain'] = value
        return request.redirect(f'/perfume-journey/oil-added?category={fragranceName_raw}&oil_code={oilCode}')

    @http.route(['/<string:language_code>/perfume-journey/oil-added', '/perfume-journey/oil-added'], type='http', auth="user", website=True)
    def oil_drop_added_page(self, language_code=None, **kwargs):
        """Confirmation page after adding oil drops"""
        self._set_language_context()
        location = kwargs.get('location') or request.session.get('location')
        fragranceName_raw = kwargs.get('fragranceName', '') or kwargs.get('category', '')
        fragranceName = str(fragranceName_raw).strip().lower()
        oilCode = kwargs.get('oilCode', '') or kwargs.get('oil_code', '')

        crm_lead = self._get_crm_lead_by_uuid(request.session.get('uuid', ''))
        oil_added_count, oil_max, oil_max_all, oil_added_all = self._get_oil_counts(fragranceName, location)
        oil_added_fragrance = request.session.get('oil_added', {}).get(fragranceName, {})
        oil_order = p.ordinal(len(oil_added_fragrance) + 1)
        try:
            count = max(0, int(kwargs.get('dropCountInput', '0')))
        except Exception:
            count = 0
            
        if location == "scentzania":
            count = 1
        value = request.session.get('oil_remain', {})
        values = {
            'fragrance_name': fragranceName_raw,
            'oil_code': oilCode,
            'drop_count': count,
            'value': value,
            'oil_order': oil_order,
            'oil_max': oil_max,
            'oil_remain': request.session['oil_remain'].get(fragranceName, 0),
            'oil_added_count': oil_added_count,
            'category': fragranceName,
            'avatar': self._get_avatar(crm_lead),
            'location': location,
            'oil_max_all': oil_max_all,
            'oil_added_all': oil_added_all,
        }
        if oil_added_count == oil_max:
            return request.redirect(f'/perfume-journey/oil-maxed?category={fragranceName}')
        if location == "scentzania":
            flashcard_id = request.env['info.card'].sudo().search([('name', '=', 'oil_added')], limit=1)
            values['flashcard_id'] = flashcard_id.with_context(bin_size=False)
            
        return request.render('gm_web.oil_drop_added_template', values)

    @http.route(['/<string:language_code>/perfume-journey/oil-maxed', '/perfume-journey/oil-maxed'], type='http', auth="user", website=True)
    def oil_drop_maxed_page(self, language_code=None, **kwargs):
        """Page displayed when maximum oil drops for a category is reached"""
        self._set_language_context()
        fragranceName_raw = kwargs.get('fragranceName', '') or kwargs.get('category', '')
        fragranceName = str(fragranceName_raw).strip().lower()

        values = {
            'fragrance_name': fragranceName_raw,
            'category': fragranceName,
            'location' : request.session.get('location'),
            'avatar': self._get_avatar(self._get_crm_lead()),
        }
        return request.render('gm_web.oil_drop_maxed_template', values)

    @http.route(['/<string:language_code>/perfume-journey/formula-naming', '/perfume-journey/formula-naming'], type='http', auth="user", website=True)
    def formula_naming_page(self, language_code=None, **kwargs):
        """Page displayed for formula naming"""
        self._set_language_context()
        values = {
            'location' : request.session.get('location'),
            'avatar': self._get_avatar(self._get_crm_lead()),
            'formula_id' : request.session.get('formula_id', False),
            'formula_data': request.env['crm.lead.purchased.formula'].sudo().browse(int(request.session.get('formula_id', False))),
        }
        return request.render('gm_web.formula_naming_template', values)

    @http.route(['/<string:language_code>/api/change-name-formula', '/api/change-name-formula'], type='http', auth='user', methods=['POST'], csrf=False)
    def change_formula_name(self, language_code=None, **kwargs):
        """API endpoint to change formula name"""
        try:
            data = json.loads(request.httprequest.data)
            formula_name = data.get('formula_name', '').strip()
            formula_id = data.get('formula_id')
            
            if not formula_name or not formula_id:
                return request.make_response('Invalid parameters', status=400)
            
            formula = request.env['crm.lead.purchased.formula'].sudo().browse(int(formula_id))
            if not formula.exists():
                return request.make_response('Formula not found', status=404)
            formula.write({'formula_name': formula_name})
            if formula.location == "team_building":
                purchase_history = request.env['crm.lead.purchase.history'].sudo().search([('formula_id', '=', formula.id)], limit=1)
                purchase_history.write({'formula_name': formula_name})
            return request.make_response('success', status=200)
            
        except Exception as e:
            return request.make_response(f'Error: {str(e)}', status=500)

    @http.route(['/<string:language_code>/perfume-journey/invalid-perfume', '/perfume-journey/invalid-perfume'], type='http', auth="user", website=True)
    def invalid_perfume_page(self, language_code=None, **kwargs):
        """Route for invalid perfume selection page"""
        self._set_language_context()
        values = {
            'page_title': 'Invalid Perfume Selection',
            'user': request.env.user,
            'fragrance_category': kwargs.get('category', ''),
            'uuid': kwargs.get('uuid', '') or self._get_crm_lead().uuid,
            'avatar': self._get_avatar(self._get_crm_lead()),
        }
        request.session['fragrance'] = kwargs.get('category')
        return request.render('gm_web.invalid_perfume_template', values)
    
    @http.route(['/<string:language_code>/perfume-journey/change-value', '/perfume-journey/change-value'], type='http', auth="user", website=True)
    def change_value(self, language_code=None, **kwargs):
        self._set_language_context()
        crm_lead_id = self._get_crm_lead_by_uuid(kwargs.get('uuid',''))
        if not crm_lead_id:
            return request.render('http_routing.404', {})
        has_manual_value = any([value.value_manual for value in crm_lead_id.fragrance_value_ids])
        fragrance_value = {}
        bottle_field_map = {
            '100ml': 'value_manual' if all(crm_lead_id.sudo().fragrance_value_ids.mapped('value_manual')) else 'value',
            '50ml': 'value_50',
            '30ml': 'value_30'
        }
        bottle_size = request.session.get('bottle_size', '30ml')
        field_name = bottle_field_map.get(bottle_size, 'value_30')
        fragrance_value = {x.fragrance_family_id: int(getattr(x, field_name)) for x in crm_lead_id.fragrance_value_ids}
        values = {
            'page_title': 'Change Value',
            'values' : fragrance_value,
            'uuid' : kwargs.get('uuid',''),
            'fragrance_selected' : request.session.get('fragrance', False),
            'value_changes' : request.session.get('data_changes', {}),
            'avatar': self._get_avatar(crm_lead_id),
            'bottle_size': bottle_size,
        }
        if kwargs.get('all_oil', False) or request.session.get('all_oil', False):
            values['all_oil'] = request.session['all_oil'] = True
            values['location'] = request.session.get('location', 'scentzania')
        return request.render('gm_web.change_value_template', values)
    
    @http.route(['/<string:language_code>/perfume-journey/set-value', '/perfume-journey/set-value'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def set_value(self, language_code=None, **kwargs):
        uuid = kwargs.get('uuid','')
        crm_id = request.env['crm.lead'].sudo().search([('uuid','=', uuid)], limit=1)
        if not crm_id or not uuid:
            return request.render('http_routing.404', {})
        data_changes = {}
        for rec in crm_id.fragrance_value_ids:
            data_changes[rec.fragrance_family_id.name] = kwargs.get(rec.fragrance_family_id.name, 0)
        request.session['uuid'] = uuid
        request.session['data_changes'] = data_changes
        return request.redirect(f'/perfume-journey/staff-validation?uuid={uuid}')

    @http.route(['/<string:language_code>/perfume-journey/staff-validation', '/perfume-journey/staff-validation'], type='http', auth="user", website=True)
    def staff_validation(self, language_code=None, **kwargs):
        self._set_language_context()
        uuid = kwargs.get('uuid','')
        crm_id = self._get_crm_lead_by_uuid(uuid)
        if not crm_id or not uuid:
            return request.render('http_routing.404', {})
        values = {
            'page_title': 'Staff Validation',
            'uuid' : uuid,
            'avatar': self._get_avatar(crm_id),
            'all_oil': request.session.get('all_oil', False),
        }
        return request.render('gm_web.staff_validation_template', values)
    
    @http.route(['/<string:language_code>/perfume-journey/check-code', '/perfume-journey/check-code'], type='http', auth='user', methods=['POST'], csrf=False)
    def check_code(self, language_code=None, **kwargs):
        kwargs.update(json.loads(request.httprequest.data))
        if not kwargs.get('staff_id', False) or not kwargs.get('access_code', False):
            return request.make_response(
                json.dumps({'success': False, 'message': 'Invalid staff ID or access code'}),
                [('Content-Type', 'application/json')]
            )
        staff = request.env['hr.employee'].sudo().search([('barcode','=', kwargs.get('staff_id'))], limit=1)
        if not staff:
            return request.make_response(
                    json.dumps({'success': False, 'message': 'Staff ID not found'}),
                    [('Content-Type', 'application/json')]
                )
        access_code = request.env['access.code.helper'].get_today_access_code()
        if access_code != kwargs.get('access_code'):
            return request.make_response(
                json.dumps({'success': False, 'message': 'Access code is incorrect, please try again'}),
                [('Content-Type', 'application/json')]
            )

        return request.make_response(
            json.dumps({'success': True, 'message': 'Access granted'}),
            [('Content-Type', 'application/json')]
        )

    @http.route(['/<string:language_code>/perfume-journey/submit-value', '/perfume-journey/submit-value'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def submit_value(self, language_code=None, **kwargs):
        staff = request.env['hr.employee'].sudo().search([('barcode','=', kwargs.get('staff_id'))], limit=1)
        if not staff:
            return request.render('http_routing.404', {})
        access_code = request.env['access.code.helper'].get_today_access_code()
        if access_code != kwargs.get('access_code'):
            return request.render('http_routing.404', {})
        uuid = request.session.get('uuid', False)
        crm_id = request.env['crm.lead'].sudo().search([('uuid','=', uuid)], limit=1)
        if not crm_id or not uuid:
            return request.render('http_routing.404', {})
        data_changes = request.session.get('data_changes', {})
        bottle_size = request.session.get('bottle_size', '30ml')
        bottle_size_field_map = {
            '100ml': 'value_manual',
            '50ml': 'value_50',
            '30ml': 'value_30'
        }
        field_name = bottle_size_field_map.get(bottle_size, 'value_30')
        
        for rec in crm_id.fragrance_value_ids.sudo():
            rec[field_name] = data_changes.get(rec.fragrance_family_id.name, 0)

        location = request.session.get('location', 'scentzania')
        request.session.pop('uuid', None)
        request.session.pop('data_changes', None)
        request.session.pop('fragrance', None)
        request.session.pop('access_code', None)
        self._clean_session()
        log.info("request.session after submit_value: %s", dict(request.session))
        return request.redirect(f'/perfume-journey/fragrance-selection?location={location}')


    @http.route(['/<string:language_code>/my/formula/oil_edit/<int:formula_id>', '/my/formula/oil_edit/<int:formula_id>'], type='http', auth='user', website=True)
    def edit_formula_page(self, language_code=None, formula_id=None, **kwargs):
        """Page for editing an existing formula"""
        self._clean_session()
        crm_lead = self._get_crm_lead()
        formula = request.env['crm.lead.purchased.formula'].sudo().search([('id', '=', formula_id), ('lead_id', '=', crm_lead.id)], limit=1)
        if not formula:
            return request.render('http_routing.404', {})
        
        oil_added = {}
        log.info(f"Editing formula ID: {formula_id} for CRM Lead ID: {crm_lead.id}")
        log.info(f"Formula details: {formula.read()}")
        # Initialize oil_added from formula samples
        sample_fields = ['sample_citrus', 'sample_floral', 'sample_woody', 'sample_fresh', 'sample_oriental']
        for field in sample_fields:
            fragrance_type = field.replace('sample_', '')
            samples = getattr(formula, field, [])
            log.info(f"samples: {samples}")
            if samples:
                oil_added[fragrance_type] = {sample.name_code: 1 for sample in samples}
        request.session['oil_added'] = oil_added
        request.session['bottle_size'] = formula.bottle_size
        oil_added_count, oil_remain, oil_max = self._initialize_oil_session_data(crm_lead, formula.location)
        request.session['location'] = formula.location or 'scentzania'
        request.session['oil_added_count'] = oil_added_count
        request.session['oil_remain'] = oil_remain
        request.session['oil_max'] = oil_max
        request.session['formula_id'] = formula.id
        return request.redirect(f"/perfume-journey/fragrance-selection?location={formula.location or 'scentzania'}")

    @http.route(['/<string:language_code>/my/formula/oil_save', '/my/formula/oil_save'], type='json', auth="user", website=True, csrf=False)
    def save_edited_formula_page(self, language_code=None, **kwargs):
        """Save changes to an existing formula"""
        data = json.loads(request.httprequest.data) if request.httprequest.data else kwargs
        formula_id = data.get('formula_id')
        crm_lead = self._get_crm_lead()
        formula = request.env['crm.lead.purchased.formula'].sudo().search([('id', '=', formula_id), ('lead_id', '=', crm_lead.id)], limit=1)
        if not formula:
            return request.render('http_routing.404', {})
        
        oil_added = request.session.get('oil_added', {})
        log.info(f"Saving edited formula ID: {formula_id} for CRM Lead ID: {crm_lead.id}")
        log.info(f"Oil added from session: {oil_added}")
        
        # Update formula samples based on oil_added
        sample_fields = {
            'citrus': 'sample_citrus',
            'floral': 'sample_floral',
            'woody': 'sample_woody',
            'fresh': 'sample_fresh',
            'oriental': 'sample_oriental',
        }
        update_data = {}
        for fragrance_type, field in sample_fields.items():
            oil_codes = oil_added.get(fragrance_type, {}).keys()
            oils = request.env['perfume.details'].sudo().search([('name_code', 'in', list(oil_codes))])
            update_data[field] = [(6, 0, oils.ids)]
            log.info(f"Updating {field} with oils: {oils.read()}")
        
        formula.sudo().write(update_data)
        log.info(f"Formula after update: {formula.read()}")
        
        # Clear session data related to editing
        request.session.pop('oil_added', None)
        request.session.pop('oil_added_count', None)
        request.session.pop('oil_remain', None)
        request.session.pop('oil_max', None)
        request.session.pop('formula_id', None)
        
        return {
            'success': True,
            'message': 'Formula saved successfully!',
            'formula_id': formula.id,
            'formula_name': formula.formula_name,
        }