# -*- coding: utf-8 -*-
from odoo import http

# class PegFinanceMods(http.Controller):
#     @http.route('/peg_finance_mods/peg_finance_mods/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/peg_finance_mods/peg_finance_mods/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('peg_finance_mods.listing', {
#             'root': '/peg_finance_mods/peg_finance_mods',
#             'objects': http.request.env['peg_finance_mods.peg_finance_mods'].search([]),
#         })

#     @http.route('/peg_finance_mods/peg_finance_mods/objects/<model("peg_finance_mods.peg_finance_mods"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('peg_finance_mods.object', {
#             'object': obj
#         })