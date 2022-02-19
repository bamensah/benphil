# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': 'PEG Customization',
    'category': 'Management',
    'version': '12.0.15',
    'author': 'Optesis SA - Robilife',
    'website': "www.optesis.sn",

    'summary': """PEG Customization""",

    'description': """
                -
                - 
                - 
        """,


    # |-------------------------------------------------------------------------
    # | Dependencies
    # |-------------------------------------------------------------------------
    # |
    # | References of all modules that this module depends on. If this module
    # | is ever installed or upgrade, it will automatically install any
    # | dependencies as well.
    # |

    'depends': ['sh_sales_custom_product_template', 'stock', 'contacts'],

    # |-------------------------------------------------------------------------
    # | Data References
    # |-------------------------------------------------------------------------
    # |
    # | References to all XML data that this module relies on. These XML files
    # | are automatically pulled into the system and processed.
    # |

    'data': [
        'security/ir.model.access.csv',
        'data/product_template_decimal_precision_data.xml',
        'data/contact_type_data.xml',
        'views/menu_views.xml',
        'wizard/landed_cost_line_make_purchase_order_views.xml',
        'views/sale_template_product_inherit_view.xml',
        'views/sale_inherit_views.xml',
        'views/landed_cost_inherit.xml',
        'views/stock_picking_inherit.xml',
        'views/contact_form_inherit.xml',
        'views/asset_localization_views.xml',
        'views/account_asset_asset_inherit_form.xml'
    ],

    # |-------------------------------------------------------------------------
    # | Demo Data
    # |-------------------------------------------------------------------------
    # |
    # | A reference to demo data
    # |

    'demo': [],

    # |-------------------------------------------------------------------------
    # | Is Installable
    # |-------------------------------------------------------------------------
    # |
    # | Gives the user the option to look at Local Modules and install, upgrade
    # | or uninstall. This seems to be used by most developers as a switch for
    # | modules that are either active / inactive.
    # |

    'installable': True,

    # |-------------------------------------------------------------------------
    # | Auto Install
    # |-------------------------------------------------------------------------
    # |
    # | Lets Odoo know if this module should be automatically installed when
    # | the server is started.
    # |

    'auto_install': True,
}