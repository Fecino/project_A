from odoo import models, fields, api
import logging
import random

_logger = logging.getLogger(__name__)

class CrmLeadSurveyAnswer(models.Model):
    _name = 'crm.lead.survey.answer'
    _description = 'CRM Lead Survey Answer'

    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade')
    pertanyaan = fields.Char(string='Pertanyaan')
    jawaban = fields.Char(string='Jawaban')
    nilai = fields.Char(string='Nilai')

class CrmLeadPersonalityMapping(models.Model):
    _name = 'crm.lead.personality.mapping'
    _description = 'CRM Lead Personality Mapping'

    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade', index=True)
    survey_user_input_id = fields.Many2one('survey.user_input', string='Survey Input', ondelete='cascade', readonly=True,related='lead_id.survey_user_input_id')
    perfume_personality = fields.Char(string='Perfume Personality')
    personality_citrus = fields.Integer(string='C', related='survey_user_input_id.personality_citrus', readonly=True)
    personality_fresh = fields.Integer(string='FR', related='survey_user_input_id.personality_fresh', readonly=True)
    personality_floral = fields.Integer(string='FL', related='survey_user_input_id.personality_floral', readonly=True)
    personality_woody = fields.Integer(string='WD', related='survey_user_input_id.personality_woody', readonly=True)
    personality_oriental = fields.Integer(string='OR', related='survey_user_input_id.personality_oriental', readonly=True)
    persona_name = fields.Char(string='Persona Name')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string='Gender', related='survey_user_input_id.partner_id.gender', readonly=True)
    link_video = fields.Char(string='Link Video')
    avatar_img = fields.Many2one('scentopia.avatar', string="Avatar Image", related='survey_user_input_id.avatar_id')

class CrmLeadPurchasedFormula(models.Model):
    _name = 'crm.lead.purchased.formula'
    _description = 'Purchased Formula'

    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade')
    formula_id = fields.Char(string='Formula ID')
    formula_name = fields.Char(string='Formula Name')
    bottle_size = fields.Selection([
            ('30ml', '30ml'),
            ('50ml', '50ml'),
            ('100ml', '100ml'),
        ], string='Bottle Size', track_visibility='onchange')
    sample_citrus = fields.Many2many('perfume.details', 'formula_citrus_rel', 'formula_id', 'perfume_id', 
                                   string='Citrus Samples')
    sample_fresh = fields.Many2many('perfume.details', 'formula_fresh_rel', 'formula_id', 'perfume_id',
                                  string='Fresh Samples')
    sample_floral = fields.Many2many('perfume.details', 'formula_floral_rel', 'formula_id', 'perfume_id',
                                   string='Floral Samples')
    sample_woody = fields.Many2many('perfume.details', 'formula_woody_rel', 'formula_id', 'perfume_id',
                                  string='Woody Samples')
    sample_oriental = fields.Many2many('perfume.details', 'formula_oriental_rel', 'formula_id', 'perfume_id',
                                     string='Oriental Samples')
    
    formula_purchased = fields.Boolean(string='Formula Purchased')
    perfume_picture = fields.Char(string='Perfume Picture')
    
    # Computed fields for counts (for backward compatibility)
    citrus_count = fields.Integer(string='Citrus Count', compute='_compute_sample_counts', store=True)
    fresh_count = fields.Integer(string='Fresh Count', compute='_compute_sample_counts', store=True)
    floral_count = fields.Integer(string='Floral Count', compute='_compute_sample_counts', store=True)
    woody_count = fields.Integer(string='Woody Count', compute='_compute_sample_counts', store=True)
    oriental_count = fields.Integer(string='Oriental Count', compute='_compute_sample_counts', store=True)
    access_code_id = fields.Many2one('pos.access.code', string='Access Code')
    notes = fields.Text(string="Personal Notes")
    location = fields.Char(string="Location")
    
    @api.depends('sample_citrus', 'sample_fresh', 'sample_floral', 'sample_woody', 'sample_oriental')
    def _compute_sample_counts(self):
        for record in self:
            record.citrus_count = len(record.sample_citrus)
            record.fresh_count = len(record.sample_fresh)
            record.floral_count = len(record.sample_floral)
            record.woody_count = len(record.sample_woody)
            record.oriental_count = len(record.sample_oriental)
    
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.formula_name or record.formula_id or 'Unnamed Formula'

class CrmLeadPurchasedFormulaDrop(models.Model):
    _name = 'crm.lead.purchased.formula.drop'
    _description = 'CRM Lead Purchase Formula Drop'

    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade')
    formula_id = fields.Many2one('crm.lead.purchased.formula', string='Formula ID')
    bottle_size = fields.Selection(related='formula_id.bottle_size', string='Bottle Size', readonly=True)
    oil_drop = fields.One2many('crm.lead.purchased.formula.drop.line', 'purchase_formula_id', string='Oil Drops')

class CrmLeadPurchasedFormulaDropLine(models.Model):
    _name = 'crm.lead.purchased.formula.drop.line'
    _description = 'CRM Lead Purchase Formula Drop Line'

    purchase_formula_id = fields.Many2one('crm.lead.purchased.formula.drop', string='Purchase Formula', ondelete='cascade')
    oil_id = fields.Many2one('perfume.details', string='Oil')
    drop_count = fields.Integer(string='Drop Count', default=0)

    def _compute_display_name(self):
        for record in self:
            oil_name = record.oil_id.display_name if record.oil_id else 'Unknown oil'
            count = record.drop_count or 0
            record.display_name = f"{oil_name} - {count} Drop"

class CrmLeadPurchaseHistory(models.Model):
    _name = 'crm.lead.purchase.history'
    _description = 'CRM Lead Purchase History'
    _order = 'purchase_date desc'

    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade', required=True)
    formula_id = fields.Char(string='Formula ID', required=True)
    # formula_name = fields.Many2one('crm.lead.purchased.formula', string='Formula Name')
    formula_name = fields.Char(string='Formula Name')
    bottling_photo = fields.Binary(string='Bottling Photo')
    purchase_formula_id = fields.Many2one('crm.lead.purchased.formula', string='Purchased Formula')
    access_code = fields.Many2one(string='Access Code', related='purchase_formula_id.access_code_id')
    

    # Purchase Details
    purchase_date = fields.Datetime(string='Purchase Date', default=fields.Datetime.now, required=True)
    bottle_size = fields.Selection([
            ('30ml', '30ml'),
            ('50ml', '50ml'),
            ('100ml', '100ml'),
        ], string='Bottle Size', track_visibility='onchange')
    custom_size = fields.Char(string='Custom Size (ml)')
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    unit_price = fields.Float(string='Unit Price', digits='Product Price')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    # Order Information
    order_reference = fields.Char(string='Order Reference')
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], string='Payment Status', default='pending')
    delivery_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='Delivery Status', default='pending')
    
    # Additional Info
    notes = fields.Text(string='Notes')
    is_sample = fields.Boolean(string='Is Sample', help='Check if this is a sample purchase')
    is_gift = fields.Boolean(string='Is Gift', help='Check if this is a gift purchase')
    gift_recipient = fields.Char(string='Gift Recipient')
    
    # Formula Details (for reference)
    sample_citrus = fields.Char(string='Sample Citrus')
    sample_fresh = fields.Char(string='Sample Fresh')
    sample_floral = fields.Char(string='Sample Floral')
    sample_woody = fields.Char(string='Sample Woody')
    sample_oriental = fields.Char(string='Sample Oriental')
    perfume_picture = fields.Char(string='Perfume Picture')

    @api.depends('quantity', 'unit_price')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.quantity * record.unit_price

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValueError("Quantity must be greater than 0")

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        readonly=False,
    )

    @api.onchange('survey_user_input_id')
    def _onchange_survey_user_input_id(self):
        if self.survey_user_input_id and self.survey_user_input_id.partner_id:
            self.partner_id = self.survey_user_input_id.partner_id

    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string='Gender',related='partner_id.gender', readonly=True)
    wk_dob = fields.Date(string='Date of Birth',  related='partner_id.wk_dob',readonly=True)
    country = fields.Char(string='Country', related='partner_id.country_id.name', readonly=True)
    
    # POS Access Code fields
    booking_code = fields.Char(string='Booking Code')
    booking_price = fields.Float(string='Booking Price')
    booking_from = fields.Char(string='Booking From')
    access_code_json = fields.Text(string='Access Code JSON')
    
    bottle_size = fields.Selection([
        ('30ml', '30ml'),
        ('50ml', '50ml'),
        ('100ml', '100ml'),
    ], string='Bottle Size',)
    elite_package = fields.Boolean(string='Elite Package')
    survey_answers = fields.Text(string='Survey Answers')
    survey_user_input_id = fields.Many2one('survey.user_input', string='Survey User Input', readonly=True)
    survey_id = fields.Many2one('survey.survey', string='Survey', related='survey_user_input_id.survey_id', store=True, readonly=True)
    secondary_email = fields.Char(string='Secondary Email')
    fax = fields.Char(string='Fax')
    number_of_employees = fields.Integer(string='Number of Employees')
    annual_revenue = fields.Float(string='Annual Revenue')
    rating = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Rating')
    scentzania_id = fields.Char(string='Scentzania ID')
    personality_result = fields.Char(string='Personality Result')
    persona_name = fields.Char(string='Persona Name')
    avatar_img = fields.Char(string='Avatar Image')
    link_video = fields.Char(string='Link Video')
    soulfulness_report = fields.Boolean(string='Soulfulness Report')
    ayurvedic_dosha_report = fields.Boolean(string='Ayurvedic Dosha Report')
    career_match_report = fields.Boolean(string='Career Match Report')
    kcm_report = fields.Boolean(string='KCM Report')
    fifth_title_report = fields.Boolean(string='5th Title Report')
    sixth_title_report = fields.Boolean(string='6th Title Report')
    formula_id = fields.Char(string='Formula ID')
    sample_citrus = fields.Char(string='Sample Citrus')
    sample_fresh = fields.Char(string='Sample Fresh')
    sample_floral = fields.Char(string='Sample Floral')
    sample_woody = fields.Char(string='Sample Woody')
    sample_oriental = fields.Char(string='Sample Oriental')
    formula_purchased = fields.Boolean(string='Formula Purchased')
    survey_answer_lines = fields.One2many('crm.lead.survey.answer', 'lead_id', string='Survey Answer Lines')
    personality_mapping_lines = fields.One2many(
        'crm.lead.personality.mapping',
        'lead_id',
        compute='_compute_personality_mapping_lines',
        string='Personality Mapping Lines',
        store=True, readonly=False
    )

    purchased_formula_ids = fields.One2many('crm.lead.purchased.formula', 'lead_id', string='Purchased Formulas')
    purchase_history_ids = fields.One2many('crm.lead.purchase.history', 'lead_id', string='Purchase History')
    total_purchases = fields.Integer(string='Total Purchases', compute='_compute_purchase_stats', store=True)
    total_spent = fields.Float(string='Total Spent', compute='_compute_purchase_stats', store=True, digits='Product Price')
    last_purchase_date = fields.Datetime(string='Last Purchase Date', compute='_compute_purchase_stats', store=True)
    user_login = fields.Char(string='Username', compute='_compute_user_portal_fields', store=True)
    user_email = fields.Char(string='User Email', compute='_compute_user_portal_fields', store=True)
    user_name = fields.Char(string='User Name', compute='_compute_user_portal_fields', store=True)
    user_portal_id = fields.Many2one('res.users', string='Portal User', compute='_compute_user_portal_fields', store=True)

    avatar_id = fields.Many2one(related="survey_user_input_id.avatar_id")
    avatar_name = fields.Char(compute="set_avatar_name", string="Avatar Name")
    fragrance_value_ids = fields.One2many(related="survey_user_input_id.fragrance_value_ids")
    # user_input_line_ids = fields.One2many(related="survey_user_input_id.user_input_line_ids", 
    #                                 string="Survey Answer Lines", 
    #                                 readonly=True, 
    #                                 domain="[('fragrance_family_id', '==', True)]")
    user_input_line_ids = fields.One2many(
        'survey.user_input.line', 
        'user_input_id',
        string='Survey Answer Lines',
        compute='_compute_user_input_lines',
        store=False,
        readonly=True
    )
    formula_drop_ids = fields.One2many('crm.lead.purchased.formula.drop', 'lead_id', string='Formula Drops')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_mapping_lines()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._sync_mapping_lines()
        return result

    def _sync_mapping_lines(self):
        for rec in self:
            if rec.survey_user_input_id:
                mappings = self.env['crm.lead.personality.mapping'].search([
                    ('lead_id', '=', rec.id)
                ])
                for mapping in mappings:
                    if not mapping.lead_id or mapping.lead_id != rec:
                        mapping.lead_id = rec

    @api.depends('avatar_id', 'partner_id', 'partner_id.firstname')
    def set_avatar_name(self):
        for rec in self:
            if rec.avatar_id and rec.partner_id and rec.partner_id.firstname:
                first_letter = rec.partner_id.firstname[0].upper()
                matching_titles = rec.avatar_id.title.filtered(
                    lambda t: t.name and t.name[0].upper() == first_letter
                )
                if matching_titles:
                    rec.avatar_name = f"{matching_titles[0].name} {rec.partner_id.firstname}"
                else:
                    rec.avatar_name = rec.partner_id.firstname
            else:
                rec.avatar_name = ''

    def _compute_user_input_lines(self):
        for rec in self:
            lines = rec.survey_user_input_id.user_input_line_ids.filtered(
                lambda l: l.fragrance_family_id
            )
            rec.user_input_line_ids = lines

    @api.depends('survey_user_input_id')
    def _compute_personality_mapping_lines(self):
        for rec in self:
            if rec.survey_user_input_id:
                mappings = self.env['crm.lead.personality.mapping'].search([
                    ('lead_id', '=', rec.id)
                ])
                rec.personality_mapping_lines = mappings
            else:
                rec.personality_mapping_lines = False

    @api.depends('partner_id')
    def _compute_user_portal_fields(self):
        for rec in self:
            user = rec.partner_id.user_ids[:1] if rec.partner_id and rec.partner_id.user_ids else False
            rec.user_portal_id = user.id if user else False
            rec.user_login = user.login if user else False
            rec.user_email = user.email if user else False
            rec.user_name = user.partner_id.name if user else False

    @api.depends('purchase_history_ids')
    def _compute_purchase_stats(self):
        for rec in self:
            purchases = rec.purchase_history_ids.filtered(lambda p: p.payment_status == 'paid')
            rec.total_purchases = len(purchases)
            rec.total_spent = sum(purchases.mapped('total_amount'))
            rec.last_purchase_date = max(purchases.mapped('purchase_date')) if purchases else False

    def action_view_purchase_history(self):
        """Open purchase history view for this lead"""
        self.ensure_one()
        action = {
            'name': 'Purchase History',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.purchase.history',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
            },
            'help': '''<p class="o_view_nocontent_smiling_face">
                Create your first purchase record!
            </p>
            <p>
                Track detailed purchase history including bottle sizes, quantities, pricing, and order status.
            </p>'''
        }
        return action

    def get_max_scent_wands_by_bottle_size(self, bottle_size):
        """
        Get maximum total scent wands based on bottle size
        """
        bottle_limits = {
            '30ml': 6,
            '50ml': 10,
            '100ml': 20
        }
        return bottle_limits.get(bottle_size, 20)  # Default to 100ml limit

    def calculate_fragrance_max_values(self):
        """
        Calculate fragrance max values based on existing fragrance_value_ids and bottle size
        """
        try:
            self.ensure_one()
            
            # Debug: Log method entry
            _logger.info(f"=== calculate_fragrance_max_values() called ===")
            _logger.info(f"Bottle size: {self.bottle_size}")
            
            # Get bottle size and max total
            bottle_size = self.bottle_size or '100ml'
            max_total = self.get_max_scent_wands_by_bottle_size(bottle_size)
            
            _logger.info(f"Max total for {bottle_size}: {max_total}")
            
            # Get existing fragrance values from fragrance_value_ids
            if not self.fragrance_value_ids:
                _logger.info("No fragrance_value_ids found, returning defaults")
                return {
                    'citrus': 1,
                    'fresh': 1,
                    'floral': 1,
                    'woody': 1,
                    'oriental': 1
                }
            
            # Build result dict from existing values
            result = {}
            has_manual_value = any([x.value_manual for x in self.fragrance_value_ids])
            for fv in self.fragrance_value_ids:
                if fv.fragrance_family_id and fv.value is not None:
                    family_name = fv.fragrance_family_id.name.lower()
                    result[family_name] = fv.value_manual if has_manual_value else fv.value
            
            _logger.info(f"Original values from fragrance_value_ids: {result}")
            
            # Apply bottle size rules
            if bottle_size == '30ml':
                # 30ml: max 6 total
                # Strategy: Give 1 to each non-zero category, then give remaining to dominant
                non_zero_scores = [(name, score) for name, score in result.items() if score > 0]
                
                if not non_zero_scores:
                    return {
                        'citrus': 1,
                        'fresh': 1,
                        'floral': 1,
                        'woody': 1,
                        'oriental': 1
                    }
                
                # Give 1 to each non-zero category
                for name, score in non_zero_scores:
                    result[name] = 1
                
                # Fill zero categories with 0
                for name, score in result.items():
                    if name not in [n for n, s in non_zero_scores]:
                        result[name] = 0
                
                # Give remaining slots to dominant category
                current_total = sum(result.values())
                remaining = 6 - current_total
                
                if remaining > 0:
                    # Find dominant category (highest original score)
                    dominant_category = max(non_zero_scores, key=lambda x: x[1])[0]
                    result[dominant_category] += remaining
                
                _logger.info(f"30ml result: {result}")
                
            elif bottle_size == '50ml':
                # 50ml: max 10 total
                # Strategy: Divide each score by 2, then distribute remaining
                
                # Store original values for reference
                original_values = result.copy()
                
                # First pass: divide by 2 (convert to int first)
                for family in result:
                    result[family] = int(result[family]) // 2
                
                # Second pass: distribute remaining slots
                current_total = sum(result.values())
                remaining = 10 - current_total
                
                if remaining > 0:
                    # Create list of (family, original_value) sorted by original value descending
                    families_by_original = sorted(original_values.items(), key=lambda x: x[1], reverse=True)
                    
                    # Distribute remaining slots round-robin style
                    for i in range(remaining):
                        family = families_by_original[i % len(families_by_original)][0]
                        result[family] += 1
                
                # Debug: Log the calculation
                _logger.info(f"50ml Debug - Original: {original_values}")
                _logger.info(f"50ml Debug - After /2: {result}")
                _logger.info(f"50ml Debug - Current total: {sum(result.values())}")
                _logger.info(f"50ml Debug - Remaining: {remaining}")
                
            else:  # 100ml
                # 100ml: use as is (no changes)
                _logger.info(f"100ml - Using original values: {result}")
            
            _logger.info(f"Final result: {result}")
            return result
            
        except Exception as e:
            _logger.error(f"Error in calculate_fragrance_max_values: {str(e)}")
            # Fallback to default values if any error
            return {
                'citrus': 1,
                'fresh': 1,
                'floral': 1,
                'woody': 1,
                'oriental': 1
            }

    def get_fragrance_max_values_for_api(self):
        """
        Get fragrance max values formatted for API response
        """
        self.ensure_one()
        max_values = self.calculate_fragrance_max_values()
        
        # Format for API response
        fragrance_values = []
        for family, value in max_values.items():
            fragrance_values.append({
                'fragrance_family': family,
                'value': value
            })
        
        return fragrance_values


    def get_data_intensity_table(self):
        values = {
            fv.fragrance_family_id.name: fv.value 
            for fv in self.fragrance_value_ids 
            if fv.value and fv.fragrance_family_id
        }
        fragrance_families = self.env['fragrance.family'].search([], order="id")
        max_len = max(len(cat.intensity_index_ids) for cat in fragrance_families)

        table = []
        for i in range(max_len):
            row = {}
            for fragrance in fragrance_families:
                traits = fragrance.intensity_index_ids.sorted("sequence")
                if i < len(traits):
                    idx_from_top = i
                    highlight = False
                    if fragrance.name in values:
                        val = values[fragrance.name]   # nilai dihitung dari bawah
                        target_idx = len(traits) - val
                        if max(0, target_idx - 2) <= idx_from_top <= min(len(traits) - 1, target_idx + 2):
                            highlight = True
                    row[fragrance.name] = {
                        'text': traits[idx_from_top].name,
                        'highlight': highlight,
                        'color': fragrance.color or 'fff'
                    }
                else:
                    row[fragrance.name] = {'text': '', 'highlight': False, 'color': 'fff'}
            table.append(row)
        return table, fragrance_families

    def get_data_intensity(self):
        data = []
        for fragrance_value in self.fragrance_value_ids:
            value = fragrance_value.value
            family_name = fragrance_value.fragrance_family_id.name

            if not value:
                continue

            if family_name == "Citrus":
                data_family = {}
                if 1 <= value <= 3.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Low {family_name}",
                            "description": "People with your Citrus score are naturally insightful, demonstrating a unique blend of qualities that make them indispensable in many social and professional settings. Here's a closer look at the traits associated with your personality profile:",
                            "Supportive": "Your Citrus score highlights your quiet yet impactful ways of supporting others. Whether you're offering advice or stepping in to help when needed, you often serve as the reliable backbone in any situation. Your efforts might go unnoticed at times, but those who know you well truly value your contributions.",
                            "Realistic": "Grounded and practical, your score reflects a balanced perspective. You appreciate optimism but prefer to temper it with realism, ensuring your decisions are thoughtful and well-measured. While this trait helps you navigate challenges effectively, it may sometimes make you second-guess opportunities that involve risk.",
                            "Hesitant": "You may hold back, particularly in leadership roles or situations where you're required to take charge. This hesitation stems not from a lack of ability but from a fear of making mistakes or disappointing others. By addressing this concern, you can unlock untapped potential and embrace opportunities for growth.",
                            "Avoidant": "Avoiding conflict is another hallmark of your Citrus score. While this helps maintain harmony in the short term, unresolved issues may resurface later. Learning to address disagreements with your natural diplomacy can lead to more lasting resolutions.",
                            "Self-Doubting": "Your Citrus score reveals a pattern of second-guessing your abilities, even when you're well-prepared. This self-doubt can prevent you from sharing ideas or seizing opportunities. Over time, learning to trust your instincts and judgment will help you grow more confident.",
                            "Overwhelmed": "When stress builds, you may lean toward avoidance—procrastinating or withdrawing from challenging situations. While this might bring temporary relief, finding proactive strategies to manage stress can help you tackle issues more effectively.",
                            "Path to balance this facet": {
                                "Start small": "Share your ideas in safe, supportive settings to build confidence gradually.",
                                "Focus on successes": "Reflect on past achievements, as evidence of your capabilities.",
                                "Step into leadership": "Take on small leadership roles aligned with your strengths to expand your comfort zone.",
                                "Address conflict constructively": "Use your diplomatic nature to approach disagreements with solutions in mind.",
                                "Challenge self-doubt": "Pause to recognize your accomplishments whenever you question your abilities.",
                                "Learn to act on empathy": "Trust your instincts to offer help when you sense someone in need.",
                                "Tackle stress proactively": "Break large tasks into manageable steps, and celebrate small wins to stay motivated."
                            }
                        }
                    
                elif 3.51 <= value <= 6.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Mid {family_name}",
                            "description": "People with your Citrus score have a remarkable ability to inspire trust and create harmony, blending emotional intelligence with a grounded approach to life. Here's how your unique traits shape your personality and interactions:",
                            "Fair": "People with your Citrus score are masters of balancing harmony and honesty. You excel at fostering positive connections while staying true to your values. Your ability to consider different perspectives makes others trust you, knowing you'll always be fair and understanding.",
                            "Efficient": "Your Citrus score reflects a natural talent for staying  efficient. This makes you a go-to person for managing responsibilities, ensuring everything gets done with precision and care.",
                            "Thoughtful": "Your decision-making process is deliberate and careful. You weigh all options to ensure the best outcomes, which others deeply appreciate. While this methodical approach helps avoid mistakes, learning to trust your instincts can help you make quicker decisions when time is of the essence.",
                            "Sensitive": "Your feedback can sometimes feel personal. By reframing criticism as a tool for growth rather than a judgment, you can harness it to improve while maintaining your confidence.",
                            "Child like empathic": "Your empathy is one of your strongest assets. You understand and support others' emotions without losing sight of your boundaries, ensuring that you maintain your own emotional balance while offering meaningful help.",
                            "Charismatic": "People naturally gravitate toward you because of your charismatic personality. Whether you're engaging in conversation or offering a listening ear, your genuine presence makes others feel valued, respected, and at ease.",
                            "Calm": "Stress can sometimes get the best of you. In challenging situations, you many lose some sleep. Your ability to stay calm and focused will fosters teamwork and a sense of stability in high-pressure environments.",
                            "Balanced": "By caring, while prioritizing your own well-being will help you avoid burnout and ensure you have the energy to continue supporting those who rely on you.",
                            "Path to balance this facet": {
                                "Trust your instincts": "Practice making quicker decisions to build confidence in your gut feel.",
                                "Embrace feedback": "See criticism as an opportunity for growth, using it to refine your strengths and improve your approach.",
                                "Take small risks": "Experiment with creative or unconventional ideas to foster adaptability and innovation.",
                                "Prioritize effectively": "Focus on managing demands, while keeping long-term goals in view.",
                                "Celebrate progress": "Reflect on your achievements and recognize how far you've come.",
                                "Foster creativity": "Allow yourself to explore ideas that may not seem immediately practical, opening new pathways for growth.",
                            }
                        }
                    
                elif 6.51 <= value <= 10.5 :
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - High {family_name}",
                            "description": "People with your Citrus score have a natural ability to inspire and uplift others, creating an atmosphere of motivation and collaboration wherever they go. Here's a closer look at the remarkable traits that define your personality and how they shape your impact:",
                            "Inspiring": "People with your Citrus score are a source of positivity and encouragement. Whether in professional settings, friendships, or community, your enthusiasm energizes those around you.",
                            "Visionary": "Your Citrus score reflects a rare combination of intuition and strategic thinking. You see the bigger picture while keeping practical steps in mind, allowing you to set meaningful goals and guide others toward achieving them with clarity and purpose.",
                            "Overcommitted": "Your deep desire to help and support others can sometimes lead you to take on too much. While your selflessness uplifts those around you, learning to prioritize your own needs will help you avoid burnout and maintain your energy.",
                            "High Standards": "Your high expectations push you and those around you to excel. However, this can sometimes cause frustration when others operate at a different pace. Embracing varied working styles will help you create a more collaborative and understanding environment.",
                            "Charismatic": "People are naturally drawn to your charm and warmth. Whether you're leading a team or engaging one-on-one, you make others feel valued and heard. This ability to inspire trust and collaboration is one of your greatest strengths as a leader.",
                            "Resilient": "Challenges fuel your drive rather than deter you. You remain calm and optimistic under pressure, guiding those around you toward solutions. Your resilience reassures others and keeps them grounded during difficult times.",
                            "Influential": "Your impact extends far beyond the moment. People carry your encouragement and vision with them, often crediting you for their growth and success long after your interactions. You're not just a motivator; you're a lasting source of inspiration.",
                            "Balanced": "By caring, while prioritizing your own well-being will help you avoid burnout and ensure you have the energy to continue supporting those who rely on you.",
                            "Path to balance this facet": {
                                "Delegate tasks": "Empower others by trusting them to take on responsibilities. This fosters growth in others and helps you avoid burnout.",
                                "Embrace imperfection": "Accept that mistakes are a part of growth—for both yourself and others. Letting go of perfection fosters creativity and adaptability.",
                                "Reflect regularly": "Take time to assess your commitments and prioritize your well-being. Self-reflection is essential for sustaining your energy and focus.",
                                "Prioritize self-care": "Balance your care for others with care for yourself. Regularly recharge to maintain your emotional and physical health.",
                                "Celebrate progress": "Acknowledge and celebrate milestones—both your own and others'. This reinforces positivity and motivation in every aspect of life.",
                            }
                        }
                    
                elif value >= 10.51:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Extreme {family_name}",
                            "description": "People with your Citrus score have a magnetic presence that draws others in and inspires action. Your unique blend of energy, vision, and charisma makes you a natural leader, but balancing your strengths with self-awareness and collaboration can amplify your impact even further.",
                            "Energy": "Your energy and presence light up any room, making you the focal point of attention in teams and communities. Your passion and charm inspire others to dream bigger and push harder toward their goals.",
                            "Visionary": "Your Citrus score reflects a deep ability to see what's possible. You easily inspire others to believe in and pursue that vision alongside you. This ability to unite people around a shared purpose is one of your most powerful qualities.",
                            "Energetic": "You bring boundless energy and adaptability to any situation. Fast-paced environments fuel your drive, and your enthusiasm is infectious. This dynamic approach helps you tackle challenges head-on and keeps teams motivated, even under pressure.",
                            "Influential": "Your assertive leadership ensures your ideas are heard and often shape the direction of projects or groups. While your influence is a tremendous strength, it's important to ensure others feel equally valued and empowered to contribute their perspectives.",
                            "Overcommitted": "Your drive to lead and support others often leads you to take on too much. You feel a strong sense of responsibility, which makes it challenging to set limits. Recognizing when to delegate or step back is crucial to maintaining your well-being and effectiveness.",
                            "Intense": "Your passion and focus are undeniable but can sometimes come across as overwhelming. In conversations or team settings, this intensity may unintentionally overshadow others' ideas or contributions. Taking a step back to listen can strengthen collaboration and trust.",
                            "Relentless": "You have a remarkable dedication to pursuing what matters to you, but this relentless drive can lead to stress when things don't go as planned. Learning to accept what's beyond your control can help you channel your energy more effectively.",
                            "Path to balance this facet": {
                                "Practice listening": "Ensure others feel heard by actively pausing to understand their perspectives. This fosters mutual respect and enhances team dynamics.",
                                "Embrace imperfection": "Accept that not everything—or everyone—will meet your high standards. Flexibility allows for creative problem-solving and collaboration.",
                                "Adapt to feedback": "Stay open to constructive criticism and differing viewpoints. This adaptability strengthens relationships and broadens your impact.",
                                "Let go when needed": "Release control over outcomes beyond your influence. This frees up mental space and energy to focus on what truly matters.",
                                "Reflect regularly": "Take time to evaluate your goals, commitments, and personal well-being. Reflection ensures you remain aligned with your values and balanced in your approach.",
                            }
                        }
                if data_family:
                    data.append(data_family)
                
            elif family_name == "Fresh":
                data_family = {}
                if 1 <= value <= 3.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Low {family_name}",
                            "description": "People with your Fresh score are the pillars of reliability & stability in any group, bringing comfort & support to those around them. Here's a deeper dive into your strengths and areas for growth:",
                            "Dependable": "You're the person everyone knows they can count on. Loyal, consistent, and reliable, your presence is a source of reassurance in both personal and professional settings. Even during challenges, your steadiness helps maintain balance and calm for those around you.",
                            "Practical": "You excel at offering tangible support that makes a real difference. Whether it's providing thoughtful advice or helping with usual tasks, your down-to-earth nature ensures harmony and order. Your practical contributions are highly valued by those who know you.",
                            "Realistic": "Your grounded perspective allows you to focus on what's achievable and necessary in the moment. While this pragmatic approach helps you navigate life effectively, it may sometimes keep you from pursuing long-term or ambitious goals that seem uncertain.",
                            "Hesitant": "Confidence doesn't always come naturally to you, which can make asserting yourself in groups or taking on leadership roles challenging. You may avoid big decisions out of fear of failure or judgment, leading to moments of frustration or feeling overlooked.",
                            "Avoidant": "Your priority for harmony often leads you to avoid conflict. While this keeps the peace initially, unresolved issues can resurface later, making them harder to address.",
                            "Self-Critical": "You have tendency to dwell on perceived mistakes or shortcomings. This self-critical nature may leave you seeking reassurance from others or hesitating to trust your own abilities.",
                            "Overwhelmed": "You're excellent at supporting others, but high-stakes situations or responsibilities can feel intimidating.",
                            "Reassurance-Seeking": "You often worry about others' opinions of you or whether your efforts are enough. This can make you overly reliant on external validation.",
                            "Path to balance this facet": {
                                "Practice assertiveness": "Start small by sharing your thoughts in group settings or volunteering for minor leadership tasks. These moments of confidence-building will add up over time.",
                                "Embrace conflict constructively": "View them as opportunities for growth. Approach them with calmness and respect to find solutions that strengthen relationships.",
                                "Celebrate your achievements": "Combat self-criticism by acknowledging your successes, no matter how small. This helps build a more positive self-image.",
                                "Trust your instincts": "When you sense someone needs support, act on it. Even small gestures can have a significant impact and remind you of your ability to help others effectively.",
                                "Reflect on your value": "Regularly remind yourself of the stability and support you bring to others. Even if not always acknowledged, your efforts make a difference.",
                                "Focus on connection": "Instead of worrying about how others perceive you, invest in building genuine, meaningful relationships. Trust that your authenticity will be appreciated.",
                            }
                        }
                    
                elif 3.51 <= value <= 6.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Mid {family_name}",
                            "description": "People with your Fresh score naturally create a warm and nurturing atmosphere wherever they go. Your genuine care for others make people feel valued and understood, and your ability to respond thoughtfully to their needs sets you apart. Here's a closer look:",
                            "Warm": "You are a team-builder and have a gift for making others feel supported and cared for. Whether through a kind word, a listening ear, or thoughtful encouragement, you foster an environment where people feel safe and appreciated.",
                            "Practical": "Your practical mindset ensures that tasks are completed efficiently and with care. Whether you're organizing a project or handling personal responsibilities, you keep everything running smoothly.",
                            "Sociable": "Social settings are where you shine. You have a natural ability to make people feel welcome. Your talent for connecting with individuals from all walks of life helps build strong communities and lasting relationships.",
                            "Sensitive": "You're deeply attuned to emotions, which makes you empathetic but also means criticism can sometimes feel personal. While you strive to grow from feedback, it may temporarily discourage you.",
                            "Overcommitted": "Your eagerness to help others often leads to taking on too many responsibilities. While your intentions are admirable, this can leave you feeling stretched too thin. Learning to set boundaries will help you preserve your energy and well-being.",
                            "Inclusive": "You create a welcoming environment where everyone feels valued. Your ability to connect with diverse groups and bring people together fosters collaboration and a strong sense of belonging. This inclusivity strengthens relationships and promotes harmony.",
                            "Path to balance this facet": {
                                "Embrace feedback": "Focus on the intent behind criticism and use it as an opportunity for growth. Building resilience will help you feel more confident in your abilities.",
                                "Set boundaries": "Prioritize tasks and say no when necessary to avoid overcommitting. Protecting your time and energy will ensure you can continue supporting others effectively.",
                                "Explore new ideas": "Push yourself to consider creative or unconventional approaches. Experimentation will enhance your adaptability and problem-solving skills",
                                "Test your independence": "While collaboration is a strength, take on solo projects to build confidence and self-reliance. This will help you grow as a leader and an individual.",
                                "Balance care": "Continue prioritizing self-care alongside your support for others. This balance ensures you can sustain your energy and effectiveness.",
                                "Practice delegation": "Share responsibilities with others to lighten your load and build trust in your team or community. This will allow you to focus on what truly matters.",
                                "Address conflicts openly": "Use your empathy to navigate disagreements and find resolutions that maintain harmony while addressing the root of the issue.",
                                "Recognise your value": "Reflect on the positive impact you have on others. Share responsibilities with others to lighten your load and build trust in your team or community. This will allow you to focus on what truly matters.",
                            }
                        }
                    
                elif 6.51 <= value <= 10.5 :
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - High {family_name}",
                            "description": "People with your Fresh score are natural connectors, bringing warmth and energy that make you the heart of any group. Your ability to foster inclusivity and create a sense of belonging ensures that everyone feels valued and appreciated in your presence.",
                            "Life of a group": "You're the life of the group, radiating positivity and charm that draws people to you effortlessly. Your inclusive nature strengthens relationships, and your knack for bringing people together builds a strong sense of community.",
                            "Emotionally Attuned": "Your sensitivity to others' emotions and needs is a standout quality. You intuitively understand unspoken feelings, which allows you to offer the right kind of support at the right time. This ability deepens trust and strengthens your connections with others.",
                            "Reliable": "Your dependability is second to none. People trust you to follow through on your commitments, and your dedication to harmony and excellence makes you a cornerstone in any project or relationship.",
                            "Organised": "You excel at creating order and structure, whether managing projects, planning events, or coordinating group efforts. Your organizational skills ensure that everything runs smoothly, and others trust you to keep things on track.",
                            "Harmony-Seeking": "You prioritize peace and avoid conflict whenever possible. While this maintains short-term harmony, it may leave important issues unresolved.",
                            "Confident": "Your confidence is magnetic, inspiring others to believe in themselves and their abilities. You create a collaborative atmosphere where everyone feels encouraged to contribute and work toward shared goals.",
                            "Resilient": "Under pressure, you stay composed and adaptive. Your resilience not only helps you navigate challenges with ease but also reassures those around you, providing stability and support in difficult times.",
                            "Path to balance this facet": {
                                "Encourage independence": "Allow others the space to manage their responsibilities and emotions. Trusting them to take ownership fosters growth and strengthens relationships.",
                                "Embrace imperfection": "Recognize that mistakes are part of progress. Letting go of rigid standards will foster adaptability and open the door to new possibilities.",
                                "Set boundaries": "Protect your time and energy by saying no when necessary. This allows you to prioritize what truly matters while maintaining your well-being.",
                                "Celebrate progress": "Acknowledge and celebrate achievements, no matter how small. Recognizing successes helps build confidence and maintain a positive outlook.",
                                "Reflect regularly": "Take time to assess your emotional well-being and workload. Regular reflection ensures balance and prevents burnout.",
                                "Cultivate self-awareness": "Be mindful of when your care might become overprotective. Adjusting your approach ensures your support nurtures autonomy and growth.",
                            }
                        }
                    
                elif value >= 10.51:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Extreme {family_name}",
                            "description": "People with your Fresh score have a natural talent for leadership, effortlessly inspiring and organizing those around them. Your confidence, charisma, and ability to make others feel valued position you as a central figure who brings people together and drives success in any group.",
                            "Leader": "People trust your vision and look to you for direction, as your warmth and confidence create an environment where everyone feels empowered to contribute.",
                            "Supportive": "Your dedication to helping others is unwavering. You go above and beyond to meet people's needs, offering both practical solutions and emotional encouragement. This genuine care fosters trust and strengthens your connections with others.",
                            "Sociable": "Social settings are where you truly shine. You excel at building relationships and creating networks, connecting with people on a personal level. Your approachable nature and ability to foster inclusivity make you a cherished leader, friend, and colleague.",
                            "Approval-Seeking": "You care deeply about others' opinions, often striving for external validation. While this stems from your genuine desire to be liked and appreciated, it can sometimes make you overly reliant on reassurance, impacting your self-confidence.",
                            "Burnout": "Your tendency to prioritize others' needs over your own often leaves little time for self-care. While you're driven by your compassion, neglecting your well-being can lead to emotional and physical exhaustion, diminishing your effectiveness over time.",
                            "Resilient": "Under pressure, you remain composed and adaptable, offering stability and reassurance to those around you. While your resilience is a strength, your attachment to outcomes can make it difficult to let go of past frustrations or failures.",
                            "Overcommitted": "You feel a strong responsibility to ensure everything runs perfectly and everyone is content. This often results in overcommitting, leaving little room for personal needs and increasing the risk of burnout.",
                            "Path to balance this facet": {
                                "Focus on intrinsic motivation": "Build self-confidence by validating your worth internally rather than seeking external approval. Reflect on your achievements and trust in your abilities.",
                                "Practice delegation:": "Share responsibilities and trust others to handle tasks their way. Delegation empowers others while lightening your workload.",
                                "Prioritize self-care": "Make time for activities that nurture your physical and emotional health. Taking care of yourself ensures you can continue to lead and support others.",
                                "Accept imperfection": "Embrace the idea that mistakes and imperfections are part of growth. Allow yourself and others the space to learn and adapt.",
                                "Address micromanaging tendencies": "Step back when you notice yourself becoming overly involved in others' tasks. Trust their capabilities and encourage autonomy.",
                                "Let go of attachment": "Practice accepting outcomes that don't align with your expectations. Focusing on the bigger picture will reduce frustration and help you move forward.",
                            }
                        }
                if data_family:
                    data.append(data_family)
                
            elif family_name == "Floral":
                data_family = {}
                if 1 <= value <= 3.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color, 
                            "title": f"Your Intensity Index - Low {family_name}",
                            "description": "People with your Floral score have a natural gift for empathy, quietly understanding the emotions and needs of others. Here's a deeper dive into your strengths and areas for growth:",
                            "Empathetic": "You deeply connect with the emotions of those around you, offering quiet, nonjudgmental support. Your ability to notice when someone is struggling makes you a comforting presence, though you may hold back if you're unsure your help will be welcomed.",
                            "Idealistic": "Your vision for a better world is a powerful internal guide. They shape your actions and decisions, inspiring you to strive for positive change in your quiet, steadfast way.",
                            "Hesitant": "You may hesitate to share your ideas or insights, fearing rejection or misunderstanding. This can lead you to stay in the background, even when your perspective could make a valuable difference. Building confidence in your voice is key to overcoming this.",
                            "Absorbed": "Your deep empathy can sometimes become overwhelming, as you tend to absorb the emotions of others. Without proper boundaries, this sensitivity can drain your emotions.",
                            "Private": "You tend to keep your inner world to yourself, sharing your thoughts and values only with those you trust completely. While this privacy protects you, it can make it harder for others to fully appreciate your unique perspective.",
                            "Quietly Creative": "Your introspection and idealism fuel your creativity, but you might hesitate to share your ideas unless you feel certain they'll be well-received. This restraint can limit the reach and impact of your innovative thinking.",
                            "Peace-Seeking": "Your desire for harmony often leads you to avoid addressing disagreements. These unresolved conflicts can weigh on you and hinder long-term relationships.",
                            "Path to balance this facet": {
                                "Share your ideas": "Start small by expressing your thoughts in safe and supportive settings. Gradually expand to sharing your vision with larger groups to build confidence.",
                                "Set boundaries": "Protect your emotional energy by establishing clear limits. This will allow you to empathize with others without becoming overwhelmed.",
                                "View conflict as growth": "Practice addressing disagreements constructively. Approach conflicts as opportunities to build understanding and strengthen relationships.",
                                "Take small leadership steps": "Test your leadership abilities in low-pressure environments, such as guiding a small group or organizing a shared activity.",
                                "Embrace imperfection": "Understand that your contributions don't need to be flawless to have value. Taking risks and learning from mistakes will help you grow.",
                                "Celebrate your values": "Remind yourself that your ideals have worth, even if they aren't immediately recognized. Your quiet influence can still inspire meaningful change.",
                                "Practice assertiveness": "Work on expressing your needs and feelings openly, even in small ways. This will help you maintain boundaries and ensure your voice is heard."
                            }
                        }
                    
                elif 3.51 <= value <= 6.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Mid {family_name}",
                            "description": "People with your Floral score possess a unique blend of emotional intelligence and intuition, enabling you to connect deeply with others. Your natural empathy and thoughtful approach make you a trusted confidant and a source of meaningful support.",
                            "Empathetic": "You intuitively understand others emotions and needs, creating strong, genuine connections. Your ability to listen without judgment and offer support makes you valuable.",
                            "Purpose-Driven": "Your actions are guided by a strong sense of purpose. You find motivation in pursuing meaningful goals and inspire others to align with your vision toward shared ideals.",
                            "Visionary": "You are skilled at turning big ideas into practical, actionable plans. Your ability to organize and execute ensures that your dreams translate into tangible, impactful results.",
                            "Sensitive": "Criticism and negativity can deeply affect you, sometimes leading you to doubt your abilities. While you value feedback, building resilience will help you process it constructively rather than internalizing it.",
                            "Idealistic": "Your strong values and ideals guide your decisions and actions. While these principles are a source of strength, they can sometimes make it challenging to adapt to new approaches or perspectives that differ from your vision.",
                            "Inspiring": "You lead through passion and authenticity, setting an example for others with your actions. People are drawn to your integrity and feel motivated by you.",
                            "Creative": "Your ability to think outside the box allows you to develop innovative solutions. Balancing creativity with effectiveness makes you a brilliant problem solver.",
                            "Path to balance this facet": {
                                "Balance idealism with pragmatism": "Stay flexible when plans don't go as expected. Adjusting to changing circumstances while staying true to your core values will help you achieve meaningful goals without unnecessary stress.",
                                "Reframe criticism": "See feedback as an opportunity to grow rather than a judgment.",
                                "Develop leadership skills": "Step into roles where you can inspire and guide others. Building confidence in your decision-making will enhance your ability to lead.",
                                "Engage in creative challenges": "Pursue opportunities that test your innovation & problem-solving abilities. These will allow you to bring your ideals to life in impactful ways.",
                                "Practice emotional regulation": "Protect yourself from emotional exhaustion by developing habits like mindfulness, self-reflection, or seeking support when needed. Maintain balance.",
                                "Seek diverse input": "Collaborate with individuals who bring varied perspectives. This will strengthen your goals and ensure they are inclusive and well-rounded.",
                                "Strengthen conflict resolution skills": "Approach disagreements with care, empathy, and a focus on understanding. Your ability to navigate sensitive topics will build trust.",
                                "Expand your network": "Connect with like-minded individuals and groups to amplify your impact. Engaging with a broader community will help you reach your goals more effectively."
                            }
                        }
                    
                elif 6.51 <= value <= 10.5 :
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - High {family_name}",
                            "description": "People with your Floral score have a natural gift for envisioning a brighter future and inspiring others to join their journey. Your ability to challenge the status quo with clear and compelling ideas sets you apart as a visionary leader who motivates others to think bigger and act boldly.",
                            "Visionary": "You see possibilities where others see limitations. Your confidence in your ideals drives you to turn innovative ideas into reality, making you a catalyst for meaningful change. Your vision inspires others to align with your purpose and contribute to a shared cause.",
                            "Compassionate": "You connect with others on a deeply intuitive level, sensing unspoken emotions and needs. This empathy allows you to provide support and guidance with precision, building trust and loyalty within your relationships and teams.",
                            "Strategic": "Your ability to organize and create actionable plans ensures your visionary ideas are not just aspirational but achievable. By combining idealism with practicality, you're highly effective in transforming big ideas into tangible results.",
                            "Driven": "Your passion and determination to fulfill your vision inspire those around you. While your drive is a strength, it can also lead to stress or burnout if you don't prioritize self-care and take time to recharge.",
                            "Rigid": "Your attachment to your vision can sometimes make it challenging to adapt when things change. By being open, you can refine your approach and enhance the impact of your plans.",
                            "Protective": "You care deeply about your ideas and their potential impact, which can sometimes make you resistant to alternative viewpoints. Embracing diverse perspectives will help strengthen your vision and broaden your understanding.",
                            "Inspirational Leader": "You don't just lead—you inspire. Your leadership style focuses on mentoring others, helping them recognize their potential and empowering them to grow. Your authenticity and encouragement bring out the best in those you guide.",
                            "Path to balance this facet": {
                                "Practice flexibility": "Reevaluate and adapt your plans as circumstances evolve. Embracing change and letting go of rigid expectations will keep you effective.",
                                "Seek diverse perspectives": "Collaborate with people from different experiences. Their input will enrich your vision and ensure your solutions are inclusive and impactful.",
                                "Set boundaries": "Protect your time and energy by saying no when necessary. This will help you stay focused on your priorities and avoid overextending yourself.",
                                "Embrace imperfection": "Understand that setbacks and challenges are opportunities for growth. Viewing imperfections as part of the process will reduce stress and build resilience.",
                                "Balance empathy with self-awareness": "Protect your emotional energy by setting boundaries around how much responsibility you take for others' feelings.",
                                "Refine conflict resolution skills": "Use your empathy and insight to mediate disagreements while ensuring conflicts lead to actionable outcomes that strengthen relationships."
                            }
                        }
                    
                elif value >= 10.51:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Extreme {family_name}",
                            "description": "People with your Floral score have an innate charisma that inspires and unites those around them. Your unique combination of empathy and confidence allows you to rally people toward meaningful causes and shared ideals.",
                            "Charismatic": "You naturally draw others in with your energy and vision. Your ability to articulate meaningful goals motivates those around you to act with purpose, fostering a sense of unity.",
                            "Purposeful": "Your strong sense of dedication and focus drives transformative change. Guided by deeply held values, you influence communities and organizations, inspiring others to align with your mission and work toward a better future.",
                            "Insightful": "You have a keen ability to understand people and systems, enabling you to navigate complex situations with clarity. Your wisdom and knack for connecting ideas make you a trusted problem-solver and advisor.",
                            "Idealistic": "Your vivid vision for a better world inspires others, but your pursuit of perfection can sometimes create challenges.",
                            "Empathetic but Overwhelmed": "Your profound empathy helps you connect deeply with others, but it can also leave you emotionally drained. Without proper boundaries, you risk burnout.",
                            "Vision-Driven": "Your commitment to your ideals fuels your efforts, often inspiring extraordinary results. Try not to overextend yourself or neglect personal needs.",
                            "Inspirational Leader": "You lead by example, demonstrating integrity and passion in your pursuits. Your ability to articulate a clear and compelling vision encourages others to dream bigger and act with purpose.",
                            "Calm Under Pressure": "Even in the most stressful situations, you remain composed and focused. Your emotional balance reassures others, helping you guide them through challenges with confidence and grace.",
                            "Path to balance this facet": {
                                "Temper idealism with realism": "Accept that imperfection is part of progress. Adjusting your expectations and embracing flexibility will help you reduce frustration.",
                                "Set healthy boundaries": "Protect your energy without becoming distant. Finding a balance between self-care and openness will ensure strong, meaningful connections.",
                                "Practice detachment": "Let go of ideas, relationships, or projects that no longer serve your purpose. Adapting to change will open new doors and allow your vision to evolve.",
                                "Encourage collaboration": "Seek input from diverse perspectives to enrich your vision. Collaborative approaches lead to more inclusive and impactful outcomes.",
                                "Reframe setbacks": "View challenges as opportunities to learn and refine your approach. Resilience in adversity will strengthen your leadership and inspire those around you.",
                                "Engage with diverse perspectives": "Surround yourself with individuals who challenge your ideas and provide new insights. This will broaden your understanding and adaptability."
                            }
                        }
                if data_family:
                    data.append(data_family)
                
            elif family_name == "Woody":
                data_family = {}
                if 1 <= value <= 3.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Low {family_name}",
                            "description": "People with your Woody score are the dependable foundation of any group or team. Your quiet reliability ensures that tasks are completed accurately and on time.",
                            "Reliable": "Your commitment to fulfilling responsibilities makes you a trusted and essential part of any team. While you often prefer to work behind the scenes, your steady dependability provides stability and ensures success.",
                            "Practical": "You approach challenges with straightforward, logical solutions, focusing on what works. Your practical mindset allows you to resolve issues efficiently.",
                            "Detail-Oriented": "Your keen attention to detail ensures that tasks are handled with precision and care. Your methodical nature is a significant asset in any project, as you excel at maintaining accuracy and thoroughness.",
                            "Rigid": "You value routines and familiar methods, which provide a sense of stability and predictability. While this preference ensures consistency, it can make adapting to new ideas or changes more challenging when flexibility is needed.",
                            "Reserved": "You have valuable insights and ideas but may hesitate to share them openly, fearing scrutiny or rejection. This reservation can make you appear passive, even though your contributions have the potential to make a significant impact.",
                            "Risk-Averse": "You prefer to stick to proven methods and avoid unnecessary risks. While this ensures reliability, it can limit your willingness to explore innovative solutions or step outside your comfort zone.",
                            "Steady": "Your preference for order and routine helps you maintain focus and consistency. This steadiness is a strength, but embracing occasional change and spontaneity can lead to new opportunities and personal growth.",
                            "Path to balance this facet": {
                                "Practice adaptability": "Challenge yourself to explore new methods, ideas, or systems. This will improve your flexibility and help you feel more comfortable with change.",
                                "Address conflicts constructively": "View disagreements as opportunities for growth. Practice calm and respectful communication to resolve issues and strengthen relationships.",
                                "Assert your ideas": "Begin sharing your thoughts in supportive, smaller settings. As you gain confidence, gradually expand to voicing your opinions in larger group dynamics.",
                                "Take calculated risks": "Step outside your comfort zone by experimenting with small risks in personal or professional settings. This will help you grow and discover new strengths.",
                                "Balance routine with exploration": "While structure is important, allow yourself to try new experiences and approaches. This will help you stay open to innovation and growth.",
                                "Seek feedback": "Invite constructive input from others on your work or ideas. This will help you refine your approach and build trust in your decision-making."
                            }
                        }
                    
                elif 3.51 <= value <= 6.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Mid {family_name}",
                            "description": "People with your Woody score have a natural talent for clear thinking and logical problem-solving. Your ability to approach challenges systematically ensures that tasks are well-organized, efficient, and effectively resolved, making you a dependable and reliable presence in any setting.",
                            "Logical": "You excel at structuring tasks and finding solutions through careful analysis. Your logical approach ensures that everything you tackle is grounded in reason and practicality, helping you make sound decisions and achieve consistent results.",
                            "Dependable": "You are the steady presence others rely on. Your strong sense of duty ensures you meet obligations and follow through on commitments, providing stability during challenging times.",
                            "Detail-Oriented": "Your meticulous attention to detail ensures work is completed with precision and accuracy. This focus on getting things right the first time and maintaining high standards is a key strength.",
                            "Risk-Averse": "You carefully assess risks before stepping out of your comfort zone. While cautious, your logical thinking helps you navigate uncertainty with confidence and clarity when necessary.",
                            "Overcommitted": "Your strong sense of responsibility can lead you to take on more than you can manage. While your dedication is admirable, overextending yourself may risk burnout and reduce your overall effectiveness.",
                            "Ambiguity-Resistant": "You thrive in structured environments and prefer clarity over uncertainty. While this is a strength, learning to navigate ambiguous or abstract situations can enhance your problem-solving toolkit and expand your adaptability.",
                            "Path to balance this facet": {
                                "Embrace new methods": "Experimenting with unconventional ideas can lead to greater efficiency and unexpected breakthroughs.",
                                "Cultivate creativity": "Engage in abstract or creative thinking to expand your problem-solving strategies. Allowing space for experimentation will enhance your adaptability and versatility.",
                                "Take dynamic roles": "Step into projects or situations that challenge your comfort zone. These experiences will help you develop greater flexibility and confidence.",
                                "Balance logic with intuition": "While logic is your strength, trust your instincts when clear facts are unavailable. Combining logic with intuition can lead to more well-rounded decisions.",
                                "Practice adaptability": "Focus on staying open-minded and flexible in uncertain situations. Learning to navigate ambiguity will make you more effective and versatile.",
                                "Celebrate progress": "Recognize your achievements, especially when they stem from stepping outside your comfort zone. Celebrating successes reinforces confidence and motivation.",
                                "Foster innovation": "Experiment with small changes in routines or methods to build comfort with adaptability. Gradually introducing new ideas will make it easier to embrace innovation.",
                                "Prioritize self-care": "Schedule regular downtime to recharge and reflect. Maintaining balance ensures you can approach your responsibilities with energy and focus."
                            }
                        }
                    
                elif 6.51 <= value <= 10.5 :
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - High {family_name}",
                            "description": "People with your Woody score excel at creating clear, actionable strategies and executing them with precision. Your ability to organize and prioritize ensures that even the most complex tasks are handled efficiently, making you a stabilizing force in any team or environment.",
                            "Strategic": "You thrive in developing and implementing structured plans, ensuring goals are met with precision. Your organized approach and foresight make you a cornerstone of stability.",
                            "Pragmatic": "Your grounded and logical mindset allows you to navigate challenges easily. You earn respect by making practical decisions, maintaining order, and staying composed under pressure.",
                            "Dependable": "Your attention to detail and focus on practicality make you a reliable problem-solver.",
                            "Visionary": "You blend a practical focus with long-term thinking, anticipating challenges and preparing for future needs. This combination ensures you're always a step ahead.",
                            "Stabilizing": "You bring a sense of calm and organization to chaotic situations. Your composed demeanor and ability to create order provide reassurance and stability to those around you.",
                            "Direct": "When conflicts arise, you address them head-on with fairness and logic. Your straightforward approach reduces tension and ensures that resolutions are practical and clear.",
                            "Resistant to Change": "You thrive in structured environments and prefer predictable routines. While this ensures consistency, developing flexibility will help you adapt more easily to unexpected changes or disruptions.",
                            "Detached": "Your focus on logic and practicality can sometimes make you appear distant or dismissive of others' emotions. Actively considering emotional perspectives will enhance collaboration and strengthen your connections.",
                            "Path to balance this facet": {
                                "Practice empathy": "Incorporate emotional awareness into your decision-making. Acknowledging others' feelings will deepen connections and foster trust within your team.",
                                "Cultivate flexibility": "Challenge yourself to adapt when plans or routines change unexpectedly. Embracing unpredictability will make you more versatile.",
                                "Balance expectations": "Collaborate with others who bring different strengths to the table. Balancing your high standards with diverse perspectives will lead to more inclusivity.",
                                "Take on open-ended challenges": "Pursue projects that require creativity and adaptability. These experiences will expand your skill set while leveraging your organizational strengths.",
                                "Encourage collaboration": "Focus on team-building and delegation. Sharing responsibilities empowers those around you and increases efficiency.",
                                "Expand your perspective": "Explore ideas and methods outside your usual preferences. Engaging with different viewpoints will help you innovate and grow.",
                                "Strengthen conflict resolution skills": "Pair your directness with empathy to address conflicts constructively, maintaining relationships while achieving practical solutions."
                            }
                        }
                    
                elif value >= 10.51:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Extreme {family_name}",
                            "description": "People with your Woody score excel in leadership roles, providing the structure and clarity needed to guide teams toward success. Your ability to maintain focus and order makes you a steady, dependable presence in any organization or group.",
                            "Leader": "You thrive on creating clear direction and ensuring that everyone works cohesively toward shared goals. Your leadership style emphasizes structure, efficiency, and results.",
                            "Visionary": "You approach balances immediate needs with long-term goals. Your attention to detail ensures that complex tasks are executed flawlessly, resulting in exceptional outcomes.",
                            "Dependable": "You are the backbone of any team, consistently delivering on commitments and maintaining high standards under pressure. Others trust your reliability and value it.",
                            "Rule-Oriented": "You value structure and processes, ensuring that operations run smoothly and efficiently. While this focus fosters order, embracing flexibility when necessary can help you adapt to dynamic environments and encourage innovation.",
                            "Perfectionist": "You strive for flawless execution, often taking on more responsibility than necessary to ensure quality. While this guarantees results, it can also lead to stress or micromanagement. Delegating and trusting others will alleviate these pressures.",
                            "Overcommitted": "Your strong sense of responsibility can push you to take on too much, leading to burnout. Prioritizing tasks and setting boundaries will help you maintain balance.",
                            "Grounded": "Your logical and methodical approach allows you to remain composed in high-stress situations. This calm demeanor reassures and keeps others moving forward during challenges.",
                            "Fair but Firm": "You address conflicts with directness and practicality, ensuring issues are resolved effectively. Pairing this firmness with empathy will help you maintain strong relationships.",
                            "Path to balance this facet": {
                                "Foster creativity": "Strike a balance between adhering to rules and allowing room for innovation. Encouraging flexibility in processes will lead to fresh ideas.",
                                "Practice self-compassion": "Accept that mistakes are a natural part of growth. Reducing self-criticism will help you embrace learning opportunities and set a positive example.",
                                "Delegate effectively": "Share responsibilities with others, trusting them to handle tasks in their own way. This reduces your workload and empowers your team to contribute meaningfully.",
                                "Adapt to change": "Seek input and remain open to new approaches during periods of transition. Embracing change will enhance your problem-solving skills.",
                                "Encourage collaboration": "Work closely with team members to incorporate diverse perspectives into your strategies. This will foster inclusivity and strengthen overall outcomes.",
                                "Empathize with others": "Balance your high standards with understanding for different working styles and capabilities. Practicing empathy will foster stronger relationships and improve teamwork."
                            }
                        }
                if data_family:
                    data.append(data_family)
                
            elif family_name == "Oriental":
                data_family = {}
                if 1 <= value <= 3.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Low {family_name}",
                            "description": "People with your Oriental score have the ability to stay focused and dependable, ensuring that tasks are completed effectively and that those around you feel supported and secure.",
                            "Determined": "You take your commitments seriously and consistently deliver on your promises. Others can count on you to follow through and keep everything on track.",
                            "Practical": "You focus on tangible outcomes and efficient solutions to immediate challenges. Your logical approach ensures problems are addressed effectively.",
                            "Innovative Thinkers": "You excel at coming up with unconventional solutions and seeing possibilities where others see obstacles.",
                            "Charismatic and Outgoing": "Your enthusiasm and charm make you magnetic in social settings, drawing people to your energy.",
                            "Adaptable and Resourceful": "You thrive in dynamic environments and are quick to adjust to new situations or challenges.",
                            "Naturally Curious": "With an insatiable desire to learn, you eagerly explore a wide range of topics and ideas.",
                            "Easily Distracted": "You love novelty and may lose interest in tasks that require sustained focus or follow-through.",
                            "Struggle with Routine": "You tend to avoid repetitive or structured tasks, preferring flexibility and spontaneity.",
                            "Impulsive Decision-Making": "You may act quickly without fully considering the consequences.",
                            "Path to balance this facet": {
                                "Gradual Social Engagement": "Start small by joining smaller, like-minded groups or engaging in one-on-one conversations to build confidence.",
                                "Leverage Your Curiosity": "Use your natural curiosity to ask open-ended questions in social settings, focusing on others' interests.",
                                "Practice Expressiveness": "Work on sharing your thoughts and ideas more openly to build stronger connections.",
                                "Practice Structured Decision-Making": "Use frameworks like pros-and-cons lists to weigh options more logically.",
                                "Balance Emotion with Logic": "Reflect on how emotions influence decisions, striving for harmony between heart and mind."
                            }
                        }
                    
                elif 3.51 <= value <= 6.5:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Mid {family_name}",
                            "description": "Innovative, charismatic, energetic, and curious, you excel at problem-solving but struggle with focus, routine, and impulsivity. Growth lies in balancing creativity with practicality, fostering empathy, and embracing structure for sustained success.",
                            "Innovative Problem-Solver": "You thrive on brainstorming and generating unconventional solutions. Your ability to think outside the box enables you to tackle challenges with fresh perspectives and creative flair.",
                            "Charismatic and Persuasive": "With your natural charm and quick wit, you excel at engaging with others, making connections, and inspiring those around you.",
                            "Energetic and Enthusiastic": "Your lively nature infuses any situation with energy, motivating others to join you in exploring new ideas or ventures.",
                            "Adaptable and Open-Minded": "Change doesn't faze you; instead, you embrace new opportunities and adjust seamlessly to evolving circumstances.",
                            "Endlessly Curious": "A hunger for knowledge drives you to dive into diverse subjects, constantly expanding your horizons and gaining new insights.",
                            "Easily Distracted": "While you're enthusiastic about starting projects, sustaining focus on long-term tasks can be a challenge, as you're often drawn to new ideas.",
                            "Impatience with Routine": "You may struggle with repetitive or highly structured activities, as they can feel restrictive and stifling to your free-spirited nature.",
                            "Overconfidence in Ideas": "Your confidence in your solutions and views may occasionally lead to overlooking potential flaws or dismissing others' input too quickly.",
                            "Impulsive Decision-Making": "Acting on instinct or excitement, you might rush into decisions without thoroughly analyzing potential consequences.",
                            "Path to balance this facet": {
                                "Refine Focus and Follow-Through": "Develop strategies like breaking tasks into smaller milestones to maintain momentum and complete projects effectively.",
                                "Practice Reflective Decision-Making": "Use decision-making frameworks, such as considering pros and cons or seeking feedback, to weigh options more thoroughly.",
                                "Embrace Constructive Routine": "Incorporate light structure into your workflow, such as flexible planning, to balance spontaneity with productivity.",
                                "Enhance Empathy in Communication": "Leverage your curiosity to understand others' perspectives more deeply, asking thoughtful questions and actively listening.",
                                "Balance Creativity with Practicality": "Pair your innovative thinking with actionable steps to ensure ideas transition smoothly into tangible results."
                            }
                        }
                    
                elif 6.51 <= value <= 10.5 :
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - High {family_name}",
                            "description": "Visionary, charismatic, and adaptable, you thrive on innovation and persuasion but struggle with routine, overcommitment, and impulsivity. Growth lies in prioritization, practical execution, empathy, and reflective decision-making for sustained impact.",
                            "Visionary and Innovative": "You excel at seeing the big picture and generating groundbreaking ideas. Your ability to think unconventionally allows you to identify opportunities where others see limitations.",
                            "Charismatic Leader": "Your natural charm and infectious enthusiasm draw people in. You inspire trust and motivate others to rally behind your vision, making you a magnetic leader.",
                            "Confident Risk-Taker": "Bold and assertive, you're not afraid to take calculated risks. This confidence empowers you to tackle challenges head-on and explore uncharted territories.",
                            "Quick-Witted and Articulate": "Your ability to think on your feet and communicate effectively makes you an engaging conversationalist and a persuasive influencer.",
                            "Adaptable and Resilient": "Thriving in dynamic and unpredictable environments, you quickly adapt to change, turning challenges into opportunities with ease.",
                            "Inexhaustibly Curious": "Your thirst for knowledge drives you to explore a wide range of subjects, enriching your understanding and fostering constant growth.",
                            "Difficulty with Routine": "Repetitive tasks and rigid structures may feel stifling, making it challenging to stay engaged with processes that lack novelty.",
                            "Impatience with Detail": "You're naturally drawn to the big picture and may overlook important details, leading to gaps in execution.",
                            "Path to balance this facet": {
                                "Cultivate Focus and Prioritization": "Practice narrowing your attention to a few high-impact projects at a time. Use tools like goal-setting frameworks to ensure you see them through.",
                                "Integrate Practicality into Vision": "Pair your innovative thinking with actionable plans. Break down ambitious ideas into manageable steps to ensure their success.",
                                "Foster Collaborative Listening": "While your confidence is a strength, balance it by actively listening to others' input. This will enhance your ability to build stronger relationships.",
                                "Practice Patience with Routine": "Develop creative ways to approach repetitive tasks, such as gamifying them or focusing on the long-term benefits they provide.",
                                "Embrace Reflective Decision-Making": "Take a moment to evaluate potential outcomes and consider the broader context. Use tools to channel your thoughts effectively.",
                                "Leverage Empathy in Leadership": "Use your charisma to not only inspire but also genuinely connect with others."
                            }
                        }
                    
                elif value >= 10.51:
                    data_family = {
                            "color": fragrance_value.fragrance_family_id.color,
                            "title": f"Your Intensity Index - Extreme {family_name}",
                            "description": "Innovative, charismatic, and adaptable, you thrive on bold ideas but struggle with focus, routine, and follow-through. Growth lies in prioritization, empathy, and balancing vision with execution.",
                            "Unstoppable Innovator": "Your mind thrives on generating groundbreaking ideas and challenging conventional wisdom. You're always on the hunt for new perspectives and disruptive solutions.",
                            "Magnetic Charisma": "Your presence lights up any room. You effortlessly inspire and energize those around you, drawing people to your vision and leadership.",
                            "Fearless Risk-Taker": "You approach life with boldness and confidence, diving headfirst into opportunities. Even setbacks are just stepping stones to greater success.",
                            "Master of Persuasion": "Your quick wit and eloquence make you a formidable communicator. You can present even the most unconventional ideas in ways that captivate and convince.",
                            "Highly Adaptable": "Thriving in change and uncertainty, you seamlessly navigate shifting circumstances and find opportunities where others see chaos.",
                            "Boundless Curiosity": "Your insatiable hunger for knowledge drives you to explore diverse fields and ideas, constantly expanding your horizons and capabilities.",
                            "Dynamic Problem-Solver": "You excel at rapidly analyzing complex situations and devising ingenious solutions. No challenge is too daunting for your agile mind.",
                            "Overwhelmed by Options": "Your endless stream of ideas and enthusiasm for new ventures can make it hard to prioritize, leading to a risk of scattering your focus.",
                            "Aversion to Routine": "You strongly resist mundane or repetitive tasks, which can lead to neglecting essential details or processes.",
                            "Path to balance this facet": {
                                "Master the Art of Focus": "Learn to channel your energy into fewer, high-impact projects at a time. Use tools like priority matrices or accountability partners to stay on track.",
                                "Balance Vision with Execution": "Break down your big ideas into actionable steps, and create systems to ensure follow-through. Delegating routine tasks to others can help.",
                                "Cultivate Patience with Details": "Set aside time to review finer details or partner with detail-oriented individuals to ensure comprehensive execution.",
                                "Pause Before Acting": "Before making decisions, take a moment to evaluate the broader implications. Tools like SWOT analysis or structured brainstorming sessions can help.",
                                "Harness Your Charisma with Empathy": "Use your natural influence not just to inspire, but to genuinely connect with others.",
                                "Commit to Long-Term Goals": "Develop habits that reinforce persistence, such as regularly reviewing progress and celebrating milestones to sustain enthusiasm for your projects."
                            }
                        }
                if data_family:
                    data.append(data_family)
                
        return data
    
    def generate_pos_access_code(self):
        """Generate POS access code and return JSON"""
        self.ensure_one()
        
        if not self.bottle_size:
            raise ValueError("Bottle size is required to generate access code")
        
        # Generate unique access code
        import string
        
        # Format: ABC-DEF-123
        part1 = ''.join(random.choices(string.ascii_uppercase, k=3))
        part2 = ''.join(random.choices(string.ascii_uppercase, k=3))
        part3 = ''.join(random.choices(string.digits, k=3))
        
        access_code = f"{part1}-{part2}-{part3}"
        
        # Extract numeric value from bottle size (remove 'ml')
        bottle_size_num = int(self.bottle_size.replace('ml', ''))
        
        # Create JSON response
        access_data = {
            "access_code": access_code,
            "bottle_size": bottle_size_num
        }
        
        # Store in field for logging
        self.access_code_json = str([access_data])
        
        # Log the generation
        self.message_post(
            body=f"POS Access Code generated: {access_code} for {self.bottle_size} bottle",
            message_type='notification'
        )
        
        return access_data
