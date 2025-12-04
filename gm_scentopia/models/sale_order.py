from odoo import api, models, fields

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    
    customer_no = fields.Char(related="partner_id.ref", string="Customer No")
    sales_commission = fields.Monetary(string="Sales Commission")
    date_time_1 = fields.Datetime(string="Date Time 1")
    quote_number = fields.Char(string="Quote Number")
     
