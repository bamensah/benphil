#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date, datetime


class AdjustmentBackdateWizard(models.TransientModel):

    _name = 'sh.adjustment.backdate.wizard'

    stock_inventory_ids = fields.Many2many('stock.inventory')
    date = fields.Datetime(string='Inventory Date', required=True,
                           default=datetime.now())
    company_id = fields.Many2one('res.company', default=lambda self:
                                 self.env.company)
    remarks = fields.Text(string='Remarks')
    is_remarks = \
        fields.Boolean(related='company_id.remark_for_adjustment',
                       string='Is Remarks')
    is_remarks_mandatory = \
        fields.Boolean(related='company_id.remark_mandatory_for_adjustment',
                       string='Is remarks mandatory')
    is_boolean = fields.Boolean()

    def _check_account_installed(self):
        account_app = self.env['ir.module.module'
                               ].sudo().search([('name', '=', 'account'
                                                 )], limit=1)
        if account_app.state != 'installed':
            return False
        else:
            return True

    @api.onchange('date')
    def onchange_date(self):
        if str(self.date.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def open_adjustment_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')
        active_record = self.env[self.env.context.get('active_model'
                                                      )].browse(self.env.context.get('active_id'
                                                                                     ))

        return {
            'name': 'Assign Backdate',
            'res_model': 'sh.adjustment.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_all_in_one_backdate.stock_adjustment_backdate_wizard_view_form'
                                    ).id,
            'context': {'default_stock_inventory_ids': [(6, 0,
                        active_ids)]},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def assign_backdate(self):
        if self.company_id.backdate_for_adjustment:

            for stock_inventory in self.stock_inventory_ids:

                stock_inventory.write({'date': self.date,
                                       'remarks': (self.remarks if self.remarks else ''
                                                   )})

                stock_moves = self.env['stock.move'
                                       ].search([('inventory_id', '=',
                                                  stock_inventory.id)])

                if self._check_account_installed():

                    account_moves = self.env['account.move'
                                             ].search([('stock_move_id', 'in',
                                                        stock_moves.ids)])

                    for account_move in account_moves:
                        account_move.button_draft()
                        account_move.name = False
                        account_move.date = self.date
                        account_move.action_post()

                for move in stock_moves:
                    move.date = self.date
                    move.remarks_for_adjustment = \
                        (self.remarks if self.remarks else '')
