# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class StockPickingInheritKhk(models.Model):
    _inherit = 'stock.picking'
    
    #product_template_id = fields.Many2one("sale.product.template",string="Product Template")
    product_template_id = fields.Many2one("sale.order.template",string="Product Template")
    qty_model = fields.Integer('Quantité Modèle', required=True, default=0) #should me remove / peg said to be removed
    landed_costs = fields.Many2many("stock.landed.cost")
    landed_cost_count = fields.Integer(compute="_compute_landed_cost_count")
    
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('first_done','First Validation'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")

    @api.depends("landed_costs")
    def _compute_landed_cost_count(self):
        for picking in self:
            picking.landed_cost_count = len(self.mapped("landed_costs"))

    # needs to open
    # @api.model
    @api.onchange('product_template_id')
    def product_template_id_change(self):
        if self.product_template_id:
#             for record in self.product_template_id.sale_product_template_ids:
            for record in self.product_template_id.sale_order_template_line_ids:
                if record.product_id.product_tmpl_id.type != 'service':
                    self.move_ids_without_package += self.env['stock.move'].create({
#                         'product_id': record.name.id,
                        'product_id': record.product_id.id,
#                         'date_expected': fields.datetime.now(),
#                         'name':record.description,
                        'name':record.name,
                         'location_id':self.location_id.id,
                         'location_dest_id':self.location_dest_id.id,
                         'product_uom':record.product_uom_id.id,
                         'product_uom_qty':self.qty_model * record.product_uom_qty
                    })
        return { 'type': 'ir.actions.client', 'tag': 'reload'}

#    @api.multi
#    def action_done(self):Add in _action_done
#        """Changes picking state to done by processing the Stock Moves of the Picking

#        Normally that happens when the button "Done" is pressed on a Picking view.
#        @return: True
#        """
#        # TDE FIXME: remove decorator when migration the remaining
#        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
#        # Check if there are ops not linked to moves yet
#        for pick in self:
#            # # Explode manually added packages
#            # for ops in pick.move_line_ids.filtered(lambda x: not x.move_id and not x.product_id):
#            #     for quant in ops.package_id.quant_ids: #Or use get_content for multiple levels
#            #         self.move_line_ids.create({'product_id': quant.product_id.id,
#            #                                    'package_id': quant.package_id.id,
#            #                                    'result_package_id': ops.result_package_id,
#            #                                    'lot_id': quant.lot_id.id,
#            #                                    'owner_id': quant.owner_id.id,
#            #                                    'product_uom_id': quant.product_id.uom_id.id,
#            #                                    'product_qty': quant.qty,
#            #                                    'qty_done': quant.qty,
#            #                                    'location_id': quant.location_id.id, # Could be ops too
#            #                                    'location_dest_id': ops.location_dest_id.id,
#            #                                    'picking_id': pick.id
#            #                                    }) # Might change first element
#            # # Link existing moves or add moves when no one is related
#            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
#                # Search move with this product
#                moves = pick.move_lines.filtered(lambda x: x.product_id == ops.product_id)
#                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
#                if moves:
#                    ops.move_id = moves[0].id
#                else:
#                    new_move = self.env['stock.move'].create({
#                                                    'name': _('New Move:') + ops.product_id.display_name,
#                                                    'product_id': ops.product_id.id,
#                                                    'product_uom_qty': ops.qty_done,
#                                                    'product_uom': ops.product_uom_id.id,
#                                                    'location_id': pick.location_id.id,
#                                                    'location_dest_id': pick.location_dest_id.id,
#                                                    'picking_id': pick.id,
#                                                    'picking_type_id': pick.picking_type_id.id
#                                                   })
#                    ops.move_id = new_move.id
#                    new_move._action_confirm()
#                    todo_moves |= new_move
#                    #'qty_done': ops.qty_done})
#        todo_moves._action_done()
#        # self.write({'date_done': fields.Datetime.now()}) replaced by the line above
#        self.write({'date_done': self.scheduled_date})
#        return True
    
    def _action_done(self):#V14
        """Call `_action_done` on the `stock.move` of the `stock.picking` in `self`.
        This method makes sure every `stock.move.line` is linked to a `stock.move` by either
        linking them to an existing one or a newly created one.

        If the context key `cancel_backorder` is present, backorders won't be created.

        :return: True
        :rtype: bool
        """
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_lines.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
#        self.write({'date_done': fields.Datetime.now(), 'priority': '0'})#V14
        self.write({'date_done': self.scheduled_date, 'priority': '0'})

        # if incoming moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code == 'incoming').move_lines.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
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
        res = self.with_context(skip_wizard_immediat_open=True)._pre_action_done_hook()
        if res is not True:
            return res

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
    
    def _action_generate_immediate_wizard(self, show_transfers=False):#added in V14
        if self._context.get('skip_wizard_immediat_open'):
            wiz = self.env['stock.immediate.transfer'].create({
                'pick_ids': [(4, p.id) for p in self],
                'immediate_transfer_line_ids': [
                    (0, 0, {'to_immediate': True, 'picking_id': p_id.id})
                    for p_id in self
                ],
            })
            wiz.process()
            return True
        return super(StockPickingInheritKhk, self)._action_generate_immediate_wizard(show_transfers=show_transfers)

    def action_custom_cancel(self):
        # For Purchase Order (Receipts)
        # For Sale Order (Delivery Order)
        Quant = self.env['stock.quant']
        if self.picking_type_code == 'outgoing' or self.picking_type_code == 'incoming':
            for move in self.move_lines:
                for ml in move.move_line_ids.filtered(
                        lambda ml: ml.move_id.state == 'done' and
                                   ml.product_id.type == 'product'):
                    qty_done_orig = ml.move_id.product_uom._compute_quantity(
                        ml.qty_done, ml.move_id.product_id.uom_id,
                        rounding_method='HALF-UP')
                    in_date = Quant._update_available_quantity(ml.product_id,
                                                               ml.location_id,
                                                               qty_done_orig,
                                                               lot_id=ml.lot_id,
                                                               package_id=ml.result_package_id,
                                                               owner_id=ml.owner_id)[1]
                    Quant._update_available_quantity(ml.product_id,
                                                     ml.location_dest_id,
                                                     -qty_done_orig,
                                                     lot_id=ml.lot_id,
                                                     package_id=ml.package_id,
                                                     owner_id=ml.owner_id,
                                                     in_date=in_date)

                    move.write({'state': 'cancel'})
                    if ml.lot_id:
                        ml.update({'lot_id': '', 'qty_done': 0.00})
                    ml.update({'qty_done': 0.00})
                    ml.write({'state': 'cancel'})
                    self.write({'state': 'cancel'})
            self.env['account.move'].search([('ref', '=', self.name)]).reverse_moves()  # add by khk

    def check_serial_number_availability(self):
        not_exist = ""
        not_available = ""
        for line in self.move_line_ids_without_package:
            if line.lot_name:
                # check if serial number exist
                serial = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                if serial:
                    # check if serial number is already linked to a product with qty > 0 and location usage == customer
                    for Quant in self.env['stock.quant'].search([('lot_id', '=', serial.id), ('quantity', '>', 0)]):
                        if Quant.location_id.usage == 'customer':
                            not_available += ', ' + str(serial.name)
                else:
                    not_exist += ', ' + str(line.lot_name)

        if not_exist != "":
            raise ValidationError(_('The following serial number does not exist %s' % (not_exist)))
        if not_available != "":
            raise ValidationError(_('The following serial number should only be linked to a single product %s' % (not_available)))

    def button_first_validate(self):
        self.state = 'first_done'

    def action_create_landed_cost(self):
        form_view_id = self.env.ref("stock_landed_costs.view_stock_landed_cost_form").id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Landed Cost',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.landed.cost',
            'views': [(form_view_id, 'form')],
            'context': { 'default_picking_ids': self.ids },
            'target': 'new',
        }

    def action_view_landed_cost(self):
        '''
        This function returns an action that display existing landed costs
        of given picking. It can either be a in a list or in a form
        view, if there is only one landed cost to show.
        '''
        action = self.env.ref('peg_dev_module.action_stock_landed_cost_tree_form').read()[0]

        landed_costs = self.mapped('landed_costs')
        if len(landed_costs) > 1:
            action['domain'] = [('id', 'in', landed_costs.ids)]
        elif landed_costs:
            form_view = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = landed_costs.id
        action['context'] = { 'default_picking_ids': self.ids }
        return action

    @api.depends('immediate_transfer', 'state')
    def _compute_show_check_availability(self):
        """ According to `picking.show_check_availability`, the "check availability" button will be
        displayed in the form view of a picking.
        """
        for picking in self:
            if picking.immediate_transfer or picking.state not in ('confirmed', 'waiting', 'assigned', 'first_done'):
                picking.show_check_availability = False
                continue
            picking.show_check_availability = any(
                move.state in ('waiting', 'confirmed', 'partially_available') and
                float_compare(move.product_uom_qty, 0, precision_rounding=move.product_uom.rounding)
                for move in picking.move_lines
            )

#    W1E-63 bulk unreserve
    def bulk_unreserve(self):
        for rec in self:
            if not ((rec.picking_type_code == 'incoming' or rec.is_locked == False) \
            or (rec.state not in ('assigned', 'partially_available') and rec.move_type != 'one') \
            or (rec.state not in ('assigned', 'partially_available', 'confirmed') and rec.move_type == 'one')):
                rec.do_unreserve()
