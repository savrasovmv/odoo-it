# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Склад. управление активами и материалами",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Savrasov Mikhail <savrasovmv@tmenergo.ru> ",
    "website": "https://github.com/savrasovmv/",
    "category": "Stock",
    "summary": "Склад. управление активами и материалами",
    "depends": ["hr"],
    "data": [
        "views/sklad.xml",
        'security/sklad_security.xml',
        'security/ir.model.access.csv',

        "data/sequence_data.xml",
        "views/menu.xml",
        ],
    "installable": True,
}
