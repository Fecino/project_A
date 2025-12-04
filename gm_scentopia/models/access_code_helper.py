from odoo import models, api
import random
import string
from datetime import date

class AccessCodeHelper(models.Model):
    _name = "access.code.helper"
    _description = "Helper for Universal Access Code"

    @api.model
    def generate_daily_access_code(self):
        """Generate code harian alphanumeric (6-8 char)"""
        length = 8
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choices(chars, k=length))

        self.env['ir.config_parameter'].sudo().set_param("universal_access_code", code)
        return code
    
    @api.model
    def get_today_access_code(self):
        return self.env['ir.config_parameter'].sudo().get_param("universal_access_code")
