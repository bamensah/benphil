# -*- coding: utf-8 -*-
{
    'name': "peg_africa_website",

    'summary': """
        Extension for Website Module to capture relevant information
        from leads""",

    'description': """
        Extends website module by adding more fields to the website contact form
    """,

    'author': "dattuah@pegafrica.com",
    'website': "https://www.pegafrica.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website_form', 'website_partner', 'crm', 'website_crm', 'wave2_peg_africa'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',

        'data/peg_africa_website_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}