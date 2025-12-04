
from odoo import http
from odoo.http import request

class UserController(http.Controller):
    @http.route('/user', type='http', auth='user', website=True)
    def user_page(self, **kw):
        return request.render('gm_web.dashboard_page')
    
    # @http.route('/take_a_survey', type='http', auth='user', website=True)
    # def take_a_survey(self):
         
