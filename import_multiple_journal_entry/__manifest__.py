# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Import Multiple Journal Entries from CSV or Excel File in Odoo',
    'version': '14.0.0.1',
    'sequence': 4,
    'price': 29,
    'currency': "EUR",
    'category': 'Accounting',
    'summary': 'Import Data App for import journal entry import account move line import account move import mass journal entries import multiple journal entries excel import journal entry excel import accounting entry  import opening journal entry import opening balance',
    'description': """
	Used to 
    odoo import the multiple journal entry from the xls or csv data file import accounting transection from CSV import odoo
    odoo Import journal entry from CSV import journal item from CSV import accouting data from CSV import account move from CSV import odoo
    odoo import account move line from CSV import accounting transection from Excel Import journal entry from Excel import odoo 
    odoo import journal item from Excel import accouting data from Excel import account move from Excel import account move line from Excel import odoo
	odoo import accounting transection from XLS Import journal entry from XLS import journal item from XLS import accouting data from XLS import account move from XLS import
    odoo import account move line from XLS import odoo journal entry import
    odoo import Multiple journal entry Import Multiple Journal Entries import Multi-ple journal entry Import Multi-ple Journal Entries
    odoo import bulk journal entries bulk joural entry import import bulk journal entry bulk joural entries import
استيراد محاسبة المحاسب من CSV ، استيراد إدخال دفتر اليومية من CSV ، استيراد عنصر دفتر اليومية من CSV ، استيراد بيانات الحصة من CSV ، نقل حساب الاستيراد من CSV ، خط نقل حساب الاستيراد من CSV.
استيراد محاسبة المحول من Excel ، استيراد إدخال دفتر اليومية من Excel ، عنصر دفتر يومية الاستيراد من Excel ، استيراد بيانات الحصة من Excel ، نقل حساب الاستيراد من Excel ، خط نقل حساب الاستيراد من Excel.
استيراد المحاسبة transection من XLS ، استيراد إدخال دفتر اليومية من XLS ، استيراد بند المجلة من XLS ، استيراد بيانات الحصة من XLS ، نقل حساب الاستيراد من XLS ، خط نقل حساب الاستيراد من XLS.

Usado para importar a entrada de diário do arquivo de dados xls ou csv.
importar transição contábil da CSV, importar diário de CSV, importar item do jornal de CSV, importar dados de cadastro de CSV, importar a conta, mover-se do CSV, importar a linha de movimento da conta de CSV.
importar transação contábil do Excel, importar entrada do diário do Excel, importar o item do jornal do Excel, importar dados de cadastro do Excel, importar a parte da conta do Excel, importar a linha de mover a conta do Excel.
importar transição contábil da XLS, importar entrada de jornal de XLS, importar item de jornal de XLS, importar dados de caducidade de XLS, importar conta mover de XLS, importar linha de movimento de conta de XLS.

Utilisé pour importer l'entrée de journal à partir du fichier de données xls ou csv.
importer la comptabilisation à partir de CSV, importer une entrée de journal à partir de CSV, importer un élément de journal à partir de CSV, importer des données de comptabilité à partir de CSV, importer un compte à partir de CSV, importer une ligne de CSV.
Importer une section de comptabilité à partir d'Excel, Importer une entrée de journal à partir d'Excel, importer un article de journal à partir d'Excel, importer des données d'Excel, importer un compte depuis Excel, importer une ligne de compte à partir d'Excel.
importer la comptabilité de XLS, importer une entrée de journal depuis XLS, importer un article de journal depuis XLS, importer des données de comptabilité depuis XLS, importer un compte depuis XLS, importer une ligne de déplacement de compte depuis XLS.

Se usa para importar la entrada del diario desde el archivo de datos xls o csv.
importar la transección de contabilidad desde CSV, Importar entrada de diario desde CSV, Importar artículo de diario desde CSV, Importar datos de asignación desde CSV, Importar movimiento de cuenta desde CSV, Importar mover línea desde CSV.
importar la sección de contabilidad desde Excel, importar la entrada de diario de Excel, importar el artículo de diario de Excel, importar los datos de asignación de Excel, importar mover la cuenta de Excel, importar la línea de movimiento de cuenta desde Excel.
importe la transección de contabilidad de XLS, importe la entrada de diario de XLS, importe el artículo de diario de XLS, importe los datos de asignación de XLS, importe el movimiento de la cuenta de XLS, importe la línea de movimiento de la cuenta de XLS.

    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.in',
    'depends': ['base','sale_management','account'],
    'data': [
            'security/ir.model.access.csv',
            'wizard/account_move.xml'
        ],
    'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
    'live_test_url':'https://youtu.be/xOX9UCs6Jlk',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
