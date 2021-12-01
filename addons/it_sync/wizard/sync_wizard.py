# -*- coding: utf-8 -*-

from odoo import fields, models, api
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, LEVEL
import json
import base64

class SyncWizard(models.TransientModel):
    _name = 'sync.wizard'
    _description = "Wizard обновление с AD и ЗУП"

    result = fields.Text(string='Результат')
    full_sync = fields.Boolean(string='Полная синхронизация')
    start_date = fields.Date(string='Дата начала')
    end_date = fields.Date(string='Дата окончания')

    def return_result(self, error=False):
        """Возвращает ошибку или результат выполнения действия"""

        if error:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Прерванно'),
                    'message': error,
                    'type':'warning',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                },
            }
            return notification
        else:
            return {
				'name': 'Message',
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'sync.wizard',
				'target':'new',
				'context':{
							'default_result':self.result,
							} 
				}


    def ad_sync_group_wizard_action(self):
        #res = self.ad_sync_group_action()
        try:
            self.result = self.env['ad.sync_group'].sudo().ad_sync_group(full_sync=self.full_sync)
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()

    def ad_sync_users_wizard_action(self):
        #res = self.ad_sync_group_action()
        try:
            self.result = self.env['ad.sync_users'].sudo().ad_sync_users(full_sync=self.full_sync)
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()

    def join_user_and_employee_wizard_action(self):
        try:
            self.result = self.env['ad.users'].sudo().join_user_and_employee(full_sync=self.full_sync)
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()

    def zup_sync_dep_wizard_action(self):
        try:
            self.result = self.env['zup.sync_dep'].sudo().zup_sync_dep()
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()

    def zup_sync_employer_wizard_action(self):
        try:
            self.result = self.env['zup.sync_employer'].sudo().zup_sync_employer()
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()

    def zup_sync_passport_wizard_action(self):
        try:
            self.result = self.env['zup.sync_passport'].sudo().zup_sync_passport()
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()


    def zup_sync_personal_doc_wizard_action(self):
        # self.result = self.env['zup.sync_personal_doc'].sudo().zup_sync_personal_doc_full(self.start_date, self.end_date)
        try:
            self.result = self.env['zup.sync_personal_doc'].sudo().zup_sync_personal_doc_full(self.start_date, self.end_date)
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()

    def update_employer_status_wizard_action(self):
        try:
            self.env['hr.employee'].sudo().search([]).get_status()
            self.result = 'Обновился статус состояния сотрудников'
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()

    
    def zup_sync_personal_doc_change_wizard_action(self):
        # self.result = self.env['zup.sync_personal_doc'].sudo().zup_sync_personal_doc_change()
        try:
            self.result = self.env['zup.sync_personal_doc'].sudo().zup_sync_personal_doc_change()
        except Exception as error:
            return self.return_result(error=error)
        
        return self.return_result()


    # def _ldap_search(self, full_sync=False, date=False, attributes=False):
    #      #     #Подключение к серверу AD
    #     LDAP_HOST = self.env['ir.config_parameter'].sudo().get_param('ldap_host')
    #     LDAP_PORT = self.env['ir.config_parameter'].sudo().get_param('ldap_port')
    #     LDAP_USER = self.env['ir.config_parameter'].sudo().get_param('ldap_user')
    #     LDAP_PASS = self.env['ir.config_parameter'].sudo().get_param('ldap_password')
    #     LDAP_SSL = self.env['ir.config_parameter'].sudo().get_param('ldap_ssl')
    #     LDAP_SEARCH_BASE = self.env['ir.config_parameter'].sudo().get_param('ldap_search_base')
    #     LDAP_SEARCH_FILTER = self.env['ir.config_parameter'].sudo().get_param('ldap_search_filter')
    #     LDAP_SEARCH_GROUP_FILTER = self.env['ir.config_parameter'].sudo().get_param('ldap_search_group_filter')

    #     if LDAP_HOST and LDAP_PORT and LDAP_USER and LDAP_PASS and LDAP_SSL and LDAP_SEARCH_BASE and LDAP_SEARCH_FILTER and LDAP_SEARCH_GROUP_FILTER:
    #         pass
    #     else:
    #         self.env['sync.log'].sudo().create({'name': 'Группы AD', 'is_error': True, 'result': 'Нет учетных данных для подключения'})
    #         notification = {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': ('Прерванно'),
    #                 'message': 'Нет учетных данных для подключения',
    #                 'type':'warning',  #types: success,warning,danger,info
    #                 'sticky': False,  #True/False will display for few seconds if false
    #             },
    #         }
    #         return notification
    #     try:
    #         ldap_server = Server(host=LDAP_HOST, port=int(LDAP_PORT), use_ssl=LDAP_SSL, get_info='ALL', connect_timeout=10)
    #         c = Connection(ldap_server, user=LDAP_USER, password=LDAP_PASS, auto_bind=True)
    #     except Exception as e:
    #         print("ERROR connect AD: ", str(e))

    #         self.env['sync.log'].sudo().create({'name': 'Группы AD', 'is_error': True, 'result': 'Невозможно соединиться с AD. Ошибка: ' + str(e)})
    #         notification = {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': ('Ошибка'),
    #                 'message': 'Невозможно соединиться с AD. Ошибка: ' + str(e),
    #                 'type':'warning',  #types: success,warning,danger,info
    #                 'sticky': False,  #True/False will display for few seconds if false
    #             },
    #         }
    #         return notification

        
        
    #     total_entries = 0
        
    #     res = c.search(
    #                     search_base=LDAP_SEARCH_BASE,
    #                     search_filter=LDAP_SEARCH_GROUP_FILTER,
    #                     search_scope=SUBTREE,
    #                     attributes=attributes,
    #                 )
    #     print("------------------------------------")
    #     total_entries += len(c.response)
    #     data = c.entries
    #     return total_entries, data


    
    # # Синхронизация групп
    # def ad_sync_group_action(self):
    #     attributes = ['cn', 'distinguishedName', 'whenChanged', 'objectSID', 'sAMAccountName']
    #     res = self._ldap_search(attributes=attributes)
    #     if res:
    #         total_entries, data = res
    #     else:
    #         return False

    #     print("total_entries = ", total_entries)

    #     n = 0
    #     message_error = ''
    #     message_update = ''
    #     message_create = ''
    #     for group in data:

    #         group_name = group['cn'].value

    #         if len(group_name) == 0:
    #             message_error += "Не указано CN поля для записи %s, пропускаю \n" % str(group) 
    #             break

    #         #Search Group
    #         g_search = self.env['ad.group'].search([
    #                                     ('object_SID', '=', group['objectSID']),
    #                                     '|',
    #                                     ('active', '=', False), 
    #                                     ('active', '=', True)
    #                                 ],limit=1)

            
    #         vals = {
    #                 'name': group_name,
    #                 'account_name': group['sAMAccountName'].value,
    #                 'object_SID': group['objectSID'].value,
    #                 'distinguished_name': group['distinguishedName'].value,
    #                 'active': True,
    #                 'is_ldap': True,
    #             }
    #         if len(g_search)>0 :
    #             message_update += group_name + '\n'
    #             g_search.write(vals)
    #         else:
    #             message_create += group_name + '\n'
    #             self.env['ad.group'].create(vals)
        

    #     result ='Всего получено из АД %s записей \n' % total_entries
    #     if not message_error == '':
    #         result = "\n Обновление прошло с предупреждениями: \n \n" + message_error
    #     else:
    #         result = "\n Обновление прошло успешно \n \n"
    #     if not message_create == '':
    #         result += "\n Создны новые группы: \n" + message_create
    #     if not message_update == '':
    #         result += "\n Обновлены группы: \n" + message_update

    #     self.result = result 
        
    #     self.env['sync.log'].sudo().create({'name': 'Группы AD', 'is_error': False, 'result': result})

    #     return {
	# 			'name': 'Message',
	# 			'type': 'ir.actions.act_window',
	# 			'view_type': 'form',
	# 			'view_mode': 'form',
	# 			'res_model': 'ad.sync_wizard',
	# 			'target':'new',
	# 			'context':{
	# 						'default_result':self.result,
	# 						} 
	# 			}
