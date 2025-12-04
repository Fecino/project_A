from odoo import models, fields, api
import base64
from odoo.exceptions import ValidationError
import os

class PortalConfig(models.Model):
    _name = 'portal.config'
    _description = 'Portal Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Name', required=True, tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    
    # Disclaimer PDF Configuration
    disclaimer_pdf = fields.Binary('Disclaimer PDF', 
        help="Upload PDF file for disclaimer terms and conditions", 
        tracking=True)
    disclaimer_pdf_filename = fields.Char('PDF Filename', 
        help="Original filename of the uploaded PDF", 
        tracking=True)
    show_disclaimer_pdf = fields.Boolean('Show Disclaimer PDF', 
        default=False, 
        help="Show PDF download link in disclaimer page", 
        tracking=True)
    disclaimer_pdf_title = fields.Char('PDF Title', 
        default='Download Full Terms & Conditions', 
        tracking=True)
    
    # http://localhost:8069/my/perfume-showoff/video
    show_video = fields.Boolean('Show Video', default=False, tracking=True)
    video_url = fields.Char('Video URL', 
        help="YouTube or Vimeo embed URL (e.g., https://www.youtube.com/embed/VIDEO_ID)", 
        tracking=True)
    video_thumbnail = fields.Binary('Video Thumbnail', 
        help="Thumbnail image for the video (displayed before play)")

    # http://localhost:8069/my/perfume-start-041
    video_title = fields.Char('Video Title', default='Tutorial Video', tracking=True)
    video_description = fields.Text('Video Description', 
        default='Video of tearing & folding the cup and smelling', tracking=True)
    video_duration = fields.Char('Video Duration', help='e.g., 2:30', tracking=True)
    video_url_perfume = fields.Char('Video URL', 
        help="YouTube or Vimeo embed URL (e.g., https://www.youtube.com/embed/VIDEO_ID)", 
        tracking=True)
    video_thumbnail_perfume = fields.Binary('Video Thumbnail', 
        help="Thumbnail image for the video (displayed before play)")

    @api.model
    def default_get(self, fields):
        res = super(PortalConfig, self).default_get(fields)
        if 'video_thumbnail' not in res and not self.video_thumbnail:
            # Set default thumbnail from static file
            static_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'static', 'src', 'img', 'video_scent.png'
            )
            try:
                with open(static_path, 'rb') as f:
                    res['video_thumbnail'] = base64.b64encode(f.read())
            except:
                pass
        return res

    @api.constrains('video_url')
    def _check_video_url(self):
        for config in self:
            if config.video_url and not any(
                config.video_url.startswith(prefix) 
                for prefix in (
                    'https://www.youtube.com/embed/',
                    'https://youtube.com/embed/',
                    'https://player.vimeo.com/video/'
                )
            ):
                raise ValidationError('Please provide a valid YouTube or Vimeo embed URL')

    @api.model
    def get_disclaimer_config(self):
        """Get disclaimer configuration for frontend"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            return {
                'show_pdf': False,
                'pdf_title': 'Download Full Terms & Conditions',
                'pdf_filename': None
            }
        
        return {
            'show_pdf': config.show_disclaimer_pdf,
            'pdf_title': config.disclaimer_pdf_title or 'Download Full Terms & Conditions',
            'pdf_filename': config.disclaimer_pdf_filename,
            'pdf_id': config.id if config.disclaimer_pdf else None
        }
                
class PortalCustomPage(models.Model):
    _name = 'portal.custom.page'
    _description = 'Portal Custom Page'
    _order = 'sequence, id'
    
    name = fields.Char('Page Name', required=True, translate=True)
    url = fields.Char('URL', required=True)
    sequence = fields.Integer('Sequence', default=10)
    is_published = fields.Boolean('Published', default=True)
    portal_config_id = fields.Many2one('portal.config', string='Portal Configuration')
    icon = fields.Char('Icon', help='Font Awesome icon class (e.g., fa-home)')