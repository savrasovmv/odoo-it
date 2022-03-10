from odoo import fields, models, api

class BaseHrDoc(models.AbstractModel):
    _name = 'hr.base_doc'
    _description = 'Базовая модель для персональных докуменов HR'

    name = fields.Char(u'Наименование', compute='_get_name', store=True )
    date = fields.Date(string='Дата документа')
    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    number_1c = fields.Char(string='Код 1С', readonly=True)
    employee_guid_1c = fields.Char(string='guid сотрудника 1C', readonly=True)
    posted = fields.Boolean(string='Проведен?')

    employee_id = fields.Many2one("hr.employee", string="Сотрудник HR", compute="_get_employee", store=True)

    @api.depends("employee_id")
    def _get_name(self):
        for line in self:
            if line.employee_id:
                line.name = line.employee_id.name

    @api.depends("employee_guid_1c")
    def _get_employee(self):

        for line in self:
            if line.employee_guid_1c:
                empl_search = self.env['hr.employee'].search([
                    ('guid_1c', '=', line.employee_guid_1c),
                    '|',
                    ('active', '=', False), 
                    ('active', '=', True)
                    ],limit=1)
                line.employee_id = empl_search.id

            else:
                line.employee_id = False



class HrRecruitmentDoc(models.Model):
    _name = "hr.recruitment_doc"
    _inherit = 'hr.base_doc'
    _description = "Прием на работу"
    _order = "date desc"
    
    service_start_date = fields.Date(string='Дата приема', help="Дата с которой сотрудник устроен на работу (первый рабочий день) и исполняет обязанности по должности")
    employment_type = fields.Char(string='Вид занятости', readonly=True)
    job_title = fields.Char(string='Должность', readonly=True)
    department_id = fields.Many2one("hr.department", string="Подразделение", compute="_get_department", store=True)
    department_guid_1c = fields.Char(string="guid подразделение 1C")

    @api.depends("department_guid_1c")
    def _get_department(self):
        for line in self:
            if line.department_guid_1c:
                dep_search = self.env['hr.department'].search([
                    ('guid_1c', '=', line.department_guid_1c),
                    '|',
                    ('active', '=', False), 
                    ('active', '=', True)
                    ],limit=1)
                line.department_id = dep_search.id
            else:
                line.department_id = False




class HrTerminationDoc(models.Model):
    _name = "hr.termination_doc"
    _inherit = 'hr.base_doc'
    _description = "Увольнения"
    _order = "date desc"

    service_termination_date = fields.Date(
        string="Дата увольнения",
        help=(
            "Дата увольнения сотрудника - последний рабочий день"
        ),
    )




class HrVacationDoc(models.Model):
    _name = "hr.vacation_doc"
    _inherit = 'hr.base_doc'
    _description = "Отпуска"
    _order = "date desc"

    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")



class HrTripDoc(models.Model):
    _name = "hr.trip_doc"
    _inherit = 'hr.base_doc'
    _description = "Командировки"
    _order = "date desc"

    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")



class HrSickLeaveDoc(models.Model):
    _name = "hr.sick_leave_doc"
    _inherit = 'hr.base_doc'
    _description = "Больничные"
    _order = "date desc"

    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")



class HrTransferDoc(models.Model):
    _name = "hr.transfer_doc"
    _inherit = 'hr.base_doc'
    _description = "Переводы сотрудников"
    _order = "date desc"

    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")

    old_job_title = fields.Char(string='Старая должность', compute='_get_old', store=True)
    old_department_id = fields.Many2one("hr.department", string="Старое подразделение", compute='_get_old', store=True)
    
    job_title = fields.Char(string='Должность')
    department_guid_1c = fields.Char(string="guid подразделение 1C")

    department_id = fields.Many2one("hr.department", string="Подразделение", compute="_get_department", store=True)

    is_multi_transfer = fields.Boolean(string='Групповой перевод', readonly=True)

    @api.depends("department_guid_1c")
    def _get_department(self):
        for line in self:
            if line.department_guid_1c:
                dep_search = self.env['hr.department'].search([
                    ('guid_1c', '=', line.department_guid_1c),
                    '|',
                    ('active', '=', False), 
                    ('active', '=', True)
                    ],limit=1)
                line.department_id = dep_search.id
            else:
                line.department_id = False


    @api.depends("employee_guid_1c", "job_title", "department_guid_1c")
    def _get_old(self):
        for line in self:
            old_transfer = self.search([
                ('date', '<', line.date),
                ('posted', '=', True),
                ('employee_guid_1c', '=', line.employee_guid_1c),
            ], limit=1)
            
            if len(old_transfer)>0:
                line.old_job_title = old_transfer.job_title
                line.old_department_id = old_transfer.department_id
            else:
                recruitment = self.env['hr.recruitment_doc'].search([
                    ('posted', '=', True),
                    ('employee_guid_1c', '=', line.employee_guid_1c),
                ], limit=1)
                if len(recruitment)>0:
                    line.old_job_title = recruitment.job_title
                    line.old_department_id = recruitment.department_id.id


