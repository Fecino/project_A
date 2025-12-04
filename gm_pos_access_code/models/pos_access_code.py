from odoo import models, fields, api
from datetime import datetime, timedelta
import random
import string
 

class PosAccessCode(models.Model):
    _name = 'pos.access.code'
    _description = 'POS Access Code'
    _order = 'create_date desc'
    
    name = fields.Char(string='Access Code', required=True, readonly=True)
    booking_code = fields.Char(string='Booking Code')
    booking_from = fields.Char(string='Booking From')
    booking_price = fields.Float(string='Booking Price')
    bottle_size = fields.Selection([
        ('30ml', '30ml'),
        ('50ml', '50ml'),
        ('100ml', '100ml'),
    ], string='Bottle Size', required=True)
    
    # Validity inputs from UI
    validity_value = fields.Integer(string='Validity Value', default=1, help='Duration number for code validity')
    validity_unit = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days'),
    ], string='Validity Unit', default='days')
    
    # Expiration fields
    create_date = fields.Datetime(string='Created Date', readonly=True)
    expiry_date = fields.Datetime(string='Expiry Date', readonly=True)
    is_expired = fields.Boolean(string='Is Expired', compute='_compute_is_expired', store=True)
    is_valid = fields.Boolean(string='Is Valid', compute='_compute_is_valid', store=True)
    
    # Usage tracking
    usage_count = fields.Integer(string='Usage Count', default=0, readonly=True)
    last_used_date = fields.Datetime(string='Last Used Date', readonly=True)
    max_usage = fields.Integer(string='Max Usage', default=1, help='Maximum number of times this code can be used')
    
    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('used', 'Used'),
        ('exhausted', 'Exhausted'),
    ], string='Status', default='active', readonly=True)
    
    # Report/helper: Binary image
    logo_b64 = fields.Binary(string='Logo (b64)', compute='_compute_logo_b64', store=False, readonly=True)
    # Image-friendly alias for backend/report usage
    logo_b64_img = fields.Image(string='Logo Image', compute='_compute_logo_b64_img', store=False, readonly=True)
    # Optional: base64 string for data URI when needed
    logo_b64_str = fields.Text(string='Logo (b64 string)', compute='_compute_logo_b64_str')
    
    @api.depends('expiry_date')
    def _compute_is_expired(self):
        for record in self:
            if record.expiry_date:
                record.is_expired = datetime.now() > record.expiry_date
            else:
                record.is_expired = False
    
    @api.depends('is_expired', 'state', 'usage_count', 'max_usage')
    def _compute_is_valid(self):
        for record in self:
            record.is_valid = (
                not record.is_expired and 
                record.state == 'active' and 
                record.usage_count < record.max_usage
            )
    
    @api.model
    def create(self, vals):
        # Generate access code
        if not vals.get('name'):
            vals['name'] = self._generate_access_code(vals.get('bottle_size', '100ml'))
        
        # Set expiry date based on validity fields if provided
        validity_value = int(vals.get('validity_value') or 0)
        validity_unit = vals.get('validity_unit') or 'days'
        if validity_value > 0:
            if validity_unit == 'hours':
                vals['expiry_date'] = datetime.now() + timedelta(hours=validity_value)
            else:
                vals['expiry_date'] = datetime.now() + timedelta(days=validity_value)
        elif not vals.get('expiry_date'):
            # default fallback: 24 hours
            vals['expiry_date'] = datetime.now() + timedelta(hours=24)
        
        return super(PosAccessCode, self).create(vals)
    
    def _generate_access_code(self, bottle_size='100ml'):
        """Generate access code with bottle size suffix"""
        part1 = ''.join(random.choices(string.ascii_uppercase, k=3))
        part2 = ''.join(random.choices(string.ascii_uppercase, k=3))
        part3 = ''.join(random.choices(string.digits, k=3))
        
        # Get bottle size suffix
        suffix_map = {
            '30ml': '030',
            '50ml': '050',
            '100ml': '100'
        }
        suffix = suffix_map.get(bottle_size, '100')
        
        return f"{part1}-{part2}-{part3}-{suffix}"
    
    def use_access_code(self):
        """Use the access code (increment usage count)"""
        if not self.is_valid:
            return False
        
        self.write({
            'usage_count': self.usage_count + 1,
            'last_used_date': datetime.now()
        })
        
        # Check if max usage reached
        if self.usage_count >= self.max_usage:
            self.write({'state': 'exhausted'})
        
        return True
    
    def mark_as_used(self):
        """Mark access code as used (legacy method)"""
        self.write({'state': 'used'})
    
    def check_validity(self):
        """Check if access code is still valid"""
        self._compute_is_expired()
        if self.is_expired:
            self.write({'state': 'expired'})
        elif self.usage_count >= self.max_usage:
            self.write({'state': 'exhausted'})
        return self.is_valid
    
    @api.model
    def get_valid_code(self, access_code):
        """Get valid access code by name"""
        code = self.search([
            ('name', '=', access_code),
            ('state', '=', 'active')
        ], limit=1)
        
        if code and code.check_validity():
            return code
        return False
    
    @api.model
    def cleanup_expired_codes(self):
        """Cleanup expired access codes (can be called by cron)"""
        expired_codes = self.search([
            ('expiry_date', '<', datetime.now()),
            ('state', '=', 'active')
        ])
        expired_codes.write({'state': 'expired'})
        return len(expired_codes)
    
    def _compute_logo_b64(self):
        """Compute base64 logo from scentopia.web header once per env."""
        b64 = False
        try:
            web_rec = self.env.ref('gm_web.scentopia_web_data', raise_if_not_found=False)
            if web_rec:
                header_line = (web_rec.line_ids.filtered(lambda l: l.name == 'header')[:1])
                if header_line and header_line.image:
                    # Binary field is already base64-encoded; assign directly
                    b64 = header_line.image
        except Exception:
            b64 = False
        for rec in self:
            rec.logo_b64 = b64

    def _compute_logo_b64_str(self):
        """Convert Binary base64 to ascii string for data URI usage."""
        for rec in self:
            val = rec.logo_b64
            if val:
                if isinstance(val, bytes):
                    try:
                        rec.logo_b64_str = val.decode('utf-8')
                    except Exception:
                        rec.logo_b64_str = False
                elif isinstance(val, str):
                    rec.logo_b64_str = val
                else:
                    rec.logo_b64_str = False
            else:
                rec.logo_b64_str = False

    def _compute_logo_b64_img(self):
        """Mirror Binary into Image field for widget and /web/image access."""
        for rec in self:
            rec.logo_b64_img = rec.logo_b64 or False
