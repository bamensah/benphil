# -*- coding: utf-8 -*-
from odoo import http

# class PegHelpdeskMods(http.Controller):
#     @http.route('/peg_helpdesk_mods/peg_helpdesk_mods/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/peg_helpdesk_mods/peg_helpdesk_mods/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('peg_helpdesk_mods.listing', {
#             'root': '/peg_helpdesk_mods/peg_helpdesk_mods',
#             'objects': http.request.env['peg_helpdesk_mods.peg_helpdesk_mods'].search([]),
#         })

#     @http.route('/peg_helpdesk_mods/peg_helpdesk_mods/objects/<model("peg_helpdesk_mods.peg_helpdesk_mods"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('peg_helpdesk_mods.object', {
#             'object': obj
#         })