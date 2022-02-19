# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class StockMoveInherit(models.Model):
    _inherit = "stock.move"

    number = fields.Char('Number')

    # needs to open

    # def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
    #     """ on redefinit pour forcer la date du account move a la date prevue du picking """
    #     self.ensure_one()
    #     account_move = self.env['account.move']
    #     quantity = self.env.context.get('forced_quantity', self.product_qty)
    #     quantity = quantity if self._is_in() else -1 * quantity
    #
    #     # Make an informative `ref` on the created account move to differentiate between classic
    #     # movements, vacuum and edition of past moves.
    #     ref = self.picking_id.name
    #     if self.env.context.get('force_valuation_amount'):
    #         if self.env.context.get('forced_quantity') == 0:
    #             ref = 'Revaluation of %s (negative inventory)' % ref
    #         elif self.env.context.get('forced_quantity') is not None:
    #             ref = 'Correction of %s (modification of past move)' % ref
    #
    #     move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
    #                                                                               credit_account_id, debit_account_id)
    #     if move_lines:
    #         date = self._context.get('force_period_date', self.picking_id.scheduled_date)  # ligne modifie
    #         new_account_move = account_move.sudo().create({
    #             'journal_id': journal_id,
    #             'line_ids': move_lines,
    #             'date': date,
    #             'ref': ref,
    #             'stock_move_id': self.id,
    #         })
    #         new_account_move.post()

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):#V14
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', self.picking_id.scheduled_date) # ligne modifie
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()

    # needs to open

#    def _action_done(self):
    def _action_done(self, cancel_backorder=False):
        res = super(StockMoveInherit, self)._action_done(cancel_backorder=cancel_backorder)
        for move in res:
            move.write({
                'date': move.picking_id.scheduled_date if move.picking_id else fields.Datetime.now()
            })
        return res
        
    # NEEDS TO OPEN

    # def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
    #     """ Create or update move lines.
    #     """
    #
    #     self.ensure_one()
    #
    #     if not lot_id:
    #         lot_id = self.env['stock.production.lot']
    #     if not package_id:
    #         package_id = self.env['stock.quant.package']
    #     if not owner_id:
    #         owner_id = self.env['res.partner']
    #
    #     taken_quantity = min(available_quantity, need)
    #
    #     # `taken_quantity` is in the quants unit of measure. There's a possibility that the move's
    #     # unit of measure won't be respected if we blindly reserve this quantity, a common usecase
    #     # is if the move's unit of measure's rounding does not allow fractional reservation. We chose
    #     # to convert `taken_quantity` to the move's unit of measure with a down rounding method and
    #     # then get it back in the quants unit of measure with an half-up rounding_method. This
    #     # way, we'll never reserve more than allowed. We do not apply this logic if
    #     # `available_quantity` is brought by a chained move line. In this case, `_prepare_move_line_vals`
    #     # will take care of changing the UOM to the UOM of the product.
    #     if not strict:
    #         taken_quantity_move_uom = self.product_id.uom_id._compute_quantity(taken_quantity, self.product_uom, rounding_method='DOWN')
    #         taken_quantity = self.product_uom._compute_quantity(taken_quantity_move_uom, self.product_id.uom_id, rounding_method='HALF-UP')
    #
    #     quants = []
    #
    #     if self.product_id.tracking == 'serial':
    #         rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         if float_compare(taken_quantity, int(taken_quantity), precision_digits=rounding) != 0:
    #             taken_quantity = 0
    #
    #     try:
    #         if not float_is_zero(taken_quantity, precision_rounding=self.product_id.uom_id.rounding):
    #             quants = self.env['stock.quant']._update_reserved_quantity(
    #                 self.product_id, location_id, taken_quantity, lot_id=lot_id,
    #                 package_id=package_id, owner_id=owner_id, strict=strict
    #             )
    #     except UserError:
    #         taken_quantity = 0
    #
    #     # Find a candidate move line to update or create a new one.
    #     for reserved_quant, quantity in quants:
    #         to_update = self.move_line_ids.filtered(lambda m: m.product_id.tracking != 'serial' and
    #                                                 m.location_id.id == reserved_quant.location_id.id and m.lot_id.id == reserved_quant.lot_id.id and m.package_id.id == reserved_quant.package_id.id and m.owner_id.id == reserved_quant.owner_id.id)
    #         if to_update:
    #             to_update[0].with_context(bypass_reservation_update=True).product_uom_qty += self.product_id.uom_id._compute_quantity(quantity, to_update[0].product_uom_id, rounding_method='HALF-UP')
    #         else:
    #             if self.product_id.tracking == 'serial':
    #                 for i in range(0, int(quantity)):
    #                     if self.number:
    #                         lot = self.env['stock.production.lot'].search([('name', '=', self.number)])
    #                         if not lot:
    #                             raise UserError(_('This lot %s doesn\'t exist.') % (self.number))
    #                         reserved_quant.write({'lot_id': lot.id})
    #                     self.env['stock.move.line'].create(self._prepare_move_line_vals(quantity=1, reserved_quant=reserved_quant))
    #             else:
    #                 self.env['stock.move.line'].create(self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))
    #     return taken_quantity

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        """ Create or update move lines.
        """
        self.ensure_one()

        if not lot_id:
            lot_id = self.env['stock.production.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        taken_quantity = min(available_quantity, need)

        # `taken_quantity` is in the quants unit of measure. There's a possibility that the move's
        # unit of measure won't be respected if we blindly reserve this quantity, a common usecase
        # is if the move's unit of measure's rounding does not allow fractional reservation. We chose
        # to convert `taken_quantity` to the move's unit of measure with a down rounding method and
        # then get it back in the quants unit of measure with an half-up rounding_method. This
        # way, we'll never reserve more than allowed. We do not apply this logic if
        # `available_quantity` is brought by a chained move line. In this case, `_prepare_move_line_vals`
        # will take care of changing the UOM to the UOM of the product.
        if not strict and self.product_id.uom_id != self.product_uom:
            taken_quantity_move_uom = self.product_id.uom_id._compute_quantity(taken_quantity, self.product_uom, rounding_method='DOWN')
            taken_quantity = self.product_uom._compute_quantity(taken_quantity_move_uom, self.product_id.uom_id, rounding_method='HALF-UP')

        quants = []

        if self.product_id.tracking == 'serial':
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(taken_quantity, int(taken_quantity), precision_digits=rounding) != 0:
                taken_quantity = 0

        try:
            if not float_is_zero(taken_quantity, precision_rounding=self.product_id.uom_id.rounding):
                quants = self.env['stock.quant']._update_reserved_quantity(
                    self.product_id, location_id, taken_quantity, lot_id=lot_id,
                    package_id=package_id, owner_id=owner_id, strict=strict
                )
        except UserError:
            taken_quantity = 0

        # Find a candidate move line to update or create a new one.
        for reserved_quant, quantity in quants:
            to_update = next((line for line in self.move_line_ids if line._reservation_is_updatable(quantity, reserved_quant)), False)
            if to_update:
                to_update.with_context(bypass_reservation_update=True).product_uom_qty += self.product_id.uom_id._compute_quantity(quantity, to_update.product_uom_id, rounding_method='HALF-UP')
            else:
                if self.product_id.tracking == 'serial':
                    if self.number:
                         lot = self.env['stock.production.lot'].search([('name', '=', self.number)])
                         if not lot:
                             raise UserError(_('This lot %s doesn\'t exist.') % (self.number))
                         reserved_quant.write({'lot_id': lot.id})
                    self.env['stock.move.line'].create([self._prepare_move_line_vals(quantity=1, reserved_quant=reserved_quant) for i in range(int(quantity))])
                else:
                    self.env['stock.move.line'].create(self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))
        return taken_quantity


class StockMoveLineInherit(models.Model):
    _inherit ="stock.move.line"

    # def _action_done(self):
    #     """ This method is called during a move's `action_done`. It'll actually move a quant from
    #     the source location to the destination location, and unreserve if needed in the source
    #     location.
    #
    #     This method is intended to be called on all the move lines of a move. This method is not
    #     intended to be called when editing a `done` move (that's what the override of `write` here
    #     is done.
    #
    #
    #     start khk comment
    #     we override this function for recovering the scheduled_date of the stock picking
    #     and set it like date of stock move line
    #     end khk comment
    #
    #     """
    #     Quant = self.env['stock.quant']
    #
    #
    #     # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
    #     # be negative and, according to the presence of a picking type or a linked inventory
    #     # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
    #     # the line. It is mandatory in order to free the reservation and correctly apply
    #     # `action_done` on the next move lines.
    #     ml_to_delete = self.env['stock.move.line']
    #     for ml in self:
    #         # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
    #         uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
    #         precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
    #         if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
    #             raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
    #                               defined on the unit of measure "%s". Please change the quantity done or the \
    #                               rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))
    #
    #         qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
    #         if qty_done_float_compared > 0:
    #             if ml.product_id.tracking != 'none':
    #                 picking_type_id = ml.move_id.picking_type_id
    #                 if picking_type_id:
    #                     if picking_type_id.use_create_lots and not picking_type_id.use_import_lots:
    #                         # If a picking type is linked, we may have to create a production lot on
    #                         # the fly before assigning it to the move line if the user checked both
    #                         # `use_create_lots` and `use_existing_lots`.
    #                         if ml.lot_name and not ml.lot_id:
    #                             lot = self.env['stock.production.lot'].create(
    #                                 {'name': ml.lot_name, 'product_id': ml.product_id.id}
    #                             )
    #                             ml.write({'lot_id': lot.id})
    #                     elif picking_type_id.use_import_lots and picking_type_id.use_create_lots:
    #                         lot = self.env['stock.production.lot'].search([('name', '=', ml.lot_name),('product_id', '=', ml.product_id.id)])
    #                         if not lot:
    #                             raise UserError(_('This lot %s doesn\'t exist.') % (ml.lot_name))
    #                         #stock_using_the_lot = self.env['stock.move.line'].search([('lot_id', '=', lot.id), ('state', '=', 'done')])
    #                         #if stock_using_the_lot:
    #                         #    raise UserError(_('This lot %s is already used.') % (ml.lot_name))
    #                         ml.write({'lot_id': lot.id})
    #                     elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
    #                         # If the user disabled both `use_create_lots` and `use_existing_lots`
    #                         # checkboxes on the picking type, he's allowed to enter tracked
    #                         # products without a `lot_id`.
    #                         continue
    #                 elif ml.move_id.inventory_id:
    #                     # If an inventory adjustment is linked, the user is allowed to enter
    #                     # tracked products without a `lot_id`.
    #                     continue
    #
    #                 if not ml.lot_id:
    #                     raise UserError(_('You need to supply a Lot/Serial number for product %s.') % ml.product_id.display_name)
    #         elif qty_done_float_compared < 0:
    #             raise UserError(_('No negative quantities allowed'))
    #         else:
    #             ml_to_delete |= ml
    #     ml_to_delete.unlink()
    #
    #     # Now, we can actually move the quant.
    #     done_ml = self.env['stock.move.line']
    #     for ml in self - ml_to_delete:
    #         if ml.product_id.type == 'product':
    #             rounding = ml.product_uom_id.rounding
    #
    #             # if this move line is force assigned, unreserve elsewhere if needed
    #             if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty, precision_rounding=rounding) > 0:
    #                 extra_qty = ml.qty_done - ml.product_qty
    #                 ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
    #             # unreserve what's been reserved
    #             if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
    #                 try:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #                 except UserError:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #
    #             # move what's been actually done
    #             quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
    #             available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             if available_qty < 0 and ml.lot_id:
    #                 # see if we can compensate the negative quants with some untracked quants
    #                 untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #                 if untracked_qty:
    #                     taken_from_untracked_qty = min(untracked_qty, abs(quantity))
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
    #         done_ml |= ml
    #     # Reset the reserved quantity as we just moved it to the destination location.
    #     (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
    #         'product_uom_qty': 0.00,
    #     })
    #     for mvl in self:
    #         mvl.write({
    #             'date': mvl.picking_id.scheduled_date if mvl.picking_id else fields.Datetime.now(), # edited line
    #         })
    
    # def _action_done(self):
    #     res = super(StockMoveLineInherit, self)._action_done()
    #     _logger.info('Before peg_dev_module MoveLine _action_done override')
    #     _logger.info(self)
    #     for mvl in self:
    #         _logger.info('Pre-loop in peg_dev_module MoveLine _action_done override')
    #         mvl.write({
    #              'date': mvl.picking_id.scheduled_date if mvl.picking_id else fields.Datetime.now(), # edited line
    #          })
    #         # Point of error. Changing Picking date deletes the moveline
    #         _logger.info('Post-loop in peg_dev_module MoveLine _action_done override')
    #     _logger.info('After peg_dev_module MoveLine _action_done override')