# -*- coding: utf-8 -*-

from odoo import fields, models, api
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, LEVEL
import ldap3.utils.conv
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups as AddUserToGroup
from datetime import datetime
import unidecode
import random
import string


import base64
import logging
_logger = logging.getLogger(__name__)


class AdConnect(models.AbstractModel):
    _name = "ad.connect"
    _description = "Класс для работы с AD"

    def ldap_connect(self):
        """Подключается к AD, возвращает объект Connection"""
        _logger.info("ldap_connect")
         #     #Подключение к серверу AD
        LDAP_HOST = self.env['ir.config_parameter'].sudo().get_param('ldap_host')
        LDAP_PORT = self.env['ir.config_parameter'].sudo().get_param('ldap_port')
        LDAP_USER = self.env['ir.config_parameter'].sudo().get_param('ldap_user')
        LDAP_PASS = self.env['ir.config_parameter'].sudo().get_param('ldap_password')
        LDAP_SSL = self.env['ir.config_parameter'].sudo().get_param('ldap_ssl')
        LDAP_CONNECT_TIMEOUT = int(self.env['ir.config_parameter'].sudo().get_param('ldap_connect_timeout'))

        if LDAP_HOST and LDAP_PORT and LDAP_USER and LDAP_PASS and LDAP_SSL:
            if not LDAP_CONNECT_TIMEOUT or LDAP_CONNECT_TIMEOUT == 0:
                LDAP_CONNECT_TIMEOUT = 30
        else:
            _logger.warning("Нет учетных данных для подключения. Настройки-Синхронизация")
            raise Exception("Нет учетных данных для подключения. Настройки-Синхронизация")
        try:
            ldap_server = Server(host=LDAP_HOST, port=int(LDAP_PORT), use_ssl=LDAP_SSL, get_info='ALL', connect_timeout=LDAP_CONNECT_TIMEOUT)
            c = Connection(ldap_server, user=LDAP_USER, password=LDAP_PASS, auto_bind=True)
            return c
        except Exception as e:
            _logger.warning('Невозможно соединиться с AD. Ошибка: ' + str(e))
            raise Exception('Невозможно соединиться с AD. Ошибка: ' + str(e))


    def ldap_search(self, full_sync=False, date=False, search_filter=False, attributes=False):
        """ Подключется к АД, ищит записи, 
            Параметры:
                full_sync - полная синхронизация, при установке ищит в журнале синхронизации, когда последний раз было обновление и добавляет в фильтр значение даты
                search_filter - строка поиска
                attributes - требуемые атрибуты
            Возвращает:
                total_entries - общее количество полученных записей
                data - данные
         """
         #     #Подключение к серверу AD
        _logger.debug("Подключение к серверу AD")
        
        LDAP_SEARCH_BASE = self.env['ir.config_parameter'].sudo().get_param('ldap_search_base')
        
        if not LDAP_SEARCH_BASE:
            raise Exception("Не указан LDAP_SEARCH_BASE. Настройки-Синхронизация")

        
        
        # search_filter = "(&(|(objectClass=user)(objectClass=contact))(whenChanged>=" + today + "))"
        #                   '(|(objectClass=user)(objectClass=contact))'

        # Если дату не определим то делаем полную синхронизацию
        if not full_sync and not date:
            sl = self.env['sync.log'].search([
                        ('obj', '=', self.__class__.__name__),
                        ('is_error', '=', False),
                    ], 
                    limit=1, 
                    order='date desc'
                )
            if sl:
                date = sl.date if sl.date else False
        
        if date:
            search_filter =  "(&"+ search_filter + "(whenChanged>=" + date.strftime('%Y%m%d%H%M')  + "00.0Z))" #секунды обнулил

        total_entries = 0

        try:
            connection = self.ldap_connect()
            # Постраничный поиск
            res = connection.search(
                            search_base=LDAP_SEARCH_BASE,
                            search_filter=search_filter,
                            search_scope=SUBTREE,
                            attributes=attributes,
                            paged_size = 500
                        )
            
            total_entries += len(connection.response)
            cookie = connection.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
            data = connection.entries
            page = 1
            while cookie:
                res = connection.search(
                                search_base=LDAP_SEARCH_BASE,
                                search_filter=search_filter,
                                search_scope=SUBTREE,
                                attributes=attributes,
                                paged_size = 500,
                                paged_cookie = cookie
                            )
                total_entries += len(connection.response)
                cookie = connection.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']
                data += connection.entries
            
            return total_entries, data
        except Exception as error:
            raise error



    def get_ou_name(self, hr_department_id):
        """Принимает hr_department_id и возвращает имя контейнера AD для данного подразделения"""
        _logger.debug("get_ou_name hr_department_id=" + str(hr_department_id))

        ad_ou = self.env['ad.ou'].search([])
        for line in ad_ou:
            _logger.debug("get_ou_name line=" + str(line))

            if line.hr_department_id:
                _logger.debug("get_ou_name line.hr_department_id=" + str(line.hr_department_id.id))
                _logger.debug("get_ou_name line.hr_department_id.child_ids=" + str(line.hr_department_id.child_ids))

                if hr_department_id == line.hr_department_id: 
                    _logger.debug("get_ou_name return1=" + str(line))

                    return line
                if hr_department_id in line.hr_department_id.child_ids:
                    _logger.debug("get_ou_name return2=" + str(line))

                    return line

        ad_ou = self.env['ad.ou'].search([('is_default_ou', '=', True)], limit=1)
        return ad_ou
    


    def check_login(self, username):
        """Проверяет существует ли пользователь с таким логином"""
        search = self.env['ad.users'].sudo().search([('username', '=', username)])
        if len(search)>0:
            return True
        
        return False



    def get_username(self, surname, name, tname=False):
        """Принимает ФИО и возвращает логин IvanovII"""
        
        surname = unidecode.unidecode('%s' % surname)
        name = unidecode.unidecode('%s' % name)
        if tname:
            tname = unidecode.unidecode('%s' % tname)
            username =  '%s%c%c' % (surname, name[0], tname[0])
        else:
            username =  '%s%c%c' % (surname, name[0])
        
        # Проверяем существует ли такой логин, если да то пробуем вариант IvanovIvanI
        if self.check_login(username):
            if tname:
                tname = unidecode.unidecode('%s' % tname)
                username =  '%s%c%c' % (surname, name, tname[0])
            else:
                username =  '%s%c%c' % (surname, name)
            
            if self.check_login(username):
                return False
            else:
                return username

        return username



    def get_pass(self):
        """Генерирует пароль"""
        num = set('0123456789')
        lowalph = set('qwertyuiopasdfghjklzxcvbnm')
        upalph = set('QWERTYUIOPASDFGHJKLZXCVBNM')
        p = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        if any((c in num) for c in p) and any((c in lowalph) for c in p) and any((c in upalph) for c in p):
            return p
        else:
            return self.get_pass()



    def set_pass(self, username, ou, password):
        """Устанавливает пароль пользователю"""
        LDAP_SEARCH_BASE = self.env['ir.config_parameter'].sudo().get_param('ldap_search_base')
        c = self.ldap_connect()
        c.bind()
        return c.extend.microsoft.modify_password('CN=%s,OU=%s,%s' % (username, ou, LDAP_SEARCH_BASE), password)

    
    def add_user_to_group(self, users_list):
        _logger.debug("add_user_to_group=" + str(users_list))

        for user in users_list:
            search_templates = self.env['ad.set_group'].sudo().search([
                ('active', '=', True),
                '|',
                ('ou_id', '=', False),
                ('ou_id', '=', user.ou_id.id if user.ou_id else False),
                '|',
                ('department_id', '=', False),
                ('department_id', '=', user.department_id.id if user.department_id else False),
            ])

            for line in search_templates:
                for group in line.set_group_line:
                    c = self.ldap_connect()
                    c.bind()
                    AddUserToGroup(c, user.distinguished_name, group.group_id.distinguished_name)

            


    def ldap_create_user(self, employee_id):
        """Создает пользователя AD из сотрудника HR"""

        if not employee_id:
            _logger.warning('Нет параметров для создния пользователя AD')
            raise Exception("Нет параметров для создния пользователя AD")

        _logger.debug("Создает пользователя AD из сотрудника HR " + str(employee_id.name))
        try:
            LDAP_SEARCH_BASE = self.env['ir.config_parameter'].sudo().get_param('ldap_search_base')
            LDAP_HOME_DIRECTORY = self.env['ir.config_parameter'].sudo().get_param('ldap_home_dirertory')
            LDAP_HOME_DRIVER = self.env['ir.config_parameter'].sudo().get_param('ldap_home_drive')
            
            
            full_name = employee_id.name

            fname = full_name.split()
            surname = fname[0]
            name = fname[1]
            tname = ''
            if len(fname)>2:
                tname = fname[2]

            username = self.get_username(surname, name, tname)

            if not username:
                _logger.error("Ошибка при создании пользователя AD: не сгенерировано имя")
                return False #Невозможно создать пользователя

            ou_id = self.get_ou_name(employee_id.department_id)
            _logger.debug("Получен ou=" + str(ou_id))

            department_name = employee_id.department_id.name[:62] + '..' if len(employee_id.department_id.name) > 63 else employee_id.department_id.name
            title = ldap3.utils.conv.escape_filter_chars(employee_id.job_title, 'utf-8')
            department = ldap3.utils.conv.escape_filter_chars(department_name, 'utf-8')

            param = {
                            'company': employee_id.company_id.name, 
                            'department': department, 
                            'displayName': full_name,
                            'givenName': name, 
                            'sAMAccountName': username, 
                            'userPrincipalName': username + '@' + employee_id.company_id.domain_name, 
                            'sn': surname,
                            'title': title, 
                            'homeDrive': LDAP_HOME_DRIVER, 
                            'homeDirectory': LDAP_HOME_DIRECTORY,
                            'physicalDeliveryOfficeName' : ou_id.name, 
                            'wWWHomePage' : employee_id.company_id.website
                    }
            _logger.debug("Попытка создать пользователя AD %s, %s, %s" % (str(full_name), ou_id.name, param))

            #print('%s %s %s' % (empl, title, department))
            c = self.ldap_connect()
            c.bind()
            result = c.add(
                    'CN=%s,OU=%s,%s' % (full_name, ou_id.name, LDAP_SEARCH_BASE), 
                    'user', 
                    param
                )
            if result:
                _logger.debug("Создан пользователь AD" + str(result))

                password = self.get_pass()
                self.set_pass(username, ou_id.name, password)

                _logger.debug("Синхронизация с AD")

                sync = self.env['ad.sync_users'].sudo().ad_sync_users(full_sync=True)
                if sync:
                    _logger.debug("Обновление пользователей AD" + str(result))


                    search_user = self.env['ad.users'].sudo().search([
                        ('username', '=', username),
                        '|',
                        ('active', '=', True),
                        ('active', '=', False),
                        ], limit=1)
                    _logger.debug("search username=" + str(username))
                    _logger.debug("search_user=" + str(search_user))
                    if len(search_user):
                        self.add_user_to_group(search_user)

            
                    mail = self.env['sync.mail'].sudo()
                    vals = {
                        'name': 'Регистрационные данные',
                        'email_from': 'portal@tmenergo.ru',
                        'email_to': "savrasovmv@tmenergo.ru",
                        'subject': 'Регистрационные данные',
                    }
                    new = mail.create(vals)
                    print('++++++++', new)
                    new.send_mail({'rrr': 'login:%s password:%s' % (username, password)})

            # ef add_to_groups(user, ou, dep):
            # print('%s %s %s' % (user, ou, dep))
            # for group in default_groups:
            #     AddUserToGroup(c, 'CN=%s,OU=%s,OU=UsersCorporate,DC=tmenergo,DC=ru' % (user, ou), 'CN=%s,OU=Global Group,OU=UsersCorporate,DC=tmenergo,DC=ru' % group)
            #     AddUserToGroup(c, 'CN=%s,OU=%s,OU=UsersCorporate,DC=tmenergo,DC=ru' % (user, ou), 'CN=%s,OU=Global Group,OU=UsersCorporate,DC=tmenergo,DC=ru' % ou_groups[ou])
            # try:
            #     AddUserToGroup(c, 'CN=%s,OU=%s,OU=UsersCorporate,DC=tmenergo,DC=ru' % (user, ou), 'CN=%s,OU=Global Group,OU=UsersCorporate,DC=tmenergo,DC=ru' % dep_groups[dep])
            # except:
            #     send_mail(SUPPORT_EMAIL, 'Не удалось добавить\\найти группу', 'Для пользователя %s из отдела %s не удалось найти группу подразделения' % (user, dep))
            # try:
            #     AddUserToGroup(c, 'CN=%s,OU=%s,OU=UsersCorporate,DC=tmenergo,DC=ru' % (user, ou), 'CN=%s,OU=Global Group,OU=UsersCorporate,DC=tmenergo,DC=ru' % print_groups[dep])
            # except:
            #     send_mail(SUPPORT_EMAIL, 'Не удалось добавить\\найти группу', 'Для пользователя %s из отдела %s не удалось найти группу принтера' % (user, dep))

        except Exception as error:
            _logger.error("Ошибка при создании пользователя AD:" + str(error))
            return False



    
    def ldap_update_user(self, object_SID=False, param=False):
        if not param:
            _logger.warning('Нет параметров для обновления пользователя AD')
            raise Exception("Нет параметров для обновления пользователя AD")
        if not object_SID:
            _logger.warning('Нет object_SID для обновления пользователя AD')
            raise Exception("Нет object_SID для обновления пользователя AD")
        pass

    def ldap_disable_user(self, object_SID=False):
        if not object_SID:
            _logger.warning('Нет object_SID для обновления пользователя AD')
            raise Exception("Нет object_SID для обновления пользователя AD")
        pass

    def create_sync_log(self, date=False, is_error=False, result=''):
        """Создает запись в журнале синхронизации с AD"""
        if not date:
            date = datetime.today()
        self.env['sync.log'].sudo().create({
                    'date': date, 
                    'obj': self.__class__.__name__, 
                    'name': self.__class__._description, 
                    'is_error': is_error,
                    'result': result
                    })




class AdSyncGroup(models.AbstractModel):
    _name = "ad.sync_group"
    _description = "Синхронизация Групп AD"
    _inherit = ['ad.connect']


     # Синхронизация групп
    def ad_sync_group(self, full_sync=False):
        _logger.info("ad_sync_group")
        date = datetime.today()
        LDAP_SEARCH_GROUP_FILTER = self.env['ir.config_parameter'].sudo().get_param('ldap_search_group_filter')
        if not LDAP_SEARCH_GROUP_FILTER:
            _logger.warning('Не заполнен параметр ldap_search_group_filter')
            raise Exception('Не заполнен параметр ldap_search_group_filter')

        attributes = ['cn', 'distinguishedName', 'whenChanged', 'objectSID', 'sAMAccountName']
        
        try:
            res = self.ldap_search(
                                    search_filter=LDAP_SEARCH_GROUP_FILTER,
                                    attributes=attributes,
                                    full_sync=full_sync
                                )
                                
        except Exception as error:
            _logger.warning(error)
            raise error
        
        if res:
            total_entries, data = res
        else:
            _logger.warning('Ошибка. Данные не получены')
            raise Exception('Ошибка. Данные не получены')
        
        if total_entries == 0:
            result = "Новых данных нет"
            self.create_sync_log(result=result)
            return result

        n = 0
        message_error = ''
        message_update = ''
        message_create = ''
        for group in data:

            group_name = group['cn'].value

            if len(group_name) == 0:
                message_error += "Не указано CN поля для записи %s, пропускаю \n" % str(group) 
                break

            #Search Group
            g_search = self.env['ad.group'].search([
                                        ('object_SID', '=', group['objectSID']),
                                        '|',
                                        ('active', '=', False), 
                                        ('active', '=', True)
                                    ],limit=1)

            
            vals = {
                    'name': group_name,
                    'account_name': group['sAMAccountName'].value,
                    'object_SID': group['objectSID'].value,
                    'distinguished_name': group['distinguishedName'].value,
                    'active': True,
                    'is_ldap': True,
                }
            if len(g_search)>0 :
                message_update += group_name + '\n'
                g_search.write(vals)
            else:
                message_create += group_name + '\n'
                self.env['ad.group'].create(vals)
        

        result ='Всего получено из АД %s записей \n' % total_entries
        if not message_error == '':
            result += "\n Обновление прошло с предупреждениями: \n \n" + message_error
        else:
            result += "\n Обновление прошло успешно \n \n"
        if not message_create == '':
            result += "\n Создны новые группы: \n" + message_create
        if not message_update == '':
            result += "\n Обновлены группы: \n" + message_update

        #self.env['sync.log'].sudo().create({'name': 'Группы AD', 'is_error': False, 'result': result})
        self.create_sync_log(date=date, result=result)

        return result



flags = [
    [0x0001, 'SCRIPT'],
    [0x0002, 'ACCOUNTDISABLE'],
    [0x0008, 'HOMEDIR_REQUIRED'],
    [0x0010, 'LOCKOUT'],
    [0x0020, 'PASSWD_NOTREQD'],
    [0x0040, 'PASSWD_CANT_CHANGE'],
    [0x0080, 'ENCRYPTED_TEXT_PWD_ALLOWED'],
    [0x0100, 'TEMP_DUPLICATE_ACCOUNT'],
    [0x0200, 'NORMAL_ACCOUNT'],
    [0x0800, 'INTERDOMAIN_TRUST_ACCOUNT'],
    [0x1000, 'WORKSTATION_TRUST_ACCOUNT'],
    [0x2000, 'SERVER_TRUST_ACCOUNT'],
    [0x10000, 'DONT_EXPIRE_PASSWORD'],
    [0x20000, 'MNS_LOGON_ACCOUNT'],
    [0x40000, 'SMARTCARD_REQUIRED'],
    [0x80000, 'TRUSTED_FOR_DELEGATION'],
    [0x100000, 'NOT_DELEGATED'],
    [0x200000, 'USE_DES_KEY_ONLY'],
    [0x400000, 'DONT_REQ_PREAUTH'],
    [0x800000, 'PASSWORD_EXPIRED'],
    [0x1000000, 'TRUSTED_TO_AUTH_FOR_DELEGATION'],
    [0x04000000, 'PARTIAL_SECRETS_ACCOUNT'],
  ]


class AdSyncUsers(models.AbstractModel):
    _name = 'ad.sync_users'
    _description = 'Синхронизация Пользователи AD'
    _inherit = ['ad.connect']

    # Синхронизация пользователей
    def ad_sync_users(self, full_sync=False):

        _logger.debug("Синхронизация пользователей ad_sync_users")

        LDAP_SEARCH_FILTER = self.env['ir.config_parameter'].sudo().get_param('ldap_search_filter')
        if not LDAP_SEARCH_FILTER:
            raise 'Не заполнен параметр ldap_search_group_filter'

        attributes = ['cn', 'title', 'ipPhone', 'mobile', 'mail', 'department', 'sn', 'memberof', 'distinguishedName', 'homePhone', 'whenChanged', 'objectSID', 'sAMAccountName', 'thumbnailPhoto', 'userAccountControl']
        
        try:
            res = self.ldap_search(
                                    search_filter=LDAP_SEARCH_FILTER,
                                    attributes=attributes,
                                    full_sync=full_sync
                                )
        except Exception as error:
            raise error
        
        if res:
            total_entries, data = res
        else:
            _logger.debug("Ошибка. Данные не получены")
            raise 'Ошибка. Данные не получены'
        
        if total_entries == 0:
            result = "Новых данных нет"
            self.create_sync_log(result=result)
            return result


        n = 0
        message_error = ''
        message_ou = ''
        message_department = ''
        message_user_update = ''
        message_user_create = ''
        for user in data:

            user_name = user['cn'].value
            

            if len(user_name) == 0:
                message_error += "Не указано CN поля для записи %s, пропускаю \n" % str(user) 
                break
            n += 1
            #if n>5: break
            #print(user)
            #Search ou
            distinguishedName = user['distinguishedName'].value
            if user['distinguishedName'].value:
                ou_name = distinguishedName.split(',OU=')[1]
                #print("ou = ", ou_name)
                ou_search = self.env['ad.ou'].search([('name', '=', ou_name)],limit=1)
                if not ou_search:
                    _logger.debug("Создание ad.ou %s", ou_name)
                    ou_id = self.env['ad.ou'].create({
                                                'name': ou_name, 
                                            }).id
                    message_ou += ou_name +"\n"
                else:
                    ou_id = ou_search.id
            else:
                message_error += "Для %s не задан ou. \n" % user_name
                ou_id = None

            #Search Department
            if user['department'].value and ou_id != None:
                department_name = user['department'].value
                if len(department_name)>0:
                    #print("department_name = ", department_name)
                    department_search = self.env['ad.department'].search([
                                                        ('name', '=', department_name),
                                                        '|',
                                                        ('ou_id', '=', ou_id),
                                                        ('ou_id', '=', False),
                                                        ],limit=1)
                    
                    if not department_search:
                        _logger.debug("Создание ad.department %s", department_name)
                        department_id = self.env['ad.department'].create({
                                                    'name': department_name, 
                                                    'ou_id': ou_id,
                                                }).id
                        message_department += department_name +"\n"
                    else:
                        department_id = department_search.id
                        if not department_search.ou_id:
                            _logger.debug("Обновление ad.department %s", department_name)
                            department_search.write({
                                                    'ou_id': ou_id,
                                                })


                else:
                    message_error += "Для %s не задан department. \n" % user_name
                    department_id = None
            else:
                message_error += "Для %s не задан department. \n" % user_name
                department_id = None



            #Photo
            if user['thumbnailPhoto'].value:
                thumbnailPhoto = base64.b64encode(user['thumbnailPhoto'].value).decode("utf-8")
            else:
                thumbnailPhoto = None

            #Search users
            user_search = self.env['ad.users'].search([
                                        ('object_SID', '=', user['objectSID']),
                                        '|',
                                        ('active', '=', False), 
                                        ('active', '=', True)
                                    ],limit=1)



            # 514 отключенный пользователь
            uic = int(user['userAccountControl'].value or '514')
            active = True
            # Если пользователь отключен, ACCOUNTDISABLE	0x0002	2
            if uic | 2 == uic:
                active = False 
            
            vals = {
                    'name': user_name,
                    'ou_id': ou_id,
                    'department_id': department_id,
                    'title': user['title'].value,
                    'ip_phone': user['ipPhone'].value,
                    'phone': user['mobile'].value,
                    'sec_phone': user['homePhone'].value,
                    'email': user['mail'].value,
                    'username': user['sAMAccountName'].value,
                    'object_SID': user['objectSID'].value,
                    'distinguished_name': user['distinguishedName'].value,
                    'user_account_control': user['userAccountControl'].value,
                    'photo': thumbnailPhoto,
                    'active': active,
                    'is_ldap': True,
                    # 'photo': base64.b64decode(user['thumbnailPhoto'].value)

                }
            if len(user_search)>0 :
                _logger.debug("Обновление пользователя %s", user_name)
                message_user_update += user_name + '\n'
                user_search.write(vals)
            else:
                _logger.debug("Создание пользователя %s", user_name)
                message_user_create += user_name + '\n'
                self.env['ad.users'].create(vals)

        result ='Всего получено из АД %s записей \n' % total_entries
        if not message_error == '':
            result = "\n Обновление прошло с предупреждениями: \n \n" + message_error
        else:
            result = "\n Обновление прошло успешно \n \n"
        if not message_ou == '':
            result = "\n Добавлены филиалы, необходимо назначить имена: \n" + message_ou
        if not message_department == '':
            result = "\n Добавлены управления/отделы AD: \n" + message_department
        if not message_user_create == '':
            result += "\n Создны новые пользователи AD: \n" + message_user_create
        if not message_user_update == '':
            result += "\n Обновлены пользователи AD: \n" + message_user_update
        #print("result sync: ", result)

        self.create_sync_log(result=result)

        return result
       



    

