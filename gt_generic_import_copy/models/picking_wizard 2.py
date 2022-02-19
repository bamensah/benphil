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

from odoo import api, exceptions, fields, models, _
import base64
import xlrd
import io
from odoo.tools import pycompat
from odoo.exceptions import ValidationError
from datetime import datetime




class Picking_wizard(models.TransientModel):
    _name = 'picking.wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")
    seq_opt = fields.Selection([('s_sequence', 'Default Sequence'),('f_sequence', 'Excel/CSV Sequence')], string='Sequence Option')
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validated')], string='Import Stage Option')
    

    def Import_picking_order(self):
        Log = self.env['log.management']
        partner_obj = self.env['res.partner']
        product_obj = self.env['product.product']
        picking_obj = self.env['stock.picking']
        location_obj = self.env['stock.location']
        picking_type_obj = self.env['stock.picking.type']
        picking_obj_fileds = picking_obj.fields_get()
        picking_default_value = picking_obj.default_get(picking_obj_fileds)
        picking_result = {}
        
        if self.select_file and self.data_file and self.option and self.seq_opt and self.state:
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
            if self.select_file == 'csv' and len(row)!=9:
                raise ValidationError("You can let empty cell in csv file or please use xls file.Make sure comma (',') not used when using csv file.")
            
            if not row[0] or not row[1] or not row[2] or not row[3] or not row[4] or not row[7]:
                raise ValidationError(_('Please fill Name,Partner,Source Location,Destination Location,Operation Type and Product they are required fields.'))
            partner = partner_obj.search([('name', '=ilike', row[1])],limit=1)
            if partner:
                partner=partner.id
            else:
                if self.option=='create':
                    partner=partner_obj.create({'name':row[1],'customer':True,'supplier':True,'company_type':'company'}).id
                else:
                    Log.create({'operation':'picking','message':'Skipped could not find the partner with name %s'% str(row[1])})
                    continue
            picking_type=picking_type_obj.search([('name','=ilike',row[4])],limit=1).id
            if not picking_type:
                raise ValidationError(_('Could not find the opertaion type with name %s')% row[4])
            
            sour_location=location_obj.search([('name','=ilike',row[2])],limit=1).id
            if not sour_location:
                raise ValidationError(_('Could not find the source location with name %s')% row[2])
            
            dest_location=location_obj.search([('name','=ilike',row[3])],limit=1).id
            if not dest_location:
                raise ValidationError(_('Could not find the destination location with name %s')% row[3])
            product = product_obj.search([('default_code', '=', row[7])],limit=1)
            if not product:
                if self.option=='create':
                    product=product_obj.create({'name':row[7],'type':'product','default_code':row[7]})
                else:
                    Log.create({'operation':'picking','message':'Skipped could not find the product with code %s'% str(row[7])})
                    continue
            
            try:
                date=datetime.strptime(row[6], '%d-%m-%Y').strftime('%Y-%m-%d %H:%M:%S')
            except:
                raise ValidationError(_('Date format must be dd-mm-yyyy.'))
#            Line Vals
            lines = [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': row[8],
                'name': product.name,
                'location_id':sour_location,
                'location_dest_id':dest_location,
                'picking_type_id':picking_type,
                'product_uom': product.uom_id.id,
                'date_deadline':date
            })]
            
            stock_picking_vals = picking_default_value.copy()
#            Picking Vals
            stock_picking_vals.update({
                'name':row[0] if self.seq_opt=='f_sequence' else '/',
                'partner_id': partner,
                'location_id': sour_location,
                'location_dest_id': dest_location,
                'picking_type_id': picking_type,
                'move_type': 'direct',
                'origin': row[5],
                'scheduled_date': date,
            })

            if picking_result.get(row[0]):
                l1 = picking_result[row[0]]['move_ids_without_package']
                picking_result[row[0]].update({'move_ids_without_package': l1 + lines})
                
            if not picking_result.get(row[0]):
                stock_picking_vals.update({'move_ids_without_package': lines})
                picking_result[row[0]] = stock_picking_vals

        for picking_data in picking_result.values():
            picking_id=picking_obj.create(picking_data)
            if self.state=='validate':
                picking_id.action_confirm()
                picking_id.action_assign()
                for line in picking_id.move_ids_without_package:
                    line.write({'quantity_done':line.product_uom_qty})
                picking_id.button_validate()
        return True