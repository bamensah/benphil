{
    "name": "Studio Customization ",
    "summary": """Fields and model added from v12 system to v14 """,
    "category": "API",
    "version": "14.0.1",
    "sequence": 1,
    "author": "Mayank Nailwal",
    "license": "Other proprietary",
    "website": "",
    "description": """Fields and model added from v12 system to v14""",
    "depends": ['base', 'account_analytic_parent', 'purchase', 'sale_management', 'stock', 'base_geolocalize'],
    "data": [
            "views/picking_view.xml",
            "views/product_view_inherit.xml",
            "views/account_analytic_view.xml",
            "views/res_partner_view.xml",
            "views/purchase_view.xml",
            "views/sale_order_view.xml",
            "views/menu_item.xml",
    ],
    # "qweb": ['static/src/xml/voucher_process_dashboard.xml'],
    # "images"               :  ['static/description/Banner.png'],
    "application": True,
    "installable": True,
    "auto_install": False,
}
# -*- coding: utf-8 -*-
#################################################################################
