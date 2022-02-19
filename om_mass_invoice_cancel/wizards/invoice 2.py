# -*- coding: utf-8 -*-

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class AccountInvoiceCancel(models.TransientModel):
    _name = 'account.invoice.cancel'
    _description = "Wizard - Account Invoice Cancel"

    def invoice_cancel(self):
        invoices = self._context.get('active_ids')
        print('-invoices----', invoices)
        invoices_ids = self.env['account.move'].browse(invoices).\
            filtered(lambda x: x.state != 'cancel')
        print('-----invoices_ids', invoices_ids)
        for invoice in invoices_ids:
            invoice.button_cancel()





