# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'IT Модуль синхронизации с AD, 1С:ЗУП, JMS',
    "author": "Savrasov Mikhail <savrasovmv@tmenergo.ru> ",
    "website": "https://github.com/savrasovmv/",
    'version': '14',
    'category': 'HR',
    'sequence': 15,
    'summary': 'Синхронизация сотрудников с 1С и AD',
    'description': "Загружает информацию из 1С:ЗУП используя рзработанное api: сотрудники, подрзделения, документы: удостоверения личности, адреса, прием на работу, увольнение, отпуска, командировки, больничные. \n Згружает информацию из AD: пользователей, группы. Создет и изменяется пользователей AD, в соответствии с изменениями сотрудников 1С:ЗУП. ",
    'external_dependencies': {
        'python': [
            'requests', 
            'ldap3',
            'unidecode',
            'random',
            ]},
    'depends': [
        'base',
        'mail',
        'it_hr',
        'it_ad_base'
    ],
    'data': [
        
        'views/settings_views.xml',
        'wizard/sync_wizard_views.xml',
        'views/sync_log_views.xml',
        'views/sync_tasks_views.xml',
        'cron/cron_ad_group_sync_views.xml',
        'views/menu.xml',
        'views/tasks_mail_templates.xml',

        'security/ir.model.access.csv',

    ],

    'installable': True,
    'application': True,
    'auto_install': False
}