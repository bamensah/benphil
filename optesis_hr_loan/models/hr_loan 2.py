# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
log = logging.getLogger('Log')


class HrLoan(models.Model):
    _name = "hr.loan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"
    _description = "Demande de pret"

    _track = {

        'state': {
            'optesis_hr_loan.mt_loan_submit': lambda self, cr, uid, obj, ctx=None: obj.state == 'submit',
            'optesis_hr_loan.mt_hr_loan_approve_1': lambda self, cr, uid, obj, ctx=None: obj.state == 'approve_1',
            'optesis_hr_loan.mt_hr_loan_valid': lambda self, cr, uid, obj, ctx=None: obj.state == 'approve',
            'optesis_hr_loan.mt_hr_expense_refuse': lambda self, cr, uid, obj, ctx=None: obj.state == 'refuse',
        },
    }

    # @api.one
    def _compute_amount(self):
        total_paid_amount = 0.00
        for loan in self:
            for line in loan.loan_line_ids:
                if line.paid == True:
                    total_paid_amount += line.paid_amount

            balance_amount = loan.loan_amount - total_paid_amount
            self.total_amount = loan.loan_amount
            self.balance_amount = balance_amount
            self.total_paid_amount = total_paid_amount

    # @api.one
    def _get_old_loan(self):
        old_amount = 0.00
        for loan in self.search([('employee_id', '=', self.employee_id.id)]):
            if loan.id != self.id:
                old_amount += loan.balance_amount
        self.loan_old_amount = old_amount

    # @api.multi
    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'refuse'):
                raise Warning(('Impossible de supprimer un Prêt approuvé.'))

        return super(HrLoan, self).unlink()

    #@api.onchange('type')
    #def on_type_change(self):
    #    if self.type:
    #        type = self.env['hr.loan.type'].browse(self.type.id)
    #        self.emp_account_id = type.emp_account_id
    #        self.treasury_account_id = type.treasury_account_id
    #        self.journal_id = type.journal_id

    # @api.one
    def _get_code_loan(self):
        self.name = 'Prêt N° ' +'{0:04}'.format(self.id)

    @api.model
    def create(self, vals):
        loan = super(HrLoan, self).create(vals)
        loan._get_code_loan()
        return loan

    name = fields.Char(string="N° du prêt", default="/", readonly=True)
    date = fields.Date(string="Date de la demande", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employé", required=True)
    parent_id = fields.Many2one('hr.employee', related="employee_id.parent_id", string="Manager")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Départment")
    job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Titre du poste")
    loan_old_amount = fields.Float(string="Montant de prêt non payé", compute='_get_old_loan')
    emp_account_id = fields.Many2one('account.account', string="Compte créditeur", readonly=True)
    treasury_account_id = fields.Many2one('account.account', string="Compte débiteur", readonly=True)
    journal_id = fields.Many2one('account.journal', string="Journal")
    loan_amount = fields.Float(string="Montant du prêt", required=True)
    total_amount = fields.Float(string="Montant total", readonly=True, compute='_compute_amount')
    balance_amount = fields.Float(string="Montant solde", compute='_compute_amount')
    total_paid_amount = fields.Float(string="Montant total payé", compute='_compute_amount')
    no_month = fields.Integer(string="Nombre de mois", default=1)
    payment_start_date = fields.Date(string="Date début de paiement", required=True)
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string="Lignes de prêt", index=True)
    entry_count = fields.Integer(string="Entry Count", compute='compute_entery_count')
    move_id = fields.Many2one('account.move', string="Entry Journal", readonly=True)
    approvers = fields.One2many('hr.loan.approver', 'loan_id', string='Approvers')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Soumis'),
        ('approve_1', 'Approbation 1'),
        ('approve', 'Validé'),
        ('refuse', 'Rejeté'),
    ], string="State", default='draft', track_visibility='onchange', copy=False)
    type = fields.Many2one('hr.loan.type', string=u"Type de Prêt", required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.user.company_id)
    comment = fields.Text(string="Commentaire")


    def _add_employee_notification(self):
        print (">>>>>>>>>>>>>>>>>>>>>>>>>")
        self.message_subscribe(partner_ids=self.employee_id.user_id.partner_id.ids)

    # @api.multi
    def action_submit(self):
        for loan in self:
            if not self.loan_line_ids:
                raise except_orm('Warning', 'Veuillez cliquer le bouton caluler avant de soumettre')

            self.env['hr.loan.approver'].create({
            'loan_id': loan.id,
            'user_id': self.env.uid, 'date_approved': fields.Datetime.now(), 'state': 'submit'})
            loan._add_employee_notification()
        return self.write({'state': 'submit'})


    # @api.multi
    def action_approve_1(self):
        self._add_employee_notification()

        self.env['hr.loan.approver'].create({
            'loan_id': self.id,
            'user_id': self.env.uid, 'date_approved': fields.Datetime.now(), 'state': 'approved'})
        return self.write({'state': 'approve_1'})


    # @api.multi
    def action_refuse(self):
        self.write({'state': 'refuse'})


    # @api.multi
    def action_validate(self):

        self.env['hr.loan.approver'].create({
            'loan_id': self.id,
            'user_id': self.env.uid, 'date_approved': fields.Datetime.now(), 'state': 'approved'})
        self.write({'state':'approve'})


    # @api.one
    def action_set_to_draft(self):
        self.state = 'draft'


    # @api.multi
    def onchange_employee_id(self, employee_id=False):
        old_amount = 0.00
        if employee_id:
            for loan in self.search([('employee_id', '=', employee_id)]):
                if loan.id != self.id:
                    old_amount += loan.balance_amount
            return {
                'value': {
                    'loan_old_amount': old_amount}
            }


    # @api.one
    @api.constrains('no_month')
    def _check_month(self):
        if self.no_month <= 0:
            raise Warning(_(u"Le nombre de mois doit être supérieur à 0."))


    # @api.one
    def action_approve(self):

        #move_obj = self.env['account.move']
        for loan in self:
            self.env['hr.loan.approver'].create({
                'loan_id': self.id, 'user_id': self.env.uid, 'date_approved': fields.Datetime.now(), 'state': 'approved'})
            self.write({'state': 'approve'})
        return True


    # @api.multi
    def compute_loan_line(self):
        loan_line = self.env['hr.loan.line']
        loan_line.search([('loan_id', '=', self.id)]).unlink()
        for loan in self:
            date_start_str = datetime.strptime(str(loan.payment_start_date), '%Y-%m-%d')
            counter = 1
            amount_per_time = loan.loan_amount / loan.no_month
            for i in range(1, loan.no_month + 1):
                line_id = loan_line.create({
                    'paid_date': date_start_str,
                    'paid_amount': amount_per_time,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                counter += 1
                date_start_str = date_start_str + relativedelta(months=1)

        return True


    @api.model
    # @api.multi
    def compute_entery_count(self):
        count = 0
        entry_count = self.env['account.move.line'].search_count([('loan_id', '=', self.id)])
        self.entry_count = entry_count


    # @api.multi
    def button_reset_balance_total(self):
        total_paid_amount = 0.00
        for loan in self:
            for line in loan.loan_line_ids:
                if line.paid == True:
                    total_paid_amount += line.paid_amount
            balance_amount = loan.loan_amount - total_paid_amount
            self.write({'total_paid_amount': total_paid_amount, 'balance_amount': balance_amount})


class HrLoanApprobation(models.Model):
        _name = "hr.loan.approver"
        _order = "id desc"
        _description = "loan approver class"

        user_id = fields.Many2one('res.users', string='Utilisateur', required=True)
        loan_id = fields.Many2one('hr.loan', string='Demande')
        comment = fields.Text(string='Commentaire')
        state = fields.Selection([('submit', 'Soumis'), ('approved', 'Approuvé'), ('cancel', 'Refusé')], string="Statut")
        date_approved = fields.Datetime(string="Date")


class hrEmployee(models.Model):
        _inherit = "hr.employee"

        # @api.one
        def _compute_loans(self):
            count = 0
            loan_remain_amount = 0.00
            loan_ids = self.env['hr.loan'].search([('employee_id', '=', self.id)])
            for loan in loan_ids:
                loan_remain_amount += loan.balance_amount
                count += 1
            self.loan_count = count
            self.loan_amount = loan_remain_amount

        loan_amount = fields.Float(string="Montant du prêt", compute='_compute_loans')
        loan_count = fields.Integer(string="Loan Count", compute='_compute_loans')


class LoanLine(models.Model):
    _name = "hr.loan.line"
    _description = "HR Loan Request Line"

    paid_date = fields.Date(string="Date paiement", required=True)
    loan_id = fields.Many2one('hr.loan', string="Ref. Prêt", required=True, ondelete='cascade')

    employee_id = fields.Many2one(related="loan_id.employee_id", string="Employé")
    loan_type = fields.Many2one(related="loan_id.type", string="Type")
    paid_amount = fields.Float(string="Montant à payer", required=True)
    paid = fields.Boolean(string="Payé")
    notes = fields.Text(string="Notes")
    payroll_id = fields.Many2one('hr.payslip', string="Payslip Ref.")

    # @api.multi
    def action_paid_amount(self):
        self.write({'paid': True})


class hr_loan_type(models.Model):
        _name = "hr.loan.type"
        _description = "loan type class"

        name = fields.Char('Nom', required=True)
        code = fields.Char('Code', size=64, required=True)
        emp_account_id = fields.Many2one('account.account', string="Compte de prêt")
        treasury_account_id = fields.Many2one('account.account', string="Compte de trésorerie")
        journal_id = fields.Many2one('account.journal', string="Journal")
        company_id = fields.Many2one('res.company', string="Société", required=True)

        @api.model
        def create(self, vals):
            loan_type_id = super(hr_loan_type, self).create(vals)
            structures = self.env['hr.payroll.structure'].search([])
            category_id = (self.env['hr.salary.rule.category'].search([('code', '=', 'DED')])[0]).id
            python_code = """result = 0
if payslip.loan_ids:
    for line in payslip.loan_ids:
        if line.loan_id.type.id == %s:
            if line.paid is False:
                result += line.paid_amount""" % (loan_type_id.id)

            condition = """total_amount = 0
if payslip.loan_ids:
    for line in payslip.loan_ids:
        if line.loan_id.type.id == %s:
            if line.paid is False:
                total_amount += line.paid_amount
    result = total_amount > 0""" % (loan_type_id.id)

            salary_rule_vals = {
                'name': vals['name'],
                'sequence': "19",
                'code': vals['code'],
                'category_id': category_id,
                'condition_select': 'python',
                'amount_select': 'code',
                'amount_python_compute': python_code,
                'condition_python': condition,
                'struct_id': structures[0].id
            }
            rule_id = self.env['hr.salary.rule'].sudo().create(salary_rule_vals)
#            rule_id.struct_id = structures[0].id
            #for structure in structures:
            #    structure.write({'rule_ids': [(4, rule_id.id)]})
            return loan_type_id


class account_move_line(models.Model):
        _inherit = "account.move.line"

        loan_id = fields.Many2one('hr.loan', string="Prêts")
