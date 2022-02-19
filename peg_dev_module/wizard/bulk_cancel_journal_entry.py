from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class BulkCancelJournnalEntryWizard(models.TransientModel):
    _name = "bulk.cacel.journal.entry"
    _description = "Bulk Cancel Journal Entry Wizard Class"

    def action_bulk_cancel_journal_entry(self):
        account_moves = self.env['account.move'].browse(
            self._context.get('active_ids', []))

        account_moves.button_cancel()