# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': 'PEG Customization',
    'category': 'Management',
    'version': '14.0.1',
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

    'depends': ['stock', 'contacts', 'repair', 'account', 'crm', 'base', #'phone_validation', 'crm_phone_validation',
                'purchase', 'stock_landed_costs', 'hr_payroll', 'account_reports' # added module used in
                ],

    # |-------------------------------------------------------------------------
    # | Data References
    # |-------------------------------------------------------------------------
    # |
    # | References to all XML data that this module relies on. These XML files
    # | are automatically pulled into the system and processed.
    # |

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        #'security/security.xml',
        'data/product_template_decimal_precision_data.xml',
        'data/contact_type_data.xml',
        'data/user_group_data.xml',
        'wizard/landed_cost_line_make_purchase_order_views.xml',
        'views/sale_template_product_inherit_view.xml',
        'views/sale_inherit_views.xml',
        'views/landed_cost_inherit.xml',
        'views/stock_picking_inherit.xml',
        'views/contact_form_inherit.xml',
        'views/asset_localization_views.xml',
        'views/account_asset_asset_inherit_form.xml',
        'views/payment_term.xml',
        'views/account_move_line_inherit.xml',
        'views/account_payment_inherit.xml',
        'views/product_template_inherit.xml',
        'views/repair_inherit.xml',
        'views/id_type.xml',
        'views/account_partner_inherit.xml',
        'views/vendor_bill_validate_inherit_form.xml',
        'views/res_users_views_inherit.xml',
        'views/account_withhold_payment.xml',
        'views/sale_channel_partner.xml',
        'views/menu_views.xml',
        'wizard/sync_activation_wizard.xml',
        'wizard/bulk_sync_activation_wizard.xml',
        'wizard/bulk_cancel_journal_entry_wizard.xml',
        'views/account_reports_inherit.xml',
        'security/stock_landed_cost_rule.xml',
        'views/account_invoice_tree_with_onboarding_inherit.xml',
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
