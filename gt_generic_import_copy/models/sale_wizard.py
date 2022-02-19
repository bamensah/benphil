# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
from datetime import datetime
import io
from odoo import models, fields, api, _
# from odoo import api
from odoo import exceptions
# from odoo import fields
# from odoo import models, 
from odoo.tools import pycompat
from openerp import models, fields, api, _
# from openerp import api
# from openerp import fields
# from openerp import models, 
from openerp.exceptions import ValidationError
from odoo.exceptions import UserError
import xlrd



class SaleOrder(models.TransientModel):
    _name = 'sale.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    data_file = fields.Binary(string="File")
    seq_opt = fields.Selection([('f_sequence', 'File Sequence'), ('s_sequence', 'System Sequence')],string='Sequence Option',help='What action perform when record not found?')
    state_stage = fields.Selection([('draft', 'Quotation'), ('sale', 'Sale Order')], string='Import State')
    import_prod_by = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')], string='Import Product By')

    def Import_sale_order(self):
        Partner = self.env['res.partner']
        Log = self.env['log.management']
        Currency = self.env['res.currency']
        Pricelist = self.env['product.pricelist']
        Uom_categ=self.env['uom.category']
        Product = self.env['product.product']
        Uom = self.env['uom.uom']
        Team = self.env['crm.team']
        Tax=self.env['account.tax']
        User=self.env['res.users']
        Term=self.env['account.payment.term']
        sale_result = {}
        tax_list = []
        
        Sale = self.env['sale.order']
        sale_fileds = Sale.fields_get()
        sale_default_value = Sale.default_get(sale_fileds)
        
        Sale_line = self.env['sale.order.line']
        line_fields = Sale_line.fields_get()
        sale_line_default_value = Sale_line.default_get(line_fields)
        
        if self.select_file and self.data_file and self.seq_opt and self.state_stage and self.option:
            try:
                if self.select_file == 'csv' :
                    csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                    csv_reader_data = iter(csv_reader_data)
                    next(csv_reader_data)
                    file_data = csv_reader_data
                elif self.select_file == 'xls':
                    file_datas = base64.decodestring(self.data_file)
                    workbook = xlrd.open_workbook(file_contents=file_datas)
                    sheet = workbook.sheet_by_index(0)
                    data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                    data.pop(0)
                    file_data = data
            except:
                raise ValidationError(_('Please select proper file type.'))
        else:
            raise ValidationError(_('Please select file type,operation,import state and seqeuance'))

        for row in file_data:
            if len(row)!=14 and self.select_file == 'csv':
                raise ValidationError("You can let empty cell in csv file or please use xls file.Make sure comma (',') not used when using csv file.")
            
            if not row[0] or not row[1] or not row[2] or not row[4] or not row[5]:
                raise exceptions.Warning(_('Order,Supplier,Currency,Date and Product are required fields.'))

#           Search if not found it will create if create option is selected
            partner_id = Partner.search([('name', '=ilike', row[1]),('active','=',True),('customer_rank','=',1)],limit=1)
            if partner_id:
                partner_id=partner_id.id
            else:
                if self.option=='create':
                    partner_id=Partner.create({'name':row[1],'supplier_rank':0,'customer_rank':1,'company_type':'company'}).id
                else:
                    Log.create({'operation':'so','message':'Skipped could not find the partner with name %s'% str(row[1])})
                    continue
#           Search if not found it will create if create option is selected
            pricelist_id = Pricelist.search([('name', '=ilike', row[2])],limit=1)
            currency_id = Currency.search([('name', '=ilike', 'USD')],limit=1)
            if pricelist_id:
                pricelist_id=pricelist_id.id
            else:
                if self.option=='create':
                    pricelist_id=Pricelist.create({'name':row[2],'currency_id':currency_id.id if currency_id else False}).id
                else:
                    Log.create({'operation':'so','message':'Skipped could not find the pricelist with name %s'% str(row[2])})
                    continue
            
            #           Search if not found it will create if create option is selected
            payment_term_id=False
            if row[12]:
                payment_term_id=Term.search([('name','ilike',str(row[12]))],limit=1)
                if payment_term_id:
                    payment_term_id=payment_term_id.id
                else:
                    if self.option=='create':
                        payment_term_id=Term.create({'name':row[12]}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the payment term with name %s'% str(row[12])})
                        continue
#           Search if not found it will create if create option is selected
            user_id=False
            if row[11]:
                user_id=User.search([('name','=ilike',row[11])],limit=1)
                if user_id:
                    user_id=user_id.id
                else:
                    if self.option=='create':
                        user_id=User.create({'name':row[11],'login':row[11].lower()}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the salesperson with name %s'% str(row[11])})
                        continue
                        
#           Search if not found it will create if create option is selected
            team_id=False
            if row[13]:
                team_id=Team.search([('name','=ilike',row[13])],limit=1)
                if team_id:
                    team_id=team_id.id
                else:
                    if self.option=='create':
                        team_id=Team.create({'name':row[13]}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the sales team with name %s'% str(row[13])})
                        continue

            reference=row[3]

            try:
                date=datetime.strptime(row[4], '%d-%m-%Y').strftime('%Y-%m-%d %H:%M:%S')
            except:
                raise ValidationError(_('Date format must be dd-mm-yyyy.'))
            
            sales_vals=sale_default_value.copy()
            sales_vals.update({
                'name': row[0] if self.seq_opt == 'f_sequence' else 'New',
                'partner_id':partner_id,
                'pricelist_id':pricelist_id,
                'date_order':date,
                'client_order_ref':reference,
                'user_id':user_id,
                'payment_term_id':payment_term_id,
                'team_id':team_id,
            })

#           Search if not found it will create if create option is selected
            if self.import_prod_by == 'barcode':
                product_id=Product.search([('barcode','=',str(row[5])),('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[9], 'barcode':str(row[5]), 'name':str(row[5]) ,'type':'product'}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the product with barcode %s'% str(row[5]) })
                        continue
            if self.import_prod_by == 'code':
                product_id=Product.search([('default_code','=ilike',str(row[5])),('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[9],'default_code': str(row[5]),'name':str(row[5]),'type':'product'}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the product with code %s'% str(row[5]) })
                        continue
            if self.import_prod_by == 'name':
                product_id=Product.search([('name','=ilike',str(row[5])),('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[9],'name':str(row[5]),'type':'product'}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the product with name %s'% str(row[5]) })
                        continue
            # print ('_______product________',product_id.name)

            ####### original
            # product_id=Product.search([('default_code','=',str(int(row[5])) if isinstance(row[5],float) else row[5]),('active','=',True)],limit=1)
            # if product_id:
            #     product_id=product_id.id
            # else:
            #     if self.option=='create':
            #         product_id=Product.create({'list_price':row[9],'default_code':str(int(row[5])) if isinstance(row[5],float) else row[5],'name':str(int(row[5])) if isinstance(row[5],float) else row[5],'type':'product'}).id
            #     else:
            #         Log.create({'operation':'so','message':'Skipped could not find the product with code %s'% (str(int(row[5])) if isinstance(row[5],float) else row[5])})
            #         continue
            ####### original

#           Search if not found it will create if create option is selected
            uom_id=Uom.search([('name','=ilike',row[7])],limit=1)
            uom_categ_id=Uom_categ.search([('name','=','Unit')],limit=1)

            if uom_id:
                uom_id=uom_id.id
            else:
                if self.option=='create':
                    uom_id=Uom.create({'name':row[7],'category_id':uom_categ_id.id}).id
                else:
                    Log.create({'operation':'so','message':'Skipped could not find the uom with name %s'% str(row[7])})
                    continue
#           Search if not found it will create if create option is selected

            for tax in str(row[10]).split(','):
                tax_id = Tax.search([('name', '=', tax.strip()),('type_tax_use', '=', 'sale')],limit=1)
                if tax_id:
                    tax_list.append(tax_id.id)
            
            # cust_tax=Tax.search([('name','=',float(row[10])),('type_tax_use','=','sale')],limit=1)
            # if row[10]:
            #     if cust_tax:
            #         cust_tax=cust_tax.id
            #     else:
            #         if self.option=='create':
            #             cust_tax=Tax.create({'name':float(row[10]),'type_tax_use':'sale','amount':float(row[10])}).id
            #         else:
            #             Log.create({'operation':'so','message':'Skipped could not find the tax with name %s'% float(row[10])})
            #             continue

            sale_line_vals=sale_line_default_value.copy()
            sale_line_vals.update({
                'product_id':product_id,
                'name':row[8],
                # 'date_planned':date,
                # 'product_qty':row[6],
                'product_uom':uom_id,
                'price_unit':row[9],
                # 'tax_id':[(6,0,[cust_tax])],
                'tax_id':[(6,0,tax_list)]
            })
            
            line=[(0,0,sale_line_vals)]
#            It will check in deictionay this key is available or not if not it will create otherwise it will update
            if sale_result.get(row[0]):
                old_line = sale_result[row[0]]['order_line']
                sale_result[row[0]].update({'order_line': old_line + line})
            if not sale_result.get(row[0]):
                sales_vals.update({'order_line': line})
                sale_result[row[0]] = sales_vals
#           Finally on sale_result dict it will loop and create po
        for sales in sale_result.values():
            sales_id = Sale.create(sales)
#            If state is confirm it will confirm the order
            if self.state_stage=='sale':
                sales_id.action_confirm()
            else:
                return sales_id


class SaleOrderLineWizard(models.TransientModel):
    _name = 'sale.order.line.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")
    import_prod_by = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')], string='Import Product By')
    prod_detail = fields.Selection([('file', 'Take Deatils From The File'), ('product', 'Take Details From Product')], string="Product Details")
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    
    def import_order_lines(self):
        print ('\n\n________def import_order_lines___________',self._context)
        Log = self.env['log.management']
        Product = self.env['product.product']
        Uom = self.env['uom.uom']
        Tax=self.env['account.tax']
        Uom_categ=self.env['uom.category']
        sale_id = self.env['sale.order'].browse(self._context.get('active_ids'))

        sale_order_line_obj = self.env['sale.order.line']
        sol_fields = sale_order_line_obj.fields_get()
        sol_fields_default_values = sale_order_line_obj.default_get(sol_fields)
        if self.select_file and self.data_file and self.import_prod_by and self.prod_detail:
            try:
                if self.select_file == 'csv' :
                    csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                    csv_reader_data = iter(csv_reader_data)
                    next(csv_reader_data)
                    file_data = csv_reader_data
                elif self.select_file == 'xls':
                    file_datas = base64.decodestring(self.data_file)
                    workbook = xlrd.open_workbook(file_contents=file_datas)
                    sheet = workbook.sheet_by_index(0)
                    data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                    data.pop(0)
                    file_data = data
            except:
                raise UserError(_('Please select proper file type.'))
        else:
            raise UserError(_('Please select file type, file, import product by and product details'))
        for row in file_data:
            tax_list = []
            #Product

            if self.import_prod_by == 'barcode':
                product_id=Product.search([('barcode','=',str(row[0])),('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[4], 'barcode':str(row[0]), 'name':str(row[0]) ,'type':'product'}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the product with barcode %s'% str(row[0]) })
                        continue
            if self.import_prod_by == 'code':
                product_id=Product.search([('default_code','=ilike',str(row[0])),('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[4],'default_code': str(row[0]),'name':str(row[0]),'type':'product'}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the product with code %s'% str(row[0]) })
                        continue
            if self.import_prod_by == 'name':
                product_id=Product.search([('name','=ilike',str(row[0])),('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[4],'name':str(row[0]),'type':'product'}).id
                    else:
                        Log.create({'operation':'so','message':'Skipped could not find the product with name %s'% str(row[0]) })
                        continue
            # print ('_______product________',product_id.name)

            

#           Search if not found it will create if create option is selected
            uom_id=Uom.search([('name','=ilike',row[2])],limit=1)
            uom_categ_id=Uom_categ.search([('name','=','Unit')],limit=1)

            if uom_id:
                uom_id=uom_id.id
            else:
                if self.option=='create':
                    uom_id=Uom.create({'name':row[2],'category_id':uom_categ_id.id}).id
                else:
                    Log.create({'operation':'so','message':'Skipped could not find the uom with name %s'% str(row[2])})
                    continue
#           Search if not found it will create if create option is selected

            for tax in str(row[5]).split(','):
                tax_id = Tax.search([('name', '=', tax.strip()),('type_tax_use', '=', 'sale')],limit=1)
                if tax_id:
                    tax_list.append(tax_id.id)
            

            sale_line_vals=sol_fields_default_values.copy()
            sale_line_vals.update({
                'product_id':product_id,
                'name':row[3],
                # 'date_planned':date,
                # 'product_qty':row[6],
                'product_uom':uom_id,
                'price_unit':row[4],
                # 'tax_id':[(6,0,[cust_tax])],
                'tax_id':[(6,0,tax_list)]
            })
            
            line=[(0,0,sale_line_vals)]
#            It will check in deictionay this key is available or not if not it will create otherwise it will update
            sale_line = sale_id.write({'order_line':line})
        return sale_line