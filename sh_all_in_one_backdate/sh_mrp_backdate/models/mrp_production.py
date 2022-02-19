from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import datetime

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

class MrpProductionn(models.Model):
    _inherit = 'mrp.production'

    remarks = fields.Text(string = "Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_mrp_production",string = "Is Remarks")
    is_remarks_mandatory = fields.Boolean(related="company_id.remark_mandatory_for_mrp_production",string = "Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_planned_start')
    def onchange_date_planned_start(self):
        if str(self.date_planned_start.date()) < str(date.today()):
           self.is_boolean = True
        else:
            self.is_boolean = False
    

    