# PEG DEV MODULE

This module has been created to meet the customization needs of peg africa.

# Features

- Generate the lines of a product template when importing a quote

- add the tax_id field in the sale.product.template.line template to get it back in the sale order line 

- Change the decimal precision for Product Template line

- Force the system to retrieve the date of the Order as the confirmation date

- Force the system to retrieve the Sale Order date as the invoice date

- Force the system to retrieve the picking date as the date for account move lines

- Recovery of the analytical account from the order line for the invoice lines

- Add analytic account at logistic cost lines

- Force the system to retrieve the stock picking date as the stock move date

- Force the system to retrieve the expected date of stock picking as the date for move line stocks

- Create Purchase order  from logistics cost lines 

- Add an invoiced field in the logistics cost lines to see if an invoice has been generated for each line

# Architecture

Regarding the architecture, we must respect the development architecture of an odoo module which is organized as below

- The data folder which contains xml files allowing to save data in the database at the installation of the module
- The models folder which contains the python files allowing to define the models
- The security file which contains a csv file allowing to define the rights of access
- The test folder that contains python for test
- The views folder that contains xml files to define the user interface
- the wizard folder that contains both xml and python files for the wizard
- And at the root of project we have the manifest file who contains information about the module and the init file who contains the import of all python file

# Implementation
Here we will detail implementation of every feature, I have not insisted too much on the xml files which include for the most part the addition of fields in interface, the most custumization part is define in sale_template_product_inherit.py file .

### 1. Generate the lines of a product template when importing a quote

For this functionality, we inherit the sale order modele and create a function called action_get_order_line_from_sale_product_template()


`models/sale_template_product_inherit.py`

    @api.multi
    def action_get_order_line_from_sale_product_template(self):
        self.ensure_one()
        for order_line in self.order_line:
            order_line.unlink()
        self.product_template_id_change()


### 2. add the tax_id field in the sale.product.template.line template to get it back in the sale order line

For this feature we create a field in the sale.product.template.line modele as below

`tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])`

then we override the function `product_template_id_change()` to get it back in the sale order line

`models/sale_template_product_inherit.py`

    @api.model
    @api.onchange('product_template_id')
    def product_template_id_change(self):
        """ fucntion is defined in sh_sales_custom_product_template
         we override it for addinq tax_id in sale_order_line"""

        if self.product_template_id:
            sale_ordr_line = []

            for record in self.product_template_id.sale_product_template_ids:

                vals = {}
                vals.update({'price_unit': record.unit_price,
                             #                             'order_id':self.id,
                             'name': record.description, 'product_uom_qty': record.ordered_qty,
                             'tax_id': record.tax_id,
                             'account_analytic': record.account_analytic,
                             'discount': record.discount, 'product_uom': record.product_uom.id})

                if record.name:
                    vals.update({'product_id': record.name.id})

                sale_ordr_line.append((0, 0, vals))

            self.order_line = sale_ordr_line

        return {'type': 'ir.actions.client', 'tag': 'reload'}`

### 3. Change the decimal precision for Product Template line

For editing the default decimal precision we create a file called product_template_decimal_precision.xml in the data folder and add the following content to save the record in database

`data/product_template_decimal_precision.xml`

    <?xml version="1.0" encoding="UTF-8" ?>
    <odoo>
        <data>
            <record forcecreate="True" id="decimal_unit_price" model="decimal.precision">
                <field name="name">Product Template Line</field>
                <field name="digits" eval="6"/>
            </record>
        </data>
    </odoo>

Then in the sale.product.template.line`modele we override the field unit_price like following

`unit_price = fields.Float(digits=dp.get_precision('Product Template Line'))`

### 4. Force the system to retrieve the date of the Order as the confirmation date

For this feature we we override `action_confirm` function in `sale.order` model and changed the date as below

`models/sale_template_product_inherit.py`

    @api.multi
    def action_confirm(self):
        """this function is defined in sale modulle
        we override it for configuring the confirmation date like the date_order"""

        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': self.date_order
        })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True

### 5. Force the system to retrieve the Sale Order date as the invoice date

For this sectio we override the ` action_invoice_create` of `sale.order` model as below

`models/sale_template_product_inherit.py`

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices

        we override it for giving the invoice the same date as SO
        """

        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)

            # We only want to create sections that have at least one invoiceable line
            pending_section = None
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    invoice.write({
                        'date_invoice': self.date_order
                    })
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        pending_section.invoice_line_create(invoices[group_key].id, pending_section.qty_to_invoice)
                        pending_section = None
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key])})
            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].reference = sale_orders.reference

        if not invoices:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            # Idem for partner
            invoice._onchange_partner_id()
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]

### 6. Force the system to retrieve the picking date as the date for account move lines

For this section we inherit the ` stock.move` model and override the ` _create_account_move_line()` as below

`models/sale_template_product_inherit.py`

    class StockMoveInherit(models.Model):
    _inherit = "stock.move"

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
            date = self._context.get('force_period_date', self.picking_id.scheduled_date)  # ligne modifie
            new_account_move = account_move.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': ref,
                'stock_move_id': self.id,
            })
            new_account_move.post()

### 7. Recovery of the analytical account from the order line for the invoice lines

For this feature we inherit ` sale.order.line`, adding field account_analytic the override `_prepare_invoice_line()` as below

`models/sale_template_product_inherit.py`

    class SaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    account_analytic = fields.Many2one('account.analytic.account', string="Compte Analytique")

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        """ on redefinit pour que le invoice line recupere le compte analytique du order line"""
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos and account:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.account_analytic.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
        }
        return res

### 8. Add analytic account at logistic cost lines

For this section we inherit ` stock.landed.cost.lines` and add the flowwing field 

`models/sale_template_product_inherit.py`

    account_analytic_id = fields.Many2one('account.analytic.account', string="Compte Analytique")

### 9. Force the system to retrieve the stock picking date as the stock move date

In this section we inherit ` stock.move` and override ` _action_done()` function as below

`models/sale_template_product_inherit.py`

    class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    def _action_done(self):
        """ we override this function for recovering the date of stock.picking
        and set the stock move for the same date
            by KHK
         """
        self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_todo = self.env['stock.move']

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0:
                if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0:
                    move._action_cancel()

        # Create extra moves where necessary
        for move in moves:
            if move.state == 'cancel' or move.quantity_done <= 0:
                continue
            # extra move will not be merged in mrp
            if not move.picking_id:
                moves_todo |= move
            moves_todo |= move._create_extra_move()

        # Split moves where necessary and move quants
        for move in moves_todo:
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
                new_move = move._split(qty_split)
                for move_line in move.move_line_ids:
                    if move_line.product_qty and move_line.qty_done:
                        # FIXME: there will be an issue if the move was partially available
                        # By decreasing `product_qty`, we free the reservation.
                        # FIXME: if qty_done > product_qty, this could raise if nothing is in stock
                        try:
                            move_line.write({'product_uom_qty': move_line.qty_done})
                        except UserError:
                            pass
                move._unreserve_initial_demand(new_move)
        moves_todo.mapped('move_line_ids')._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo\
                .mapped('move_line_ids.result_package_id')\
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.mapped('location_id')) > 1:
                raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        picking = moves_todo and moves_todo[0].picking_id or False
        moves_todo.write({'state': 'done', 'date': self.picking_id.scheduled_date if self.picking_id else fields.Datetime.now()})
        moves_todo.mapped('move_dest_ids')._action_assign()

        # We don't want to create back order for scrap moves
        if all(move_todo.scrapped for move_todo in moves_todo):
            return moves_todo

        if picking:
            picking._create_backorder()
        return moves_todo

### 10. Force the system to retrieve the expected date of stock picking as the date for move line stocks

In this section we inherit ` stock.move.line` and override ` _action_done()` function as below

`models/sale_template_product_inherit.py`

    class StockMoveLineInherit(models.Model):
    _inherit ="stock.move.line"

    def _action_done(self):

        Quant = self.env['stock.quant']

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_to_delete = self.env['stock.move.line']
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:
                                lot = self.env['stock.production.lot'].create(
                                    {'name': ml.lot_name, 'product_id': ml.product_id.id}
                                )
                                ml.write({'lot_id': lot.id})
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % ml.product_id.display_name)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_to_delete |= ml
        ml_to_delete.unlink()

        # Now, we can actually move the quant.
        done_ml = self.env['stock.move.line']
        for ml in self - ml_to_delete:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding

                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty, precision_rounding=rounding) > 0:
                    extra_qty = ml.qty_done - ml.product_qty
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                # unreserve what's been reserved
                if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
                    try:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    except UserError:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            done_ml |= ml
        # Reset the reserved quantity as we just moved it to the destination location.
        (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': self.picking_id.scheduled_date if self.picking_id else fields.Datetime.now(),
        })

### 11. Create Purchase order  from logistics cost lines

In the wizard folder, we create two files landed_cost_line_make_purchase_order_view.xml for the user interface and landed_cost_line_make_purchase_order.py for models and asoociated function.

below we have the content of the python file with hight quality code, i think :-)

`wizard/landed_cost_line_make_purchase_order.py `

    import odoo.addons.decimal_precision as dp
    from odoo import _, api, exceptions, fields, models
    from datetime import datetime
    import logging
    _logger = logging.getLogger(__name__)


    class LandedCostLinesMakeInvoice(models.TransientModel):

        _name = "landed.cost.lines.make.invoice"
        _description = "Landed Cost Line Make Purchase Order"

        supplier_id = fields.Many2one('res.partner', string='Provider',
                                    required=False,
                                    domain=[('supplier', '=', True)])
        item_ids = fields.One2many(
            'landed.cost.lines.make.invoice.item',
            'wiz_id', string='Items')
        landed_cost_id = fields.Many2one('stock.landed.cost',
                                            string='Landed Cost',
                                            required=False,
                                            domain=[('state', '=', 'draft')])

        @api.model
        def _prepare_item(self, line):
            """ prepare every selected landed cost line who will passed to _prepare_invoice_line function """
            return {
                'line_id': line.id,
                'request_id': line.cost_id.id,
                'product_id': line.product_id.id,
                'account_id': line.account_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'name': line.name or line.product_id.name,
                'price_unit': line.price_unit,
                'product_qty': 1, # landed cost has no qty cuz i define 1 for the invoice line
                'date_planned': line.cost_id.date,
                }

        @api.model
        def default_get(self, fields):
            """ recover the selected landed cost line and prepare line for the invoice"""
            res = super(LandedCostLinesMakeInvoice, self).default_get(
                fields)
            landed_cost_line_obj = self.env['stock.landed.cost.lines']
            landed_cost_line_ids = self.env.context.get('active_ids', False)
            active_model = self.env.context.get('active_model', False)
            if not landed_cost_line_ids:
                return res
            assert active_model == 'stock.landed.cost.lines', \
                'Bad context propagation'

            items = []
            #self._check_valid_request_line(request_line_ids)
            landed_lines = landed_cost_line_obj.browse(landed_cost_line_ids)
            for line in landed_lines:
                if not line.invoiced:
                    items.append([0, 0, self._prepare_item(line)])
            res['item_ids'] = items
            return res

        @api.model
        def _prepare_invoice(self):
            """ this function prepare the invoice data"""
            if not self.supplier_id:
                raise exceptions.Warning(
                    _('Enter a supplier.'))
            supplier = self.supplier_id
            data = {
                'partner_id': self.supplier_id.id,
                'date_invoice': str(datetime.today()),
                'journal_id': self.env['account.journal'].search([('type', '=', 'purchase')]).id,  # by khk
                'account_id': self.env['account.account'].search([('code', '=', '401100')]).id  # by khk
                }
            return data

        @api.model
        def _prepare_invoice_line(self,purchase,item):
            """ this function prepare the invoice line"""
            res = dict()
            product = item.product_id
            for record in self:
                lines = []
                for line in record.item_ids:
                    _logger.info("quantité => %s",(line.product_qty))
                    lines.append({
                        'name': line.product_id.name,
                        'invoice_id': purchase.id,
                        'product_id': line.product_id.id,
                        'account_id':line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
                        'account_analytic_id': line.account_analytic_id.id,
                        'quantity': line.product_qty,
                        'price_unit': line.price_unit,
                        'uom_id': product.uom_po_id.id,
                        'landed_cost_line_origin': line.line_id.id,
                    })
            return lines

        @api.multi
        def make_invoice(self):
            """ this function is called when user clic on make invoice"""
            res = []
            invoice_obj = self.env['account.invoice']
            invoice_line_obj = self.env['account.invoice.line']
            invoice = False
            for item in self.item_ids:
                line = item.line_id
                if self.landed_cost_id:
                    invoice = self.landed_cost_id
                if not invoice:
                    invoice_data = self._prepare_invoice()
                    invoice = invoice_obj.create(invoice_data)
                values = self._prepare_invoice_line(invoice,item)
                purchase_order_line = invoice_line_obj.create(values)
                res.append(invoice.id)
                return {
                    'domain': [('id', 'in', res)],
                    'name': _('Invoice'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.invoice',
                    'view_id': False,
                    'context': False,
                    'type': 'ir.actions.act_window'
                }
            
    class PurchaseRequestLineMakeInvoiceItem(models.TransientModel):
        _name = "landed.cost.lines.make.invoice.item"
        _description = "Landed Cost Line Make Purchase Order Item"

        wiz_id = fields.Many2one(
            'landed.cost.lines.make.invoice',
            string='Wizard', required=True, ondelete='cascade',
        )
        line_id = fields.Many2one('stock.landed.cost.lines',
                                string='Purchase Request Line',
                                )
        request_id = fields.Many2one('stock.landed.cost',
                                    related='line_id.cost_id',
                                    string='Landed Cost',
                                    )
        product_id = fields.Many2one('product.product', string='Product')

        account_id = fields.Many2one('account.account', string='Compte',
                                        required=True,
                                        domain=[('deprecated', '=', False)],
                                        help="The income or expense account related to the selected product.")

        account_analytic_id = fields.Many2one('account.analytic.account',
                                            'Analytic Account',
                                            track_visibility='onchange')

        name = fields.Char(string='Description', required=True)
        product_qty = fields.Float(string='Quantity to invoice',
                                digits=dp.get_precision('Product UoS'),
                                )
        price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))

        @api.onchange('product_id')
        def onchange_product_id(self):
            """this function update line when user change product """
            if self.product_id:
                name = self.product_id.name
                code = self.product_id.code
                self.account_id = self.product_id.property_account_expense_id.id or self.product_id.categ_id.property_account_expense_categ_id
                sup_info_id = self.env['product.supplierinfo'].search([
                    '|', ('product_id', '=', self.product_id.id),
                    ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                    ('name', '=', self.wiz_id.supplier_id.id)])
                if sup_info_id:
                    p_code = sup_info_id[0].product_code
                    p_name = sup_info_id[0].product_name
                    name = '[%s] %s' % (p_code if p_code else code,
                                        p_name if p_name else name)
                else:
                    if code:
                        name = '[%s] %s' % (code, name)
                if self.product_id.description_purchase:
                    name += '\n' + self.product_id.description_purchase
                self.product_uom_id = self.product_id.uom_id.id
                self.product_qty = 1.0
                self.name = name



### 12. Add an invoiced field in the logistics cost lines to see if an invoice has been generated for each line

there we create field invoiced in ` stock.landed.cost.lines` model as below

` invoiced = fields.Boolean(string="Invoiced", readonly=True)`

we also create field landed_cost_line_origin in ` account.invoice.line` as below for determine the origin

` landed_cost_line_origin = fields.Many2one('stock.landed.cost.lines')`

then in the function ` _prepare_invoice_line() ` of ` landed.cost.lines.make.invoice` model we recover the landed cost line as below 

`wizard/landed_cost_line_make_purchase_order.py`

    @api.model
    def _prepare_invoice_line(self,purchase,item):
        """ this function prepare the invoice line"""
        res = dict()
        product = item.product_id
        for record in self:
            lines = []
            for line in record.item_ids:
                _logger.info("quantité => %s",(line.product_qty))
                lines.append({
                    'name': line.product_id.name,
                    'invoice_id': purchase.id,
                    'product_id': line.product_id.id,
                    'account_id':line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id,
                    'account_analytic_id': line.account_analytic_id.id,
                    'quantity': line.product_qty,
                    'price_unit': line.price_unit,
                    'uom_id': product.uom_po_id.id,
                    'landed_cost_line_origin': line.line_id.id,
                })
        return lines

then we inherit ` account.invoice` model and override ` invoice_validate` as below for set the of invoiced field as true

`models/sale_template_product_inherit.py`

    class AccountInvoiceInherit(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def invoice_validate(self):
        for invoice in self.filtered(lambda invoice: invoice.partner_id not in invoice.message_partner_ids):
            invoice.message_subscribe([invoice.partner_id.id])

            # Auto-compute reference, if not already existing and if configured on company
            if not invoice.reference and invoice.type == 'out_invoice':
                invoice.reference = invoice._get_computed_reference()
        self._check_duplicate_supplier_reference()
        
        for invoice in self:
            for invoice_line in invoice.invoice_line_ids:
                if invoice_line.landed_cost_line_origin:
                    invoice_line.landed_cost_line_origin.write({'invoiced': True})

        return self.write({'state': 'open'})


