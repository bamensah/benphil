# -*- coding: utf-8 -*-
{
    'name': "Helpdesk PEG Mods",

    'summary': """
        All modifications of the Helpdesk module and 
        other related features and function by PEG Africa""",

    'description': """
        All modifications of the Helpdesk module and other related features and function by PEG Africa
    """,

    'author': "sfiam-coblavie@pegafrica.com",
    'website': "https://pegafrica.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customer Relationship Management',
    'version': '2.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'helpdesk', 'sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/helpdesk.xml',
        'views/res_partner.xml',
        'views/menu.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'auto-install': True
}
