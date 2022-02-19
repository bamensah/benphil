# -*- coding: utf-8 -*-
# by khk
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrPayslipEmployeeInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    # @api.multi
#    def compute_sheet(self):
#        payslips = self.env['hr.payslip']
#        [data] = self.read()
#        active_id = self.env.context.get('active_id')
#        if active_id:
#            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
#        from_date = run_data.get('date_start')
#        to_date = run_data.get('date_end')
#        if not data['employee_ids']:
#            raise UserError(_("You must select employee(s) to generate payslip(s)."))
#        for employee in self.env['hr.employee'].browse(data['employee_ids']):
#            for empl_contract in self.env['hr.contract'].search(
#                    [('employee_id', '=', employee.id)], order='id desc', limit=1):  # add by khk
#                #if empl_contract.date_start <= from_date:  # add by khk
#                slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id,
#                                                                        contract_id=False)
#                res = {
#                    'employee_id': employee.id,
#                    'name': slip_data['value'].get('name'),
#                    'struct_id': slip_data['value'].get('struct_id'),
#                    'contract_id': slip_data['value'].get('contract_id'),
#                    'payslip_run_id': active_id,
#                    'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
#                    'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
#                    'date_from': from_date,
#                    'date_to': to_date,
#                    'credit_note': run_data.get('credit_note'),
#                    'company_id': employee.company_id.id,
#                }
#                if empl_contract.date_end:
#                    if from_date <= empl_contract.date_end:
#                        payslips += self.env['hr.payslip'].create(res)
#                else:
#                    payslips += self.env['hr.payslip'].create(res)
#                    
#                #
#                
#        payslips.compute_sheet()
#        return {'type': 'ir.actions.act_window_close'}
    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': from_date.strftime('%B %Y'),
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        if not self.employee_ids:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = self.employee_ids._get_contracts(payslip_run.date_start, payslip_run.date_end, states=['open', 'close'])
        contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', self.employee_ids.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                raise UserError(_("Some work entries could not be validated."))


        default_values = Payslip.default_get(Payslip.fields_get())
        for contract in contracts:
            values = dict(default_values, **{
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            })
            payslip = self.env['hr.payslip'].new(values)
            payslip._onchange_employee()
            values = payslip._convert_to_write(payslip._cache)
            payslips += Payslip.create(values)
        payslips.compute_sheet()
        #payslip_run.state = 'verify'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }

