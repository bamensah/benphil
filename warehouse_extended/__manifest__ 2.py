# -*- coding: utf-8 -*-
{
    'name': "Warehouse Extended",

    'summary': """ Warehouse extended is divided from the peg_dev_module of v12 to get more module visibility""",

    'description': """
        Warehouse extended is divided from the peg_dev_module of v12 to get more module visibility by PEG Africa partner 
        developer """,

    'author': "mayanknailwal298@gmail.com",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '1.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/rules.xml',
        # 'views/helpdesk.xml',
        # 'views/partner_view.xml',
        # 'views/menu.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'auto-install': True
}
