# -*- coding: utf-8 -*-
# from odoo import http


# class GmScentopia(http.Controller):
#     @http.route('/gm_scentopia/gm_scentopia', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gm_scentopia/gm_scentopia/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('gm_scentopia.listing', {
#             'root': '/gm_scentopia/gm_scentopia',
#             'objects': http.request.env['gm_scentopia.gm_scentopia'].search([]),
#         })

#     @http.route('/gm_scentopia/gm_scentopia/objects/<model("gm_scentopia.gm_scentopia"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gm_scentopia.object', {
#             'object': obj
#         })

