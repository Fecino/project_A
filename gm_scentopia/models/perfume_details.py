# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PerfumeDetails(models.Model):
    _name = 'perfume.details'
    _description = 'Perfume Details'
    _rec_name = 'perfume_name'

    # Basic Information
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex')
    ], string='Gender', required=True)
    
    name_code = fields.Char(string='Name Code', required=True)
    scentopia_oil = fields.Char(string='Scentzania Oil')
    main_category_id = fields.Many2one('fragrance.family', string='Main Category')
    sub_category_id = fields.Many2one('fragrance.family', string='Sub Category')
    perfume_name = fields.Char(string='Scentzania Perfume Name', required=True)
    main_note = fields.Char(string='Main Note (Attribute)')
    
    # Perfume Pyramid
    top_note = fields.Text(string='Perfume Pyramid Top Note')
    middle_note = fields.Text(string='Perfume Pyramid Middle Note')
    base_note = fields.Text(string='Perfume Pyramid Base Note')
    
    # Additional Information
    historical_significance = fields.Text(string='Historical Significance of Key Ingredient')
    health_benefits = fields.Text(string='Health Benefits')
    strength = fields.Integer(string='Strength (0-10)', help='Strength attribute from 0 to 10')
    main_accords = fields.Text(string='Main Accords')
    
    # Attributes
    attribute_category = fields.Selection([
        ('1- Teen', '1 - Teen'),
        ('2- Adult', '2 - Adult'),
        ('3- money', '3 - Money'),
        ('4- Season', '4 - Season'),
        ('5- Sexy', '5 - Sexy'),
        ('6- Health', '6 - Health')
    ], string='Attribute Category')
    
    scent_writeup = fields.Text(string='Write up about the scent')
    
    # Image fields for oil detail page
    image1 = fields.Binary(string='Image 1', help='First product image')
    image2 = fields.Binary(string='Image 2', help='Second product image')
    image3 = fields.Binary(string='Image 3', help='Third product image')
    image4 = fields.Binary(string='Image 4', help='Fourth product image')
    image5 = fields.Binary(string='Image 5', help='Fifth product image')
    
    # Computed fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('name_code', 'perfume_name')
    def _compute_display_name(self):
        for record in self:
            if record.name_code and record.perfume_name:
                record.display_name = f"[{record.name_code}] {record.perfume_name}"
            elif record.perfume_name:
                record.display_name = record.perfume_name
            else:
                record.display_name = record.name_code or 'New Perfume'
