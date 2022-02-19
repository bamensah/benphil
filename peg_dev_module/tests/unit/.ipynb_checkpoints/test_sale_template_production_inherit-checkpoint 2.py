# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
import logging

_logger = logging.getLogger(__name__)


class TestSaleOrder(TransactionCase):

    def test_sale_order_confirmation_date(self):
                                     
        # create an user
        #self.partner1 = self.env['res.users'].create({
        #    'name': 'KHK'
        #})

        # create product product
        #product = self.env['product.product'].create({
        #    'name': 'Product 1',
        #    'type': 'product',
        #    'categ_id': 1,
        #    'purchase_method': 'receive',
        #    'invoice_policy': 'order',
        #    'expense_policy': 'no',
        #    'responsible_id': 2,
        #    'lst_price': 2000.0,
        #})
        
        #_logger.info('ID PRODUCT ' + str(product.id))
        
        # create product template
        #sale_product_template = self.env['sale.product.template'].create({
        #    'name': 'product tempalte 1',
        #})
        
        #template_line = self.env['sale.product.template.line'].create({
        #    'name': product.id,
        #    'sale_template_id': sale_product_template.id,
        #    'ordered_qty': 2,
        #    'discount': 0,
        #    'product_uom':1,
        #    'unit_price': 2000.0
        #})
        
        #sale_product_template.write({
        #    'sale_product_template_ids': template_line
        #})
        
        
        #_logger.info('ID PRODUCT TEMPLATE ' + str(sale_product_template.id))
        
        # create product template line
        
        
        #_logger.info('ID PRODUCT TEMPLATE LINE' + str(template_line.id))
        
        #product_product1 = []
        #product_product1.append((0, 0, val))
        
        

        
        
        #_logger.info('ID PRODUCT TEMPLATE ' + str(sale_product_template1.id))

        # create an partner
        #partner1 = self.env['res.partner'].create({
        #    'name': 'Robilife'
        #})

        # create SO
        sale_order = self.env['sale.order'].create({
            'partner_id': 2,
            'product_template_id': 2,
            'date_order': '1991-10-08:07:00'
        })                           
                                     
        sale_order.action_get_order_line_from_sale_product_template()
        
        #self.assertEqual(str(sale_order.order_line[0].name), 'Product 1')
        #self.assertEqual(str(sale_order1.order_line[0].tax_id.id), '1')
                                     
        sale_order.action_confirm()
        self.assertEqual(str(sale_order.state), 'sale')
        self.assertEqual(str(sale_order.confirmation_date), '1991-10-08 07:00:00')
                                     
        invoice = []
        invoice = sale_order.action_invoice_create()
        invoice_obj = self.env['account.invoice'].search([('id', '=', invoice[0])])
        self.assertEqual(str(invoice_obj.date_invoice), '1991-10-08')