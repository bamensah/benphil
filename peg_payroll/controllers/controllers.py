# -*- coding: utf-8 -*-
# from odoo import http


# class PegPayroll(http.Controller):
#     @http.route('/peg_payroll/peg_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/peg_payroll/peg_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('peg_payroll.listing', {
#             'root': '/peg_payroll/peg_payroll',
#             'objects': http.request.env['peg_payroll.peg_payroll'].search([]),
#         })

#     @http.route('/peg_payroll/peg_payroll/objects/<model("peg_payroll.peg_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('peg_payroll.object', {
#             'object': obj
#         })
