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



class Bank_account_wizard(models.TransientModel):
    _name = 'bank.wizard'


    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validated')], string='Import Stage Option')
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    

 
    def Import_Bank_AC(self):
        Log = self.env['log.management']
        Partner=self.env['res.partner']
        Journal=self.env['account.journal']
        bank_result={}
        
        Bank=self.env['account.bank.statement']
        bank_fileds = Bank.fields_get()
        bank_default_value = Bank.default_get(bank_fileds)
        bank_vals=bank_default_value.copy()
        
        if self.select_file and self.data_file and self.state and self.option:
            try:
                if self.select_file == 'csv' :
                    csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
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
            if self.select_file == 'csv' and len(row) != 10:
                raise ValidationError("You can not let empty cell in csv file or please use xls file.")
           
            if not row[1] or not row[0] or not row[2] or not row[5] or not row[6]:
                raise ValidationError(_('Name,Journal,Remark,Date and Transaction Date values are required.'))
            
            partner_id=False
            if row[7]:
                partner_id = Partner.search([('name', '=ilike', row[7])],limit=1).id
                if not partner_id:
                    if self.option=='create':
                        partner_id=Partner.create({'name':row[7],'company_type':'company'}).id
                    else:
                        Log.create({'operation':'bank','message':'Skipped could not find the partner with name %s'% str(row[7])})
                        continue
                        
            journal_id=Journal.search([('name','=ilike',row[1])],limit=1).id
            if not journal_id:
                raise ValidationError(_('Could not find the Journal with name %s')%row[1])
            
            try:
                date=datetime.strptime(row[5], '%d-%m-%Y').strftime('%Y-%m-%d')
            except:
                raise ValidationError(_('Date format must be dd-mm-yyyy.'))
            
            bank_line=[(0,0,{
            'date':date,
            'payment_ref':row[6],
            'partner_id':partner_id,
            'ref':row[8],
            'amount':float(row[9]),
            })]
            
            try:
                date=datetime.strptime(row[2], '%d-%m-%Y').strftime('%Y-%m-%d')
            except:
                raise ValidationError(_('Date format must be dd-mm-yyyy.'))
            
            bank_vals.update({
                'name': row[0],
                'journal_id': journal_id,
                'date': date,
                'balance_start': row[3],
                'balance_end_real': row[4],
            })
            
            if bank_result.get(row[0]):
                old_line = bank_result[row[0]]['line_ids']
                bank_result[row[0]].update({'line_ids': old_line + bank_line})

            if not bank_result.get(row[0]):
                bank_vals.update({'line_ids': bank_line})
                bank_result[row[0]] = bank_vals
            
    #    Finally on purchase_result dict it will loop and create po
        for bank_data in bank_result.values():
            bank_id = Bank.create(bank_data)
    #       If state is confirm it will confirm the ord
            if self.state=='validate':
                bank_id.check_confirm_bank()
            print("///////////////",bank_id)
            return True

class Bank_account_line_wizard(models.TransientModel):
    _name = 'bank.line.wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")

    def Import_Bank_Lines(self):
        Log = self.env['log.management']
        Partner=self.env['res.partner']
        Journal=self.env['account.journal']
        bank_result={}
        
        Bank=self.env['account.bank.statement.line']
        # active_ids = self._context.get('active_ids') or self._context.get('active_id')
        bank_stat = self.env['account.bank.statement'].browse(self._context.get('active_ids'))
        bank_fileds = Bank.fields_get()
        bank_default_value = Bank.default_get(bank_fileds)
        bank_vals=bank_default_value.copy()
        
        if self.select_file and self.data_file:
            try:
                if self.select_file == 'csv' :
                    csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
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
            if self.select_file == 'csv' and len(row) != 10:
                raise ValidationError("You can not let empty cell in csv file or please use xls file.")
           
            if not row[1] or not row[0] or not row[2] or not row[5] or not row[6]:
                raise exceptions.Warning(_('Name,Journal,Remark,Date and Transaction Date values are required.'))
            
            partner_id=False
            if row[7]:
                partner_id = Partner.search([('name', '=ilike', row[7])],limit=1).id
                if not partner_id:
                    if self.option=='create':
                        partner_id=Partner.create({'name':row[7],'company_type':'company'}).id
                    else:
                        Log.create({'operation':'bank','message':'Skipped could not find the partner with name %s'% str(row[7])})
                        continue
                        
            journal_id=Journal.search([('name','=ilike',row[1])],limit=1).id
            if not journal_id:
                raise exceptions.Warning(_('Could not find the Journal with name %s')%row[1])
            
            try:
                date=datetime.strptime(row[5], '%d-%m-%Y').strftime('%Y-%m-%d')
            except:
                raise exceptions.Warning(_('Date format must be dd-mm-yyyy.'))
            
            bank_vals.update({
            'date':date,
            'payment_ref':row[6],
            'partner_id':partner_id,
            'ref':row[8],
            'amount':float(row[9]),
            })
            bank_line = bank_stat.write({'line_ids':[(0,0,bank_vals)]})
        return bank_line
          