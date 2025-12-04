
from odoo import api, fields, models, _
import re
from datetime import datetime,date
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    country_id = fields.Many2one('res.country', string='Country')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string='Gender')
    wk_dob = fields.Date( string='Date of Birth')
    bottle_size = fields.Selection([('25ml', '25 ml'), ('50ml', '50 ml'), ('100ml', '100 ml'), ('200ml', '200 ml')], string='Bottle Size')

    @api.constrains('wk_dob')
    def age_cal(self):
        for rec in self:	
            if rec.wk_dob > date.today():
                raise ValidationError("DOB should not exceed the Current Date")