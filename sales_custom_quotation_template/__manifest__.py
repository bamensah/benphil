# -*- coding: utf-8 -*-
{
    'name': "Sales Custom Quatation Template",

    'summary': """ Sales Custom Quatation Template""",

    'description': """
        Sales Custom Quatation Template """,

    'author': "mayanknailwal298@gmail.com",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '1.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'product', 'sale_management'],

    # always loaded
    'data': [
        'views/sale_order_template_line_view.xml',
        'views/sale_order_view.xml',
        ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'auto-install': True
}
