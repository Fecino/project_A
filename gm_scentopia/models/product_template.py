from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    commission_rate = fields.Float(string="Commission Rate")
    manufacturer_id = fields.Many2one('res.partner', string="Manufacturer")
    
