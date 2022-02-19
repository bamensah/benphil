# See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock Picking Cancel',
    'version': '14.0.0.1.0',
    'license': 'AGPL-3',
    'author': 'ERP Labz',
    'maintainer': 'ERP Labz',
    'summary': 'Cancel SO/PO Picking',
    'description': """
    Click on Cancel button to do picking cancel when state 'Done'
    """,
    'website': 'https://erplabz.com/',
    'category': 'Warehouse',
    'images': [],
    'depends': ['stock'],
    'data': [
        'security/security.xml',
        'views/stock_picking_views.xml',
    ],
    'demo': [],
    "images": ['static/description/icon.png'],
    'price': 35,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False,
}
