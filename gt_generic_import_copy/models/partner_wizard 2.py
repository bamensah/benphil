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
#from datetime import  timedelta

import base64
import io
import xlrd
import base64
from odoo.tools import pycompat

class Followers(models.Model):
    _inherit = 'mail.followers'
    
 
    def create(self, vals):
        print('dupsdupwwwwwwwwwwwwwwwwwwwsdupsdupsdupsdupsdups', vals)
        if 'res_model' and 'res_id' and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=',vals.get('res_model')),
                    ('res_id', '=', vals.get('res_id')),
                    ('partner_id', '=', vals.get('partner_id'))])
            print('dupsdupsdupsdupsdupsdupsdups',dups)
            if len(dups):
                for p in dups:
                    p.unlink()
        res = super(Followers, self).create(vals)
        return res

class Partner_wizard(models.TransientModel):
    _name = 'partner.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type')
    data_file = fields.Binary(string="File")


    def Import_partner(self):
        Partner = self.env['res.partner']
        Partner_fields = Partner.fields_get()
        Partner_values = Partner.default_get(Partner_fields)
        User=self.env['res.users']
        Term=self.env['account.payment.term']
        Country=self.env['res.country']
        State=self.env['res.country.state']
        if self.select_file and self.data_file:
            try:
                if self.select_file == 'csv':
                    csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",
                                                          delimiter=",")
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
            if not row[0]:
                raise exceptions.Warning(_('Name value is required.'))
            if self.select_file == 'csv' and len(row) != 21:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            salesperson_id=False
            if row[15]:
                salesperson_id = User.search([('name', '=', row[15])],limit=1)
                if salesperson_id:
                    salesperson_id=salesperson_id.id
                else:
                    salesperson_id=User.create({'name':row[15],'login':row[15].lower()}).id
                    
            cust_payment_term_id=False
            if row[17]:
                cust_payment_term_id = Term.search([('name', '=', row[17])],limit=1)
                if cust_payment_term_id:
                    cust_payment_term_id=cust_payment_term_id.id
                else:
                    cust_payment_term_id=Term.create({'name':row[17]}).id
            
            vendar_payment_term_id=False
            if row[18]:
                vendar_payment_term_id = Term.search([('name', '=', row[18])],limit=1)
                if vendar_payment_term_id:
                    vendar_payment_term_id=vendar_payment_term_id.id
                else:
                    vendar_payment_term_id=Term.create({'name':row[18]}).id
            
            country_id=False
            if row[8]:
                country_id = Country.search([('name', '=ilike', row[8])],limit=1)
                if country_id:
                    country_id=country_id.id
                else:
                    country_id=Country.create({'name':row[8]}).id
            
            state_id=False
            if row[6]:
                state_id = State.search([('name', '=ilike', row[6])],limit=1)
                if state_id:
                    state_id=state_id.id
                else:
                    state_id=State.create({'name':row[6],'code':row[6][:2],'country_id':country_id}).id
            
            Partner_values.update({
            'company_type':'company' if row[1]=='Company' else 'person',
            'street':row[3],
            'street2':row[4],
            'city':row[5],
            'state_id':state_id,
            'zip':int(row[7]) if isinstance(row[7],float) else row[7],
            'country_id':country_id,
            'vat':row[19],
            'function':row[20],
            'phone':int(row[10]) if isinstance(row[10],float) else row[10],
            'mobile':int(row[11]) if isinstance(row[11],float) else row[11],
            'email':row[12],
            'website':row[9],
            'customer_rank':1 if row[13] in ('TRUE',1) else 0,
            'supplier_rank':1 if row[14] in ('TRUE',1) else 0,
            'user_id':salesperson_id,
            'property_payment_term_id':cust_payment_term_id,
            'property_supplier_payment_term_id':vendar_payment_term_id,
            'ref':int(row[16]) if isinstance(row[16],float) else row[16],
            })
    
#           Parent partner
            parent_partner_id=False
            if row[2]:
                parent_partner_id = Partner.search([('name', '=', row[2])],limit=1)
                if parent_partner_id:
                    # parent_partner_id.write(Partner_values)
                    parent_partner_id=parent_partner_id.id
                else:
                    Partner_values.update({'name':row[2]})
                    parent_partner_id=Partner.create(Partner_values).id
            self._cr.commit()
            Partner_values.update({
                'parent_id':parent_partner_id})
#           Main partner
            Partner_values.update({'name':row[0]})
            partner_id = Partner.search([('name', '=', row[0]),('ref', '=', row[16])],limit=1)
            if partner_id:
                partner_id.write(Partner_values)
            else:
                partner_id=Partner.create(Partner_values)
            self._cr.commit()
        return True
