# -*- coding: utf-8 -*-
{
    'name': "Send Payslips By Email",
    'license': 'AGPL-3',
    'support': 'support@optima.co.ke',

    'summary': """
        Send Payslips to your Employees via email in a click of a button """,

    'description': """
        This module will assist you to send PDF copies of the payslips to your employee mailbox. You can click a button to send a batch of payslips at once or send one by one
    """,

    'author': "Optima ICT Services LTD",
    'website': "http://www.optima.co.ke",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    # 'images': ['static/description/sendbyemail.png'],
    'category': 'Human Resources',
    'images': ['static/description/main.png'],
    'version': '14.0.1.0',
    'price': 49,
    'currency': 'EUR',

    # any module necessary for this one to work correctly
    'depends': ['hr_payroll', 'mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/email_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
