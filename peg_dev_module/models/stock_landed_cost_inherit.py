# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, tools
from odoo.tools.float_utils import float_round
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LandedCostInherit(models.Model):
    _inherit = "stock.landed.cost"

    adjustment_lines_total = fields.Float('Total', compute='_compute_adjustment_lines_total', digits=0)
    # bill_ids = fields.One2many('stock.landed.cost.bill', 'landed_cost_id', 'Bill References', required=True)#W1E-74 add bill number to landed cost
    invoiced = fields.Boolean(string="Invoiced", readonly=True, compute='_compute_invoiced')#W1E-7-add invoiced field landed cost


#    W1E-7-add invoiced field landed cost
    @api.depends('cost_lines.invoiced')
    def _compute_invoiced(self):
        for record in self:
            record.invoiced = True
            for cost_line in record.cost_lines:
                if not cost_line.invoiced:
                    record.invoiced = False
                    break

    def _compute_adjustment_lines_total(self):
        self.ensure_one()

        total = 0.0
        for line in self.valuation_adjustment_lines:
            total += line.additional_landed_cost

        self.adjustment_lines_total = total

#    W1E-74 add bill number to landed cost
    # @api.model
    # def create(self, vals):
    #     if not vals.get("bill_ids"):#[DT-320]-add return and improve bill ref check
    #         raise UserError('A landed cost must have atleast one bill reference')
    #     return super(LandedCostInherit, self).create(vals)
    
#    @api.multi
#    def compute_landed_cost(self):
#        AdjustementLines = self.env['stock.valuation.adjustment.lines']
#        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

#        digits = dp.get_precision('Product Price')(self._cr)
#        towrite_dict = {}
#        for cost in self.filtered(lambda cost: cost.picking_ids):
#            total_qty = 0.0
#            total_cost = 0.0
#            total_weight = 0.0
#            total_volume = 0.0
#            total_line = 0.0
#            all_val_line_values = cost.get_valuation_lines()
#            for val_line_values in all_val_line_values:
#                for cost_line in cost.cost_lines:
#                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id, 'account_analytic_id': cost_line.account_analytic_id.id}) # add account_analytic_id
#                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
#                total_qty += val_line_values.get('quantity', 0.0)
#                total_weight += val_line_values.get('weight', 0.0)
#                total_volume += val_line_values.get('volume', 0.0)

#                former_cost = val_line_values.get('former_cost', 0.0)
#                # round this because former_cost on the valuation lines is also rounded
#                total_cost += tools.float_round(former_cost, precision_digits=digits[1]) if digits else former_cost

#                total_line += 1

#            for line in cost.cost_lines:
#                value_split = 0.0
#                for valuation in cost.valuation_adjustment_lines:
#                    value = 0.0
#                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
#                        if line.split_method == 'by_quantity' and total_qty:
#                            per_unit = (line.price_unit / total_qty)
#                            value = valuation.quantity * per_unit
#                        elif line.split_method == 'by_weight' and total_weight:
#                            per_unit = (line.price_unit / total_weight)
#                            value = valuation.weight * per_unit
#                        elif line.split_method == 'by_volume' and total_volume:
#                            per_unit = (line.price_unit / total_volume)
#                            value = valuation.volume * per_unit
#                        elif line.split_method == 'equal':
#                            value = (line.price_unit / total_line)
#                        elif line.split_method == 'by_current_cost_price' and total_cost:
#                            per_unit = (line.price_unit / total_cost)
#                            value = valuation.former_cost * per_unit
#                        else:
#                            value = (line.price_unit / total_line)

#                        if digits:
#                            value = tools.float_round(value, precision_digits=digits[1], rounding_method='UP')
#                            fnc = min if line.price_unit > 0 else max
#                            value = fnc(value, line.price_unit - value_split)
#                            value_split += value

#                        if valuation.id not in towrite_dict:
#                            towrite_dict[valuation.id] = value
#                        else:
#                            towrite_dict[valuation.id] += value
#        for key, value in towrite_dict.items():
#            AdjustementLines.browse(key).write({'additional_landed_cost': value})
#        return True
    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
            rounding = cost.currency_id.rounding
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            all_val_line_values = cost.get_valuation_lines()
            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id, 'account_analytic_id': cost_line.account_analytic_id.id}) # add account_analytic_id
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += cost.currency_id.round(former_cost)

                total_line += 1

            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if rounding:
                            value = tools.float_round(value, precision_rounding=rounding, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        for key, value in towrite_dict.items():
            AdjustementLines.browse(key).write({'additional_landed_cost': value})
        return True


#W1E-74 add bill number to landed cost
# class LandedCostBill(models.Model):
#     _name = "stock.landed.cost.bill"

#     bill_reference = fields.Char(required=True, string="Bill Reference")
#     landed_cost_id = fields.Many2one("stock.landed.cost", string="Landed Cost")

#     _sql_constraints = [ 
#         ('unique_landed_cost_bill', 'UNIQUE (bill_reference, landed_cost_id)', 'A bill reference can only be used once on a landed cost'),
#         ('unique_bill_reference', 'UNIQUE (bill_reference)', 'A bill reference cannot be used on more than one landed cost')	
#     ]


class StockLandedCostInherit(models.Model):
    _inherit = "stock.landed.cost.lines"
    
    account_analytic_id = fields.Many2one('account.analytic.account', string="Compte Analytique", required=True)
    invoiced = fields.Boolean(string="Invoiced", readonly=True)
