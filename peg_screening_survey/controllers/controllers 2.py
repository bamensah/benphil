# -*- coding: utf-8 -*-
from odoo import http

# class PegScreeningSurvey(http.Controller):
#     @http.route('/peg_screening_survey/peg_screening_survey/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/peg_screening_survey/peg_screening_survey/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('peg_screening_survey.listing', {
#             'root': '/peg_screening_survey/peg_screening_survey',
#             'objects': http.request.env['peg_screening_survey.peg_screening_survey'].search([]),
#         })

#     @http.route('/peg_screening_survey/peg_screening_survey/objects/<model("peg_screening_survey.peg_screening_survey"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('peg_screening_survey.object', {
#             'object': obj
#         })