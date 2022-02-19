# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class AccountAssetAssetInherit(models.Model):
    _inherit = "account.asset.asset"
    
    barcode = fields.Char(string='Code Barre')
    site_id = fields.Many2one('optesis.site', string="Site")
    level_id = fields.Many2one('optesis.level', string="Niveau")
    room_id = fields.Many2one('optesis.room', string="Local")
    
    @api.onchange('site_id')
    def onchange_site_id(self):
        self.level_id = False
        return {'domain': {'level_id': [('site_id', '=', self.site_id.id)]}}
    
    @api.onchange('level_id')
    def onchange_level_id(self):
        self.room_id = False
        return {'domain': {'room_id': [('level_id', '=', self.level_id.id)]}}
    
    
    @api.model
    def compute_generated_entries(self, date, asset_type=None):
        # Entries generated : one by grouped category and one by asset from ungrouped category
        created_move_ids = []
        type_domain = []
        if asset_type:
            type_domain = [('type', '=', asset_type)]

        ungrouped_assets = self.env['account.asset.asset'].search(type_domain + [('state', '=', 'open'), ('category_id.group_entries', '=', False)])
        created_move_ids += ungrouped_assets._compute_entries(date, group_entries=False)

        for grouped_category in self.env['account.asset.category'].search(type_domain + [('group_entries', '=', True)]):
            assets = self.env['account.asset.asset'].search([('state', '=', 'open'), ('category_id', '=', grouped_category.id)])
            created_move_ids += assets._compute_entries(date, group_entries=True)
        return created_move_ids
    
    
    
    
class AccountAssetDepreciationLineInherit(models.Model):
    _inherit = "account.asset.depreciation.line"
    
    def _prepare_move_grouped(self):
        asset_id = self[0].asset_id
        category_id = asset_id.category_id  # we can suppose that all lines have the same category
        account_analytic_id = asset_id.account_analytic_id
        analytic_tag_ids = asset_id.analytic_tag_ids
        depreciation_date = self.env.context.get('depreciation_date') or fields.Date.context_today(self)
        amount = 0.0
        line_ids = []
        dic = {}
        for line in self:
            # Sum amount of all depreciation lines
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            company = line.asset_id.company_id
            analytic_id = line.asset_id.account_analytic_id.id
            amount += current_currency._convert(line.amount, company_currency, company, fields.Date.today())
            if analytic_id in dic:
                dic[analytic_id]['debit'] += current_currency._convert(line.amount, company_currency, company, fields.Date.today())
            else:
                dic[analytic_id] = {}
                dic[analytic_id]['name'] = category_id.name + _(' (grouped)')
                dic[analytic_id]['account_id'] = category_id.account_depreciation_expense_id.id, #category_id.account_depreciation_id.id
                dic[analytic_id]['debit'] = current_currency._convert(line.amount, company_currency, company, fields.Date.today())
                dic[analytic_id]['credit'] = 0.0 # current_currency._convert(line.amount, company_currency, company, fields.Date.today())
                dic[analytic_id]['journal_id'] = category_id.journal_id.id
                dic[analytic_id]['analytic_account_id'] = line.asset_id.account_analytic_id.id if category_id.type == 'purchase' else False
                dic[analytic_id]['analytic_tag_ids'] = [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False

        for key, value in dic.items():
            move_line = (0, 0, {
                'name': dic[key]['name'],
                'account_id': dic[key]['account_id'],
                'journal_id': dic[key]['journal_id'],
                'debit': dic[key]['debit'],
                'credit': dic[key]['credit'],
                'analytic_account_id': dic[key]['analytic_account_id'],
                'analytic_tag_ids': dic[key]['analytic_tag_ids'],
            })
            line_ids.append(move_line)
            
        move_line_2 = {
            'name': category_id.name + _(' (grouped)'),
            'account_id': category_id.account_depreciation_id.id, #category_id.account_depreciation_expense_id.id,
            'credit': amount,
            'debit': 0.0, # amount,
            'journal_id': category_id.journal_id.id,
            'analytic_account_id': account_analytic_id.id if category_id.type == 'sale' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'sale' else False,
        }
        line_ids.append((0, 0, move_line_2))
        
        move_vals = {
            'ref': category_id.name,
            'date': depreciation_date or False,
            'journal_id': category_id.journal_id.id,
            'line_ids': line_ids
        }
        
        return move_vals