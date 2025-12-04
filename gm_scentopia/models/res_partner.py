from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    designation = fields.Char(string='Designation')
    department = fields.Many2one('hr.department', string='Department')
    account_type = fields.Char(string='Account Type')
    
    
