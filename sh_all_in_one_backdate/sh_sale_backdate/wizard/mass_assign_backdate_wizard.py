#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from datetime import date, datetime

class BackdateWizard(models.TransientModel):

    _name = 'sh.sale.backdate.wizard'
    _description = 'Sale Backdate Wizard'

    sale_order_ids = fields.Many2many('sale.order')
    date_order = fields.Datetime(string='Order Date', required=True,
                                 default=datetime.now())
    company_id = fields.Many2one('res.company', default=lambda self: \
                                 self.env.company)
    remarks = fields.Text(string='Remarks')
    is_remarks = \
        fields.Boolean(related='company_id.remark_for_sale_order',
                       string='Is Remarks')
    is_remarks_mandatory = \
        fields.Boolean(related='company_id.remark_mandatory_for_sale_order'
                       , string='Is remarks mandatory')
    is_boolean = fields.Boolean()

    @api.onchange('date_order')
    def onchange_date_order(self):
        if str(self.date_order.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def open_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')
        self.env[self.env.context.get('active_model'
                                 )].browse(self.env.context.get('active_id'
                ))
        return {
            'name': 'Assign Backdate',
            'res_model': 'sh.sale.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_all_in_one_backdate.sale_order_backdate_wizard_view_form'
                                    ).id,
            'context': {'default_sale_order_ids': [(6, 0,
                        active_ids)]},
            'target': 'new',
            'type': 'ir.actions.act_window',
            }

    def assign_backdate(self):

        for sale_order in self.sale_order_ids:

            if self.company_id.backdate_for_sale_order:
                sale_order.write({'date_order': self.date_order,
                                 'remarks': (self.remarks if self.remarks else ''
                                 )})

            if self.company_id.backdate_for_invoice:
                for invoice in sale_order.invoice_ids:
                    invoice.invoice_date = self.date_order
                    invoice.remarks_for_sale = \
                        (self.remarks if self.remarks else '')

            if self.company_id.backdate_for_stock_move:
                for picking in sale_order.picking_ids:
                    picking.scheduled_date = self.date_order
                    picking.date_done = self.date_order
                    picking.remarks_for_sale = \
                        (self.remarks if self.remarks else '')

                    stock_moves = self.env['stock.move'
                            ].search([('picking_id', '=', picking.id)])
                    account_moves = self.env['account.move'
                            ].search([('stock_move_id', 'in',
                            stock_moves.ids)])

                    for account_move in account_moves:
                        account_move.button_draft()
                        account_move.name = False
                        account_move.date = self.date_order
                        account_move.action_post()

                    for move in stock_moves:
                        move.date = self.date_order
                        move.remarks_for_sale = \
                            (self.remarks if self.remarks else '')
