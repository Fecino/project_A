from odoo import fields, models, api
from urllib.parse import urlparse, parse_qs

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    scentzania_oil_drop = fields.Integer(
        string="Scentzania Oil Drop",
        config_parameter='gm_scentopia.scentzania_oil_drop',
        help="Drop level for per ml."
    )
    font_link = fields.Char(
        string="Font Link",
        config_parameter='gm_scentopia.font_link',
        help="URL for the font"
    )
    font_name = fields.Char(
        string="Font Name",
        config_parameter='gm_scentopia.font_name',
        help="Name for the font"
    )
    bottling_video_url = fields.Char(
        string="Bottling Video URL",
        config_parameter='gm_scentopia.bottling_video_url',
        help="URL for the bottling video"
    )
    pump_video_url = fields.Char(
        string="Pump Video URL",
        config_parameter='gm_scentopia.pump_video_url',
        help="URL for the pump video"
    )
    seal_video_url = fields.Char(
        string="Seal Video URL",
        config_parameter='gm_scentopia.seal_video_url',
        help="URL for the seal video"
    )

    @api.onchange('font_link')
    def _onchange_font_url(self):
        if self.font_link and "fonts.googleapis.com" in self.font_link:
            query = parse_qs(urlparse(self.font_link).query)
            families = query.get('family')
            if families:
                family_name = families[0].split(':')[0].replace('+', ' ')
                self.font_name = family_name