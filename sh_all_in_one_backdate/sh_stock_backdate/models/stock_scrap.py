from odoo import fields, models,_,api
from datetime import date,datetime
from odoo.exceptions import UserError, ValidationError

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    date_done = fields.Datetime('Date',readonly = False,default = fields.Datetime.now,required=True)

    remarks = fields.Text(string = "Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_scrap",string = "Is Remarks")
    is_remarks_mandatory = fields.Boolean(related="company_id.remark_mandatory_for_scrap",string = "Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_done')
    def onchange_date_done(self):
        if str(self.date_done.date()) < str(date.today()):
           self.is_boolean = True
        else:
            self.is_boolean = False

    def _prepare_move_values(self):
        self.ensure_one()
        return {
            'name': self.name,
            'origin': self.origin or self.picking_id.name or self.name,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'state': 'draft',
            'product_uom_qty': self.scrap_qty,
            'location_id': self.location_id.id,
            'scrapped': True,
            'location_dest_id': self.scrap_location_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                           'product_uom_id': self.product_uom_id.id, 
                                           'qty_done': self.scrap_qty,
                                           'location_id': self.location_id.id,
                                           'location_dest_id': self.scrap_location_id.id,
                                           'package_id': self.package_id.id, 
                                           'owner_id': self.owner_id.id,
                                           'lot_id': self.lot_id.id, })],
#             'restrict_partner_id': self.owner_id.id,
            'picking_id': self.picking_id.id,
            'scrap_id':self.id,
        }

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            scrap.name = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True)._action_done()
            scrap.write({'move_id': move.id, 'state': 'done'})
            # scrap.date_done = fields.Datetime.now()
        return True