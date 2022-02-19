# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class CustomCrmStage(models.Model):
    _inherit = 'crm.stage'

    type_of_product  = fields.Many2one('wave2.peg.africa.type.of.product', string='Product', ondelete='set null',
        help='Specific product that uses this stage. Other products will not be able to see or use this stage.')


class CustomCrmLead(models.Model):
    _inherit = 'crm.lead'

    # migrate later v14 -----------
    def _default_stage_id(self):
        #product = self.env['wave2.peg.africa.type.of.product'].sudo()._get_default_team_id(user_id=self.env.uid)
        product = self.type_of_product
        return self._stage_find(type_of_product=product.id, domain=[('fold', '=', False)]).id
    # end ------------------------

    type_of_product  = fields.Many2one('wave2.peg.africa.type.of.product', string='Product',index=True, track_visibility='onchange')
    # migrate later v14 ----------------
    stage_id = fields.Many2one('crm.stage', string='Stage', ondelete='restrict', track_visibility='onchange', index=True,
        domain="['|', ('type_of_product', '=', False), ('type_of_product', '=', type_of_product)]",
        group_expand='_read_group_stage_ids', default=lambda self: self._default_stage_id())
    # end --------------------


    team_id = fields.Many2one('crm.team', string='Sales Team', oldname='section_id', default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(user_id=self.env.uid),
        index=True, track_visibility='onchange', help='When sending mails, the default email address is taken from the Sales Team.')


    # migrate later v14 ---------------------
    def _stage_find(self, type_of_product=False, domain=None, order='sequence'):
        """ Determine the stage of the current lead with its products, the given domain and the given type of product
            :param type_of_product
            :param domain : base search domain for stage
            :returns crm.stage recordset
        """
        # collect all products by adding given one, and the ones related to the current leads
        products = set()
        if type_of_product:
            products.add(type_of_product)
        for lead in self:
            if lead.type_of_product:
                products.add(lead.type_of_product.id)
        # generate the domain
        if products:
            search_domain = ['|', ('type_of_product', '=', False), ('type_of_product', 'in', list(products))]
        else:
            search_domain = [('type_of_product', '=', False)]

        team_ids = set()
        # team_id = self._context.get('default_team_id')
        # if team_id:
        #     team_ids.add(team_id)
        for lead in self:
            if lead.team_id:
                team_ids.add(lead.team_id.id)
        # generate the domain
        if team_ids:
            search_domain = ['|', ('team_id', '=', False), ('team_id', 'in', list(team_ids))]
        else:
            search_domain = [('team_id', '=', False)]
        # AND with the domain in parameter
        if domain:
            search_domain += list(domain)
        # perform search, return the first found
        return self.env['crm.stage'].search(search_domain, order=order, limit=1)
    #
    # @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve type of product and team id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        type_of_product = self._context.get('default_type_of_product')
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]
        if type_of_product:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('type_of_product', '=', False), ('type_of_product', '=', type_of_product)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('type_of_product', '=', False)]

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
    # end -----------------------