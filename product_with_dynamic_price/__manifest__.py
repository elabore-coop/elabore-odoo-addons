# Copyright 2021 Elabore ()
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'product_with_dynamic_price',
    'version': '12.0.2.0.3',
    'author': 'Elabore',
    'maintainer': 'False',
    'website': 'False',
    'license': '',
    'category': 'False',
    'summary': 'Allow customer to customize the product price from website product page',
    'description': """
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3
==========================
product_with_dynamic_price
==========================
This module add an option "dynamic price" in the product template, that allow the customer to modify the price online

Installation
============
Just install product_with_dynamic_price, all dependencies will be installed by default.

Known issues / Roadmap
======================

Bug Tracker
===========
Bugs are tracked on `GitHub Issues
<https://github.com/elabore-coop/elabore-odoo-addons/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------
* Elabore: `Icon <https://elabore.coop/web/image/res.company/1/logo?unique=f3db262>`_.

Contributors
------------
* Stéphan Sainléger <https://github.com/stephansainleger>
* Nicolas Jeudy <https://github.com/njeudy>

Funders
-------
The development of this module has been financially supported by:
* Elabore (https://elabore.coop)
* Mycéliandre (https://myceliandre.fr)

Maintainer
----------
This module is maintained by ELABORE.

""",

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'product',
    ],
    'external_dependencies': {
        'python': [],
    },

    # always loaded
    'data': [
        'views/product_template_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'js': [],
    'css': [],
    'qweb': [],

    'installable': True,
    # Install this module automatically if all dependency have been previously
    # and independently installed.  Used for synergetic or glue modules.
    'auto_install': False,
    'application': False,
}