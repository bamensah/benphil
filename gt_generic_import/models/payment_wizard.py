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
from odoo.exceptions import ValidationError
import xlrd
import io
from odoo.tools import pycompat
from datetime import datetime


class Payment_wizard(models.TransientModel):
    _name = 'payment.wizard'
    
    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='State')
    payment_type = fields.Selection([('customer_py', 'Customer Payment'), ('supp_py', 'Supplier Payment')],string='Payment')
    data_file = fields.Binary(string="File")


    def Import_payment(self):
        
        if not self.payment_type or not self.option or not self.select_file or not self.state:
            raise ValidationError(_('Payment,File Type and Operation fields are required.'))
        try:
            if self.select_file == 'csv':
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            else:
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        except:
            raise ValidationError(_('Please select proper file type.'))

        Partner = self.env['res.partner']
        Journal = self.env['account.journal']
        Log = self.env['log.management']

        for row in file_data:
            if not (row[0] or row[2] or row[3]):
                raise ValidationError(_('Partner,Journal,Date values are required.'))
            if len(row)!=5 and self.select_file == 'csv':
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            partner_id = Partner.search([('name', '=ilike', row[0])],limit=1)
            if partner_id:
                partner_id=partner_id.id
            else:
                if self.option=='create':
                    partner_id=Partner.create({'name':row[0],'supplier':True if self.payment_type=='supp_py' else False,'customer':True if self.payment_type=='customer_py' else False}).id
                else:
                    Log.create({'operation':'payment','message':'Skipped could not find the partner with name %s'% str(row[0])})
                    continue
            journal_id = Journal.search([('name', '=ilike', row[2])],limit=1)
            if journal_id:
                journal_id=journal_id.id
            else:
                if self.option=='create':
                    journal_id=Journal.create({'name':row[2],'type':'bank','code':row[2][:2] if len(row[2])>2 else row[2][0:1]}).id
                else:
                    Log.create({'operation':'payment','message':'Skipped could not find the journal with name %s'% str(row[2])})
                    continue
            
            try:
                date=datetime.strptime(row[3], '%d-%m-%Y').strftime('%Y-%m-%d')
            except:
                raise ValidationError(_('Date format must be dd-mm-yyyy.'))

            payment_vals = {
                'partner_type':'customer' if self.payment_type == 'customer_py' else 'supplier',
                'partner_id': partner_id,
                'date': date,
                'journal_id': journal_id,
                'amount': row[1],
                'ref': row[4],
                'payment_method_id': 1 if self.payment_type == 'customer_py' else 2,
                'state': 'draft',
                'payment_type': 'inbound' if self.payment_type == 'customer_py' else 'outbound',
                }
            payment_id = self.env['account.payment'].create(payment_vals)
            if self.state=='posted':
                payment_id.action_post()
