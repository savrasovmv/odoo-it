# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'ActiveDirectory базовый модуль',
    'version': '1',
    'category': 'SM',
    "author": "Savrasov Mikhail <savrasovmv@tmenergo.ru> ",
    "website": "https://github.com/savrasovmv/",
    'sequence': 15,
    'summary': 'Базовый модуль для ActiveDirectory',
    'description': "Создает модели пользователей и групп из ActiveDirectory",
    'depends': [
        # 'base_setup',
        'base',
        'web',
        # 'website'
        'fetchmail',
    ],
    'data': [
        
        # 'views/ad_organizacion_views.xml',
        'views/ad_organizacion_views.xml',
        'views/ad_ou_views.xml',
        'views/ad_department_views.xml',
        'views/ad_users_views.xml',
        'views/ad_group_views.xml',
        'views/set_group_views.xml',
        'views/mailbox_views.xml',
        'views/jms_event_log_views.xml',
        'wizard/jms_wizard_views.xml',
        'reports/jms_report_views.xml',

        # 'views/ad_sync_wizard_view.xml',
        'views/menu.xml',
        # 'views/templates_head.xml',
        # 'views/templates_list.xml',
        # 'views/templates_list_search.xml',
        # 'views/templates.xml',
        
        'security/ad_security.xml',
        'security/ir.model.access.csv',

    ],

    'js': [
        #'static/src/js/toggle_widget.js',
        # 'static/src/js/disabled_copy.js',
    ],

    'css': [
        'static/src/css/uit_base.css',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}