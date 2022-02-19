from odoo import models, fields


class SyncActivationWizard(models.TransientModel):
    _name = "sync.activation.wizard"
    _description = "Sync Activation Wizard Class"

    last_sync_activated_token = fields.Char(string="Paygops Sync Token")