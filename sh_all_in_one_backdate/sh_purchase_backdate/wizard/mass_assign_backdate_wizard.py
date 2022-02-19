# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date,datetime

class BackdateWizard(models.TransientModel):
    _name = 'sh.purchase.backdate.wizard'
    _description = "Purchase Backdate Wizard"

    purchase_order_ids = fields.Many2many('purchase.order')
    date_planned = fields.Datetime(string = "Receipt Date",required=True,default = datetime.now())
    company_id = fields.Many2one('res.company',default=lambda self:self.env.company)
    remarks = fields.Text(string = "Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_purchase_order",string = "Is Remarks")
    is_remarks_mandatory = fields.Boolean(related="company_id.remark_mandatory_for_purchase_order",string = "Is remarks mandatory")
    is_boolean = fields.Boolean()
    
    @api.onchange('date_planned')
    def onchange_date_planned(self):
        if self.date_planned:
            if str(self.date_planned.date()) < str(date.today()):
                self.is_boolean = True
            else:
                self.is_boolean = False

    def open_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')
        active_record = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))

        return{
                'name': 'Assign Backdate',
                'res_model': 'sh.purchase.backdate.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('sh_all_in_one_backdate.purchase_order_backdate_wizard_view_form').id,
                'context': {
                    'default_purchase_order_ids': [(6, 0, active_ids)],
                },
                'target': 'new',
                'type': 'ir.actions.act_window'
            }

    def assign_backdate(self):
        
        for purchase_order in self.purchase_order_ids:

            if self.company_id.backdate_for_purchase_order:
                purchase_order.write({
                    'date_planned':self.date_planned,
                    'date_approve':self.date_planned,
                    'remarks':self.remarks if self.remarks else ''
                })

            if self.company_id.backdate_for_bill:
                for bill in purchase_order.invoice_ids:
                    bill.invoice_date = self.date_planned
                    bill.remarks_for_purchase = self.remarks if self.remarks else ''
        
            if self.company_id.backdate_for_stock_move:
                for picking in purchase_order.picking_ids:
                    picking.scheduled_date = self.date_planned
                    picking.date_done = self.date_planned
                    picking.remarks_for_purchase = self.remarks if self.remarks else ''
                
                    stock_moves = self.env['stock.move'].search([('picking_id','=',picking.id)])
                    account_moves = self.env['account.move'].search([('stock_move_id','in',stock_moves.ids)])

                    for account_move in account_moves:
                        account_move.button_draft()
                        account_move.name = False
                        account_move.date = self.date_planned
                        account_move.action_post()

                    for move in stock_moves:
                        move.date = self.date_planned
                        move.remarks_for_purchase = self.remarks if self.remarks else ''