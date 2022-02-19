# -*- coding: utf-8 -*-
{
    'name': "PEG Account Journal Modifications",
    'summary': """
        Modifications to the Account Journal Entries and Due Report""",

    'description': """
        Customization to let the Account Journal Entries store the Due Type so it can be used by the Due Report.
        The 2nd phase included the rebuild of the Due Report to show more requested fields.
    """,

    'author': "sfiam-coblavie@pegafrica.com",
    'website': "https://www.pegafrica.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'account', # added for 14 mig for temp
                # 'wave2_peg_africa', removed for 14 mig for temp
                # 'peg_custom_sale_orders' removed for 14 mig for temp
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}