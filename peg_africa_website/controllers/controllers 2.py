# -*- coding: utf-8 -*-
from odoo import http

class PegAfricaWebsite(http.Controller):
    @http.route('/contactus', type="http", website=True, auth='public')
    def index(self, **kw):
        product_types = http.request.env['wave2.peg.africa.type.of.product'].sudo().search([])
        return http.request.render('peg_africa_website.peg_contactus_form', {
            'product_types': product_types
        })
