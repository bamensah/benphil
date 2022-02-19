# -*- coding: utf-8 -*-
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from datetime import date,datetime

class PickngBackdateWizard(models.TransientModel):
    _name = 'sh.picking.backdate.wizard'

    stock_picking_ids = fields.Many2many('stock.picking',)
    scheduled_date = fields.Datetime(string = "Scheduled Date",required=True,default = datetime.now())
    company_id = fields.Many2one('res.company',default=lambda self:self.env.company)
    remarks = fields.Text(string = "Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_picking",string = "Is Remarks")
    is_remarks_mandatory = fields.Boolean(related="company_id.remark_mandatory_for_picking",string = "Is remarks mandatory")
    is_boolean = fields.Boolean()

    def _check_account_installed(self):
        account_app = self.env['ir.module.module'].sudo().search([('name','=','account')],limit=1)
        if account_app.state != 'installed':
            return False
        else:
            return True

    @api.onchange('scheduled_date')
    def onchange_scheduled_date(self):
        if str(self.scheduled_date.date()) < str(date.today()):
           self.is_boolean = True
        else:
            self.is_boolean = False

    def open_picking_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')
        active_record = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))

        return{
                'name': 'Assign Backdate',
                'res_model': 'sh.picking.backdate.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('sh_all_in_one_backdate.stock_picking_backdate_wizard_view_form').id,
                'context': {
                    'default_stock_picking_ids': [(6, 0, active_ids)],
                },
                'target': 'new',
                'type': 'ir.actions.act_window'
            }
    
    def assign_backdate(self):
        if self.company_id.backdate_for_picking:
            
            for stock_picking in self.stock_picking_ids:
                
                stock_moves = self.env['stock.move'].search([('picking_id','=',stock_picking.id)])
                
                if self._check_account_installed():

                    account_moves = self.env['account.move'].search([('stock_move_id','in',stock_moves.ids)])
                    
                    for account_move in account_moves:
                        account_move.button_draft()
                        account_move.name = False
                        account_move.date = self.scheduled_date
                        account_move.action_post()

                for move in stock_moves:
                   
                    move.write({
                        'date':self.scheduled_date,
                        'remarks_for_picking' : self.remarks
                    })
                    
                stock_picking.write({
                    'scheduled_date':self.scheduled_date,
                    'remarks':self.remarks if self.remarks else '',
                })
                stock_picking.write({
                    'date_done':self.scheduled_date,
                })