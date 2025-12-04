from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    daily_access_code = fields.Char(compute="set_daily_access_code", string="Daily Access Code")

    @api.depends('name')
    def set_daily_access_code(self):
        for rec in self:
            rec.daily_access_code = self.env['access.code.helper'].get_today_access_code()

