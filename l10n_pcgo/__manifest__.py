# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) Optesis 2018 www.optesis.com

{
    'name': 'Syscohada révisé',
    'version': '12.1.2',
    'author': 'Optesis',
    'category': 'Localization',
    'description': """

New Accounting chart for OHADA counrtries.
========================================================================

Ce module permet de gérer le nouveau plan compable SYSCOHADA Révisé applicable à partir du 1er janvier 2018 pour tous les pays faisant partie de l'espace OHADA.


**Credits:** cabinet d'expertise comptable www.kyriex.com.
""",
    'depends': ['base_iban', 'account','account_accountant', 'base_vat', 'account_type_menu'],
    # account_type_menu added to depends in 14 mig
    'data': [
        'data/l10n_pcgo_chart_data.xml',
        'data/account_chart_template_data.xml',
        'views/l10n_pcgo_view.xml',
        'data/account_tax_data.xml',
    ],

}
