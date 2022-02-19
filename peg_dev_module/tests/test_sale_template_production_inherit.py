# -*- coding: utf-8 -*-
from odoo.tests import common


class TestSaleOrder(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrder, self).setUp()

        self.sale_order = self.env['sale.order']
        self.sale_order_line = self.env['sale.order.line']
        self.sale_product_template = self.env['sale.product.template']
        # self.sale_product_template_line = self.env['sale.product.template.line']
        self.product_product = self.env['product.product']
        self.partner = self.env['res.partner']
        self.partner = self.env['res.partner']

        # create product product
        self.product_product1 = []
        self.product_product1.append((0, 0, self.product_product.create({'name': 'Product 1', 'tax_id': 1})))

        # create product template
        self.sale_product_template1 = self.sale_product_template.create({
            'name': 'product tempalte 1',
            'sale_product_template_ids': self.product_product1,
            'templ_active': True
        })

        # create an partner
        self.partner1 = self.partner.create({
            'name': 'Robilie'
        })

        # create SO

        self.sale_order1 = self.sale_order.create({
            'partner_id': self.partner1,
            'product_template_id': self.sale_product_template1,
            'date_order': '1991-10-08:07:00'
        })

    def test_generate_sale_order(self):
        self.sale_order1.action_get_order_line_from_sale_product_template()
        self.assertEqual(str(self.sale_order1.order_line[0].name), 'Product 1')
        self.assertEqual(str(self.sale_order1.order_line[0].tax_id.id), '1')

    def test_confirmation_date(self):
        self.sale_order1.action_confirm()
        self.assertEqual(self.sale_order1.state, 'done')
        self.assertEqual(str(self.sale_order1.confirmation_date), '1991-10-08:07:00')

    def test_invoice_date(self):
        self.invoice = []
        self.invoice = self.sale_order1.action_invoice_create()
        self.invoice_obj = self.env['account.invoice'].serach([('id', '=', self.invoice[0])])
        self.assertEqual(str(self.invoice_obj.date_invoice), '1991-10-08:07:00')
