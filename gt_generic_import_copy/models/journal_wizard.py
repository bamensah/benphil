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



class Journal_wizard(models.TransientModel):
    _name = 'journal.wizard'


    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validated')], string='Import Stage Option')
    seq_opt = fields.Selection([('f_sequence', 'CSV/EXCEL Sequence'), ('s_sequence', 'System Sequence')],string='Sequence Option')
    option = fields.Selection([('create', 'Create'), ('skip', 'Skip ')], string='Operation')
    

    def Import_journal(self):
        Log = self.env['log.management']
        Move = self.env['account.move']
        Account=self.env['account.account']
        Journal=self.env['account.journal']
        Currency=self.env['res.currency']
        Partner=self.env['res.partner']
        Analytic=self.env['account.analytic.account']
        journal_result={}
        
        move_fileds = Move.fields_get()
        move_default_value = Move.default_get(move_fileds)
        move_vals=move_default_value.copy()
        
        if self.select_file and self.data_file and self.state and self.seq_opt and self.option:
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
            if self.select_file == 'csv' and len(row) != 12:
                raise ValidationError("You can not let empty cell in csv file or please use xls file.")
            if not row[3] or not row[0] or not row[2] or not row[4] or not row[11]:
                raise ValidationError(_('Name,Journal,Reference,Date and Account values are required.'))
            
            partner_id=False
            if row[1]:
                partner_id = Partner.search([('name', '=ilike', row[1])],limit=1).id
                if not partner_id:
                    if self.option=='create':
                        partner_id=Partner.create({'name':row[1],'supplier_rank':True,'customer_rank':True,'company_type':'company'}).id
                    else:
                        Log.create({'operation':'journal','message':'Skipped could not find the partner with name %s'% str(row[1])})
                        continue
                    
            journal_id=Journal.search([('name','=ilike',row[2])],limit=1).id
            if not journal_id:
                raise ValidationError(_('Could not find the Journal with name %s')%row[2])
            
            account_id=Account.search([('code','=',int(row[11]) if isinstance(row[11],float) else row[11])],limit=1).id
            if not account_id:
                raise ValidationError(_('Could not find the Account with name %s')%row[11])
            
            currency_id=False
            if row[10]:
                currency_id = Currency.search([('name', '=ilike', row[10])],limit=1).id
                if not currency_id:
                    raise ValidationError(_('Could not find the Currency with name %s')%row[10])
            
            analytic_id=False
            if row[5]:
                analytic_id = Analytic.search([('name', '=ilike', row[5])],limit=1).id
                if not analytic_id:
                    raise ValidationError(_('Could not find the Analytic Account  with name %s')%row[5])
            
            try:
                date=datetime.strptime(row[4], '%d-%m-%Y').strftime('%Y-%m-%d')
            except:
                raise ValidationError(_('Date format must be dd-mm-yyyy.'))
            
#            Move Vals
            move_vals.update({
                'date':date,
                'journal_id':journal_id,
                'ref':row[3],
                'name':row[0] if self.seq_opt=='f_sequence' else '/',
            })
#            Move line Vals            
            line=[(0,0,
            {
                'name':row[9],
                'account_id': account_id,
                'partner_id': partner_id,
                'analytic_account_id': analytic_id,
                'date': date,
                'currency_id': currency_id,
                'debit': float(row[7]),
                'credit':float(row[8]),
            }
            )]

            if journal_result.get(row[0]):
                old_line = journal_result[row[0]]['line_ids']
                journal_result[row[0]].update({'line_ids': old_line + line})

            if not journal_result.get(row[0]):
                move_vals.update({'line_ids': line})
                journal_result[row[0]] = move_vals
            
    #    Finally on purchase_result dict it will loop and create po
        for move_data in journal_result.values():
            move_id = Move.create(move_data)
    #       If state is confirm it will confirm the ord
            if self.state=='validate':
                move_id.action_post()
