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

from openerp import fields, models ,api, _
from openerp.exceptions import ValidationError
from odoo import api, exceptions, fields, models, _
import base64
import io
import xlrd
import base64
from odoo.tools import pycompat


class Product_wizard(models.TransientModel):
    _name = 'product.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")

    def Import_product_order(self):
        Partner=self.env['res.partner']
        Product=self.env['product.product']
        Category=self.env['product.category']
        Uom=self.env['uom.uom']
        Tax=self.env['account.tax']
        Uom_categ=self.env['uom.category']
        product_fields=Product.fields_get()
        
#       Fetch default values for the fields
        pro_def_val=Product.default_get(product_fields)
        new_pro_up = pro_def_val.copy()
        file_data = False

        if self.select_file and self.data_file:
            try:
                if self.select_file == 'csv':
                    csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar="," ,delimiter=",")
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
                raise exceptions.Warning(_('Please select proper file type.'))
        else:
            raise exceptions.Warning(_('Please select all the required fields.'))
        
        for row in file_data:
            if self.select_file == 'csv' and len(row) != 21:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            if not row[0] or not row[2] or not row[3] or not row[5] or not row[6]:
                raise ValidationError("Please Assign The Product Name,Type,Uom And Category.")
            
            categ_id=Category.search([('name','=',row[2])],limit=1)
            uom_id=Uom.search([('name','=',row[5])],limit=1)
            purch_uom_id=Uom.search([('name','=',row[6])],limit=1)
            uom_categ_id=Uom_categ.search([('name','=','Unit')],limit=1)
            partner_id=Partner.search([('name','=',row[13])],limit=1)
            cust_tax=Tax.search([('name','=',row[19]),('type_tax_use','=','sale')],limit=1)
            vend_tax=Tax.search([('name','=',row[20]),('type_tax_use','=','purchase')],limit=1)
            
            if row[13]:
                if partner_id:
                    partner_id=partner_id.id
                else:
                    partner_id=Partner.create({'name':row[13],'supplier_rank':True,'customer_rank':False}).id
                new_pro_up.update({'seller_ids' : [(0,0,{'min_qty':1,'name':partner_id,'price':row[8]})]})
                
            if categ_id:
                categ_id=categ_id.id
            else:
                categ_id=Category.create({'name':row[2]}).id
            if uom_id:
                uom_id=uom_id.id
            else:
                uom_id=Uom.create({'name':row[5],'category_id':uom_categ_id.id}).id
            if purch_uom_id:
                purch_uom_id=purch_uom_id.id
            else:
                purch_uom_id=Uom.create({'name':row[6],'category_id':uom_categ_id.id}).id
                
            if row[19]:
                if cust_tax:
                    cust_tax=cust_tax.id
                else:
                    cust_tax=Tax.create({'name':row[19],'type_tax_use':'sale','amount':float(row[19])}).id
                    
            if row[20]:
                if vend_tax:
                    vend_tax=vend_tax.id
                else:
                    vend_tax=Tax.create({'name':row[20],'type_tax_use':'purchase','amount':float(row[20])}).id
            new_pro_up.update({
                    'name':row[0],
                    'default_code': row[1],
                    'type':row[3] if row[3] in ('consu','service','product') else 'product',
                    'list_price': row[7],
                    'standard_price': row[8],
                    'barcode':int(row[4]) if isinstance(row[4],float) else row[4],
                    'categ_id':categ_id,
                    'uom_id' : uom_id,
                    'taxes_id' : [(6,0,[cust_tax])],
                    'supplier_taxes_id' :[(6,0,[vend_tax])],
                    'uom_po_id' : purch_uom_id,
                    'weight':row[9],
                    'volume':row[10],
                    'sale_delay':row[14],
                    'description_pickingout':row[17],
                    'description_pickingin':row[18],
                    'sale_ok':True if row[11] in ('TRUE',1) else False,
                    'purchase_ok':True if row[12] in ('TRUE',1) else False,
                    'description_sale' : row[15],
                    'description_purchase' : row[16],
                })
            p_id=Product.search([('default_code','=',str(int(row[1])) if isinstance(row[1],float) else row[1])],limit=1)
            if p_id:
                p_id.write(new_pro_up)
            else:
                Product.create(new_pro_up)