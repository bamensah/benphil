## -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude  (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#                                                                                 
###################################################################################

{
    'name': 'Optipay',
    'version': '12.0.26',
    'summary': """Gérez vos dossiers de paie salariale""",
    'description': """""",
    'category': 'Human Resources',
    'author': 'Optesis SA, Robilife',
    'maintainer': 'Optesis',
    'company': 'Optesis SA',
    'website': 'https://www.optesis.com',
    'depends': [
                'base', 'hr', 'hr_payroll', 'hr_contract', 'hr_payroll_account', 'optesis_hr_loan',
                ],
    'data': [
        'static/src/css/my_css.xml',
        'security/ir.model.access.csv',
        'security/optipay_security.xml',
        'wizard/payslip_simul_wizard_views.xml',
        'views/custom_external_layout_bulletin.xml',
        'views/employee_bonus_view.xml',
        'views/report_declaration_retenues.xml',
        'views/report_transfer_order.xml',
        'views/report_cotisation_ipres.xml',
        'views/report_securite_sociale.xml',
        'views/convention_view.xml',
        'data/employee_scheduler.xml',
        'views/account_move_view.xml',
        'views/payslip_batches_action.xml',
        'views/net_salary_to_payslip.xml',
        'views/batch_payslip_fixed.xml',
        'data/custom_paper_format.xml',
        'data/custom_format_paper_bulletin.xml',
        'views/bulletin_paie.xml',
        'views/hr_salary_rule_inherit_view.xml',
        'views/res_company_inherit_view.xml',
        'views/detail_versement.xml',
        'views/report_dads_page1.xml',
        'views/report_dads_page2.xml',
        'views/res_config_settings_inherit_view.xml',
        'wizard/securite_sociale.xml',
        'wizard/cotisation_ipres.xml',
        'wizard/declaration_retenues.xml',
        'wizard/dads.xml',
        'wizard/transfer_order.xml',
        'views/menu_reports_payslip.xml',
              ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
