# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from collections import Counter
import ast
import requests
import json
import phonenumbers
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


def format_date(date):
    timestamp = ""
    try:
        timestamp = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        timestamp = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d %H:%M:%S')

    return timestamp
class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    # Allow to modify source location during a sale (when quotation is confirmed)
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        readonly=True, required=True,
        states={'draft': [('readonly', False)], 'assigned': [('readonly', False)], 'confirmed': [('readonly', False)]})

    lot_ids_list = fields.Many2many('stock.production.lot',store=True,invisible=True)

    location_dest_id = fields.Many2one('stock.location', "Destination Location",states={'draft': [('readonly', False)]})
    location_type = fields.Selection(related="location_dest_id.usage", string="Location Type")
    partner_id_return = fields.Many2one('res.partner', 'Partner to return stock')
    partner_id = fields.Many2one(
        'res.partner', 'Partner',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirmed': [('readonly', True)], 'assigned': [('readonly', True)]})
    is_repair= fields.Boolean()


    # Leave the location_dest_id field blank when the operation type selected is internal

    # migrate later v14 --------------------------------------
    @api.onchange('picking_type_id')
    def onchange_picking_type(self):
        if self.picking_type_id:
            if self.picking_type_id.default_location_src_id:
                location_id = self.picking_type_id.default_location_src_id.id
            elif self.partner_id:
                location_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

            if self.picking_type_id.default_location_dest_id:
                location_dest_id = self.picking_type_id.default_location_dest_id.id
            #  Disable default Partner location
            # elif self.partner_id:
            #     location_dest_id = self.partner_id.property_stock_customer.id
            else:
                location_dest_id = None

            if self.state == 'draft':
                self.location_id = location_id
                self.location_dest_id = location_dest_id

        # TDE CLEANME move into onchange_partner_id
        if self.partner_id and self.partner_id.picking_warn:
            if self.partner_id.picking_warn == 'no-message' and self.partner_id.parent_id:
                partner = self.partner_id.parent_id
            elif self.partner_id.picking_warn not in (
            'no-message', 'block') and self.partner_id.parent_id.picking_warn == 'block':
                partner = self.partner_id.parent_id
            else:
                partner = self.partner_id
            if partner.picking_warn != 'no-message':
                if partner.picking_warn == 'block':
                    self.partner_id = False
                return {'warning': {
                    'title': ("Warning for %s") % partner.name,
                    'message': partner.picking_warn_msg
                }}

        if self.picking_type_id:
            if self.picking_type_id.code =='internal':
            #Show only internal locations when the type of operation is internal
                self.location_id = location_id
                return {
                    'domain': {'location_id': [('usage', '=', 'internal')],'location_dest_id': [('usage', '=', 'internal')]},
                }
    #
    @api.onchange('location_id')
    def _onchange_unreserve(self):
        msg = 'Please Unreserve the Transfer'
        for picking in self:
            for move_id in picking.move_line_ids_without_package:
                raise UserError(_(msg))
    #
    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.picking_type_id:
            if self.picking_type_id.code=='outgoing':
                if self.location_id:
                    if self.move_line_ids_without_package:
                        for move_line in self.move_line_ids_without_package:
                            move_line.location_id = self.location_id

                    if self.move_ids_without_package:
                        for move in self.move_ids_without_package:
                            move.location_id = self.location_id
                            if move.move_line_ids:
                                move_line_ids = move.move_line_ids
                                for move_line in move_line_ids:
                                    move_line.write({'location_id': self.location_id.id})

    @api.onchange('location_id','state','move_line_ids_without_package','move_ids_without_package','move_lines')
    def onchange_lot_ids_list(self):
        self.lot_ids_list = []
        lots_list=[]
        lots_list_with_customer=[]
        lots_list_sale_stock=[]
        if self.picking_type_id:
            if self.location_id:
                if self.move_line_ids_without_package:
                    for move_line in self.move_line_ids_without_package:
                        move_line.lot_ids = []
                        # Retrieves in stock.quant the products that are in the current location with quantity > 0
                        domain = self.env['stock.quant'].search([('location_id', '=', self.location_id.id), ('product_id', '=', move_line.product_id.id), ('quantity', '>', 0), ('lot_id', '!=', False)])
                        if domain:
                            for product in domain:
                                if product.lot_id.status=='with customer':
                                    lots_list_with_customer.append(product.lot_id.id)
                                elif product.lot_id.status=='sale stock':
                                    lots_list_sale_stock.append(product.lot_id.id)
                            if self.location_id.usage=='customer':
                                lots_list = lots_list_with_customer
                            elif self.location_id.usage=='internal':
                                lots_list = lots_list_sale_stock
                            self.lot_ids_list = lots_list
                            move_line.lot_ids = self.lot_ids_list
                        else:
                            self.lot_ids_list=[]
                            move_line.lot_ids = self.lot_ids_list

    def action_done(self):
        """Changes picking state to done by processing the Stock Moves of the Picking

        Normally that happens when the button "Done" is pressed on a Picking view.
        @return: True
        """
        # Extra line for IT4Life Stock State updates
        if self.move_line_ids_without_package:
            for mvl in self.move_line_ids_without_package:
                if mvl.lot_id:
                    serial_number_delivery = self.env['stock.production.lot'].search(
                    [('name', '=', mvl.lot_id.name)])
                    for serial in serial_number_delivery:
                        if mvl.location_dest_id.usage=='customer':
                            serial.write({
                                'status': 'with customer'})
                        elif mvl.location_id.usage=='customer' and not mvl.move_id.picking_id.is_repair:
                            serial.write({'status': 'returned not tested'})
                            serial_number = serial_number_delivery.name
                            if serial_number:
                                self._deregister_device(serial_number)
                        elif self.picking_type_id.code=='incoming' and mvl.location_dest_id.usage=='internal':
                            serial.write({'status': 'sale stock'})

                        serial.write({
                            'partner_id': self.destination_individual_id.id if self.destination_individual_id and self.location_dest_id.individual_location else None,
                            'sale_order_id': self.sale_id.id if self.sale_id and self.location_dest_id.individual_location and mvl.location_id.usage!='customer' else None
                        })
                if mvl.lot_name:
                    serial_number_returned = self.env['stock.production.lot'].search(
                        [('name', '=', mvl.lot_name)])
                    for serial in serial_number_returned:
                        if mvl.location_id.usage=='customer' and not mvl.move_id.picking_id.is_repair:
                            serial.write({'status': 'returned not tested'})
                            serial_number = serial_number_returned.name
                            if serial_number:
                                self._deregister_device(serial_number)
                        elif mvl.location_dest_id.usage=='customer':
                            serial.write({'status': 'with customer'})
                        elif self.picking_type_id.code=='incoming' and mvl.location_dest_id.usage=='internal':
                            serial.write({'status': 'sale stock'})

                        serial.write({
                            'partner_id': self.destination_individual_id.id if self.destination_individual_id else None,
                            'sale_order_id': self.sale_id.id if self.sale_id and self.location_dest_id.individual_location and mvl.location_id.usage!='customer' else None
                        })

        return True

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        for picking in self:
            picking.action_done()

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()
        return True

    #
    def _deregister_device(self, serial_number):
        """ Call API Gateway to deregister device
            :return
        """
        parameters = self.env['ir.config_parameter'].sudo()
        access_token = parameters.get_param('api_gateway_access_token')
        API_GATEWAY_URL = parameters.get_param('api_gateway_url')
        country = self.company_id.country_id.code.lower()
        API_GATEWAY_PAYGOPS_ENDPOINT = API_GATEWAY_URL + "/api/v1/" + country + "/device/deregister"

        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        data = {
            'device_serial': serial_number,
        }
        req = requests.post(API_GATEWAY_PAYGOPS_ENDPOINT, json=data, headers=headers)

        if req.status_code == 200:
            reponse = req.json()
            if not reponse['answer_data'][0]['success']:
                raise UserError(reponse['answer_data'][0]['status'])
        return

    def _action_generate_backorder_wizard(self, show_transfers=False):
        view = self.env.ref('stock.view_backorder_confirmation')
        is_delivery = True if self.picking_type_id.code == 'outgoing' else False
        return {
            'name': _('Create Backorder?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.backorder.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(self.env.context, outgoing=is_delivery, default_show_transfers=show_transfers, default_pick_ids=[(4, p.id) for p in self]),
        }
    #
    # @api.multi
    def force_picking_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(
            float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids)
        no_reserved_quantities = all(
            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_(
                'You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(
                            _('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            #call process to directly create a backorder
            wiz = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, self.id)]})
            wiz.process()

        self.action_done()
        return


    def button_first_validate(self):
        number_base_unit = 0
        self.state = 'first_done'

        if self.move_line_ids_without_package:
            for mvl in self.move_line_ids_without_package:
                if not mvl.qty_done:
                    mvl.qty_done = mvl.product_uom_qty

                message = None
                if mvl.lot_name or mvl.lot_id:
                    move_lines_to_check = mvl._get_similar_move_lines() - mvl
                    if mvl.lot_name:
                        counter = Counter([line.lot_name for line in move_lines_to_check])
                        if counter.get(mvl.lot_name) and counter[mvl.lot_name] > 1:
                            message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                    elif mvl.lot_id:
                        counter = Counter([line.lot_id.id for line in move_lines_to_check])
                        if counter.get(mvl.lot_id.id) and counter[mvl.lot_id.id] > 1:
                            message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')

                if mvl.base_unit:
                    number_base_unit+=1

                if message:
                    raise exceptions.Warning(message)

            if self.from_sale and self.location_type == 'customer':
                if self.sale_id.payment_term_id.paygops_offer_id != 0 and number_base_unit==0:
                    raise exceptions.Warning(_('There is no base unit to register to customer'))
                elif number_base_unit>1:
                    raise exceptions.Warning(_('You can only have one base unit to register to customer'))

    # @api.multi
    def action_assign(self):
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True
        """
        self.do_unreserve()
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        # If a package level is done when confirmed its location can be different than where it will be reserved.
        # So we remove the move lines created when confirmed to set quantity done to the new reserved ones.
        package_level_done = self.mapped('package_level_ids').filtered(lambda pl: pl.is_done and pl.state == 'confirmed')
        package_level_done.write({'is_done': False})
        moves._action_assign()
        package_level_done.write({'is_done': True})
        return True
#     end =================================================


class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    lot_ids = fields.Many2many('stock.production.lot', store=True, compute='_compute_lot_ids', invisible=True)
    base_unit = fields.Boolean(string="Base unit")

    @api.depends('location_id','product_id')
    def _compute_lot_ids(self):
        for rec in self:
            rec.lot_ids = []
            lots_list=[]
            lots_list_with_customer = []
            lots_list_sale_stock = []
            picking = rec.picking_id
            if rec.location_id:
                domain = self.env['stock.quant'].search([('location_id', '=', rec.location_id.id), ('product_id', 'in', rec.product_id.ids), ('quantity', '>', 0)], limit=1)
                if domain:
                    for product in domain:
                        if product.lot_id.status == 'with customer':
                            lots_list_with_customer.append(product.lot_id.id)
                        elif product.lot_id.status == 'sale stock':
                            lots_list_sale_stock.append(product.lot_id.id)
                    if rec.location_id.usage == 'customer':
                        lots_list = lots_list_with_customer
                    elif rec.location_id.usage == 'internal':
                        lots_list = lots_list_sale_stock
                    rec.lot_ids = lots_list
                else:
                    rec.lot_ids=[]

rec = 0
def autoIncrement():
    global rec
    pStart = 1
    pInterval = 1
    if rec == 0:
        rec = pStart
    else:
        rec += pInterval
    return rec

#  migrate later v14 ------------------------------
# class TraceabilityReport(models.TransientModel):
#     _inherit = 'stock.traceability.report'
#
#     @api.model
#     def _get_move_lines(self, move_lines, line_id=None):
#         # _logger.info("Third def - Get Move Line")
#         lines_seen = move_lines
#         lines_todo = list(move_lines)
#         # _logger.info(lines_todo)
#         while lines_todo:
#             move_line = lines_todo.pop(0)
#             # if MTO
#             if move_line.move_id.move_orig_ids:
#                 lines = move_line.move_id.move_orig_ids.mapped('move_line_ids').filtered(
#                     lambda m: m.lot_id == move_line.lot_id and m.state == 'done'
#                 ) - lines_seen
#             # if MTS
#             elif move_line.location_id.usage == 'internal':
#                 lines = self.env['stock.move.line'].search([
#                     ('product_id', '=', move_line.product_id.id),
#                     ('lot_id', '=', move_line.lot_id.id),
#                     ('location_dest_id', '=', move_line.location_id.id),
#                     ('id', 'not in', lines_seen.ids),
#                     ('date', '<=', move_line.date),
#                     ('state', '=', 'done'),
#                     ('move_id.company_id', '=', self.env.user.company_id.id),
#                 ])
#             else:
#                 continue
#             if line_id is None or line_id in lines.ids:
#                 lines_todo += list(lines)
#             lines_seen |= lines
#         return lines_seen - move_lines
#
#     # Retrieves the last partner that was allocated stock
#     @api.model
#     def _get_previous_partner(self, move_line):
#         previous_partner_id = ''
#
#         lot_picking_ids= {}
#         picking_dates_done=[]
#         dates_to_compare=[]
#         picking_id = move_line.picking_id or move_line.move_id.picking_id
#         if picking_id and picking_id.picking_type_id.code!='incoming':
#             if (move_line.lot_id):
#                 domain = self.env['stock.move.line'].search([('lot_id', '=', move_line.lot_id.id),('id', '!=', move_line.id), ('move_id.company_id', '=', self.env.user.company_id.id)],order='date asc')
#                 if domain:
#                     for mv_line in domain:
#                         # Retrieves all the pickings related to the lot_id with the done dates
#                         if mv_line.picking_id:
#                             lot_picking_ids[mv_line.picking_id] = mv_line.picking_id.date_done
#                         elif mv_line.move_id.repair_id:
#                             lot_picking_ids[mv_line.move_id.repair_id] = mv_line.date
#                     if len(lot_picking_ids) >=1:
#                         picking_dates_done = list(lot_picking_ids.values())
#                         if len(picking_dates_done) > 0 and picking_id.date_done:
#                             for dt in picking_dates_done:
#                                 if dt!=False and dt<= picking_id.date_done:
#                                     dates_to_compare.append(dt)
#                             if len(dates_to_compare)>0:
#                                 # Get the previous current picking
#                                 previous_date = max(dates_to_compare)
#                                 previous_picking_id = list(lot_picking_ids.keys())[list(lot_picking_ids.values()).index(previous_date)]
#                                 if previous_picking_id and previous_picking_id._name=='stock.picking' and previous_picking_id.location_id.usage != 'supplier':
#                                     if previous_picking_id.partner_id_return:
#                                         previous_partner_id = previous_picking_id.partner_id_return.name
#                                     else:
#                                         if previous_picking_id.location_id.usage!='customer':
#                                             previous_partner_id = previous_picking_id.partner_id.name
#                                 elif previous_picking_id and previous_picking_id._name=='repair.order':
#                                     previous_partner_id = previous_picking_id.partner_id.name
#
#         return previous_partner_id
#
#     # Retrieves the partner dest
#     @api.model
#     def _get_partner_id_dest(self, move_line):
#         partner_id_dest = ''
#
#         if move_line.picking_id and move_line.picking_id.location_id.usage != 'supplier':
#             if move_line.picking_id.location_id.usage != 'customer':
#                 partner_id_dest=move_line.picking_id.partner_id.name
#             else:
#                 if move_line.picking_id.partner_id_return:
#                     partner_id_dest=move_line.picking_id.partner_id_return.name
#                 else:
#                     partner_id_dest=''
#         elif move_line.move_id.repair_id and move_line.move_id.location_dest_id.usage=='customer':
#             repair_id = move_line.move_id.repair_id
#             partner_id_dest = repair_id.partner_id.name
#         else:
#             partner_id_dest = ''
#
#         return partner_id_dest
#
#     @api.model
#     def _lines(self, line_id=None, model_id=False, model=False, level=0, move_lines=[], **kw):
#         final_vals = []
#         lines = move_lines or []
#         if model and line_id:
#             move_line = self.env[model].browse(model_id)
#             move_lines, is_used = self._get_linked_move_lines(move_line)
#             if move_lines:
#                 lines = move_lines
#             else:
#                 # Traceability in case of consumed in.
#                 lines = self._get_move_lines(move_line, line_id=line_id)
#         for line in lines:
#             unfoldable = False
#             if line.consume_line_ids or ( line.lot_id and self._get_move_lines(line) and model != "stock.production.lot"):
#                 unfoldable = True
#             final_vals += self._make_dict_move(level, parent_id=line_id, move_line=line, unfoldable=unfoldable)
#         return final_vals
#
#     @api.model
#     def get_lines(self, line_id=None, **kw):
#         context = dict(self.env.context)
#         model = kw and kw['model_name'] or context.get('model')
#         rec_id = kw and kw['model_id'] or context.get('active_id')
#         level = kw and kw['level'] or 1
#         lines = self.env['stock.move.line']
#         move_line = self.env['stock.move.line']
#         if rec_id and model == 'stock.production.lot':
#             lines = move_line.search([
#                 ('lot_id', '=', context.get('lot_name') or rec_id),
#                 ('state', '=', 'done'),
#                 ('move_id.company_id', '=', self.env.user.company_id.id),
#             ])
#         elif  rec_id and model == 'stock.move.line' and context.get('lot_name'):
#             record = self.env[model].browse(rec_id)
#             dummy, is_used = self._get_linked_move_lines(record)
#             if is_used:
#                 lines = is_used
#         elif rec_id and model in ('stock.picking', 'mrp.production'):
#             record = self.env[model].browse(rec_id)
#             if model == 'stock.picking':
#                 lines = record.move_lines.mapped('move_line_ids').filtered(lambda m: m.lot_id and m.state == 'done')
#             else:
#                 lines = record.move_finished_ids.mapped('move_line_ids').filtered(lambda m: m.state == 'done')
#         move_line_vals = self._lines(line_id, model_id=rec_id, model=model, level=level, move_lines=lines)
#         final_vals = sorted(move_line_vals, key=lambda v: v['date'], reverse=False)
#         lines = self._final_vals_to_lines(final_vals, level)
#         return lines
#
#     def _get_html(self):
#         result = {}
#         rcontext = {}
#         context = dict(self.env.context)
#         rcontext['lines'] = self.with_context(context).get_lines()
#         result['html'] = self.env.ref('stock.report_stock_inventory').render(rcontext)
#         return result
#
#     @api.model
#     def get_html(self, given_context=None):
#         res = self.search([('create_uid', '=', self.env.uid)], limit=1)
#         if not res:
#             return self.create({}).with_context(given_context)._get_html()
#         return res.with_context(given_context)._get_html()
#
#     def _make_dict_move(self, level, parent_id, move_line, unfoldable=False):
#         partner_column = self.env['sale.order']
#         res_model, res_id, ref = self._get_reference(move_line)
#         dummy, is_used = self._get_linked_move_lines(move_line)
#         previous_partner_id = self._get_previous_partner(move_line) if move_line.picking_id.picking_type_id.code != 'incoming' else move_line.picking_id.partner_id.name
#         #partner_id_dest = move_line.picking_id.partner_id.name if move_line.picking_id.picking_type_id.code != 'incoming' else ''
#         partner_id_dest = self._get_partner_id_dest(move_line)
#         #date = move_line.picking_id.date_done if move_line.picking_id.date_done else move_line.move_id.date
#         done_date = self._find_done_date(move_line)
#         date = done_date if done_date else move_line.picking_id.date_done
#         date = date if date else move_line.date
#         data = [{
#             'level': level,
#             'unfoldable': unfoldable,
#             'date': date,
#             'parent_id': parent_id,
#             'is_used': bool(is_used),
#             'usage': self._get_usage(move_line),
#             'model_id': move_line.id,
#             'model': 'stock.move.line',
#             'product_id': move_line.product_id.name,
#             'product_qty_uom': "%s %s" % (
#                 self._quantity_to_str(move_line.product_uom_id, move_line.product_id.uom_id, move_line.qty_done),
#                 move_line.product_id.uom_id.name),
#             'lot_name': move_line.lot_id.name,
#             'lot_id': move_line.lot_id.id,
#             'location_source': move_line.location_id.name,
#             'partner_id_from': previous_partner_id,
#             'partner_id_dest': partner_id_dest,
#             'location_destination': move_line.location_dest_id.name,
#             'reference_id': ref,
#             'res_id': res_id,
#             'res_model': res_model}]
#         return data
#
#     @api.model
#     def _final_vals_to_lines(self, final_vals, level):
#         lines = []
#         for data in final_vals:
#             lines.append({
#                 'id': autoIncrement(),
#                 'model': data['model'],
#                 'model_id': data['model_id'],
#                 'parent_id': data['parent_id'],
#                 'usage': data.get('usage', False),
#                 'is_used': data.get('is_used', False),
#                 'lot_name': data.get('lot_name', False),
#                 'lot_id': data.get('lot_id', False),
#                 'reference': data.get('reference_id', False),
#                 'res_id': data.get('res_id', False),
#                 'res_model': data.get('res_model', False),
#                 'columns': [data.get('reference_id', False),
#                             data.get('product_id', False),
#                             data.get('date', False),
#                             data.get('lot_name', False),
#                             data.get('location_source', False),
#                             data.get('partner_id_from', False),
#                             data.get('location_destination', False),
#                             data.get('partner_id_dest', False),
#                             data.get('product_qty_uom', 0)],
#                 'level': level,
#                 'unfoldable': data['unfoldable'],
#             })
#         return lines
#
#     def _find_done_date(self, move_line):
#         date_done = None
#         picking = move_line.picking_id
#         notes = self.env['mail.message'].sudo().search([('subtype_id', '=', self.env.ref("mail.mt_note").id),
#         ('res_id', '=', picking.id),('model', '=', 'stock.picking')], order='date desc')
#
#         for note in notes:
#             tracking_value = self.env['mail.tracking.value'].sudo().search(['&', '&', ('mail_message_id', '=', note.id),
#             ('field', '=', 'state'),'|', ('new_value_char', '=', 'Done'), ('new_value_char', '=', 'Fait')], limit = 1)
#             if tracking_value:
#                 date_done = note.date
#                 break
#
#         return date_done
#
# end --------------------------

class ReturnPartnerPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    partner_id = fields.Many2one('res.partner', 'Partner to return', index=True)

    source_individual_id = fields.Many2one(string='Source Individual', comodel_name='res.partner')
    source_location_individual = fields.Boolean()
    destination_individual_id = fields.Many2one(string='Destination Individual', comodel_name='res.partner')
    destination_location_individual = fields.Boolean()

    # migrate later v14 -----------------------
    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError(_("You may only return one picking at a time."))
        res = super(ReturnPartnerPicking, self).default_get(fields)

        move_dest_exists = False
        product_return_moves = []
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking:
            res.update({'picking_id': picking.id})
            if picking.state != 'done':
                raise UserError(_("You may only return Done pickings."))
            for move in picking.move_lines:
                if move.scrapped:
                    continue
                if move.move_dest_ids:
                    move_dest_exists = True
                quantity = move.product_qty - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).mapped('move_line_ids').mapped('product_qty'))
                quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                #Singleton error: Select the first item when 'move_line_ids' contains many items
                product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id, 'lot_id': move.move_line_ids[0].lot_id.id}))

            if not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': product_return_moves})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': move_dest_exists})
            if 'parent_location_id' in fields and picking.location_id.usage == 'internal':
                res.update({'parent_location_id': picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': picking.location_id.id})
            if 'location_id' in fields:
                location_id = picking.location_id.id
                if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
                res['location_id'] = location_id
        return res
    #
    def _prepare_move_default_values(self, return_line, new_picking):
        print('return_line, new_picking', return_line, new_picking)
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
            'lot_ids': [(6, 0, return_line.lot_ids.ids)],
        }
        return vals

    def _create_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s", self.picking_id.name),
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id,
            'partner_id_return': self.partner_id.id,
            'destination_individual_id': self.picking_id.source_individual_id.id if self.picking_id.source_individual_id else None,
            'source_individual_id': self.picking_id.destination_individual_id.id if self.picking_id.destination_individual_id else None
            })
        new_picking.write({
            'destination_individual_id': self.picking_id.source_individual_id.id if self.picking_id.source_individual_id else None,
            'source_individual_id': self.picking_id.destination_individual_id.id if self.picking_id.destination_individual_id else None
        })
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)
                r = return_line.move_id.copy(vals)
                vals = {}

                # +--------------------------------------------------------------------------------------------------------+
                # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                # |              | returned_move_ids              ↑                                  | returned_move_ids
                # |              ↓                                | return_line.move_id              ↓
                # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                # +--------------------------------------------------------------------------------------------------------+
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

    # method v12 method
    # def _create_returns(self):
    #     # TODO sle: the unreserve of the next moves could be less brutal
    #     for return_move in self.product_return_moves.mapped('move_id'):
    #         return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()
    #
    #     # create new picking for returned products
    #     picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
    #     new_picking = self.picking_id.copy({
    #         'move_lines': [],
    #         'picking_type_id': picking_type_id,
    #         'state': 'draft',
    #         'origin': _("Return of %s") % self.picking_id.name,
    #         'location_id': self.picking_id.location_dest_id.id,
    #         'location_dest_id': self.location_id.id,
    #         'partner_id_return': self.partner_id.id})
    #         #'partner_id': self.partner_id.id})
    #     new_picking.message_post_with_view('mail.message_origin_link',
    #         values={'self': new_picking, 'origin': self.picking_id},
    #         subtype_id=self.env.ref('mail.mt_note').id)
    #     returned_lines = 0
    #     for return_line in self.product_return_moves:
    #         if not return_line.move_id:
    #             raise UserError(_("You have manually created product lines, please delete them to proceed."))
    #         # TODO sle: float_is_zero?
    #         if return_line.quantity:
    #             returned_lines += 1
    #             vals = self._prepare_move_default_values(return_line, new_picking)
    #             r = return_line.move_id.copy(vals)
    #             vals = {}
    #
    #             # +--------------------------------------------------------------------------------------------------------+
    #             # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
    #             # |              | returned_move_ids              ↑                                  | returned_move_ids
    #             # |              ↓                                | return_line.move_id              ↓
    #             # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
    #             # +--------------------------------------------------------------------------------------------------------+
    #             move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
    #             move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
    #             vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
    #             vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
    #             r.write(vals)
    #     if not returned_lines:
    #         raise UserError(_("Please specify at least one non-zero quantity."))
    #
    #     new_picking.action_confirm()
    #     new_picking.action_assign()
    #     return new_picking.id, picking_type_id
# end -------------------------------------

class ReturnPartnerPickingInherit(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    lot_id = fields.Many2one('stock.production.lot', string='Lot')
    lot_ids = fields.Many2many('stock.production.lot')

# 52_Swap_Process: Display customer location by default in destination location

# migrate later v14 ----------------------------------
class RepairLine(models.Model):
    _inherit = 'repair.line'
#
    @api.onchange('product_id')
    def default_so_acc(self):
        if self.product_id and self.repair_id.sale_order:
        # Search sale.order.line for matching sale_order, product to get analytic account
            sale_order = self.repair_id.sale_order
            sale_order_line = self.env['sale.order.line'].search([('order_id', '=', sale_order.id), ('product_id', '=', self.product_id.id)], limit=1)
            if any(sale_order_line):
                self.analytic_account_id = sale_order_line[0].account_analytic

#
#
    analytic_account_id = fields.Many2one(string='Analytic Account', comodel_name='account.analytic.account')
#
    def _get_first_value(self):
        return self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
#
#
    @api.onchange('type', 'repair_id')
    def onchange_operation_type(self):
        """ On change of operation type it sets source location, destination location
        and to invoice field.
        @param product: Changed operation type.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values.
        """
        if not self.type:
            self.location_dest_id = self._get_first_value()
            #default value: destination location in repair order
            self.location_id = self.repair_id.location_dest_id.id
        elif self.type == 'add':
            self.onchange_product_id()
            self.location_dest_id = self._get_first_value()
            #default value: destination location in repair order
            self.location_id = self.repair_id.location_dest_id.id
        else:
            self.price_unit = 0.0
            self.tax_id = False
            self.location_dest_id = self._get_first_value()
            #default value: destination location in repair order
            self.location_id = self.repair_id.location_dest_id.id
#  end ------------------

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    is_used_in_repairs = fields.Boolean('Used in Repairs')

class ProductStatus(models.Model):
    _inherit = 'stock.production.lot'

    status = fields.Selection([
        ('sale stock', 'Sales Stock'),
        ('with customer', 'With Customer'),
        ('broken discard', 'Broken, Discard'),
        ('warranty stock', 'Warranty Stock'),
        ('suspended', 'Suspended'),
        ('returned not tested', 'Returned, not Tested'),
        ('in transit', 'In Transit'),
        ('defective part', 'Defective part'),
        ('2nd warranty stock', '2nd Warranty Stock'),
        ('2nd hand full kit for sale', '2nd Hand Full Kit For Sale'),
    ], string='Stock State', store=True)

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner'
    )
    
    sale_order_id = fields.Many2one(
        string='Sale Order',
        comodel_name='sale.order'
    )
    
# Update Stock Status
class ProductStatusRepair(models.Model):
    _inherit = 'repair.order'

    # migrate later v14 ----------------
    # @api.model
    # def _default_stock_location(self):
    #     """Choose the partner location customer by default"""
    #     return super(ProductStatusRepair, self)._default_stock_location()
    #  end -------------------------

    token = fields.Boolean('Requires a new token')
    sale_order= fields.Many2one('sale.order', string='Sale Order-Origin')
    sale_order_ids_list = fields.Many2many('sale.order',store=True,invisible=True)
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        index=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]}) #default=_default_stock_location,

    picking_type_id = fields.Many2one('stock.picking.type', "Operation type",
        index=True, readonly=True, required=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})

    # migrate later v14 -----------------------
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.sale_order_ids_list = []
        sale_order_list=[]
        domain = self.env['sale.order'].search([('partner_id', '=', self.partner_id.id)])
        if domain:
            for sale_order in domain:
                sale_order_list.append(sale_order.id)
            self.sale_order_ids_list = sale_order_list
    #
    @api.model
    def default_get(self,default_fields):

        res = super(ProductStatusRepair, self).default_get(default_fields)
        res['location_id'] = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1).id
        return res
    #
    def action_repair_confirm(self):
        analytic_account = None
        # Compute analytic account
        sale_order_line = self.env['sale.order.line'].search([('order_id', '=', self.sale_order.id), ('product_id', '=', self.product_id.id)], limit=1)
        if any(sale_order_line):
            analytic_account = sale_order_line[0].account_analytic
        picking = self.env['stock.picking'].create({
            'is_repair': True,
            'partner_id': self.partner_id.id,
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'qty_model': self.product_qty,
            'origin': self.name,
            'move_ids_without_package': [(0, 0, {
                'name': self.name,
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'product_uom_qty': self.product_qty,
                'analytic_account_id': analytic_account.id if analytic_account else None
            })]
        })

        picking.sale_id = self.sale_order.id

        #Mark as Todo
        picking.action_confirm()
        #Check Availability
        picking.action_assign()
        #Set serial number to item before first validate
        if picking and picking.move_line_ids_without_package:
            picking.move_ids_without_package[0].move_line_ids[0].lot_id = self.lot_id
        #First Validation
        picking.button_first_validate()
        #Validate
        picking.button_validate()
        #Mark item returned
        self.lot_id.write({'status': 'returned not tested'})
        self.env.cr.commit()

        return super(ProductStatusRepair, self).action_repair_confirm()
    #
    # @api.multi
    def action_repair_end(self):
        """ Writes repair order state to 'To be invoiced' if invoice method is
        After repair else state is set to 'Ready'.
        @return: True
        """
        if self.filtered(lambda repair: repair.state != 'under_repair'):
            raise UserError(_("Repair must be under repair in order to end reparation."))

        serial_number_end_repair = self.env['stock.production.lot'].search(
            [('name', '=', self.operations.lot_id.name)])
        for number in serial_number_end_repair:
            number.write({'status': 'with customer'})
            if self.token:
                if self.sale_order:
                    self.swap_device(number.name, self.lot_id.name, self.sale_order)
                else:
                    raise exceptions.Warning(_('Please specify the sale order related to this swap'))

        for repair in self:
            repair.write({'repaired': True})
            vals = {'state': 'done'}
            vals['move_id'] = repair.action_repair_done().get(repair.id)
            if not repair.invoiced and repair.invoice_method == 'after_repair':
                vals['state'] = '2binvoiced'
            repair.write(vals)
        return True
    #
    # @api.multi
    def action_repair_done(self):
        """ Creates stock move for operation and stock move for final product of repair order.
        @return: Move ids of final products

        """
        if self.filtered(lambda repair: not repair.repaired):
            raise UserError(_("Repair must be repaired in order to make the product moves."))
        self._check_company()
        self.operations._check_company()
        self.fees_lines._check_company()
        res = {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        Move = self.env['stock.move']
        for repair in self:
            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id, repair.lot_id, owner_id=repair.partner_id, strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id

            moves = self.env['stock.move']
            for operation in repair.operations:
                move = Move.create({
                    'name': repair.name,
                    'product_id': operation.product_id.id,
                    'product_uom_qty': operation.product_uom_qty,
                    'product_uom': operation.product_uom.id,
                    'partner_id': repair.address_id.id,
                    'location_id': operation.location_id.id,
                    'location_dest_id': operation.location_dest_id.id,
                    'repair_id': repair.id,
                    'origin': repair.name,
                    'company_id': repair.company_id.id,
                    'analytic_account_id' : operation.analytic_account_id.id,
                })
                
                # Best effort to reserve the product in a (sub)-location where it is available
                product_qty = move.product_uom._compute_quantity(
                    operation.product_uom_qty, move.product_id.uom_id, rounding_method='HALF-UP')
                available_quantity = self.env['stock.quant']._get_available_quantity(
                    move.product_id,
                    move.location_id,
                    lot_id=operation.lot_id,
                    strict=False,
                )
                move._update_reserved_quantity(
                    product_qty,
                    available_quantity,
                    move.location_id,
                    lot_id=operation.lot_id,
                    strict=False,
                )
                # Then, set the quantity done. If the required quantity was not reserved, negative
                # quant is created in operation.location_id.
                move._set_quantity_done(operation.product_uom_qty)

                if operation.lot_id:
                    move.move_line_ids.lot_id = operation.lot_id

                moves |= move
                operation.write({'move_id': move.id, 'state': 'done'})
                # Record Serialized stock state
                operation.lot_id.write({
                    'partner_id': repair.partner_id.id if repair.partner_id else None,
                    'sale_order_id': repair.sale_order.id if repair.sale_order else None
                })
            move = Move.create({
                'name': repair.name,
                'product_id': repair.product_id.id,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'product_uom_qty': repair.product_qty,
                'partner_id': repair.address_id.id,
                'location_id': repair.location_id.id,
                'location_dest_id': repair.location_id.id,
                'move_line_ids': [(0, 0, {'product_id': repair.product_id.id,
                                           'lot_id': repair.lot_id.id,
                                           'product_uom_qty': 0,  # bypass reservation here
                                           'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                                           'qty_done': repair.product_qty,
                                           'package_id': False,
                                           'result_package_id': False,
                                           'owner_id': owner_id,
                                           'company_id': repair.company_id.id,
                                           'location_id': repair.location_id.id, #TODO: owner stuff
                                           'location_dest_id': repair.location_id.id,})],
                'repair_id': repair.id,
                'origin': repair.name,
                'company_id': repair.company_id.id,
                'analytic_account_id' : operation.analytic_account_id.id
            })
            consumed_lines = moves.mapped('move_line_ids')
            produced_lines = move.move_line_ids
            moves |= move
            
            # Update the affected accounts
            # journal_entry = self.env['account.move'].sudo().search([('stock_move_id', 'in', moves.ids)])
            # if any(journal_entry):
            #     journal_items = journal_entry[0].line_ids
            #     journal_entry.sudo().write({
            #         'ref': repair.name,
            #         'partner_id': repair.partner_id.id
            #     })
            #     journal_items.sudo().write({
            #         'partner_id': repair.partner_id.id
            #     })
            # ###
            
            moves._action_done()
            produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
            res[repair.id] = move.id
            
        return res
    #
    # @api.multi
    def swap_device(self, new_device_serial, old_device_serial, sale_order):

        params = self.env['ir.config_parameter'].sudo()
        API_GATEWAY_URL = params.get_param('api_gateway_url')
        API_GATEWAY_TOKEN = params.get_param('api_gateway_access_token')
        HEADERS = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_GATEWAY_TOKEN,
        }

        URL = API_GATEWAY_URL + "/api/v1/" + self.get_country() + "/swap_device"
        data = {"new_device_serial": new_device_serial, "old_device_serial": old_device_serial}
        resp = requests.post(URL, data=json.dumps(data), headers=HEADERS)
        response = resp.json()

        response_code = resp.status_code
        #TODO REPLACE BY TRY CATCH
        if str(response_code) == '200' or str(response_code)=='201':
            if 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            elif 'answer_data' in response:
                if len(response["answer_data"]) > 1:
                    if 'activation_answer_code' in response["answer_data"][1]:
                        duration = 0
                        token_code = response["answer_data"][1]["activation_answer_code"]
                        credit_end_date = response["answer_data"][1]["expiration_time_year"] + '-' + response["answer_data"][1]["expiration_time_month"] + '-' + response["answer_data"][1]["expiration_time_day"]
                        token_id = response["uuid"]
                        if 'free_time' in response["answer_data"][1]:
                            duration = response["answer_data"][1]["free_time"]
                        generated_date=response["time"]
                        token_type = response["type"]
                        client_id= response["client"]
                        registration_answer_code_new = response["answer_data"][0]["registration_answer_code_new"]
                        registration_answer_code_old = response["answer_data"][0]["registration_answer_code_old"]
                        device_id = self.env['stock.production.lot'].search([('name', '=', new_device_serial)],limit=1)

                        #Retrieve last token sent to get the phone number
                        token_old = self.env['credit.token'].search([('loan_id', '=', sale_order.id),('phone_number', '!=', False)],order='create_date desc',limit=1)

                        token = self.env['credit.token'].create({'code': token_code, 'token_id': token_id, 'duration': duration, 'token_type': token_type, 'credit_end_date': datetime.strptime(credit_end_date, '%Y-%m-%d'), 'generated_date': format_date(generated_date),
                            'inventory_id': device_id.id,'partner_id': self.partner_id.id, 'amount': 0.0, 'device_serial': new_device_serial,
                            'salesperson': sale_order.user_id.id, 'loan_id': sale_order.id, 'phone_number': token_old.phone_number if token_old and token_old.phone_number else '', 'phone_number_partner':self.partner_id.phone})
                        paygops_id = self.env['peg.africa.paygops'].search([('id', '=', sale_order.paygops_id.id)])
                        paygops_id.update({'device_id': new_device_serial, 'old_device_id': old_device_serial,'client_id':client_id, 'registration_answer_code':registration_answer_code_new})
                        sale_order.calculate_status()

                else:
                    message_no_activation=''
                    if response["answer_data"][0]["status"] == 'NO_ACTIVATION_TIME_ON_DEVICE':
                        message_no_activation = ' Please register a payment for this client and the corresponding sale order to activate the device and generate a token.'
                    raise exceptions.Warning(_('PaygOps : ' + response["answer_data"][0]["status"] + message_no_activation))
            elif 'error_message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
        else :
            if 'msg' in response:
                raise exceptions.Warning(_(response["msg"]))
            elif 'error' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["error_message"]))
            elif 'message' in response:
                raise exceptions.Warning(_('PaygOps ERROR : ' + response["message"]))
    #
    # @api.multi
    def get_country(self):
        return self.sale_order.company_id.country_id.code.lower()

#FIX Account move creation in Repair module
class StockMoveInherit(models.Model):
    _inherit = "stock.move"

    # base_unit = fields.Boolean(string="Base unit")

    # migrate later v14 ----------------------
    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        """ on redefinit pour forcer la date du account move a la date prevue du picking """
        self.ensure_one()
        account_move = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty)
        quantity = quantity if self._is_in() else -1 * quantity

        # Make an informative `ref` on the created account move to differentiate between classic
        # movements, vacuum and edition of past moves.
        ref = self.picking_id.name
        if self.env.context.get('force_valuation_amount'):
            if self.env.context.get('forced_quantity') == 0:
                ref = 'Revaluation of %s (negative inventory)' % ref
            elif self.env.context.get('forced_quantity') is not None:
                ref = 'Correction of %s (modification of past move)' % ref

        move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
                                                                                  credit_account_id, debit_account_id)
        if move_lines:
            date = self._context.get('force_period_date', self.picking_id.scheduled_date) if self.picking_id.scheduled_date else self._context.get('force_period_date',fields.Datetime.now())  # ligne modifie
            new_account_move = account_move.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': ref,
                'stock_move_id': self.id,
            })
            new_account_move.post()
    # end ----------------------------------
