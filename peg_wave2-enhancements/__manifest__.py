# -*- coding: utf-8 -*-
{
    'name': "PEG wave2-enhancements",

    'summary': """
        Extending the wave2 modifications""",

    'description': """
        wave2_peg_africa module has centralized all other modules by depending on all of them. 
        This module will safely extend it as its author is still IT4Life 
    """,

    'author': "PEG Africa",
    'website': "https://pegafrica.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','wave2_peg_africa', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sales_product_template_inherit.xml',
        'views/sale_order_inherit.xml',
        'views/res_partner.xml',
        'views/stock_production_lot.xml',
        'data/contact_relationship_data.xml',
        'data/automated_actions.xml',
        'views/account_payment_unblock_wizard.xml'
    ],
    # only loaded in demonstration mode
}