# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Payroll (Odoo 14 Community)",
  "summary"              :  "Manage your employee payroll records",
  "category"             :  "Human Resources",
  "version"              :  "1.0.0",
  "author"               :  "Webkul Software Pvt. Ltd., Odoo S.A.",
  "website"              :  "https://store.webkul.com/",
  "live_test_url"        :  "",
  "description"          :  """""",
  "depends"              :  [
                             'hr_contract',
                             'hr_holidays',
                            ],
  "data"                 :  [
                             'security/security.xml',
                             'security/ir.model.access.csv',
                             'wizard/wk_hr_payroll_payslips_by_employees_views.xml',
                             'views/hr_contract_views.xml',
                             'views/wk_hr_payroll_structure_views.xml',
                             'views/wk_hr_salary_rule_category_views.xml',
                             'views/wk_hr_contribution_register_views.xml',
                             'views/wk_hr_salary_rule_views.xml',
                             'views/wk_hr_payslip_line_views.xml',
                             'views/wk_hr_payslip_views.xml',
                             'views/wk_hr_payslip_run_views.xml',
                             'views/hr_employee_views.xml',
                             'data/hr_payroll_sequence.xml',
                             'views/wk_hr_payroll_report.xml',
                             'data/hr_payroll_data.xml',
                             'wizard/wk_hr_payroll_contribution_register_report_views.xml',
                             'views/res_config_settings_views.xml',
                             'views/report_contributionregister_templates.xml',
                             'views/report_payslip_templates.xml',
                             'views/report_payslipdetails_templates.xml',
                            ],
  "demo"                 :  [
                             'data/hr_payroll_demo.xml'
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "pre_init_hook"        :  "pre_init_check",
}
