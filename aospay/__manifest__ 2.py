## -*- coding: utf-8 -*-
###################################################################################

#   AOS payroll module                                                                                 
###################################################################################

{
    'name': 'AOSpay',
    'version': '14.0.30',
    'summary': """Gérez les salaires de vos employés""",
    'description': """Ce module vous permet de gérer les salaires selon la loi Malienne""",
    'category': 'Human Resources',
    'author': 'AOS SARL',
    'maintainer': 'AOS',
    'company': 'AOS SARL',
    'website': 'https://www.aosmali.com',
    'depends': [
                 'base', 'hr', 'hr_payroll', 'account_accountant','hr_contract', 'hr_holidays', 'hr_payroll_account', 
                ],
    'data': [
    'security/aos_pay_security.xml',
    'security/ir.model.access.csv',
    'views/convention_view.xml',
    'views/res_company_extend_view.xml',
    'views/hr_contract_extend_view.xml',
    'views/hr_employee_extend_view.xml',
    'views/bulletin_paie.xml',
    'data/aospay_data.xml',
        
              ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
