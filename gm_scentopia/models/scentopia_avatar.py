from odoo import models, fields, api, _
import base64
from odoo.tools.mimetypes import guess_mimetype

class ScentopiaAvatar(models.Model):
    _name = 'scentopia.avatar'
    _description = 'Scentopia Avatar'

    name = fields.Char(string='Personality Type', required=True)
    title = fields.One2many('scentopia.avatar.title', 'avatar_id', string="Avatar Titles")

    image = fields.Binary(string='Unisex Avatar')
    male_image = fields.Binary(string='Male Avatar')
    female_image = fields.Binary(string='Female Avatar')
    is_unisex = fields.Boolean(string='Is Unisex Avatar')

    video_url = fields.Char(string="Avatar Video")
    overview = fields.Text(string="Overview")
    emotions = fields.Char(string="Emotions")
    goal = fields.Char(string="Goal")
    judges_other_by = fields.Char(string="Judges Other By")
    influences_other_by = fields.Char(string="Influences Other By")
    strengths = fields.Html(string="Strengths and Limitations")
    communication = fields.Char(string="Communication and Decision-Making Style")
    values_to_org = fields.Char(string="Values to the Organization")
    under_pressure = fields.Char(string="Under Pressure")
    fears = fields.Char(string="Fears")
    personality = fields.Text(string="Personality")
    increase_effectiveness = fields.Text(string="Would increase effectiveness with")
    
    fragrance_family_ids = fields.Many2many('fragrance.family', string="Fragrance Families")
    
    five_elements_report  = fields.Binary(string="Five Elements Report")
    five_elements_report_name = fields.Char(string="Five Elements Report Name")
    love_match_report = fields.Binary(string="Love Match Report")
    love_match_report_name = fields.Char(string="Love Match Report Name")
    career_match_report = fields.Binary(string="Career Match Report")
    career_match_report_name = fields.Char(string="Career Match Report Name")
    soulfulness_report = fields.Binary(string="Soulfulness Report")
    soulfulness_report_name = fields.Char(string="Soulfulness Report Name")
    thirty_one_types_report = fields.Binary(string="31 Types Report")
    thirty_one_types_report_name = fields.Char(string="31 Types Report Name")
    tcm_report = fields.Binary(string="TCM Report")
    tcm_report_name = fields.Char(string="TCM Report Name")
    ayurvedic_report = fields.Binary(string="Ayurvedic Report")
    ayurvedic_report_name = fields.Char(string="Ayurvedic Report Name")
    perfume_personality_report = fields.Binary(string="Perfume Personality Report")
    perfume_personality_report_name = fields.Char(string="Perfume Personality Report Name")

    def get_image_mime(self, gender):
        for record in self.with_context(bin_size=False):
            if gender == 'male':
                image = record.male_image
            elif gender == 'female':
                image = record.female_image
            else:
                image = record.image

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
        return image  # already string or None
    # measurements = fields.One2many('scentopia.avatar.measurement', 'avatar_id', string="Measurements")


class ScentopiaAvatarTitle(models.Model):
    _name = 'scentopia.avatar.title'
    _description = 'Scentopia Avatar Title'
    _order = 'name asc'

    name = fields.Char(string='Title', required=True)
    avatar_id = fields.Many2one('scentopia.avatar', string="Avatar")
