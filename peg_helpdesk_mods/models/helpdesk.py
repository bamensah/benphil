# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
import datetime

_logger = logging.getLogger(__name__)


class HelpdeskTicketInherit(models.Model):
    _inherit = 'helpdesk.ticket'

    subteam_id = fields.Many2one(
        'helpdesk.subteam',
        string='Subteam',
#        comodel_name='helpdesk.subteam',
        track_visibility='onchange', 
#        translate=True
    )

    team_id = fields.Many2one(track_visibility='onchange', required=True, default=None)

    linked_ticket = fields.Many2one(
        'helpdesk.ticket',
        string='Previous Ticket',
#        comodel_name='helpdesk.ticket',
        readonly=True, 
        #translate=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        'Sale Order',
        #translate=True
    )

    interaction_ids = fields.One2many(
        'helpdesk.ticket.interaction',
        string='Interactions',
#        comodel_name='helpdesk.ticket.interaction',
        inverse_name='ticket_id', 
        #translate=True

    )

    product_id = fields.Many2one(string="Component", comodel_name="product.product",
                                 help="What is the component we are swapping?")
    serial_number_swap = fields.Many2one(string="Serial number to Swap", comodel_name="stock.production.lot",
                                         help="What is the account/serial number of the customer?")
    troubleshooting_completed = fields.Boolean(string="Troubleshooting Completed",
                                               help="Has troubleshooting been conducted and completed?")
    swap_needed = fields.Boolean(string="Swap Needed", help="Does the customer's issue require a swap?")
    swap_available = fields.Selection(selection=[('available', 'Swap Available'), ('pending', 'Pending HQ OPs Supply')],
                                      string="Swap Available",
                                      help="Is there swap available at the service centre to meet the swap need of the customer?")
    swap_status_field = fields.Selection(selection=[('pending', 'Pending'), ('completed', 'Completed')],
                                         string="Field Swap Status",
                                         help="Has the component been swapped for the customer on the field?")
    swap_status_pegasus = fields.Selection(selection=[('pending', 'Pending'), ('completed', 'Completed')],
                                           string="Pegasus Swap Status",
                                           help="Has the component been swapped in Pegasus?")
    new_serial_number = fields.Many2one(string="New serial number", comodel_name="stock.production.lot",
                                        help="New account and serial number for component given to the customer")
    preferred_swap_method = fields.Selection(string="Preferred Swap method",
                                             help="This is the method which the customer prefers his swapped device to be delivered to him",
                                             selection=[('self-pickup', 'Self Pickup'), ('go-delivery', 'Go Delivery')])
    assigned_go = fields.Many2one(string="Assigned GO", help="The name of the G.O who has been assigned",
                                  comodel_name="res.partner")
    allocated_by_hso = fields.Boolean(string="Allocated to G.O by HSO",
                                      help="Has the device been allocated to the GO by the HSO")
    swap_status_with_customer = fields.Selection(help="Has the G.O delivered the customer's swap to him",
                                                 string="Swap Status with Customer",
                                                 selection=[('pending', 'Pending'), ('completed', 'Completed')])
    swap_device_returned_sc = fields.Selection(help="Has the swapped device of the customer been returned to the SC",
                                               string="Swapped device returned to SC",
                                               selection=[('pending', 'Pending'), ('completed', 'Completed')])
    service_center = fields.Many2one(string="Service Center", comodel_name="crm.team",
                                     help="What service centre will the customer want to be served?")
    ticket_type_name = fields.Char(string='ticket_type_name', related='ticket_type_id.name')
    product_tracking = fields.Selection(related='product_id.tracking')

    def write(self, vals):
        # we set the assignation date (assign_date) to now for tickets that are being assigned for the first time
        # same thing for the closing date
        assigned_tickets = closed_tickets = self.browse()
        if vals.get('user_id'):
            assigned_tickets = self.filtered(
                lambda ticket: not ticket.assign_date)
            new_ticket_state_id = self.env['helpdesk.stage'].search(
                [('name', '=', 'New')], limit=1).id
            for s in self:
                _logger.info(s.stage_id)
                if s.stage_id.id == new_ticket_state_id:
                    assigned_state_id = self.env['helpdesk.stage'].search(
                        [('name', '=', 'Assigned')], limit=1).id
                    s.write({
                        'stage_id': assigned_state_id
                    })
        if vals.get('stage_id') and self.env['helpdesk.stage'].browse(vals.get('stage_id')).is_close:
            closed_tickets = self.filtered(
                lambda ticket: not ticket.close_date)

        now = datetime.datetime.now()
        res = super(HelpdeskTicketInherit, self - assigned_tickets -
                    closed_tickets).write(vals)
        res &= super(HelpdeskTicketInherit, assigned_tickets - closed_tickets).write(dict(vals, **{
            'assign_date': now,
        }))
        res &= super(HelpdeskTicketInherit, closed_tickets - assigned_tickets).write(dict(vals, **{
            'close_date': now,
        }))
        res &= super(HelpdeskTicketInherit, assigned_tickets & closed_tickets).write(dict(vals, **{
            'assign_date': now,
            'close_date': now,
        }))

        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])

        return res

    def assign_ticket_to_self(self):
        self.ensure_one()
        self.user_id = self.env.user
        new_ticket_state_id = self.env['helpdesk.stage'].search(
            [('name', '=', 'New')], limit=1).id
        for s in self:
            _logger.info(s.stage_id)
            if s.stage_id.id == new_ticket_state_id:
                assigned_state_id = self.env['helpdesk.stage'].search(
                    [('name', '=', 'Assigned')], limit=1).id
                s.write({
                    'stage_id': assigned_state_id
                })

    def escalate_ticket(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket.escalate_wizard',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id
            }
        }

    def add_interaction(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.interaction.entry_wizard',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_tag_ids': self.tag_ids.ids,
                'default_ticket_type_id' : self.ticket_type_id.id,
                'default_partner_id': self.partner_id.id,
                'default_sale_order_id': self.sale_order_id.id
            }
        }

    def create_link_ticket(self):
        self.ensure_one()
        old_ticket = self.env['helpdesk.ticket'].search(
            [('id', '=', self.id)], limit=1)

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'context': {
                'default_linked_ticket': self.id,
                'default_user_id': old_ticket.user_id.id,
                'default_partner_id': old_ticket.partner_id.id,
                'default_partner_name': old_ticket.partner_name
            }
        }

    def resolve_ticket(self):
        self.ensure_one()
        stage_id = self.env['helpdesk.stage'].search(
            [('name', '=', 'Resolved')], limit=1).id
        self.write({
            'stage_id': stage_id
        })


class HelpdeskTicketSubtag(models.Model):
    _name = 'helpdesk.ticket.subtag'
    _description = 'Sub Tags based on selected Interaction Tags'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True
    )

    interaction_tag_id = fields.Many2one(
        'helpdesk.ticket.interaction.tag',
        string='Interaction Tag',
#        comodel_name='helpdesk.ticket.interaction.tag',
        required=True,
        #translate=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id,
        readonly=True,
#        translate=True
    )


class HelpdeskSubteam(models.Model):
    _name = 'helpdesk.subteam'
    _description = 'Sub team based on selected Team'

    name = fields.Char(string='Subteam Name', required=True)

    team_id = fields.Many2one(
        'helpdesk.team',
        string='Helpdesk Team',
#        comodel_name='helpdesk.team',
        required=True, 
#        translate=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.user.company_id,
        readonly=True,
#        translate=True
    )


class HelpdeskTicketEscalateWizard(models.TransientModel):
    _name = 'helpdesk.ticket.escalate_wizard'
    _description = 'Temporary data to Escalate a ticket to another team'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string="Ticket",
#        comodel_name='helpdesk.ticket',
        readonly=True, 
#        translate=True
    )

    team_id = fields.Many2one(
        'helpdesk.team', 
        string='Team',
#        comodel_name='helpdesk.team', 
#        translate=True
    )

    subteam_id = fields.Many2one(
        'helpdesk.subteam',
        string='Sub Team',
#        comodel_name='helpdesk.subteam', 
#        translate=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
#        comodel_name='res.users', 
#        translate=True
    )

    def process_escalation(self):

        stage_id = self.env['helpdesk.stage'].search(
            [('name', '=', 'Escalated')], limit=1).id

        self.env['helpdesk.ticket'].search([('id', '=', self.ticket_id.id)], limit=1).write(
            {
                'team_id': self.team_id.id,
                'subteam_id': self.subteam_id.id,
                'user_id': self.user_id.id,
                'stage_id': stage_id
            })

        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('team_id')
    def onchange_team(self):
        return {'domain': {
            'user_id': [('id', 'in', self.team_id.member_ids.ids)]
        }}


class HelpdeskInteraction(models.Model):
    _name = 'helpdesk.ticket.interaction'

    _description = 'Customer interactions on Ticket'

    summary = fields.Char(
        string='Summary', 
        translate=True
    )

    notes = fields.Text(
        string='Notes', 
        translate=True
    )

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
#        comodel_name='helpdesk.ticket',
        required=False, 
#        translate=True
    )

    initiation_channel_id = fields.Many2one(
        'helpdesk.ticket.interaction.initiation_channel',
        string='Initiation Channel',
#        comodel_name='helpdesk.ticket.interaction.initiation_channel', 
#        translate=True
    )

    status = fields.Selection(
        string='State',
        selection=[('success', 'Success'), ('failure', 'Failure')], 
        translate=True
    )

    tag_ids = fields.Many2many(
        'helpdesk.tag',
        string='Tags',
#        comodel_name='helpdesk.tag',
        readonly=True, 
#        translate=True
    )

    subtag_ids = fields.Many2many(
        'helpdesk.ticket.subtag',
        string='Interaction Sub-Tags',
#        comodel_name='helpdesk.ticket.subtag', 
#        translate=True
    )

    type = fields.Selection(
        string='Type',
        selection=[('inbound', 'Inbound'), ('outbound', 'Outbound')],
        required=True, 
        translate=True
    )

    tool_id = fields.Many2one(
        'helpdesk.ticket.interaction.tool',
        string='Tool',
#        comodel_name='helpdesk.ticket.interaction.tool',
        ondelete='restrict', 
#        translate=True
    )

    #W2E-51 : HELPDESK : Add new fields
    interaction_tag_ids = fields.Many2many(
        'helpdesk.ticket.interaction.tag',
        string='Interaction Tags',
#        comodel_name='helpdesk.ticket.interaction.tag',
        ondelete='restrict', 
#        translate=True
    )

    outcome_interaction_id = fields.Many2one(
        'helpdesk.ticket.interaction.outcome',
        string='Outcome of interaction',
#        comodel_name='helpdesk.ticket.interaction.outcome',
        ondelete='restrict', 
#        translate=True
    )

    why_id = fields.Many2one(
        'helpdesk.ticket.interaction.why',
        string='Why ?',
#        comodel_name='helpdesk.ticket.interaction.why',
        ondelete='restrict', 
#        translate=True
    )

    followup_action_id = fields.Many2one(
        'helpdesk.ticket.interaction.followup.action',
        string='Follow-up action',
#        comodel_name='helpdesk.ticket.interaction.followup.action',
        ondelete='restrict', 
#        translate=True
    )

    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket',
#        comodel_name='helpdesk.ticket.type',
        required=True, 
#        translate=True
    )
    partner_id = fields.Many2one(string='Partner', store=True, compute='_compute_partner')

    sale_order_id = fields.Many2one(
        string='Sale Order',
        comodel_name='sale.order',
        ondelete='restrict',
    )
    
    @api.depends('ticket_id')
    def _compute_partner(self):
        for record in self:
            if record.ticket_id and not record.partner_id:
                record.partner_id = record.ticket_id.partner_id.id
    

class HelpdeskInteractionInitiationChannel(models.Model):

    _name = 'helpdesk.ticket.interaction.initiation_channel'
    _description = 'Collection of channels for initiation communication'

    name = fields.Char(string='Name', required=True, translate=True)


class HelpdeskInteractionTool(models.Model):
    _name = 'helpdesk.ticket.interaction.tool'
    _description = 'Interaction Tools'

    name = fields.Char(string='Name', required=True, translate=True)


# HELPDESK INTERACTION TAGS
class HelpdeskInteractionTag(models.Model):
    _name = 'helpdesk.ticket.interaction.tag'
    _description = 'Interaction Tags'

    name = fields.Char(string='Name', required=True, translate=True)
    ticket_type_id = fields.Many2one(
        string='Ticket Type',
        comodel_name='helpdesk.ticket.type',
        required=True,
#        translate=True
    )


# HELPDESK OUTCOME OF INTERACTION
class HelpdeskInteractionOutcome(models.Model):
    _name = 'helpdesk.ticket.interaction.outcome'
    _description = 'Outcomes of Interaction'

    name = fields.Char(string='Name', required=True, translate=True)


# HELPDESK INTERACTION WHY
class HelpdeskInteractionWhy(models.Model):
    _name = 'helpdesk.ticket.interaction.why'
    _description = 'Why'

    name = fields.Char(string='Name', required=True, translate=True)


# HELPDESK FOLLOWUP ACTIONS
class HelpdeskFollowUpActions(models.Model):
    _name = 'helpdesk.ticket.interaction.followup.action'
    _description = 'Follow up actions'

    name = fields.Char(string='Name', required=True, translate=True)


# Add ticket type in Helpdesk tags
class HelpdeskTagCustom(models.Model):
    _inherit = 'helpdesk.tag'
    _description = 'Helpdesk Tags'

    ticket_type_id = fields.Many2one(
        string='Ticket Type',
        comodel_name='helpdesk.ticket.type',
        required=True,
#        translate=True
    )


class HelpdeskTicketInteractionEntryWizard(models.TransientModel):
    _name = 'helpdesk.interaction.entry_wizard'
    _description = 'Wizard for Helpdesk Ticket Entry'

    summary = fields.Char(
        string='Summary', 
        translate=True
    )

    notes = fields.Text(
        string='Notes', 
        translate=True
    )

    ticket_id = fields.Many2one(
        string='Ticket',
        comodel_name='helpdesk.ticket',
        required=False, 
#        translate=True
    )

    initiation_channel_id = fields.Many2one(
        string='Initiation Channel',
        comodel_name='helpdesk.ticket.interaction.initiation_channel', 
#        translate=True
    )

    status = fields.Selection(
        string='State',
        selection=[('success', 'Success'), ('failure', 'Failure')], 
        translate=True
    )

    tag_ids = fields.Many2many(
        string='Tags',
        comodel_name='helpdesk.tag', 
#        translate=True
    )

    subtag_ids = fields.Many2many(
        string='Interaction Sub-Tags',
        comodel_name='helpdesk.ticket.subtag', 
#        translate=True
    )

    type = fields.Selection(
        string='Type',
        selection=[('inbound', 'Inbound'), ('outbound', 'Outbound')],
        required=True, 
        translate=True
    )

    tool_id = fields.Many2one(
        string='Tool',
        comodel_name='helpdesk.ticket.interaction.tool', 
#        translate=True
    )

    #W2E-51 : HELPDESK : Add new fields
    interaction_tag_ids = fields.Many2many(
        string='Interaction Tags',
        comodel_name='helpdesk.ticket.interaction.tag',
        relation = 'helpdesk_ticket_interaction_tag_rel',
        ondelete='restrict', 
#        translate=True
    )

    outcome_interaction_id = fields.Many2one(
        string='Outcome of interaction',
        comodel_name='helpdesk.ticket.interaction.outcome',
        ondelete='restrict', 
#        translate=True
    )

    why_id = fields.Many2one(
        string='Why ?',
        comodel_name='helpdesk.ticket.interaction.why',
        ondelete='restrict', 
#        translate=True
    )

    followup_action_id = fields.Many2one(
        string='Follow-up action',
        comodel_name='helpdesk.ticket.interaction.followup.action',
        ondelete='restrict', 
#        translate=True
    )

    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type',
#        comodel_name='helpdesk.ticket.type',
        required=True, 
#        translate=True
    )
    
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner'
    )

    sale_order_id = fields.Many2one(
        string='Sales Order',
        comodel_name='sale.order'
    )

    def save_interaction(self):
        rec = self.env['helpdesk.ticket.interaction'].create(
            {
                'notes': self.notes,
                'ticket_type_id': self.ticket_type_id.id,
                'initiation_channel_id': self.initiation_channel_id.id,
                'status': self.status,
                'tag_ids': [(6, 0, self.tag_ids.ids)],
                'subtag_ids': [(6, 0, self.subtag_ids.ids)],
                'type': self.type,
                'tool_id': self.tool_id.id,
                'interaction_tag_ids': [(6, 0, self.interaction_tag_ids.ids)],
                'outcome_interaction_id': self.outcome_interaction_id.id,
                'why_id': self.why_id.id,
                'followup_action_id': self.followup_action_id.id,
                'partner_id': self.partner_id.id,
                'sale_order_id': self.sale_order_id.id
            })
        rec.write({'partner_id': self.partner_id.id})
        return {'type': 'ir.actions.act_window_close'}
