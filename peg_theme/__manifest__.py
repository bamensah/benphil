# -*- coding: utf-8 -*-
{
    'name': "PEG Theme",

    'summary': """
        Theme specific to PEG Africa""",

    'description': """
        Theme specific to PEG Africa
    """,

    'author': "PEG Africa",
    'website': "https://pegafrica.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Theme',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['web','web_enterprise'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}