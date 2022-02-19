
import time
from datetime import datetime
from odoo import api, fields, models,_

class LogManagement(models.Model):
    _name = "log.management"
    _order='create_date desc'
    
    operation = fields.Selection([('po','Purchase Order'),('pol','Purchase Order Line'),('payment','Payment'),('so','Sale Order'),('sol','Sale Order Line'),('inv','Invoice'),('invLine','Invoice Line'),('picking','Picking'),('inventory','Inventory'),('bom','BOM'),('journal','Journal'),('bank','Bank Statement')],string="Operation")
    message = fields.Text(string='Message')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)