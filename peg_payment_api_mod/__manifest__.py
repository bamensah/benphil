# -*- coding: utf-8 -*-
{
    'name': "Payment API Modifications",

    'summary': """
        Modifications for integration with PEG's Payment API""",

    'description': """
        Modifications to the payment model to automate validation of payments
        made through the PEG Payment API
    """,

    'author': "sfiam-coblavie@pegafrica.com",
    'website': "https://pegafrica.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'peg_dev_module'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_inherit.xml',
        'views/payment_api_partner.xml'
    ]
}