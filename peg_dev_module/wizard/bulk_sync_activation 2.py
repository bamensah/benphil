from odoo import models, fields, api
from datetime import datetime
import logging
from odoo.addons.wave2_peg_africa.models.wave2_peg_africa_payment import format_date

_logger = logging.getLogger(__name__)


class BulkSyncActivationWizard(models.TransientModel):
    _name = "bulk.sync.activation"
    _description = "Bulk Sync Activation Wizard Class"

    def action_bulk_sync_activation(self):
        """this function calls the api gateway to ask Paygops to generate a
        sync activation token for a list of SO. Then it stores and displays it to the user.
        """
        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', []))

        for sale_order in sale_orders:
            if sale_order.paygops_id.device_id:
                data = sale_order.syn_activation(sale_order.paygops_id.device_id)

                if isinstance(data, dict):
                    device_id = self.env['stock.production.lot'].search([('name', '=', sale_order.paygops_id.device_id)],limit=1)
                    token = self.env['credit.token'].create({'code': data['code'], 'token_id': data['token_id'], 'duration': False, 'token_type': data['token_type'], 'credit_end_date': datetime.strptime(data['credit_end_date'], '%Y-%m-%d'), 'generated_date': format_date(data['generated_date']),
                                'inventory_id': device_id.id, 'transaction_id': '', 'payment_id': False, 'partner_id': sale_order.partner_id.id, 'amount': False, 'device_serial': sale_order.paygops_id.device_id,
                                'salesperson': sale_order.user_id.id, 'loan_id': sale_order.id, 'phone_number': False, 'phone_number_partner': sale_order.partner_id.phone })

                    sale_order.calculate_status()
                else:
                    msg = data.msg
                    _logger.error(f'Paygops Error: {msg}')
            else:
                _logger.error("No Paygops device assigned to this sale.")