from odoo import fields, models, api
import base64
from odoo.tools.mimetypes import guess_mimetype
import logging

_logger = logging.getLogger(__name__)

class ScentopiaWeb(models.Model):
    _name = 'scentopia.web'
    _description = 'Scentzania Web Model' 

    name = fields.Char(required=True, string="Name")
    description = fields.Html(string='Description', required=True)

    line_ids = fields.One2many(
        comodel_name='scentopia.web.line',
        inverse_name='scentopia_web_id',
        string='Lines'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide the Scentzania Web without removing it.'
    )

class ScentopiaWebLine(models.Model):
    _name = 'scentopia.web.line'
    _description = 'Scentzania Web Line Model'

    scentopia_web_id = fields.Many2one(
        comodel_name='scentopia.web',
        string='Scentzania Web',
        ondelete='cascade'
    )
    name = fields.Selection(selection=[
        ('header', 'Header'),
        ('image_1', 'Image 1'),
        ('image_2', 'Image 2'),
        ('image_3', 'Image 3'),
        ('image_4', 'Image 4'),
    ], string='Name')
    image = fields.Binary(string='Image')
    image_filename = fields.Char(string='Image Filename')
    image_mime = fields.Char(string='Image MIME Type', compute='_compute_image_mime')

    @api.depends('image')
    def _compute_image_mime(self):
        for record in self.with_context(bin_size=False):
            if record.image:
               img_bytes = base64.b64decode(record.image)
               record.image_mime = guess_mimetype(
                   img_bytes
               )
            else:
                record.image_mime = False

    def decode_image(self, image):
        if image and isinstance(image, bytes):
            return image.decode('utf-8')  # Convert bytes -> string
        return image  # already string or None
