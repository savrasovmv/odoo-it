
from odoo import fields, models, api
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
import time

import json


import logging
_logger = logging.getLogger(__name__)



def get_date(date_text):
    """Возвращает форматированную дату если она не пуста, т.е не равна 0001-01-01T00:00:00"""
    date = False

    if date_text != '0001-01-01T00:00:00' and date_text !='':
        date = datetime.strptime(date_text, '%Y-%m-%dT%H:%M:%S').date()
    _logger.debug("Преобразована дата из ЗУП: %s, в дату: %s " % (date_text, date))
    return date


def is_change_value_obj(obj, new_value):
    """Проверяет новые значения реквизитов (new_value) с реквизитами объекта. Если реквизит изменился, то возврат True, иначе False"""
    for key in new_value:
        if new_value[key] != obj[key]:
            return True
    return False

class ZupConnect(models.AbstractModel):
    _name = "zup.connect"
    _description = "Класс для работы с 1С:ЗУП"


    def get_result(self, 
                    error=False,
                    message_error='', 
                    message_create='', 
                    message_update='', 
                    total_entries='',
                    total_create='',
                    total_update='',
                    ):
        """Возвращает текстовое представления результата"""

        result =''
        if error:
            result = "\n Ошибка: \n \n" + message_error
            return result

        if total_entries>0:
            result ='Всего получено из ЗУП %s записей \n' % total_entries
        if not message_error == '':
            result += "\n Обработка прошла с предупреждениями: \n \n" + message_error
        else:
            result += "\n Обработка прошла успешно \n \n"

        total_create = len(message_create.splitlines())
        result += "\n Создно %s новых записей: \n" % str(total_create)
        result += message_create

                                    
        total_update = len(message_update.splitlines())
        result += "\n Обновлено %s записей: \n" % str(total_update)
        result += message_update
        
        return result
    
    
        
    def zup_search(self, url_api=False, full_sync=False, date=False, search_filter=False, attributes=False):
        pass


    def zup_api(self, url_api=False, method='GET', param={}, full_sync=False, date=False, search_filter=False, attributes=False):
        """ Подключется к ЗУП, ищит записи, 
            Параметры:
                full_sync - полная синхронизация, при установке ищит в журнале синхронизации, когда последний раз было обновление и добавляет в фильтр значение даты
                search_filter - строка поиска
                attributes - требуемые атрибуты
            Возвращает:
                total_entries - общее количество полученных записей
                data - данные, list []
         """
        _logger.info("Подключение к ЗУП, метод " + method)

        ZUP_USER = self.env['ir.config_parameter'].sudo().get_param('zup_user')
        ZUP_PASSWORD = self.env['ir.config_parameter'].sudo().get_param('zup_password')
        ZUP_TIMEOUT = self.env['ir.config_parameter'].sudo().get_param('zup_timeout')

        if not ZUP_USER or not ZUP_PASSWORD:
            str_error = "Нет учетных данных для доступ к API ЗУП. Проверьте настройки"
            _logger.error(str_error)
            self.create_sync_log(result=str_error)
            raise str_error

        if not url_api:
            str_error = "Не заполнен параметр url_api"
            _logger.error(str_error)
            self.create_sync_log(result=str_error)
            raise Exception(str_error)
        
        try:
            if method == 'GET':
                response = requests.get(
                                url_api,
                                auth=HTTPBasicAuth(ZUP_USER, ZUP_PASSWORD),
                                timeout=int(ZUP_TIMEOUT)
                                )
            if method == 'POST':
                response = requests.post(
                                url_api,
                                data=json.dumps(param),
                                auth=HTTPBasicAuth(ZUP_USER, ZUP_PASSWORD),
                                timeout=int(ZUP_TIMEOUT)
                            )
            if response.status_code != 200:
                str_error = "Ошибка, Код ответа: %s" % response.status_code
                _logger.error(str_error)
                self.create_sync_log(result=str_error)
                raise Exception(str_error)
     
        except Exception as error:
            str_error = "Ошибка при выполнении подключения к ЗУП:" + str(error)
            _logger.error(str_error)
            self.create_sync_log(result=str_error)
            raise Exception(str_error)

        res = response.json()
        if 'data' in res:
            total_entries = len(res['data'])
            if total_entries == 0:
                _logger.info("Успех. Нет данных для обработки")
                self.create_sync_log(result='Успех. Нет данных для обработки')
                return False

            data = res['data']
            _logger.info("Получены данные из ЗУП, в кол-ве: %s" % str(total_entries))
            return total_entries, data
        else:
            _logger.info("Подключение выполнено успешно, без возврата данных")
            self.create_sync_log(result='Подключение выполнено успешно, без возврата данных')
            return False
    


    @api.model
    def zup_get(self, url_api=False, full_sync=False, date=False, search_filter=False, attributes=False):
        """ Подключется к ЗУП, ищит записи, 
            Параметры:
                full_sync - полная синхронизация, при установке ищит в журнале синхронизации, когда последний раз было обновление и добавляет в фильтр значение даты
                search_filter - строка поиска
                attributes - требуемые атрибуты
            Возвращает:
                total_entries - общее количество полученных записей
                data - данные, list []
         """
        _logger.info("Подключение к ЗУП")

        ZUP_USER = self.env['ir.config_parameter'].sudo().get_param('zup_user')
        ZUP_PASSWORD = self.env['ir.config_parameter'].sudo().get_param('zup_password')
        ZUP_TIMEOUT = self.env['ir.config_parameter'].sudo().get_param('zup_timeout')

        if not ZUP_USER or not ZUP_PASSWORD:
            str_error = "Нет учетных данных для доступ к API ЗУП. Проверьте настройки"
            _logger.error(str_error)
            self.create_sync_log(result=str_error)
            raise str_error

        if not url_api:
            str_error = "Не заполнен параметр url_api"
            _logger.error(str_error)
            self.create_sync_log(result=str_error)
            raise Exception(str_error)
        
        try:
            response = requests.get(
                                url_api,
                                auth=HTTPBasicAuth(ZUP_USER, ZUP_PASSWORD),
                                timeout=int(ZUP_TIMEOUT)
                            )
            if response.status_code != 200:
                str_error = "Ошибка, Код ответа: %s" % response.status_code
                _logger.error(str_error)
                self.create_sync_log(result=str_error)
                raise Exception(str_error)
     
        except Exception as error:
            str_error = "Ошибка при выполнении подключения к ЗУП:" + str(error)
            _logger.error(str_error)
            self.create_sync_log(result=str_error)
            raise Exception(str_error)

        res = response.json()
        if 'data' in res:
            total_entries = len(res['data'])
            data = res['data']
            _logger.info("Получены данные из ЗУП, в кол-ве: %s" % str(total_entries))
            return total_entries, data
        else:
            _logger.info("Подключение выполнено успешно, без возврата данных")
            self.create_sync_log(result='Подключение выполнено успешно, без возврата данных')
            return False



    def zup_post(self, url_api=False, param={}, full_sync=False, date=False,search_filter=False, attributes=False):
        """ Подключется к ЗУП, POST, 
            Параметры:
                param - параметры запроса
                full_sync - полная синхронизация, при установке ищит в журнале синхронизации, когда последний раз было обновление и добавляет в фильтр значение даты
                search_filter - строка поиска
                attributes - требуемые атрибуты
            Возвращает:
                total_entries - общее количество полученных записей
                data - данные
         """
        _logger.info("Подключение к ЗУП (post)")

        ZUP_USER = self.env['ir.config_parameter'].sudo().get_param('zup_user')
        ZUP_PASSWORD = self.env['ir.config_parameter'].sudo().get_param('zup_password')
        ZUP_TIMEOUT = self.env['ir.config_parameter'].sudo().get_param('zup_timeout')

        if not ZUP_USER or not ZUP_PASSWORD:
            _logger.error("Нет учетных данных для доступ к API ЗУП. Проверьте настройки")
            raise "Нет учетных данных для доступ к API ЗУП. Проверьте настройки"
        
        try:
            response = requests.post(
                                url_api,
                                data=json.dumps(param),
                                auth=HTTPBasicAuth(ZUP_USER, ZUP_PASSWORD),
                                timeout=int(ZUP_TIMEOUT)
                            )
            if response.status_code != 200:
                str_error = "Ошибка, Код ответа: %s" % response.status_code
                _logger.error(str_error)
                self.create_sync_log(result=str_error)
                raise Exception(str_error)
     
        except Exception as error:
            str_error = "Ошибка при выполнении подключения к ЗУП:" + str(error)
            _logger.error(str_error)
            self.create_sync_log(result=str_error)
            raise Exception(str_error)

        res = response.json()
        if 'data' in res:
            total_entries = len(res['data'])
            data = res['data']
            _logger.info("Получены данные из ЗУП, в кол-ве: %s" % total_entries)
            #return total_entries, data
            return total_entries, data
        else:
            _logger.info("Подключение выполнено успешно, без возврата данных")
            self.create_sync_log(result='Подключение выполнено успешно, без возврата данных')
            return False


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




class ZupSyncDep(models.AbstractModel):
    _name = 'zup.sync_dep'
    _description = 'Синхронизация подразделений ЗУП'
    _inherit = ['zup.connect']


    def load_department(self, data):
        """Создать или обновить подразделения из данных API
            'departamentList': [{'code': 'УД0000019',
                               'guid1C': '4b11e662-7577-11e0-9863-00155d003102',
                               'managerGuid1C': '',
                               'name': 'Отдел информационных технологий',
                               'parentGuid1C': '8ebff4a4-3194-11de-a918-0021853a356f'}],
            data: набор записей из departamentList
        """

        n = 0
        message_error = ''
        message_update = ''
        message_create = ''
        # print(self.data)
        for line in data:
            if 'name' in line and 'guid1C' in line:
                name = line['name'] 
                guid_1c = line['guid1C']
                code_1c = line['code'] if 'code' in line else ''
                parent_guid_1c = line['parentGuid1C'] if 'parentGuid1C' in line else ''
                manager_guid_1c = line['managerGuid1C'] if 'managerGuid1C' in line else ''

                manager_id = self.env['hr.employee'].search([
                    ('guid_1c', '=', manager_guid_1c)
                ],limit=1).id

                parent_id = self.env['hr.department'].search([
                    ('guid_1c', '=', parent_guid_1c)
                ],limit=1).id

                record_search = self.env['hr.department'].search([
                    ('guid_1c', '=', guid_1c)
                ],limit=1)

                vals = {
                    'name': name,
                    'guid_1c': guid_1c,
                    'code_1c': code_1c,
                    'parent_id': parent_id,
                    'manager_id': manager_id,
                }

                if len(record_search)>0:
                    is_update = False # Нужно ли обновлять
                    record_vals = {
                        'name': record_search.name,
                        'guid_1c': record_search.guid_1c,
                        'code_1c': record_search.code_1c,
                        'manager_id': record_search.manager_id.id,
                        'parent_id': record_search.parent_id.id,
                    }
                    
                    for key in vals:
                        if vals[key] != record_vals[key]:
                            is_update = True
                            break # Прерываем цикл. Значения не совпадают значит нужно обновить
                    
                    if is_update:
                        message_update += name + '\n'
                        record_search.write(vals)
                else:
                    n +=1
                    message_create += name + '\n'
                    record_search.create(vals)
            else:
                message_error += "Отсутствует Наименование или УИД 1С  в запси: %s \n" % str(line)

        result = self.get_result(
                                    total_entries=len(data), 
                                    message_update=message_update, 
                                    message_create=message_create, 
                                    message_error=message_error
                                    )
        self.create_sync_log(result=result)
        return result
  

    def zup_sync_dep(self):
        """Загрузка информации по подразделениям из ЗУП"""

        _logger.debug("Загрузка информации по подразделениям из ЗУП zup_sync_dep")

        URL_API = self.env['ir.config_parameter'].sudo().get_param('zup_url_get_dep_list')

        res = self.zup_api(method='GET', url_api=URL_API)

        if not res:
            return "Нет данных"

        total_entries, data = res
        # Пример записи {'guid1C': 'e91bef40-1d5a-4942-80d4-e6febb61edb5', 'code': '49', 'name': 'Планово-экономический отдел', 'parentGuid1C': '493c1dd5-ba5b-11e9-94b3-00155d000c0e', 'managerGuid1C': ''}
        result = self.load_department(data)

        return result



class ZupSyncEmployer(models.AbstractModel):
    _name = 'zup.sync_employer'
    _description = 'Синхронизация сотрудников ЗУП'
    _inherit = ['zup.connect']

    def zup_sync_employer(self, by_guid_1c=False, is_def_change=False):
        """Загрузка информации по Сотрудникам из ЗУП"""

        _logger.debug("Загрузка информации по Сотрудникам из ЗУП zup_sync_employer")

        date = datetime.today()

        if by_guid_1c:
            URL_API = self.env['ir.config_parameter'].sudo().get_param('zup_url_get_empl')
        else:
            URL_API = self.env['ir.config_parameter'].sudo().get_param('zup_url_get_empl_list')
        
        if not URL_API:
            raise Exception("Не заполнен параметр zup_url_get_empl_list или zup_url_get_empl")

        try:
            if by_guid_1c:
                param = {'guid1C': by_guid_1c}
                res = self.zup_post(
                                    param=param,
                                    url_api=URL_API
                                )

            else:
                res = self.zup_search(
                                    url_api=URL_API
                                )
        except Exception as error:
            self.create_sync_log(date=date,result=error, is_error=True)
            raise error

        total_entries = 0
        
        if res and isinstance(res, tuple):
            if by_guid_1c:
                total_entries, line = res
                data = [line,] # Преобразуем в массив для, т.к результат содержит одну запись
            else:
                total_entries, data = res
        else:
            self.create_sync_log(date=date,result='Ошибка. Данные не получены', is_error=True)
            result = "Данные по сотруднику не получены"
            return result
        
        if total_entries == 0:
            result = "Новых данных нет"
            self.create_sync_log(result=result)
            return result
        
        n = 0
        message_error = ''
        message_update = ''
        message_create = ''
        # Пример записи {
            # 'guid1C': 'd71e435e-8abe-11e2-bf2d-009c029f6565', 
            # 'number': '0001118', 
            # 'name': 'Иванов Иван Иванович',
            # 'employmentDate': '2013-03-12T00:00:00',
            # 'birthDate': '1987-05-28T00:00:00', 
            # 'gender': 'Мужской', 
            # 'citizenship': 'RU', 
            # 'eMail': '', 
            # 'employmentType': 'Основное место работы', 
            # 'departament': 'e9c52c32-d042-41f3-9f6f-85c6896ee423', 
            # 'position': 'Ведущий инженер'}
        for line in data:
            if 'name' in line and 'guid1C' in line and 'departament' in line and 'position' in line:

                _logger.debug("Данные по сотруднику: %s" % line)
                name = line['name'] 
                guid_1c = line['guid1C']
                
                _logger.debug("Сотрудник: %s" % name)

                #Подразделение
                department_guid_1c = line['departament']
                department = self.env['hr.department'].search([
                    ('guid_1c', '=', department_guid_1c)
                ],limit=1)
                department_id = department.id 
                
                # Должность
                job_title = line['position']
                # Дата рождение
                birthday = None
                birthday_text = line['birthDate'] if 'birthDate' in line else ''
                if birthday_text != '':
                    birthday = get_date(birthday_text)

                # Дата принятия на работу
                service_start_date = None
                service_start_date_text = line['employmentDate'] if 'employmentDate' in line else ''
                if service_start_date_text != '':
                    service_start_date = get_date(service_start_date_text)

                # Пол
                gender = None
                gender_text = line['gender'] if 'gender' in line else ''
                if gender_text =='Мужской':
                    gender = 'male'
                if gender_text =='Женский':
                    gender = 'female'
                # Гражданство, страна
                country_id = None
                country_text = line['citizenship'] if 'citizenship' in line else ''
                if country_text != '':
                    country_id = self.env['res.country'].search([
                        ('code', '=', country_text)
                    ],limit=1).id
                # Личный адрес
                personal_email = line['eMail'] if 'eMail' in line else ''
                
                # Вид знятости
                employment_type_1c = line['employmentType'] if 'employmentType' in line else ''

                number_1c = line['number'] if 'number' in line else ''

                

                record_search = self.env['hr.employee'].search([
                    ('guid_1c', '=', guid_1c)
                ],limit=1)

                # Менеджер
                parent_id = None
                # Если Менеджер это есть текущий сотрудник, то нужно искать менеджера в вышестоящем подразделеии
                if record_search.id != department.manager_id.id:
                    parent_id = self.env['hr.employee'].search([
                        ('id', '=', department.manager_id.id)
                    ],limit=1).id
                else:
                    parent_id = self.env['hr.employee'].search([
                        ('id', '=', department.parent_id.manager_id.id)
                    ],limit=1).id


                vals = {
                    'name': name,
                    'guid_1c': guid_1c,
                    'department_id': department_id,
                    'job_title': job_title,
                    'birthday': birthday,
                    'service_start_date': service_start_date,
                    'gender': gender,
                    'country_id': country_id,
                    'personal_email': personal_email,
                    'employment_type_1c': employment_type_1c,
                    'number_1c': number_1c,
                    'parent_id': parent_id,
                }

                if len(record_search)>0:
                    is_update = False # Нужно ли обновлять
                    record_vals = {
                        'name': record_search.name,
                        'guid_1c': record_search.guid_1c,
                        'department_id': record_search.department_id.id,
                        'job_title': record_search.job_title,
                        'birthday': record_search.birthday,
                        'service_start_date': record_search.service_start_date,
                        'gender': record_search.gender,
                        'country_id': record_search.country_id.id,
                        'personal_email': record_search.personal_email,
                        'employment_type_1c': record_search.employment_type_1c,
                        'number_1c': record_search.number_1c,
                        'parent_id': record_search.parent_id.id,
                    }
                    
                    for key in vals:
                        if vals[key] != record_vals[key]:
                            is_update = True
                            break # Прерываем цикл. Значения не совпадают значит нужно обновить
                    
                    if is_update:
                        message_update += name + '\n'
                        record_search.write(vals)
                else:
                    n +=1
                    message_create += name + '\n'
                    record_search.create(vals)
            else:
                message_error += "Отсутствует обязательное поле в запси: %s \n" % line

        if is_def_change:
            return {
                'result': True,
                'message_update': message_update,
                'message_create': message_create,
                'message_error': message_error,
            }

        result ='Всего получено из ЗУП %s записей \n' % total_entries
        if not message_error == '':
            result += "\n Обновление прошло с предупреждениями: \n \n" + message_error
        else:
            result += "\n Обновление прошло успешно \n \n"

        if not message_create == '':
            result += "\n Создно %s новых Сотрудников: \n" % n
            result += message_create

        if not message_update == '':
            result += "\n Обновлены Сотрудники: \n" + message_update

        self.create_sync_log(result=result)

        return result






class ZupSyncPersonalDoc(models.AbstractModel):
    _name = 'zup.sync_personal_doc'
    _description = 'Синхронизация кадровых документов ЗУП'
    _inherit = ['zup.connect']

    def zup_sync_personal_doc_full(self, date_start=False, date_end=False):
        """Загрузка всех типов документов"""

        ZUP_QINTERVAL = self.env['ir.config_parameter'].sudo().get_param('zup_query_interval')

        _logger.debug("Загрузка всех типов документов zup_sync_personal_doc_full")

        if not date_start or not date_end:
            raise Exception("Не указан период для синхронизации")
        
        date = datetime.today()

        doc_obj_list = [
                'hr.recruitment_doc',
                'hr.termination_doc',
                'hr.vacation_doc',
                'hr.trip_doc',
                'hr.sick_leave_doc',
                'hr.transfer_doc',
                'hr.transfer_doc_multi', # такого объекта нет, потом преобразуем в hr.transfer_doc
            ]
        result = ''
        for doc_obj in doc_obj_list:
            try:
                result += self.zup_sync_personal_doc(doc_obj=doc_obj, date_start=date_start, date_end=date_end)
                time.sleep(int(ZUP_QINTERVAL)) # Задержка выполнения запросов
            except Exception as error:
                _logger.warning("Ошибка zup_sync_personal_doc_full %s" % str(error))
                self.create_sync_log(date=date,result=str(error), is_error=True)
                raise error

        return result

    def zup_sync_personal_doc(self, doc_obj=False, date_start=False, date_end=False):
        """Загрузка документов ЗУП

            Пример ответа:
            {
                'dataType': 'recruitmentDocumentList', 
                'discription': '', 
                'data': [{
                    'guid1C': '3a48388e-91c1-11ea-94df-00155d01140c', 
                    'posted': True, 
                    'number': '465-к', 
                    'documentDate': '2020-05-08T17:25:11',
                    'recruitmenDate': '2020-05-08T00:00:00', 
                    'employeeGuid1C': '5afc9b7a-91bf-11ea-94df-00155d01140c', 
                    'employmentType': 'Основное место работы'
				}, ]
		}

        
        """

        _logger.debug("Загрузка документов ЗУП zup_sync_personal_doc")

        if not date_start or not date_end or not date_end:
            raise Exception("Не указан период или объект для синхронизации")
        

        date = datetime.today()

        # param = {
        #     "startDate": date_start.strftime("%Y-%m-%dT%H:%M:%S"),
		#     "endDate": date_end.strftime("%Y-%m-%dT%H:%M:%S"),
        # }
        # Выборка документов по дате документа
        param = {
            "documentDateStart": date_start.strftime("%Y-%m-%dT%H:%M:%S"),
		    "documentDateEnd": date_end.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        

        param_api = False
        last_update_employee = False
        if doc_obj == 'hr.recruitment_doc':
            param_api = 'zup_url_get_recruitment_doc_list'
            last_update_employee = self.env['sync.log'].search([('obj','=','sync.zup_employer')],order='date desc').date
        if doc_obj == 'hr.termination_doc':
            param_api = 'zup_url_get_termination_doc_list'
        if doc_obj == 'hr.vacation_doc':
            param_api = 'zup_url_get_vacation_doc_list'
        if doc_obj == 'hr.trip_doc':
            param_api = 'zup_url_get_trip_doc_list'
        if doc_obj == 'hr.sick_leave_doc':
            param_api = 'zup_url_get_sick_leave_doc_list'
        if doc_obj == 'hr.transfer_doc':
            param_api = 'zup_url_get_transfer_doc_list'
        if doc_obj == 'hr.transfer_doc_multi': # т.к transfer_doc_multi не существует заменяем объект
            param_api = 'zup_url_get_multi_transfer_doc_list'

        # print("+++++ doc_obj",doc_obj)

        if not param_api:
            raise Exception("Не указан тип объект документа для синхронизации")

        URL_API = self.env['ir.config_parameter'].sudo().get_param(param_api)
        if not URL_API:
            raise Exception("Не заполнен параметр zup_url_get_recruitment_doc_list")

        try:

            res = self.zup_post(
                                    url_api=URL_API,
                                    param=param
                                )
        except Exception as error:
            self.create_sync_log(date=date,result=error, is_error=True)
            raise error

        if res:
            total_entries, data = res
        else:
            self.create_sync_log(date=date,result='Ошибка. Данные не получены', is_error=True)
            raise Exception('Ошибка. Данные не получены')
        
        if total_entries == 0:
            result = "Новых данных нет"
            self.create_sync_log(result=result)
            return result

        if doc_obj == 'hr.transfer_doc_multi': # Перевод на другую ф-ю
            return self.zup_sync_multi_transfer_doc(data)

        doc_name = self.env[doc_obj]._description
        n = 0
        message_error = ''
        message_update = ''
        message_create = ''
        message_create_employee = ''
        
        for line in data:
            # print(line)
            _logger.debug("Обработка данных из ЗУП value: %s" % line)

            if 'guid1C' in line:
                # print(line)
                
                guid_1c = line['guid1C'] # Идентификатор документа
                _logger.debug("Идентификатор документа: %s" % guid_1c)

                document_date = get_date(line['documentDate'])
                employee_guid_1c = line['employeeGuid1C']
                empl_search = self.env['hr.employee'].search([
                    ('guid_1c', '=', employee_guid_1c),
                    '|',
                    ('active', '=', False), 
                    ('active', '=', True)
                    ],limit=1)
                if len(empl_search) == 0:
                        message_error += "не найден сотрудник с gud1c %s \n" % ( employee_guid_1c)


                # if last_update_employee:
                #     if last_update_employee<document_date:
                #         empl_search = self.env['hr.employee'].search([
                #             ('guid_1c', '=', employee_guid_1c),
                #             '|',
                #             ('active', '=', False), 
                #             ('active', '=', True)
                #             ],limit=1)
                #         if len(empl_search) == 0:
                #             _logger.debug("Запрос в ЗУП для получения сотрудника по employee_guid_1c: %s" % employee_guid_1c)

                #             # Запрос в ЗУП для получения сотрудника по employee_guid_1c
                #             message_create_employee += self.env['zup.sync_employer'].zup_sync_employer(by_guid_1c=employee_guid_1c, is_def_change=True)

                #             # Повторный поиск сотрудника
                #             empl_search = self.env['hr.employee'].search([
                #             ('guid_1c', '=', employee_guid_1c),
                #             '|',
                #             ('active', '=', False), 
                #             ('active', '=', True)
                #             ],limit=1)
                #             if len(empl_search) == 0:
                #                 _logger.debug("не найден сотрудник с employee_guid_1c %s, пропуск" % employee_guid_1c)
                #                 message_error += "не найден сотрудник с gud1c %s, пропуск \n" % ( employee_guid_1c)
                

                
                # if empl_search.department_id:
                #     department_id = empl_search.department_id.id
                # else:
                #     department_id = False

                # Постоянные параметры документов
                const_vals = {
                    'date': get_date(line['documentDate']),
                    'posted': line['posted'],
                    'guid_1c': line['guid1C'],
                    'number_1c': line['number'],
                    'employee_guid_1c': line['employeeGuid1C'],
                    # 'employee_id': empl_search.id,
                }

                

                # Индивидуальные параметры
                doc_vals = {}

                if doc_obj == 'hr.recruitment_doc':
                    doc_vals = {
                        'service_start_date': get_date(line['recruitmenDate']),
                        'employment_type': line['employmentType'],
                        # 'department_id': department_id,
                        'job_title': line['position'],
                        'department_guid_1c': line['departament'],
                    }

                if doc_obj == 'hr.termination_doc':
                    doc_vals = {
                        'service_termination_date': get_date(line['dismissDate']),
                    }

                if doc_obj == 'hr.vacation_doc' or doc_obj == 'hr.trip_doc' or doc_obj == 'hr.sick_leave_doc':
                    doc_vals = {
                        'start_date': get_date(line['startDate']),
                        'end_date': get_date(line['endDate']),
                    }
                    
                if doc_obj == 'hr.transfer_doc':
                    # dep_search = self.env['hr.department'].search([
                    #         ('guid_1c', '=', line['departament'])
                    #     ],limit=1)

                    # print('++++++++++++===')
                    doc_vals = {
                        'start_date': get_date(line['startDate']),
                        'end_date': get_date(line['endDate']),
                        'job_title': line['position'],
                        'department_guid_1c': line['departament'],
                        # 'department_id': dep_search.id if len(dep_search)>0 else False,
                    }

                vals = {**const_vals, **doc_vals}

                _logger.debug("Данные объекта %s, со значениями: %s " % (doc_obj, vals))



                doc_search = self.env[doc_obj].search([
                        ('guid_1c', '=', guid_1c)
                    ],limit=1)
                if len(doc_search)>0:
                    _logger.debug("Обновление объекта %s" % doc_search)
                    doc_search.write(vals)
                    message_update += line['number'] + ' от ' + line['documentDate'] + '\n'

                elif vals['posted'] == True: #создаем только проведенные документ
                    _logger.debug("Создание объекта %s " % doc_obj)
                    self.env[doc_obj].create(vals)
                    message_create += line['number'] + ' от ' + line['documentDate'] + '\n'
                
            else:
                message_error += "Отсутствует обязательное поле в запси: %s \n" % line
                _logger.debug("Отсутствует обязательное поле в запси: %s" % line)



        result ='Всего получено из ЗУП %s записей \n' % total_entries
        if len(message_error)>0:
            result += "\n Обновление прошло с предупреждениями: \n \n" + message_error
            _logger.warning(result)
        else:
            result += "\n Обновление прошло успешно \n \n"



        if not message_update == '':
            result += "\n Обновлены Документы %s: \n" % doc_name 
            result +=  message_update
        if not message_create == '':
            result += "\n Созданы Документы %s: \n" % doc_name 
            result +=  message_create

        _logger.debug(result)

        self.create_sync_log(result=result)

        return result





    def zup_sync_multi_transfer_doc(self, data, is_def_change=False):
        """Загрузка документов групповых переводов ЗУП
            is_def_change - признак запуска этой функции в другой функции. Если да, то вернет значения результата выполнения, иначе запишит лог
        """
        _logger.debug("Загрузка документов групповых переводов ЗУП zup_sync_multi_transfer_doc")

        if not data:
            raise Exception("Нет данных для синхронизации")
        

        date = datetime.today()
        doc_name = self.env['hr.transfer_doc']._description
        n = 0
        message_error = ''
        message_update = ''
        message_create = ''
        
        for line in data:

            if 'guid1C' in line and 'employeesList' in line:
                
                guid_1c = line['guid1C'] # Идентификатор документа
                employee_list = line['employeesList'] # список сотрудников

                # Постоянные параметры документов
                const_vals = {
                    'date': get_date(line['documentDate']),
                    'posted': line['posted'],
                    'guid_1c': line['guid1C'],
                    'number_1c': line['number'],
                }

                for emp_line in employee_list:
                    n += 1
                    # Индивидуальные параметры
                    # dep_search = self.env['hr.department'].search([
                    #     ('guid_1c', '=', emp_line['departament'])
                    # ],limit=1)

                    employee_guid_1c = emp_line['employeeGuid1C']
                    # empl_search = self.env['hr.employee'].search([
                    #     ('guid_1c', '=', employee_guid_1c),
                    #     '|',
                    #     ('active', '=', False), 
                    #     ('active', '=', True)
                    #     ],limit=1)
                    # if len(empl_search) == 0:
                    #     message_error += "не найден сотрудник с gud1c %s, пропуск \n" % ( guid_1c)
                    #     continue # Переход к следующей записи

                    doc_vals = {
                        'start_date': get_date(emp_line['startDate']),
                        'end_date': get_date(emp_line['endDate']),
                        'job_title': emp_line['position'],
                        'department_guid_1c': emp_line['departament'],
                        # 'department_id': dep_search.id if len(dep_search)>0 else False,
                        'employee_guid_1c': employee_guid_1c,
                        # 'employee_id': empl_search.id,
                    }

                    vals = {**const_vals, **doc_vals}

                    doc_search = self.env['hr.transfer_doc'].search([
                            ('guid_1c', '=', guid_1c),
                            ('employee_guid_1c', '=', employee_guid_1c)
                        ],limit=1)

                    if len(doc_search)>0:
                        doc_search.write(vals)
                        message_update += line['number'] + ' от ' + line['documentDate'] + '\n'

                    elif vals['posted'] == True: #создаем только проведенные документ
                        self.env['hr.transfer_doc'].create(vals)
                        message_create += line['number'] + ' от ' + line['documentDate'] + '\n'
                
            else:
                message_error += "Отсутствует обязательное поле в запси: %s \n" % line

        if is_def_change:
            return {
                'result': True,
                'message_update': message_update,
                'message_create': message_create,
                'message_error': message_error,
            }


        result ='Всего получено из ЗУП %s записей \n' % n
        if not message_error == '':
            result = "\n Обновление прошло с предупреждениями: \n \n" + message_error
        else:
            result = "\n Обновление прошло успешно \n \n"

        _logger.info(result)

        if not message_update == '':
            result += "\n Обновлены Документы %s: \n" % doc_name 
            result +=  message_update
        if not message_create == '':
            result += "\n Созданы Документы %s: \n" % doc_name 
            result +=  message_create

        self.create_sync_log(result=result)

        return result




    


    def update_personal_doc(self, doc_obj, data, create_employer=False):

        _logger.debug("Обновление персональных документв ЗУП update_personal_doc")

        message_update = ''
        message_create = ''
        message_error = ''
        doc_name = ''

        if 'guid1C' in data:
             
            guid_1c = data['guid1C'] # Идентификатор документа

            employee_guid_1c = data['employeeGuid1C']
            document_date = get_date(data['documentDate'])

            # Если это прием на работу
            if doc_obj == 'hr.recruitment_doc':

                empl_search = self.env['hr.employee'].search([
                            ('guid_1c', '=', employee_guid_1c),
                            '|',
                            ('active', '=', False), 
                            ('active', '=', True)
                            ],limit=1)
                if len(empl_search)==0:
                    message_error += "Не найден сотрудник с employeeGuid1C=%s \n" % employee_guid_1c

                # # Последнее обновление сотрудников
                # last_update_employee = self.env['sync.log'].search([('obj','=','sync.zup_employer')],order='date desc').date

                # if last_update_employee:
                #     empl_search = self.env['hr.employee'].search([
                #             ('guid_1c', '=', employee_guid_1c),
                #             '|',
                #             ('active', '=', False), 
                #             ('active', '=', True)
                #             ],limit=1)
                #     # Если последнее обновление сотрудников меньше чем дата документа, то обновляем сотрудника 
                #     if last_update_employee<document_date and len(empl_search)==0:
                #         result_doc = self.env['zup.sync_employer'].zup_sync_employer(by_guid_1c=employee_guid_1c, is_def_change=True)
                #         if 'result' in result_doc:
                #             message_create += result_doc['message_create']
                #             message_update += result_doc['message_update']
                #             message_error += result_doc['message_error']

                                    


            # if empl_search.department_id:
            #     department_id = empl_search.department_id.id
            # else:
            #     if 'departament' in data:
            #         dep_search = self.env['hr.department'].search([
            #             ('guid_1c', '=', data['departament'])
            #             ],limit=1)
            #         if len(dep_search)>0:
            #             department_id = dep_search.id
            #         else:
            #             department_id = False

            # Постоянные параметры документов
            const_vals = {
                'date': get_date(data['documentDate']),
                'posted': data['posted'],
                'guid_1c': data['guid1C'],
                'number_1c': data['number'],
                'employee_guid_1c': data['employeeGuid1C'],
                # 'employee_id': empl_search.id,
            }
            

            # Индивидуальные параметры
            doc_vals = {}
            if doc_obj == 'hr.recruitment_doc':
                doc_vals = {
                    'service_start_date': data['recruitmenDate'],
                    'employment_type': data['employmentType'],
                    # 'department_id': department_id,
                    'job_title': data['position'],
                    'department_guid_1c': data['departament'],
                }

            if doc_obj == 'hr.termination_doc':
                doc_vals = {
                    'service_termination_date': data['dismissDate'],
                }

            if doc_obj == 'hr.vacation_doc' or doc_obj == 'hr.trip_doc' or doc_obj == 'hr.sick_leave_doc':
                doc_vals = {
                    'start_date': get_date(data['startDate']),
                    'end_date': get_date(data['endDate']),
                }

            if doc_obj == 'hr.transfer_doc':
                dep_search = self.env['hr.department'].search([
                    ('guid_1c', '=', data['departament'])
                    ],limit=1)

                doc_vals = {
                    'start_date': get_date(data['startDate']),
                    'end_date': get_date(data['endDate']),
                    'job_title': data['position'],
                    'department_guid_1c': data['departament'],
                    # 'department_id': dep_search.id if len(dep_search)>0 else False,
                }

            vals = {**const_vals, **doc_vals}

            doc_name = self.env[doc_obj]._description
            doc_search = self.env[doc_obj].search([
                ('guid_1c', '=', guid_1c)
            ],limit=1)
            if len(doc_search)>0:
                # print(vals)
                doc = doc_search.write(vals)
                message_update += doc_name + ' ' + data['number'] + ' от ' + data['documentDate'] + '\n'
            elif vals['posted'] == True: #создаем только проведенные документы
                doc = self.env[doc_obj].create(vals)
                message_create += doc_name + ' ' + data['number'] + ' от ' + data['documentDate'] + '\n'
            
        else:
            message_error = "Отсутствует обязательное поле в запси: %s \n" % data
            return {
                'result': False,
                'message_update': message_update,
                'message_create': message_create,
                'message_error': message_error,
            }

        return {
            'result': True,
            'message_update': message_update,
            'message_create': message_create,
            'message_error': message_error,
        }
       

    
    def zup_sync_personal_doc_change(self):
        """Загрузка измененных документов из ЗУП

            GET - получение измененных документов
                Пример ответа:
                {
                    {
                        'dataType': 'objectChanges', 
                        'discription': '', 
                        'data': {
                            'recruitmentDocumentList': [
                                {
                                    'guid1C': 'afbc2313-0ecc-11ec-94f9-00155d01140c', 
                                    'posted': True, 
                                    'number': '679-к', 
                                    'documentDate': '2021-09-06T09:41:23', 
                                    'recruitmenDate': '2021-09-06T00:00:00', 
                                    'employeeGuid1C': 'e7527b99-0ec8-11ec-94f9-00155d01140c', 
                                    'employmentType': 'Основное место работы'
                                    },
                }

                Виды документов:
                            departamentList
                            employeesList
                            recruitmentDocumentList
                            transferDocumentList
                            multipleTransferDocumentList
                            dismissDocumentList
                            vacationDocumentList
                            sickLeaveDocumentList
                            businessTripList


            POST - для пометки обработанных документов
                пример тела
                {
                "objectList": [
                                    {
                                        "type": "transfer",
                                        "guid1C": "feb5c95e-0b1d-11ec-94f8-00155d01140c"
                                    },
                                    {
                                        "type": "sickLeave",
                                        "guid1C": "b6cd8d3f-0970-11ec-94f8-00155d01140c"
                                    }
                                ]
                }

                type может принимать типы:
                                            departament
                                            employee
                                            recruitment
                                            transfer
                                            multipleTransfer
                                            dismiss
                                            vacation
                                            sickLeave
                                            businessTrip

        
        """

        _logger.debug("Загрузка измененных документов из ЗУП zup_sync_personal_doc_change")

        date = datetime.today()


        URL_API = self.env['ir.config_parameter'].sudo().get_param('zup_url_get_change_doc_list')
        if not URL_API:
            raise Exception("Не заполнен параметр zup_url_get_change_doc_list")

        URL_API_REMOVE = self.env['ir.config_parameter'].sudo().get_param('zup_url_remove_change_doc_list')
        if not URL_API_REMOVE:
            raise Exception("Не заполнен параметр zup_url_remove_change_doc_list")
            
        try:
            res = self.zup_search(
                                    url_api=URL_API,
                                )
        except Exception as error:
            self.create_sync_log(date=date,result=error, is_error=True)
            raise error

        if res:
            total_entries, data = res
        else:
            self.create_sync_log(date=date,result='Ошибка. Данные не получены', is_error=True)
            raise Exception('Ошибка. Данные не получены')
        
        if total_entries == 0:
            result = "Новых данных нет"
            self.create_sync_log(result=result)
            return result
        
        n = 0
        message_error = ''
        message_update = ''
        message_create = ''
        guid_change_doc_list = []
        for type_doc in data:
            _logger.debug("Тип документа: %s" % type_doc)

            doc_obj = False
                           
            if type_doc == 'recruitmentDocumentList':
                doc_obj = 'hr.recruitment_doc'
                remove_type  = 'recruitment'
            if type_doc == 'transferDocumentList':
                doc_obj = 'hr.transfer_doc'
                remove_type  = 'transfer'
            if type_doc == 'multipleTransferDocumentList':
                doc_obj = 'hr.transfer_doc'
                remove_type  = 'multipleTransfer'
            if type_doc == 'dismissDocumentList':
                doc_obj = 'hr.termination_doc'
                remove_type  = 'dismiss'
            if type_doc == 'vacationDocumentList':
                doc_obj = 'hr.vacation_doc'
                remove_type  = 'vacation'
            if type_doc == 'sickLeaveDocumentList':
                doc_obj = 'hr.sick_leave_doc'
                remove_type  = 'sickLeave'
            if type_doc == 'businessTripList':
                doc_obj = 'hr.trip_doc'
                remove_type  = 'businessTrip'
            
            if not doc_obj:
                message_error += "не найден объект с именем %s, пропуск \n" % ( type_doc)
                continue # Переход к следующей записи

            for line in data[type_doc]:
                if 'guid1C' in line:
                    guid_1c = line['guid1C']
                    n += 1
                    if type_doc == 'multipleTransferDocumentList':
                        # print(line)
                        result_doc = self.zup_sync_multi_transfer_doc(data=line, is_def_change=True)
                    else:
                        result_doc = self.update_personal_doc(doc_obj=doc_obj, data=line, create_employer=True)
                
                result_create = result_doc['result']
                if result_create:
                    guid_change_doc_list.append({'type': remove_type, 'guid1C': guid_1c}) 
                message_create += result_doc['message_create']
                message_update += result_doc['message_update']
                message_error += result_doc['message_error']



        result ='Всего получено из ЗУП %s записей \n' % n
        if not message_error == '':
            result = "\n Обновление прошло с предупреждениями: \n \n" + message_error
        else:
            result = "\n Обновление прошло успешно \n \n"

        _logger.info(result)

        if not message_update == '':
            result += "\n Обновлены Документы %s: \n" 
            result +=  message_update
        if not message_create == '':
            result += "\n Созданы Документы %s: \n" 
            result +=  message_create

        self.create_sync_log(result=result)

        # print(guid_change_doc_list)

        param = {
            "documentList": guid_change_doc_list
        }

        try:
            if len(guid_change_doc_list)>0:
                res = self.zup_post(
                                    param=param,
                                    url_api=URL_API_REMOVE
                                )
        except Exception as error:
            self.create_sync_log(date=date,result=error, is_error=True)
            raise error

        if not res:
            result += "Ошибка при пометке измененных документов"

        return result






class ZupSyncPassport(models.AbstractModel):
    _name = 'zup.sync_passport'
    _description = 'Синхронизация документов УЛ и адресов ЗУП'
    _inherit = ['zup.connect']

    def zup_sync_passport(self):
        """Загрузка информации по удостоверениям личности и адресам Сотрудников из ЗУП
            Пример ответа:
            {'dataType': 'identityDocumentList', 
		'discription': '', 
		'data': [
					{'employeeGuid1C': 'c3c66a3c-17c2-11e0-86c5-00155d003102', 
					'documentType': 'Паспорт гражданина РФ', 
					'country': '', 
					'series': '77 11', 
					'number': '882255', 
					'issuedBy': 'Территориальным пунктом УФМС России ....', 
					'departamentCode': '790-016', 
					'issueDate': '2011-05-31T00:00:00', 
					'validUntil': '0001-01-01T00:00:00', 
					'birthPlace': '0,Комсомолец,Комсомольский,Кустанайская,Россия', 
					'registrationAddress': {
											'value': '626020, Тюменская обл, .....', 
											'comment': '', 
											'type': 'Адрес', 
											'Country': 'РОССИЯ', 
											'addressType': 'Административно-территориальный', 
											'CountryCode': '643', 
											'ZIPcode': '626020', 
											'area': 'Тюменская', 
											'areaType': 'обл', 
											'city': '', 
											'cityType': '', 
											'street': 'Ульянова', 
											'streetType': 'ул', 
											'id': '', 
											'areaCode': '', 
											'areaId': '', 
											'district': 'sdgfsdfg', 
											'districtType': 'р-н', 
											'districtId': '', 
											'munDistrict': '', 
											'munDistrictType': '', 
											'munDistrictId': '', 
											'cityId': '', 
											'settlement': '', 
											'settlementType': '', 
											'settlementId': '', 
											'cityDistrict': '', 
											'cityDistrictType': '', 
											'cityDistrictId': '', 
											'territory': '', 
											'territoryType': '', 
											'territoryId': '', 
											'locality': 'JHkjhkjk', 
											'localityType': 'с', 
											'localityId': '', 
											'streetId': '', 
											'houseType': 'Дом', 
											'houseNumber': '12', 
											'houseId': '', 
											'buildings': [], 
											'apartments': [{
															'type': 'Квартира', 
															'number': '88'
															}],
											'codeKLADR': '', 
											'oktmo': '', 
											'okato': '', 
											'asInDocument': '', 
											'ifnsFLCode': '', 
											'ifnsULCode': '', 
											'ifnsFLAreaCode': '', 
											'ifnsULAreaCode': ''}, 
					'residenceAddress': ''
				}, ]
		}

        
        """

        _logger.debug("Загрузка информации по удостоверениям личности и адресам Сотрудников из ЗУП zup_sync_passport")

        date = datetime.today()
        URL_API = self.env['ir.config_parameter'].sudo().get_param('zup_url_get_passport_list')
        if not URL_API:
            raise Exception("Не заполнен параметр zup_url_get_passport_list")

        try:
            res = self.zup_search(
                                    url_api=URL_API
                                )
        except Exception as error:
            self.create_sync_log(date=date,result=error, is_error=True)
            raise error

        if res:
            total_entries, data = res
        else:
            self.create_sync_log(date=date,result='Ошибка. Данные не получены', is_error=True)
            raise Exception('Ошибка. Данные не получены')
        
        if total_entries == 0:
            result = "Новых данных нет"
            self.create_sync_log(result=result)
            return result
        
        n = 0
        message_error = ''
        message_update = ''
        message_create = ''
        
        for line in data:
            # print(line)
            if 'employeeGuid1C' in line:
                guid_1c = line['employeeGuid1C'] # Идентификатор сотрудника
                
                record_search = self.env['hr.employee'].search([
                    ('guid_1c', '=', guid_1c)
                ],limit=1)
                if len(record_search) == 0:
                    message_error += "не найден сотрудник с gud1c %s \n" % guid_1c
                    continue # Переход к следующей записи
                
                passport_type = line['documentType'] 
                passport_country = line['country'] 
                if passport_country == '':
                    passport_country = record_search.country_id.name
                passport_series = line['series'] 
                passport_number = line['number'] 
                passport_issued_by = line['issuedBy'] 
                passport_department_code = line['departamentCode'] 

                # Дата выдачи
                passport_date_issue = None
                passport_date_issue_text = line['issueDate']
                if passport_date_issue_text != '' and passport_date_issue_text != '0001-01-01T00:00:00':
                    passport_date_issue = get_date(passport_date_issue_text)
                
                # Срок действия
                passport_date_validity = None
                passport_date_validity_text = line['validUntil'] 
                if passport_date_validity_text != '' and passport_date_validity_text != '0001-01-01T00:00:00':
                    passport_date_validity = get_date(passport_date_validity_text)
                
                # Место рождения
                passport_place_birth = line['birthPlace'] 

                vals = {
                    'passport_type': passport_type,
                    'passport_country': passport_country,
                    'passport_series': passport_series,
                    'passport_number': passport_number,
                    'passport_issued_by': passport_issued_by,
                    'passport_department_code': passport_department_code,
                    'passport_date_issue': passport_date_issue,
                    'passport_date_validity': passport_date_validity,
                    'passport_place_birth': passport_place_birth,
                }



                
                reg_adr = line['registrationAddress'] 
                fact_adr = line['residenceAddress'] 

                adr_list_param = [
                    {'name':'full', 'key':'value'},
                    {'name':'zipcode', 'key':'ZIPcode'},
                    {'name':'area_type', 'key':'areaType'},
                    {'name':'area', 'key':'area'},
                    {'name':'district_type', 'key':'districtType'},
                    {'name':'district', 'key':'district'},
                    {'name':'city_type', 'key':'cityType'},
                    {'name':'city', 'key':'city'},
                    {'name':'locality_type', 'key':'localityType'},
                    {'name':'locality', 'key':'locality'},
                    {'name':'mun_district_type', 'key':'munDistrictType'},
                    {'name':'mun_district', 'key':'munDistrict'},
                    {'name':'settlement_type', 'key':'settlementType'},
                    {'name':'settlement', 'key':'settlement'},
                    {'name':'city_district_type', 'key':'cityDistrictType'},
                    {'name':'city_district', 'key':'cityDistrict'},
                    {'name':'territory_type', 'key':'territoryType'},
                    {'name':'territory', 'key':'territory'},
                    {'name':'street_type', 'key':'streetType'},
                    {'name':'street', 'key':'street'},
                    {'name':'house_type', 'key':'houseType'},
                    {'name':'house', 'key':'houseNumber'},
                    {'name':'stead', 'key':'stead'},
                ]
                    # {'buildings_type':''},
                    # {'buildings':''},
                    # {'apartments_type':''},
                    # {'apartments':''},

                if len(reg_adr) > 0:

                    for param in adr_list_param:
                        vals['ra_%s' % param['name']] = reg_adr[param['key']] if param['key'] in reg_adr else ''
                    
                    buildings_text = reg_adr['buildings'] if 'buildings' in reg_adr else ''
                    if len(buildings_text) > 0:
                        vals['ra_buildings_type'] = buildings_text[0]['type']
                        vals['ra_buildings'] = buildings_text[0]['number']
                    
                    apartments_text = reg_adr['apartments'] if 'apartments' in reg_adr else ''
                    if len(apartments_text) > 0:
                        vals['ra_apartments_type'] = apartments_text[0]['type']
                        vals['ra_apartments'] = apartments_text[0]['number']
                    
                
                if len(fact_adr) > 0:

                    for param in adr_list_param:
                        vals['fa_%s' % param['name']] = fact_adr[param['key']] if param['key'] in fact_adr else ''

                    buildings_text = fact_adr['buildings'] if 'buildings' in fact_adr else ''
                    if len(buildings_text) > 0:
                        vals['fa_buildings_type'] = buildings_text[0]['type']
                        vals['fa_buildings'] = buildings_text[0]['number']
                    
                    apartments_text = fact_adr['apartments'] if 'apartments' in fact_adr else ''
                    if len(apartments_text) > 0:
                        vals['fa_apartments_type'] = apartments_text[0]['type']
                        vals['fa_apartments'] = apartments_text[0]['number']

                message_update += record_search.name + '\n'
                record_search.write(vals)
                
            else:
                message_error += "Отсутствует обязательное поле в запси: %s \n" % line


        result ='Всего получено из ЗУП %s записей \n' % total_entries
        if not message_error == '':
            result = "\n Обновление прошло с предупреждениями: \n \n" + message_error
        else:
            result = "\n Обновление прошло успешно \n \n"

        _logger.info(result)

        if not message_update == '':
            result += "\n Обновлены Документы УЛ и адреса сотрудников: \n" + message_update

        self.create_sync_log(result=result)

        return result