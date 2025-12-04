from odoo import models, fields, api, _

class FragranceFamily(models.Model):
    _name = 'fragrance.family'
    _description = 'Fragrance Family'

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Description')
    color = fields.Char(string='Color')
    threshold = fields.Float(string='Threshold', default=3.5, help="Minimum value to be considered in this fragrance family")
    value_ids = fields.One2many('fragrance.family.value', 'fragrance_family_id', string='Values')
    intensity_index_ids = fields.One2many('fragrance.intensity.index', 'fragrance_family_id', string='Intensity Indices')

    @api.onchange('value_ids.value_end', 'value_ids.value_start')
    def onchange_value(self):
        for rec in self.value_ids:
            rec._compute_percentage_start()
            rec._compute_percentage_end()

class FragranceFamilyValue(models.Model):
    _name = 'fragrance.family.value'
    _description = 'Fragrance Family Value'

    level = fields.Selection([
            ('low','Low'),
            ('mid','Mid'),
            ('high','High'),
            ('extreme','Extreme')
        ], string='Level', help="Level of the fragrance family value")
    label = fields.Char(string="Label for Initial", help="Label to be shown on the initial oil selection page")
    value_start = fields.Float(string='Value Start')
    value_end = fields.Float(string='Value End')
    percentage_start = fields.Float(string='Percentage Start', compute='_compute_percentage_start')
    percentage_end = fields.Float(string='Percentage End', compute='_compute_percentage_end')
    fragrance_family_id = fields.Many2one('fragrance.family', string='Fragrance Family')

    @api.depends('value_start')
    def _compute_percentage_start(self):
        for rec in self:
            if rec.value_start:
                highest = max(rec.fragrance_family_id.value_ids.mapped('value_end'))
                if highest:
                    rec.percentage_start = rec.value_start / highest * 100
                else :
                    rec.percentage_start = 0.0
            else:
                rec.percentage_start = 0.0


    @api.depends('value_end')
    def _compute_percentage_end(self):
        for rec in self:
            if rec.value_end:
                highest = max(rec.fragrance_family_id.value_ids.mapped('value_end'))
                if highest:
                    rec.percentage_end = rec.value_end / highest * 100
                else :
                    rec.percentage_end = 0.0
            else:
                rec.percentage_end = 0.0
            
class FragranceIntensityIndex(models.Model):
    _name = 'fragrance.intensity.index'
    _description = 'Fragrance Intensity Index'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Sequence', help="Order of the intensity index")
    name = fields.Char(string='Name')
    fragrance_family_id = fields.Many2one('fragrance.family', string='Fragrance Family')
