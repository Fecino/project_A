from odoo import models, fields, api
import base64
from odoo.tools.mimetypes import guess_mimetype

class InfoCard(models.Model):
    _name = 'info.card'
    _description = 'Information Card'
    _rec_name = 'fragrance_family_id'

    name = fields.Selection(
        [

            ('intro_app', 'Intro to App Page (/perfume-journey/intro)'),
            ('scent_paper', 'Scent Paper Page (/perfume-journey/scent-paper)'),
            ('collect_sticker', 'Collect Sticker Page (/perfume-journey/intro/collect-sticker)'),
            ('test_result', 'Test Result Page (/perfume-journey/intro/test-result)'),
            ('female_scent_ward', 'Female Scent Ward Page (/perfume-journey/intro/female-scent-ward)'),
            ('male_scent_ward', 'Male Scent Ward Page (/perfume-journey/intro/male-scent-ward)'),
            ('unisex_scent_ward', 'Unisex Scent Ward Page (/perfume-journey/intro/unisex-scent-ward)'),
            ('smell_scent_ward', 'Smell Scent Ward Page (/perfume-journey/intro/smell-scent-ward)'),
            ('marking_scent_paper', 'Marking Scent Paper Page (/perfume-journey/intro/marking-scent-paper)'),
            ('part_of_plants', 'Part of Plants Page (/perfume-journey/intro/part-of-plant)'),
            ('oil_added', 'Oil Added Page (/perfume-journey/oil-added)'),
            ('bottling_page', 'Bottling Page (/my/formula/bottling)'),
            ('formula_guide', 'Formula Guide Page (/perfume-journey/formula-guide)')
        ], string="Page", required=True
    )
    fragrance_family_id = fields.Many2one('fragrance.family', string='Fragrance Family')
    image_1 = fields.Binary(string="Image 1")
    image_2 = fields.Binary(string="Image 2")
    image_3 = fields.Binary(string="Image 3")
    image_4 = fields.Binary(string="Image 4")
    youtube_link = fields.Char(string="YouTube Link", help="URL to related YouTube video")
    mastertext = fields.Text(string="Master Text")
    subtext = fields.Text(string="Sub Text")

    # Checklists to control which content is needed/displayed
    has_youtube_link = fields.Boolean(string="Needs YouTube Link", default=False)
    has_mastertext = fields.Boolean(string="Needs Master Text", default=False)
    has_subtext = fields.Boolean(string="Needs Sub Text", default=False)
    has_image_2 = fields.Boolean(string="Needs Image 2", default=False)
    has_image_3 = fields.Boolean(string="Needs Image 3", default=False)
    has_image_4 = fields.Boolean(string="Needs Image 4", default=False)

    def get_image_mime(self):
        for record in self.with_context(bin_size=False):
            image = record.image_1

            if image:
               img_bytes = base64.b64decode(image)
               return guess_mimetype(
                   img_bytes
               )
            else:
                return False

    def decode_image(self, image):
        if image and isinstance(image, bytes):
            return image.decode('utf-8')  # Convert bytes -> string
        return image