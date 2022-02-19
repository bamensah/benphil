# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Multi Confirmation',
    'version': '12.0.1',
    'summary': """Allow multi sale order confirmation""",
    'description': """Allow multi sale order confirmation""",
    'category': 'Sale',
    'author': 'KHK',
    'maintainer': 'Optesis',
    'company': 'Optesis SA',
    'website': 'https://www.optesis.com',
    'depends': [
                'sale',
                ],
    'data': [
        'views/sale_order_multi_confirmation_action.xml',
              ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
