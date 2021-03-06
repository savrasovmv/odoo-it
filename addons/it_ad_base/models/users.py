# -*- coding: utf-8 -*-

from odoo import fields, models, api
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, LEVEL
import json
import base64
import re

from openpyxl import Workbook
import os, fnmatch
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font
from datetime import datetime



class AdOrganization(models.Model):
    _name = "ad.organizacion"
    _description = "Организация AD"
    _order = "name"

    name = fields.Char(u'Наименование', required=True)
    active = fields.Boolean('Active', default=True)
    hr_department_id = fields.Many2one("hr.department", string="HR Подразделене")
    domain_name = fields.Char(string='Домен', help="Для userPrincipalName: username + @ + domain_name")
    web_page = fields.Char(string='Веб-страница')

class AdOU(models.Model):
    _name = "ad.ou"
    _description = "Организационное подразделение AD"
    _order = "name"

    name = fields.Char(u'Наименование', required=True)
    active = fields.Boolean('Active', default=True)
    is_default = fields.Boolean(string='AD контейнер по умолчанию', help='Если установлено, новые пользователи не вошедшие не в одну группу будут создаваться тут')
    hr_department_id = fields.Many2one("hr.department", string="HR Подразделене")
    organizacion_id = fields.Many2one("ad.organizacion", string="Организация")



class AdDepartment(models.Model):
    _name = "ad.department"
    _description = "Подразделения AD"
    _order = "name"

    name = fields.Char(u'Наименование', required=True)
    ou_id = fields.Many2one("ad.ou", string="Организационное подразделение AD")
    active = fields.Boolean('Active', default=True)


class AdGroup(models.Model):
    _name = "ad.group"
    _description = "Группы AD"
    _order = "name"

    name = fields.Char(u'Наименование', required=True)

    distinguished_name = fields.Char(u'AD distinguishedName')
    account_name = fields.Char(u'sAMAccountName')
    object_SID = fields.Char(u'AD objectSID')
    is_ldap = fields.Boolean('LDAP?', default=False)

    active = fields.Boolean('Active', default=True)
    is_managed = fields.Boolean('Управляемая', default=False, help="Включите, для управления вхождения пользователя в эту группу в форме Пользователя")



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


class AdUsers(models.Model):
    _name = "ad.users"
    _description = "Пользователи AD"
    _order = "name"

    name = fields.Char(u'ФИО', required=True)
    first_name = fields.Char(u'Имя', compute="_compute_nemes_field", store=True)
    last_name = fields.Char(u'Фамилия', compute="_compute_nemes_field", store=True)
    middle_name = fields.Char(u'Отчество', compute="_compute_nemes_field", store=True)
    employee_id = fields.Many2one("hr.employee", string="Сотрудник")

    active = fields.Boolean('Active', default=True)
    is_del = fields.Boolean('Удален из АД', default=False, readonly=True)
    is_ldap = fields.Boolean('LDAP?', default=False, readonly=True)
    is_fit_middle = fields.Boolean('Отчетсво совпадает с middleName АД?', compute="_compute_is_fit_middle", store=True)

    # organization_id = fields.Many2one("ad.organizacion", string="Организация", compute="_compute_organization", store=True)
    # company_id = fields.Many2one('res.company', string='Компания', compute="_compute_company", store=True)

    ou_id = fields.Many2one("ad.ou", string="Организационное подразделение")
    department_id = fields.Many2one("ad.department", string="Подразделение")
    title = fields.Char(u'Должность')

    ip_phone = fields.Char(u'Вн. номер')
    phone = fields.Char(u'Мобильный телефон 1')
    sec_phone = fields.Char(u'Мобильный телефон 2')

    email = fields.Char(u'E-mail')

    username = fields.Char(u'sAMAccountName', readonly=True)
    ad_middle_name = fields.Char(u'middleName', readonly=True)

    company = fields.Char(u'Company', readonly=True)
    display_name = fields.Char(u'displayName', readonly=True)
    user_principal_name = fields.Char(u'userPrincipalName', readonly=True)
    sn = fields.Char(u'SN', readonly=True)
    home_drive = fields.Char(u'homeDrive', readonly=True)
    home_directory = fields.Char(u'homeDirectory', readonly=True)
    physical_delivery_office_name = fields.Char(u'physicalDeliveryOfficeName', readonly=True)
    www_home_page = fields.Char(u'wWWHomePage', readonly=True)

    pwd_last_set = fields.Char(u'pwdLastSet', readonly=True)
    date_pwd_last_set = fields.Datetime('Дата изменения пароля', compute="_compute_date_pwd_last_set", store=True)
    
    when_changed = fields.Char(u'whenChanged', readonly=True)
    date_when_changed = fields.Datetime('Дата изменения в АД', compute="_compute_date_when_changed", store=True)

    when_created = fields.Char(u'whenCreated', readonly=True)
    date_when_created = fields.Datetime('Дата создания в АД', compute="_compute_date_when_created", store=True)
    
    object_SID = fields.Char(u'objectSID', readonly=True)
    distinguished_name = fields.Char(u'distinguishedName', readonly=True)
    user_account_control = fields.Char(u'userAccountControl', readonly=True)
    user_account_control_result = fields.Char(u'UAC результат', compute="_get_user_account_control_result", store=True)

    photo = fields.Binary('Фото', default=False)

    users_group_line = fields.One2many('ad.users_group_line', 'users_id', string=u"Строка Группы AD")

    @api.depends("name")
    def _compute_nemes_field(self):
        """Разделяет ФИО на Ф И и О"""
        for record in self:
            fio = record.name.split(' ')
            if len(fio)>1:
                record.last_name = fio[0]
                record.first_name = fio[1]
            if len(fio)>2:
                record.middle_name = fio[2]

    def _get_date_by_str(self, date_str):
        try:
            return datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
        except:
            return False



    @api.depends("pwd_last_set")
    def _compute_date_pwd_last_set(self):
        """Преобразование текстовой даты в дату поле Дата изменения пароля"""
        for record in self:
            record.date_pwd_last_set = self._get_date_by_str(record.pwd_last_set)

    @api.depends("when_changed")
    def _compute_date_when_changed(self):
        """Преобразование текстовой даты в дату поле Дата изменения в АД"""
        for record in self:
            record.date_when_changed = self._get_date_by_str(record.when_changed)
    
    @api.depends("when_created")
    def _compute_date_when_created(self):
        """Преобразование текстовой даты в дату поле Дата создания в АД"""
        for record in self:
            record.date_when_created = self._get_date_by_str(record.when_created)




    @api.depends("middle_name", "ad_middle_name")
    def _compute_is_fit_middle(self):
        """Расчитывает соврадает ли установленное middleName в АД с фактическим Отчеством"""
        for record in self:
            if record.ad_middle_name and record.middle_name==record.ad_middle_name:
                record.is_fit_middle = True
            else:
                record.is_fit_middle = False

                


    def get_employee_by_name(self):
        """Связывает пользователей АД с сотрудниками"""
        for user in self:
            empl = self.env['hr.employee'].search([
                ('name', '=', user.name),
                '|',
                ('active', '=', False), 
                ('active', '=', True)

            ], limit=1)


            if len(empl)>0:
                user.employee_id = empl[0].id
                employee = self.env['hr.employee'].browse(empl[0].id)
               
                if user.photo:
                    employee.image_1920 = user.photo
                else:
                    employee._default_image()

                employee.ad_users_id = user.id
                employee.mobile_phone = user.phone
                employee.mobile_phone2 = user.sec_phone
                employee.ip_phone = user.ip_phone
                employee.work_email = user.email

            else:
                user.employee_id = None

    
    def join_user_and_employee(self, full_sync=False):
        for user in self.search([]):
            if not user.employee_id or full_sync:
                user.get_employee_by_name()



    @api.model
    def set_del_user(self):
        """Устанавливает пользователю признак удаленного из АД и не активного, is_del = True, active = False"""
        
        for record in self:
            record.active = False
            record.is_del = True



    def _get_user_account_control_result(self):
        for record in self:
            if record.user_account_control:
                result = ''
                for value in flags:
                    if (int(record.user_account_control) | int(value[0])) == int(record.user_account_control):
                        result += value[1] + ','
                record.user_account_control_result = result

    def action_update_from_ldap(self):
        pass


    def action_update_employee_by_user(self):
        """Обновляет данные сотрудника из пользователя (тел, фото, email)"""
        for user in self:
            if user.employee_id:
                employee = user.employee_id
                if user.photo:
                    employee.image_1920 = user.photo
                else:
                    employee._default_image()

                employee.mobile_phone = user.phone
                employee.mobile_phone2 = user.sec_phone
                employee.ip_phone = user.ip_phone
                employee.work_email = user.email


    

    
class UsersGroupLine(models.Model):
    _name = "ad.users_group_line"
    _description = "Строка Установка групп пользователя"
    _order = "name"

    name = fields.Char(u'Наименование', compute="_get_name")
    group_id = fields.Many2one("ad.group", string="Группа AD")
    is_enable = fields.Boolean(string='Включена?')

    users_id = fields.Many2one('ad.users',
		ondelete='cascade', string=u"Пользователь", required=True)

    @api.depends("group_id")
    def _get_name(self):
        self.name = self.group_id.name

    




