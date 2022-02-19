from odoo import fields, models,_,api
from datetime import date,datetime
from odoo.exceptions import UserError, ValidationError


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    date = fields.Datetime(
        'Inventory Date',
        readonly = False,
        required=True,
        default=fields.Datetime.now,
        help="If the inventory adjustment is not validated, date at which the theoritical quantities have been checked.\n"
             "If the inventory adjustment is validated, date at which the inventory adjustment has been validated.")
    
    remarks = fields.Text(string = "Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_adjustment",string = "Is Remarks")
    is_remarks_mandatory = fields.Boolean(related="company_id.remark_mandatory_for_adjustment",string = "Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date')
    def onchange_date(self):
        if str(self.date.date()) < str(date.today()):
           self.is_boolean = True
        else:
            self.is_boolean = False

    def _action_done(self):
        negative = next((line for line in self.mapped('line_ids') if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_(
                'You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s',
                negative.product_id.display_name,
                negative.product_qty
            ))
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True

    def _action_start(self):
        """ Confirms the Inventory Adjustment and generates its inventory lines
        if its state is draft and don't have already inventory lines (can happen
        with demo data or tests).
        """
        for inventory in self:
            if inventory.state != 'draft':
                continue
            vals = {
                'state': 'confirm',
            }
            if not inventory.line_ids and not inventory.start_empty:
                self.env['stock.inventory.line'].create(inventory._get_inventory_lines_values())
            inventory.write(vals)