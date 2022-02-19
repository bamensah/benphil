# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
{
    'name' : 'Odoo all import for BOM, Sales, Purchase, Invoice, Inventory, Customer/Supplier Payment, Bank Statement, Journal Entry, Picking, Product, Customer.',
    'version' : '2.3',
    'author' : 'Globalteckz',
    'category' : 'Extra Tools',
    'description' : """
import all in one
all in one import
all in 1 import
import BOM
import sale orders
import sale order
import sales
Import Sales order
import purchase
import purchase order
import invoice
import products
import Inventory
import Payments
import Bank Statement
import statement
import Journal entry
import Picking
import stock
import stock with serial number
import sales order line
import purchase order line
import serial number
import lot
import Customer
import Supplier
excel bom
Import excel bom
xls bom
Import xls bom
csv bom
Import csv bom
excel sales
import excel sales
xls sales
import xls sales
csv sales
import csv sales
excel sales order
import excel sales order
xls sales order
import xls sales order
csv sales order
import csv sales order
excel purchase
import excel purchase
xls purchase
import xls purchase
csv purchase
import csv purchase
excel purchase order
import excel purchase order
xls purchase order
import xls purchase order
csv purchase order
import csv purchase order
excel invoice
import excel invoice
xls invoice
import xls invoice
csv invoice
import csv invoice
excel products
xls products
csv products
import excel products
import xls products
import csv products
excel inventory
xls inventory
csv inventory
import excel inventory
import xls inventory
import csv inventory
excel payments
xls payments
csv payments
import excel payments
import xls payments
import csv payments
excel bank statement
xls bank statement
csv bank statement
import excel bank statement
import xls bank statement
import csv bank statement
excel statement
xls statement
csv statement
import excel statement
import xls statement
import csv statement
excel journal entry
xls journal entry
csv journal entry
import excel journal entry
import xls journal entry
import csv journal entry
excel picking
xls picking
csv picking
import excel picking
import xls picking
import csv picking
excel stock
xls stock
csv stock
import excel stock
import xls stock
import csv stock
excel stock with serial number
xls stock with serial number
csv stock with serial number
import excel stock with serial number
import xls stock with serial number
import csv stock with serial number
excel sales order line
xls sales order line
csv sales order line
import excel sales order line
import xls sales order line
import csv sales order line
excel purchase order line
xls purchase order line
csv purchase order line
import excel purchase order line
import xls purchase order line
import csv purchase order line
excel serial number
xls serial number
csv serial number
import excel serial number
import xls serial number
import csv serial number
excel lot
xls lot
csv lot
import excel lot
import xls lot
import csv lot
excel customer
xls customer
csv customer
import excel customer
import xls customer
import csv customer
excel supplier
xls supplier
csv supplier
import excel supplier
import xls supplier
import csv supplier
import all csv
import so
import po
import account
with different scenario as per your business requirements

""",
    "summary":"Odoo import Data Import All in one import Invoice import Sales import Inventory import Purchase import stock inventory import Picking import Product image import Customer import serial import lot import bank statement import journal entry import payment Advance import App for import Invoices import Sales order import Inventory import Purchase order import stock import Picking import Product image import Customer import serial import lot import bom import bank statement import journal entry import payment",
    'website': 'https://www.globalteckz.com',
    "price": "49.00",
    "currency": "EUR",
    'license': 'Other proprietary',
    'images': ['static/description/Banner.jpg'],
    'depends' : ['sale_management','sale','stock','purchase','base','mrp', 'account', 'l10n_us'],
    'data': [
        'security/ir.model.access.csv',
        'view/invoice_wizard.xml',
        'view/payment_wizard.xml',
        'view/sale_wizard.xml',
        'view/inventory_wizard.xml',
        'view/purchase_wizard.xml',
        'view/picking_wizard.xml',
        'view/product_wizard.xml',
        'view/partner_wizard.xml',
        'view/journal_wizard.xml',
        'view/bank_wizard.xml',
        'view/bom_wizard.xml',
        'view/log_file_view.xml',
        'view/sale_views.xml',
    ],
    'qweb' : [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
