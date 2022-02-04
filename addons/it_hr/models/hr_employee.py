from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime
from math import fabs

from odoo import api, fields, models

import unidecode
# from trans import trans


FLAGS = [
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

  

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # 1С
    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    employment_type_1c = fields.Char(string='Вид занятости', readonly=True, groups="hr.group_hr_user",)
    number_1c = fields.Char(string='Номер в 1С', readonly=True)

    # Возраст
    age = fields.Integer(string="Возраст", compute="_compute_age", compute_sudo=True)
    birthday_month = fields.Integer(string="Месяц рождения", compute="_compute_age", store=True, compute_sudo=True)
    birthday_day = fields.Integer(string="День месяца рождения", compute="_compute_age", store=True, compute_sudo=True)

    is_fired = fields.Boolean(string='Уволен')
    
    # Доп Телефоны
    mobile_phone2 = fields.Char(string='Мобильный телефон 2')
    ip_phone = fields.Char(string='Внутренний номер')
    
    is_collective_work_email = fields.Boolean(string='Это общий email', help="Когда установлен, означет что этот рабочий email используется у нескольких сотрудников. При регистрации нового пользователя будет использоваться личная почта")
    personal_email = fields.Char(string='Личный email')

    passport_type = fields.Char(string='Вид удостоверения личности')
    passport_country = fields.Char(string='Страна выдачи')
    passport_series = fields.Char(string='Серия')
    passport_number = fields.Char(string='Номер')
    passport_issued_by = fields.Char(string='Кем выдан')
    passport_department_code = fields.Char(string='Код подразделения')
    passport_date_issue = fields.Date(string='Дата выдачи')
    passport_date_validity = fields.Date(string='Срок действия')
    passport_place_birth = fields.Char(string='Место рождения')
    
    # Адрес регистрации(постоянной/временной)
    ra_full = fields.Char(string='Адрес регистрации(постоянной/временной)')
    ra_zipcode = fields.Char(string='Почтовый индекс')
    ra_area_type = fields.Char(string='Тип области')
    ra_area = fields.Char(string='Область')
    ra_district_type = fields.Char(string='Тип района')
    ra_district = fields.Char(string='Район')
    ra_city_type = fields.Char(string='Тип города')
    ra_city = fields.Char(string='Город')
    ra_locality_type = fields.Char(string='Тип местности')
    ra_locality = fields.Char(string='Местность')
    ra_mun_district_type = fields.Char(string='Тип муниц. р-на')
    ra_mun_district = fields.Char(string='Муниц. р-н')
    ra_settlement_type = fields.Char(string='Тип поселения')
    ra_settlement = fields.Char(string='Поселение')
    ra_city_district_type = fields.Char(string='Тип р-на города')
    ra_city_district = fields.Char(string='Р-н города')
    ra_territory_type = fields.Char(string='Тип территории')
    ra_territory = fields.Char(string='Территории')
    ra_street_type = fields.Char(string='Тип улицы')
    ra_street = fields.Char(string='Улица')
    ra_house_type = fields.Char(string='Тип дома')
    ra_house = fields.Char(string='Дом')
    ra_buildings_type = fields.Char(string='Тип строения дома')
    ra_buildings = fields.Char(string='Номер строения')
    ra_apartments_type = fields.Char(string='Тип квартиры')
    ra_apartments = fields.Char(string='Номер квартиры')
    ra_stead = fields.Char(string='Земельный участок')
  
    ra_end_date = fields.Date(string='Дата окончания временной регистрации')

    # Адрес фактического проживания
    fa_full = fields.Char(string='Адрес фактического проживания')
    fa_zipcode = fields.Char(string='Почтовый индекс')
    fa_area_type = fields.Char(string='Тип области')
    fa_area = fields.Char(string='Область')
    fa_district_type = fields.Char(string='Тип района')
    fa_district = fields.Char(string='Район')
    fa_city_type = fields.Char(string='Тип города')
    fa_city = fields.Char(string='Город')
    fa_locality_type = fields.Char(string='Тип местности')
    fa_locality = fields.Char(string='Местность')
    fa_mun_district_type = fields.Char(string='Тип муниц. р-на')
    fa_mun_district = fields.Char(string='Муниц. р-н')
    fa_settlement_type = fields.Char(string='Тип поселения')
    fa_settlement = fields.Char(string='Поселение')
    fa_city_district_type = fields.Char(string='Тип р-на города')
    fa_city_district = fields.Char(string='Р-н города')
    fa_territory_type = fields.Char(string='Тип территории')
    fa_territory = fields.Char(string='Территории')
    fa_street_type = fields.Char(string='Тип улицы')
    fa_street = fields.Char(string='Улица')
    fa_house_type = fields.Char(string='Тип дома')
    fa_house = fields.Char(string='Дом')
    fa_buildings_type = fields.Char(string='Тип строения дома')
    fa_buildings = fields.Char(string='Номер строения')
    fa_apartments_type = fields.Char(string='Тип квартиры')
    fa_apartments = fields.Char(string='Номер квартиры')
    fa_stead = fields.Char(string='Земельный участок')
    
    
    # AD
    ad_users_id = fields.Many2one("ad.users", string="Пользователь AD")

    # Справочник
    # is_view_adbook = fields.Boolean(string='Отоброжать в справочнике контактов', default=True)
    # sequence = fields.Integer(string=u"Сортировка", help="Сортировка")


    # Даты приема и увольнения
    service_start_date = fields.Date(
        string="Дата приема",
        groups="hr.group_hr_user",
        tracking=True,
        help=(
            "Дата с которой сотрудник устроен на работу (первый рабочий день) и исполняет обязанности по должности"
            
        ),
    )
    service_termination_date = fields.Date(
        string="Дата увольнения",
        groups="hr.group_hr_user",
        tracking=True,
        help=(
            "Дата увольнения сотрудника - последний рабочий день"
        ),
    )
    service_duration = fields.Integer(
        string="Отработано в днях",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration",
        help="Отработано дней в должности",
    )
    service_duration_years = fields.Integer(
        string="Отработано, лет",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration_display",
    )
    service_duration_months = fields.Integer(
        string="Отработано, мес",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration_display",
    )
    service_duration_days = fields.Integer(
        string="Отработано, дней",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration_display",
    )
    

    service_status = fields.Selection([
        ('work', 'На работе'),
        ('vacation', 'Отпуск'),
        ('trip', 'Командировка'),
        ('sick_leave', 'Больничный'),
        ('fired', 'Уволен'),
    ], string='Статус', default='work', compute="_compute_status")

    service_status_start_date = fields.Date(string='Начало', compute="_compute_status")
    service_status_end_date = fields.Date(string='Окончание', compute="_compute_status")

    # @api.depends("user_account_control")
    # def _get_user_account_control_result(self):
    #     for record in self:
    #         if record.user_account_control:
    #             result = ''
    #             for value in FLAGS:
    #                 if (int(record.user_account_control) | int(value[0])) == int(record.user_account_control):
    #                     result += value[1] + ','
    #             record.user_account_control_result = result
    #         else:
    #             record.user_account_control_result = ''


    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            age = 0
            birthday_month = 0
            birthday_day = 0
            if record.birthday:
                age = relativedelta(fields.Date.today(), record.birthday).years
                birthday_month = record.birthday.month
                birthday_day = record.birthday.day
            record.age = age
            record.birthday_month = birthday_month
            record.birthday_day = birthday_day


    @api.depends("service_start_date", "service_termination_date")
    def _compute_service_duration(self):
        for record in self:
            service_until = record.service_termination_date or fields.Date.today()
            if record.service_start_date and service_until > record.service_start_date:
                service_since = record.service_start_date
                service_duration = fabs(
                    (service_until - service_since) / timedelta(days=1)
                )
                record.service_duration = int(service_duration)
            else:
                record.service_duration = 0

    @api.depends("service_start_date", "service_termination_date")
    def _compute_service_duration_display(self):
        for record in self:
            service_until = record.service_termination_date or fields.Date.today()
            if record.service_start_date and service_until > record.service_start_date:
                service_duration = relativedelta(
                    service_until, record.service_start_date
                )
                record.service_duration_years = service_duration.years
                record.service_duration_months = service_duration.months
                record.service_duration_days = service_duration.days
            else:
                record.service_duration_years = 0
                record.service_duration_months = 0
                record.service_duration_days = 0
    

    # NOTE: Support odoo/odoo@90731ad170c503cdfe89a9998fa1d1e2a5035c86
    def _get_date_start_work(self):
        return self.service_start_date or super()._get_date_start_work()

        

    def _compute_status(self):
        """Установка статуса сотрудника, на основании документов Отпуск, Командировка, Больничный"""

        date = datetime.today().date()
        for line in self:
            # Сброс по умолчанию
            line.service_status = 'work'
            line.service_status_start_date = False
            line.service_status_end_date = False

            vacation = self.env['hr.vacation_doc'].search([
                ('start_date', '<=', date),
                ('end_date', '>=', date),
                ('posted', '=', True),
                ('employee_id', '=', line.id),
            ], limit=1, order='date desc')

            if len(vacation)>0:
                line.service_status = 'vacation'
                line.service_status_start_date = vacation.start_date
                line.service_status_end_date = vacation.end_date


            trip = self.env['hr.trip_doc'].search([
                ('start_date', '<=', date),
                ('end_date', '>=', date),
                ('posted', '=', True),
                ('employee_id', '=', line.id),
            ], limit=1, order='date desc')

            if len(trip)>0:
                line.service_status = 'trip'
                line.service_status_start_date = trip.start_date
                line.service_status_end_date = trip.end_date


            sick_leave = self.env['hr.sick_leave_doc'].search([
                ('start_date', '<=', date),
                ('end_date', '>=', date),
                ('posted', '=', True),
                ('employee_id', '=', line.id),
            ], limit=1, order='date desc')

            if len(sick_leave)>0:
                line.service_status = 'sick_leave'
                line.service_status_start_date = sick_leave.start_date
                line.service_status_end_date = sick_leave.end_date

            

    def get_status(self):
        date = datetime.today().date()

        for line in self:
            # # Сброс по умолчанию
            # line.service_status = 'work'
            # line.service_status_start_date = False
            # line.service_status_end_date = False

            # vacation = self.env['hr.vacation_doc'].search([
            #     ('start_date', '<=', date),
            #     ('end_date', '>=', date),
            #     ('posted', '=', True),
            #     ('employee_id', '=', line.id),
            # ], limit=1, order='date desc')

            # if len(vacation)>0:
            #     line.service_status = 'vacation'
            #     line.service_status_start_date = vacation.start_date
            #     line.service_status_end_date = vacation.end_date


            # trip = self.env['hr.trip_doc'].search([
            #     ('start_date', '<=', date),
            #     ('end_date', '>=', date),
            #     ('posted', '=', True),
            #     ('employee_id', '=', line.id),
            # ], limit=1, order='date desc')

            # if len(trip)>0:
            #     line.service_status = 'trip'
            #     line.service_status_start_date = trip.start_date
            #     line.service_status_end_date = trip.end_date


            # sick_leave = self.env['hr.sick_leave_doc'].search([
            #     ('start_date', '<=', date),
            #     ('end_date', '>=', date),
            #     ('posted', '=', True),
            #     ('employee_id', '=', line.id),
            # ], limit=1, order='date desc')

            # if len(sick_leave)>0:
            #     line.service_status = 'sick_leave'
            #     line.service_status_start_date = sick_leave.start_date
            #     line.service_status_end_date = sick_leave.end_date

            fired = self.env['hr.termination_doc'].search([
                ('service_termination_date', '<=', date),
                ('posted', '=', True),
                ('employee_id', '=', line.id),
            ], limit=1, order='date desc')

            if len(fired)>0:
                line.service_status = 'fired'
                line.service_termination_date = fired.service_termination_date
                line.is_fired = True
            else:
                line.service_termination_date = False
                line.is_fired = False


    def set_fired(self, fired=True, date=False):
        self.is_fired = fired
        if fired:
            self.service_termination_date = date
            self.service_status = 'fired'
        else:
            self.service_termination_date = False
            self.service_status = 'work'


    

    def get_registration_email(self):
        """Возвращает адрес электронный почты для регистрации, рабочий (при условии наличии персонального адреса) или личный"""

        self.ensure_one()
        email = False
        if self.work_email and not self.is_collective_work_email:
            email = self.work_email
        elif self.personal_email:
            email = self.personal_email
        return email



    # def action_update_user_and_partner_by_employee(self):
    #     """Обновляет информацию в пользователях и партнерах из сотрудников"""

    #     for record in self:
    #         email = record.get_registration_email()
            
    #         mobile = record.mobile_phone if self.mobile_phone else ''
    #         mobile += ' ' + self.mobile_phone2 if self.mobile_phone2 else ''

    #         if record.user_id and email:
    #             user_id = record.user_id
    #             user_id.name = record.name
    #             user_id.login = email
    #             user_id.phone = record.ip_phone
    #             user_id.mobile = mobile
    #             user_id.image_1920 = record.image_1920
    #             record.active = False if record.is_fired else True
    #             user_id.active = False if record.is_fired else True
                
    #             if user_id.partner_id:
    #                 partner_id = user_id.partner_id
    #                 partner_id.name = record.name
    #                 partner_id.parent_id = record.company_id.partner_id.id
    #                 partner_id.company_id = record.company_id.id
    #                 partner_id.company_type = 'person'
    #                 partner_id.email = email
    #                 partner_id.function = record.job_title
    #                 partner_id.phone = record.ip_phone
    #                 partner_id.mobile = mobile
    #                 partner_id.employee = True
    #                 partner_id.image_1920 = record.image_1920
    #                 partner_id.active = False if record.is_fired else True



    @api.model
    def disabled_users_fired_employee(self):
        """Отключает учетные записи уволенных сотрудников"""

        empls = self.env['hr.employee'].sudo().search([
            ('is_fired', '=', True),
            ])
        for empl in empls:
            if empl.user_id:
                if empl.user_id.active:
                    empl.user_id.active = False
                    if empl.user_id.partner_id:
                        empl.user_id.partner_id.active = False      



    def test_work_email_by_name(self):
        """Проверяет соответствует ли рабочий email ФИО сотрудника, возвращает Истина если соответствует"""
        self.ensure_one()
        if self.work_email:
            surname = self.name.split(' ')[0]
            surname = unidecode.unidecode('%s' % surname)
            surname = surname.replace('\'', '')
            f = self.work_email.find(surname)
            if f==0:
                return True
            else:
                return False

        return True

    def action_test_work_email_by_name(self):
        """Действие. Проверяет все рабочии адреса на соответствие ФИО"""
        records = self.search([])
        for record in records:
            if not record.test_work_email_by_name():
                record.is_collective_work_email = True   
            else:
                record.is_collective_work_email = False   

    def action_set_all_is_collective_work_email_false(self):
        """Действие. Устанавливает у все сотрудников is_collective_work_email=False"""
        records = self.search([])
        for record in records:
            record.is_collective_work_email = False   


    # Отключить действие синхронизации при изменении пользователя
    # функция _sync_user находится в HR модуле hr_employee.py
    def _sync_user(self, user, employee_has_image=False):
        return {}



    def action_create_user_by_employee(self):
        """Создает пользователя из сотрудника, при условии наличия учетной записи в АД"""

        self.ensure_one()
        email = self.work_email
        if not email:
            err = "Нет электронного адреса"
            raise ValueError(str(err))
        if self.user_id:
            err = "Пользователь уже зарегистрирован"
            raise ValueError(str(err))
        
        if not self.ad_users_id:
            err = "Пользователь не зарегистрирован в АД "
            raise ValueError(str(err))

        login = self.ad_users_id.username.lower()

        if not login:
            err = "Не задан username для пользователя"
            raise ValueError(str(err))

        mobile = self.mobile_phone if self.mobile_phone else ''
        mobile += ' ' + self.mobile_phone2 if self.mobile_phone2 else ''

        partner_vals = {
            'name': self.name,
            'parent_id': self.company_id.partner_id.id,
            'company_id': self.company_id.id,
            'company_type': 'person',
            'email': email,
            'function': self.job_title,
            'phone': self.ip_phone,
            'mobile': mobile,
            'employee': True,
            'image_1920': self.image_1920,
        }

        part_search = self.env['res.partner'].search([
            ('name', '=', self.name),
            ('email', '=', email)
        ], limit=1)
        

        if len(part_search)>0:
            part_search.write(partner_vals)
            new_partner = part_search
        else:
            new_partner = self.env['res.partner'].create(partner_vals)


        new_user = False
        user_vals = {
            'name': self.name,
            'login': login,
            'partner_id': new_partner.id,
        }

        user_search = self.env['res.users'].search([
            ('login', '=', login)
        ], limit=1)
        if len(user_search)>0:
            user_search.write(user_vals)
            new_user = user_search
        else:
            new_user = self.env['res.users'].with_context(no_reset_password=True).create(user_vals)
        
        if new_user:
            self.user_id = new_user.id
            