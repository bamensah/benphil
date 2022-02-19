from odoo import models, api, _, fields
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging 
_logger = logging.getLogger(__name__) 


class ReportPartnerLedgerInherit(models.AbstractModel):
    _inherit = "account.partner.ledger"

    # filter_account = True

    #needs to open

    # def _set_context(self, options):
    #     ctx = super(ReportPartnerLedgerInherit, self)._set_context(options)
    #     if options.get('account_ids'):
    #         ctx['account_ids'] = self.env['account.account'].browse([int(account) for account in options['account_ids']])
    #     return ctx

    # needs to open

    # @api.model
    # def _get_options(self, previous_options=None):
    #     # Be sure that user has group analytic if a report tries to display analytic
    #     if self.filter_analytic:
    #         self.filter_analytic_accounts = [] if self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids else None
    #         self.filter_analytic_tags = [] if self.env.user.id in self.env.ref('analytic.group_analytic_tags').users.ids else None
    #         #don't display the analytic filtering options if no option would be shown
    #         if self.filter_analytic_accounts is None and self.filter_analytic_tags is None:
    #             self.filter_analytic = None
    #     # if self.filter_partner:
    #         # self.filter_partner_ids = []
    #         # self.filter_partner_categories = []
    #     # if self.filter_account:
    #     #     self.filter_account_ids = []
    #     return super(ReportPartnerLedgerInherit, self)._get_options(previous_options)

    # needs to open

    # def get_report_informations(self, options):
    #     options = self._get_options(options)
    #     # if options and options.get('account') is not None:
    #     #     options['selected_account_ids'] = [self.env['account.account'].browse(int(account)).name for account in options['account_ids']]
    #     return super(ReportPartnerLedgerInherit, self).get_report_informations(options)

class ReportAccountAgedPayableInherit(models.AbstractModel):
    _inherit = "account.aged.payable"

    # filter_account = True
    #
    # @api.model
    # def _get_options(self, previous_options=None):
    #     # Be sure that user has group analytic if a report tries to display analytic
    #     if self.filter_analytic:
    #         self.filter_analytic_accounts = [] if self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids else None
    #         self.filter_analytic_tags = [] if self.env.user.id in self.env.ref('analytic.group_analytic_tags').users.ids else None
    #         #don't display the analytic filtering options if no option would be shown
    #         if self.filter_analytic_accounts is None and self.filter_analytic_tags is None:
    #             self.filter_analytic = None
    #     # if self.filter_partner:
    #         # self.filter_partner_ids = []
    #         # self.filter_partner_categories = []
    #     # if self.filter_account:
    #     #     self.filter_account_ids = []
    #     return self._get_options(previous_options)
    #
    #
    # def _set_context(self, options):
    #     ctx = super(ReportAccountAgedPayableInherit, self)._set_context(options)
    #     if options.get('account_ids'):
    #         ctx['account_ids'] = self.env['account.account'].browse([int(account) for account in options['account_ids']])
    #     return ctx

class ReportAccountAgedReceivableInherit(models.AbstractModel):
    _inherit = "account.aged.receivable"

    # filter_account = True

    # needs to open

    # @api.model
    # def _get_options(self, previous_options=None):
    #     # Be sure that user has group analytic if a report tries to display analytic
    #     if self.filter_analytic:
    #         self.filter_analytic_accounts = [] if self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids else None
    #         self.filter_analytic_tags = [] if self.env.user.id in self.env.ref('analytic.group_analytic_tags').users.ids else None
    #         #don't display the analytic filtering options if no option would be shown
    #         if self.filter_analytic_accounts is None and self.filter_analytic_tags is None:
    #             self.filter_analytic = None
    #     # if self.filter_partner:
    #         # self.filter_partner_ids = []
    #         # self.filter_partner_categories = []
    #     # if self.filter_account:
    #     #     self.filter_account_ids = []
    #     return self._get_options(previous_options)


    # needs to open

    # def _set_context(self, options):
    #     ctx = super(ReportAccountAgedReceivableInherit, self)._set_context(options)
    #     if options.get('account_ids'):
    #         ctx['account_ids'] = self.env['account.account'].browse([int(account) for account in options['account_ids']])
    #     return ctx

class ReportAgedPartnerBalanceInherit(models.AbstractModel):

    _inherit = 'account.aged.partner'
    _description = 'Aged Partner Balance Report'

    # needs to open

    # def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
    #     # This method can receive the context key 'include_nullified_amount' {Boolean}
    #     # Do an invoice and a payment and unreconcile. The amount will be nullified
    #     # By default, the partner wouldn't appear in this report.
    #     # The context key allow it to appear
    #     # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
    #     # Name       Stop         Start
    #     # 1 - 30   : 2019-02-07 - 2019-01-09
    #     # 31 - 60  : 2019-01-08 - 2018-12-10
    #     # 61 - 90  : 2018-12-09 - 2018-11-10
    #     # 91 - 120 : 2018-11-09 - 2018-10-11
    #     # +120     : 2018-10-10
    #     ctx = self._context
    #     periods = {}
    #     date_from = fields.Date.from_string(date_from)
    #     start = date_from
    #     for i in range(5)[::-1]:
    #         stop = start - relativedelta(days=period_length)
    #         period_name = str((5-(i+1)) * period_length + 1) + '-' + str((5-i) * period_length)
    #         period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
    #         if i == 0:
    #             period_name = '+' + str(4 * period_length)
    #         periods[str(i)] = {
    #             'name': period_name,
    #             'stop': period_stop,
    #             'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
    #         }
    #         start = stop
    #
    #     res = []
    #     total = []
    #     partner_clause = ''
    #     cr = self.env.cr
    #     user_company = self.env.user.company_id
    #     user_currency = user_company.currency_id
    #     company_ids = self._context.get('company_ids') or [user_company.id]
    #     move_state = ['draft', 'posted']
    #     if target_move == 'posted':
    #         move_state = ['posted']
    #     arg_list = (tuple(move_state), tuple(account_type), date_from, date_from,)
    #     if ctx.get('partner_ids'):
    #         partner_clause = 'AND (l.partner_id IN %s)'
    #         arg_list += (tuple(ctx['partner_ids'].ids),)
    #     if ctx.get('partner_categories'):
    #         partner_clause += 'AND (l.partner_id IN %s)'
    #         partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
    #         arg_list += (tuple(partner_ids or [0]),)
    #     if ctx.get('account_ids'):
    #         partner_clause += 'AND (account_account.id IN %s)'
    #         arg_list += (tuple(ctx['account_ids'].ids),)
    #     arg_list += (date_from, tuple(company_ids))
    #     query = '''
    #         SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
    #         FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
    #         WHERE (l.account_id = account_account.id)
    #             AND (l.move_id = am.id)
    #             AND (am.state IN %s)
    #             AND (account_account.internal_type IN %s)
    #             AND (
    #                     l.reconciled IS FALSE
    #                     OR l.id IN(
    #                         SELECT credit_move_id FROM account_partial_reconcile where max_date > %s
    #                         UNION ALL
    #                         SELECT debit_move_id FROM account_partial_reconcile where max_date > %s
    #                     )
    #                 )
    #                 ''' + partner_clause + '''
    #             AND (l.date <= %s)
    #             AND l.company_id IN %s
    #         ORDER BY UPPER(res_partner.name)'''
    #     cr.execute(query, arg_list)
    #
    #     partners = cr.dictfetchall()
    #     # put a total of 0
    #     for i in range(7):
    #         total.append(0)
    #
    #     # Build a string like (1,2,3) for easy use in SQL query
    #     partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
    #     lines = dict((partner['partner_id'] or False, []) for partner in partners)
    #     if not partner_ids:
    #         return [], [], {}
    #
    #     # Use one query per period and store results in history (a list variable)
    #     # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
    #     history = []
    #     for i in range(5):
    #         args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
    #         dates_query = '(COALESCE(l.date_maturity,l.date)'
    #
    #         if periods[str(i)]['start'] and periods[str(i)]['stop']:
    #             dates_query += ' BETWEEN %s AND %s)'
    #             args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
    #         elif periods[str(i)]['start']:
    #             dates_query += ' >= %s)'
    #             args_list += (periods[str(i)]['start'],)
    #         else:
    #             dates_query += ' <= %s)'
    #             args_list += (periods[str(i)]['stop'],)
    #         args_list += (date_from, tuple(company_ids))
    #
    #         query = '''SELECT l.id
    #                 FROM account_move_line AS l, account_account, account_move am
    #                 WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
    #                     AND (am.state IN %s)
    #                     AND (account_account.internal_type IN %s)
    #                     AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
    #                     AND ''' + dates_query + '''
    #                 AND (l.date <= %s)
    #                 AND l.company_id IN %s
    #                 ORDER BY COALESCE(l.date_maturity, l.date)'''
    #         cr.execute(query, args_list)
    #         partners_amount = {}
    #         aml_ids = cr.fetchall()
    #         aml_ids = aml_ids and [x[0] for x in aml_ids] or []
    #         for line in self.env['account.move.line'].browse(aml_ids).with_context(prefetch_fields=False):
    #             partner_id = line.partner_id.id or False
    #             if partner_id not in partners_amount:
    #                 partners_amount[partner_id] = 0.0
    #             line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
    #             if user_currency.is_zero(line_amount):
    #                 continue
    #             for partial_line in line.matched_debit_ids:
    #                 if partial_line.max_date <= date_from:
    #                     line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
    #             for partial_line in line.matched_credit_ids:
    #                 if partial_line.max_date <= date_from:
    #                     line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
    #
    #             if not self.env.user.company_id.currency_id.is_zero(line_amount):
    #                 partners_amount[partner_id] += line_amount
    #                 lines.setdefault(partner_id, [])
    #                 lines[partner_id].append({
    #                     'line': line,
    #                     'amount': line_amount,
    #                     'period': i + 1,
    #                     })
    #         history.append(partners_amount)
    #
    #     # This dictionary will store the not due amount of all partners
    #     undue_amounts = {}
    #     query = '''SELECT l.id
    #             FROM account_move_line AS l, account_account, account_move am
    #             WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
    #                 AND (am.state IN %s)
    #                 AND (account_account.internal_type IN %s)
    #                 AND (COALESCE(l.date_maturity,l.date) >= %s)\
    #                 AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
    #             AND (l.date <= %s)
    #             AND l.company_id IN %s
    #             ORDER BY COALESCE(l.date_maturity, l.date)'''
    #     cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
    #     aml_ids = cr.fetchall()
    #     aml_ids = aml_ids and [x[0] for x in aml_ids] or []
    #     for line in self.env['account.move.line'].browse(aml_ids):
    #         partner_id = line.partner_id.id or False
    #         if partner_id not in undue_amounts:
    #             undue_amounts[partner_id] = 0.0
    #         line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
    #         if user_currency.is_zero(line_amount):
    #             continue
    #         for partial_line in line.matched_debit_ids:
    #             if partial_line.max_date <= date_from:
    #                 line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
    #         for partial_line in line.matched_credit_ids:
    #             if partial_line.max_date <= date_from:
    #                 line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
    #         if not self.env.user.company_id.currency_id.is_zero(line_amount):
    #             undue_amounts[partner_id] += line_amount
    #             lines.setdefault(partner_id, [])
    #             lines[partner_id].append({
    #                 'line': line,
    #                 'amount': line_amount,
    #                 'period': 6,
    #             })
    #
    #     for partner in partners:
    #         if partner['partner_id'] is None:
    #             partner['partner_id'] = False
    #         at_least_one_amount = False
    #         values = {}
    #         undue_amt = 0.0
    #         if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
    #             undue_amt = undue_amounts[partner['partner_id']]
    #
    #         total[6] = total[6] + undue_amt
    #         values['direction'] = undue_amt
    #         if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
    #             at_least_one_amount = True
    #
    #         for i in range(5):
    #             during = False
    #             if partner['partner_id'] in history[i]:
    #                 during = [history[i][partner['partner_id']]]
    #             # Adding counter
    #             total[(i)] = total[(i)] + (during and during[0] or 0)
    #             values[str(i)] = during and during[0] or 0.0
    #             if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
    #                 at_least_one_amount = True
    #         values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
    #         ## Add for total
    #         total[(i + 1)] += values['total']
    #         values['partner_id'] = partner['partner_id']
    #         if partner['partner_id']:
    #             #browse the partner name and trust field in sudo, as we may not have full access to the record (but we still have to see it in the report)
    #             browsed_partner = self.env['res.partner'].sudo().browse(partner['partner_id'])
    #             values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
    #             values['trust'] = browsed_partner.trust
    #         else:
    #             values['name'] = _('Unknown Partner')
    #             values['trust'] = False
    #
    #         if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
    #             res.append(values)
    #
    #     return res, total, lines
