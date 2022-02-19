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
from datetime import datetime, date
import io
from odoo import models, fields, api, _
# from odoo import api
# from odoo import exceptions
# from odoo import fields
# from odoo import models
from odoo.tools import pycompat
from openerp import models, fields, api, _
# from openerp import api
# from openerp import fields
# from openerp import models
from openerp.exceptions import ValidationError
import xlrd



class Purchase_wizard(models.TransientModel):
    _name = 'purchase.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    data_file = fields.Binary(string="File")
    seq_opt = fields.Selection([('f_sequence', 'File Sequence'), ('s_sequence', 'System Sequence')],string='Sequence Option',help='What action perform when record not found?')
    state_stage = fields.Selection([('draft', 'Draft'), ('purchase', 'Purchase')], string='Import State')
    import_prod_by = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')], string='Import Product By')

    def Import_purchase_order(self):
        Partner = self.env['res.partner']
        Log = self.env['log.management']
        Currency = self.env['res.currency']
        Uom_categ=self.env['uom.category']
        Product = self.env['product.product']
        Uom = self.env['uom.uom']
        Tax=self.env['account.tax']
        purchase_result = {}
        
        Purchase = self.env['purchase.order']
        Purchase_fileds = Purchase.fields_get()
        purchase_default_value = Purchase.default_get(Purchase_fileds)
        
        Purchase_line = self.env['purchase.order.line']
        line_fields = Purchase_line.fields_get()
        purchase_line_default_value = Purchase_line.default_get(line_fields)
        
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
            if len(row)!=11 and self.select_file == 'csv':
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            
            if not row[0] or not row[1] or not row[2] or not row[4] or not row[5]:
                raise ValidationError(_('Order,Supplier,Currency,Date and Product are required fields.'))

#           Search if not found it will create if create option is selected
            partner_id = Partner.search([('name', '=ilike', row[1]),('active','=',True),('supplier_rank','=',True)],limit=1)
            if partner_id:
                partner_id=partner_id.id
            else:
                if self.option=='create':
                    partner_id=Partner.create({'name':row[1],'supplier_rank':True,'customer_rank':False,'company_type':'company'}).id
                else:
                    Log.create({'operation':'po','message':'Skipped could not find the partner with name %s'% str(row[1])})
                    continue
#           Search if not found it will create if create option is selected
            currency_id = Currency.search([('name', '=ilike', row[2])],limit=1)
            if currency_id:
                currency_id=currency_id.id
            else:
                if self.option=='create':
                    currency_id=Currency.create({'name':row[2],'symbol':'$'}).id
                else:
                    Log.create({'operation':'po','message':'Skipped could not find the currency with name %s'% str(row[2])})
                    continue

            reference=row[3]

            try:
                date=datetime.strptime(row[4], '%d-%m-%Y').strftime('%Y-%m-%d %H:%M:%S')
            except:
                raise ValidationError(_('Date format must be dd-mm-yyyy.'))
            
            purchase_vals=purchase_default_value.copy()
            purchase_vals.update({
                'name': row[0] if self.seq_opt == 'f_sequence' else 'New',
                'partner_id':partner_id,
                'currency_id':currency_id,
                'date_order':date,
                'partner_ref':reference
            })

#           Search if not found it will create if create option is selected
            if self.import_prod_by == 'barcode':
                product_id=Product.search([('barcode','=',str(row[5])), ('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[9], 'barcode':str(row[5]), 'name':str(row[5]), 'type':'product'}).id
                    else:
                        Log.create({'operation':'po','message':'Skipped could not find the product with code %s'% str(row[5]) })
                        continue
            if self.import_prod_by == 'code':
                product_id=Product.search([('default_code','=ilike',str(row[5])), ('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[9], 'default_code':str(row[5]), 'name':str(row[5]), 'type':'product'}).id
                    else:
                        Log.create({'operation':'po','message':'Skipped could not find the product with code %s'% str(row[5]) })
                        continue
            if self.import_prod_by == 'name':
                product_id=Product.search([('name','=ilike',str(row[5])), ('active','=',True)],limit=1)
                if product_id:
                    product_id=product_id.id
                else:
                    if self.option=='create':
                        product_id=Product.create({'list_price':row[9], 'name':str(row[5]), 'type':'product'}).id
                    else:
                        Log.create({'operation':'po','message':'Skipped could not find the product with name %s'% str(row[5]) })
                        continue





            ####### original
            # product_id=Product.search([('default_code','=',str(int(row[5])) if isinstance(row[5],float) else row[5]),('active','=',True)],limit=1)
            # if product_id:
            #     product_id=product_id.id
            # else:
            #     if self.option=='create':
            #         product_id=Product.create({'list_price':row[9],'default_code':str(int(row[5])) if isinstance(row[5],float) else row[5],'name':str(int(row[5])) if isinstance(row[5],float) else row[5],'type':'product'}).id
            #     else:
            #         Log.create({'operation':'po','message':'Skipped could not find the product with code %s'% (str(int(row[5])) if isinstance(row[5],float) else row[5])})
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
                    Log.create({'operation':'po','message':'Skipped could not find the uom with name %s'% str(row[7])})
                    continue
#           Search if not found it will create if create option is selected
            cust_tax=Tax.search([('name','=',row[10]),('type_tax_use','=','purchase')],limit=1)
            if row[10]:
                if cust_tax:
                    cust_tax=cust_tax.id
                else:
                    if self.option=='create':
                        cust_tax=Tax.create({'name':row[10],'type_tax_use':'purchase','amount':row[10]}).id
                    else:
                        Log.create({'operation':'po','message':'Skipped could not find the tax with name %s'% row[10]})
                        continue
            purchase_line_vals=purchase_line_default_value.copy()
            purchase_line_vals.update({
                'product_id':product_id,
                'name':row[8],
                'date_planned':date,
                'product_qty':row[6],
                'product_uom':uom_id,
                'price_unit':row[9],
                'taxes_id':[(6,0,[cust_tax])],
            })
            
            line=[(0,0,purchase_line_vals)]
#            It will check in deictionay this key is available or not if not it will create otherwise it will update
            if purchase_result.get(row[0]):
                old_line = purchase_result[row[0]]['order_line']
                purchase_result[row[0]].update({'order_line': old_line + line})
            if not purchase_result.get(row[0]):
                purchase_vals.update({'order_line': line})
                purchase_result[row[0]] = purchase_vals
#           Finally on purchase_result dict it will loop and create po
        for purchase in purchase_result.values():
            purchase_id = Purchase.create(purchase)
#            If state is confirm it will confirm the order
            if self.state_stage=='purchase':
                purchase_id.button_confirm()
            
                
class PurchaseOrderLineWizard(models.TransientModel):
    _name = 'purchase.order.line.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")
    import_prod_by = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')], string='Import Product By')
    prod_detail = fields.Selection([('file', 'Take Deatils From The File'), ('product', 'Take Details From Product')], string="Product Details")
    
    def import_order_lines(self):
        print ('\n\n________def import_order_lines___________',self._context)
        Log = self.env['log.management']
        Product = self.env['product.product']
        Uom = self.env['uom.uom']
        Tax=self.env['account.tax']

        purchase_order_line_obj = self.env['purchase.order.line']
        pol_fields = purchase_order_line_obj.fields_get()
        pol_fields_default_values = purchase_order_line_obj.default_get(pol_fields)
        print ('_________pol_fields_default_values____________',pol_fields_default_values)

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
                raise ValidationError(_('Please select proper file type.'))
        else:
            raise ValidationError(_('Please select file type, file, import product by and product details'))
        for row in file_data:
            tax_list = []
            #Product
            if self.import_prod_by == 'barcode':
                product_id=Product.search([('barcode','=',str(row[0])),('active','=',True)],limit=1)
                if product_id:
                    pol_fields_default_values.update({'product_id': product_id.id, 'order_id': self._context.get('active_id')})
                else:
                    Log.create({'operation':'pol','message':'Skipped could not find the product with barcode %s'% str(row[0]) })
                    # continue
            elif self.import_prod_by == 'code':
                product_id=Product.search([('default_code','=ilike',str(row[0])),('active','=',True)],limit=1)
                if product_id:
                    pol_fields_default_values.update({'product_id': product_id.id, 'order_id': self._context.get('active_id')})
                else:
                    Log.create({'operation':'pol','message':'Skipped could not find the product with code %s'% str(row[0]) })
                    # continue
            elif self.import_prod_by == 'name':
                product_id=Product.search([('name','=ilike',str(row[0])),('active','=',True)],limit=1)
                if product_id:
                    pol_fields_default_values.update({'product_id': product_id.id, 'order_id': self._context.get('active_id')})
                else:
                    Log.create({'operation':'pol','message':'Skipped could not find the product with name %s'% str(row[0]) })
                    # continue
            if product_id:
                if self.prod_detail == 'file':
                    #Quantity
                    if isinstance(row[1],float):
                        pol_fields_default_values.update({'product_qty': row[1], 'order_id': self._context.get('active_id')})
                    #Unit of Measure
                    uom_id = Uom.search([('name', 'ilike', row[2])], limit=1)
                    if uom_id:
                        pol_fields_default_values.update({'product_uom': uom_id.id, 'order_id': self._context.get('active_id')})
                    #Description
                    description = str(row[3])
                    if description:
                        pol_fields_default_values.update({'name': description, 'order_id': self._context.get('active_id')})
                    #Price Unit
                    if isinstance(row[4],float):
                        pol_fields_default_values.update({'price_unit': row[4]})
                    #Tax
                    for tax in str(row[5]).split(','):
                        tax_id = Tax.search([('name', '=', tax.strip()),('type_tax_use', '=', 'purchase')],limit=1)
                        if tax_id:
                            tax_list.append(tax_id.id)
                    pol_fields_default_values.update({'taxes_id':[(6,0,tax_list)], 'order_id': self._context.get('active_id')})
                    #Discount
                    # if isinstance(row[6],float):
                    #     discount = row[6]
                    #     pol_fields_default_values.update({'discount': row[6], 'order_id': self._context.get('active_id')})
                    
                    #Scheduled Date
                    scheduled_date = datetime.strptime(row[6], '%d-%m-%Y').strftime('%Y-%m-%d %H:%M:%S')
                    pol_fields_default_values.update({'date_planned': scheduled_date})
                    print ('_________After___________',pol_fields_default_values)
                    purchase_order_line_obj.create(pol_fields_default_values)
                else:
                    pol_fields_default_values.update({
                                                        'price_unit': product_id.standard_price,
                                                        'name': product_id.name,
                                                        'product_qty': row[1] or 1,
                                                        'product_uom': product_id.uom_po_id.id,
                                                        'date_planned': date.today()
                                                        })
                    purchase_order_line_obj.create(pol_fields_default_values)