from operator import mod
from odoo import fields, models,_,api
from datetime import date,datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    remarks = fields.Text(string = "Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_purchase_order",string = "Is Remarks")
    is_remarks_mandatory = fields.Boolean(related="company_id.remark_mandatory_for_purchase_order",string = "Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_planned')
    def onchange_date_planned(self):
        if self.date_planned:
            if str(self.date_planned.date()) < str(date.today()):
                self.is_boolean = True
            else:
                self.is_boolean = False
    
    
    def button_confirm(self, force=False):
        res = super(PurchaseOrder, self).button_confirm()
        if self.company_id.backdate_for_purchase_order:
            self.write({
                'date_approve':self.date_order
            })
        return res
    

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'invoice_date':self.date_approve if self.company_id.backdate_for_bill else date.today(),
            'remarks_for_purchase' : self.remarks if self.remarks else False
        }
        return invoice_vals

    