# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Payslip inputs : Csv mass upload",
  "summary"              :  """This module helps to easily import payslip inputs""",
  "category"             :  "Marketing",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "website"              :  "https://store.webkul.com/Odoo-Payslip-Inputs-CSV-Mass-Upload.html",
  "description"          :  """This module helps to easily import payslip inputs""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=payslip_input_csv_upload",
  "depends"              :  ['hr_payroll', 'hr_work_entry_contract'],
  "data"                 :  ['views/payslip_view.xml'],
  # "demo"                 :  ['demo/demo_data.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  10,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
