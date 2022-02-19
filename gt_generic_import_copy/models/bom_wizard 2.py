# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it or not/or modify
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

from odoo import api, exceptions, fields, models, _
import base64
import xlrd
import io
from odoo.tools import pycompat
from odoo.exceptions import ValidationError
from datetime import datetime



class Bom_wizard(models.TransientModel):
    _name = 'bom.wizard'


    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    bom_option = fields.Selection([('create', 'Create'), ('update', 'Update')], string='BOM Operation')
    imp_product_by = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')],
                               string='Import Product By')


    def Import_BOM(self):
        Log = self.env['log.management']
        product_teml_obj = self.env['product.template']
        product_obj = self.env['product.product']
        mrp_obj = self.env['mrp.bom']
        Uom = self.env['uom.uom']
        mrp_obj_fileds = mrp_obj.fields_get()
        mrp_default_value = mrp_obj.default_get(mrp_obj_fileds)
        mrp_result = {}
        
        if self.select_file and self.data_file and self.option and self.imp_product_by and self.bom_option:
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
            raise ValidationError(_('Please select all the required fields.'))

        for row in file_data:
            
            if self.select_file == 'csv' and len(row) != 8:
                raise ValidationError("You can not let empty cell in csv file or please use xls file.")
            if not row[0] or not row[1] or not row[2] or not row[4] or not row[5] or not row[7]:
                raise ValidationError(_('Reference,Bom Type,Product,Product Uom,Components,Components Uom are required.'))
#            Search Product Template 
            if self.imp_product_by=='barcode':
                product_teml=product_teml_obj.search([('barcode','=',str(int(row[2])) if isinstance(row[2],float) else row[2]),('active','=',True)],limit=1)
            if self.imp_product_by=='code':
                product_teml=product_teml_obj.search([('default_code','=',str(int(row[2])) if isinstance(row[2],float) else row[2]),('active','=',True)],limit=1)
            if self.imp_product_by=='name':
                product_teml=product_teml_obj.search([('name','=ilike',str(int(row[2])) if isinstance(row[2],float) else row[2]),('active','=',True)],limit=1)
            
            if not product_teml:
                if self.option=='create':
                    product_teml=product_teml_obj.create({'name':str(int(row[2])) if isinstance(row[2],float) else row[2],'type':'product','default_code':str(int(row[2])) if isinstance(row[2],float) else row[2]})
                else:
                    Log.create({'operation':'bom','message':'Skipped could not find the product with name %s'% str(row[2])})
                    continue
#            Search Product Product 
            if self.imp_product_by=='barcode':
                product=product_obj.search([('barcode','=',str(int(row[5])) if isinstance(row[5],float) else row[5]),('active','=',True)],limit=1)
            if self.imp_product_by=='code':
                product=product_obj.search([('default_code','=',str(int(row[5])) if isinstance(row[5],float) else row[5]),('active','=',True)],limit=1)
            if self.imp_product_by=='name':
                product=product_obj.search([('name','=ilike',str(int(row[5])) if isinstance(row[5],float) else row[5]),('active','=',True)],limit=1)
            
            if not product:
                if self.option=='create':
                    product=product_obj.create({'name':str(int(row[5])) if isinstance(row[5],float) else row[5],'type':'product','default_code':str(int(row[5])) if isinstance(row[5],float) else row[5]})
                else:
                    Log.create({'operation':'bom','message':'Skipped could not find the product with name %s'% str(row[5])})
                    continue
            
            uom_id=Uom.search([('name','=ilike',row[4])],limit=1) 
            
            mrp_obj_update = mrp_default_value.copy()
            mrp_obj_update.update({
                'product_tmpl_id': product_teml.id,
                'product_qty': row[3],
                'product_uom_id': uom_id.id if row[4] and uom_id else product_teml.uom_id.id,
                'type':'phantom' if row[1] in ('Kit','KIT') else 'normal',
                'code': row[0],
            })
            
            uom_id=Uom.search([('name','=ilike',row[7])],limit=1) 
            
            l2 = [(0, 0,{
            'product_id':product.id,
            'product_qty':row[6],
            'product_uom_id':uom_id.id if row[7] and uom_id else product.uom_id.id,
            })]
            if mrp_result.get(row[0]):
                l1 = mrp_result[row[0]]['bom_line_ids']
                mrp_result[row[0]].update({'bom_line_ids': l1 + l2})
                
            if not mrp_result.get(row[0]):
                mrp_obj_update.update({'bom_line_ids': l2})
                mrp_result[row[0]] = mrp_obj_update
                
        for mrp_data in mrp_result.values():
            bom_ids=mrp_obj.search([('code','=ilike',mrp_data.get('code'))])
            if bom_ids and self.bom_option=='update':
                for bom in bom_ids:
                    bom.bom_line_ids.unlink()
                    bom.write(mrp_data)
            else:
                mrp_obj.create(mrp_data)
        return True

