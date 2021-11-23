from odoo import fields, models, api

class HrRecruitmentDoc(models.Model):
    _name = "hr.recruitment_doc"
    _description = "Прием на работу"
    _order = "date desc"

    name = fields.Char(u'Наименование', compute='_get_name', store=True )
    date = fields.Date(string='Дата документа')
    service_start_date = fields.Date(string='Дата приема', help="Дата с которой сотрудник устроен на работу (первый рабочий день) и исполняет обязанности по должности")

    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    number_1c = fields.Char(string='Код 1С', readonly=True)
    employee_guid_1c = fields.Char(string='guid сотрудника 1C', readonly=True)
    employment_type = fields.Char(string='Вид занятости', readonly=True)
    job_title = fields.Char(string='Должность', readonly=True)
    department_id = fields.Many2one("hr.department", string="Подразделение")
    department_guid_1c = fields.Char(string="guid подразделение 1C")
    posted = fields.Boolean(string='Проведен?')

    employee_id = fields.Many2one("hr.employee", string="Сотрудник HR")


    @api.depends("employee_id")
    def _get_name(self):
        for line in self:
            if line.employee_id:
                line.name = line.employee_id.name

    @api.model
    def create(self, vals):
        doc = super(HrRecruitmentDoc, self).create(vals)
        if vals.get('posted'):
            self.env['sync.tasks'].sudo().create_task(self)
        return doc
    
    def write(self, vals):
        doc = super(HrRecruitmentDoc, self).write(vals)
        self.env['sync.tasks'].sudo().update_task(self)
        return doc


class HrTerminationDoc(models.Model):
    _name = "hr.termination_doc"
    _description = "Увольнения"
    _order = "date desc"

    name = fields.Char(u'Наименование', compute='_get_name', store=True )
    date = fields.Date(string='Дата документа', readonly=True)
    service_termination_date = fields.Date(
        string="Дата увольнения",
        help=(
            "Дата увольнения сотрудника - последний рабочий день"
        ),
    )

    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    number_1c = fields.Char(string='Код 1С', readonly=True)
    employee_guid_1c = fields.Char(string='guid сотрудника 1C', readonly=True)
    posted = fields.Boolean(string='Проведен?')

    employee_id = fields.Many2one("hr.employee", string="Сотрудник HR", readonly=True)

    @api.depends("employee_id")
    def _get_name(self):
        for line in self:
            if line.employee_id:
                line.name = line.employee_id.name

    @api.model
    def create(self, vals):
        doc = super(HrTerminationDoc, self).create(vals)
        if vals.get('posted'):
            self.env['sync.tasks'].sudo().create_task(self)
        return doc
    
    def write(self, vals):
        doc = super(HrTerminationDoc, self).write(vals)
        self.env['sync.tasks'].sudo().update_task(self)
        return doc

    # def write(self, vals):
    #     result = super(Survey, self).write(vals)
    #     if 'certification_give_badge' in vals:
    #         return self.sudo()._handle_certification_badges(vals)
    #     return result

    



class HrVacationDoc(models.Model):
    _name = "hr.vacation_doc"
    _description = "Отпуска"
    _order = "date desc"

    name = fields.Char(u'Наименование', compute='_get_name', store=True )
    date = fields.Date(string='Дата документа', readonly=True)
    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")

    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    number_1c = fields.Char(string='Код 1С', readonly=True)
    employee_guid_1c = fields.Char(string='guid сотрудника 1C', readonly=True)
    posted = fields.Boolean(string='Проведен?', readonly=True)

    employee_id = fields.Many2one("hr.employee", string="Сотрудник HR", readonly=True)

    @api.depends("employee_id")
    def _get_name(self):
        for line in self:
            if line.employee_id:
                line.name = line.employee_id.name


class HrTripDoc(models.Model):
    _name = "hr.trip_doc"
    _description = "Командировки"
    _order = "date desc"

    name = fields.Char(u'Наименование', compute='_get_name', store=True )
    date = fields.Date(string='Дата документа', readonly=True)
    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")

    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    number_1c = fields.Char(string='Код 1С', readonly=True)
    employee_guid_1c = fields.Char(string='guid сотрудника 1C', readonly=True)
    posted = fields.Boolean(string='Проведен?', readonly=True)

    employee_id = fields.Many2one("hr.employee", string="Сотрудник HR", readonly=True)

    @api.depends("employee_id")
    def _get_name(self):
        for line in self:
            if line.employee_id:
                line.name = line.employee_id.name



class HrSickLeaveDoc(models.Model):
    _name = "hr.sick_leave_doc"
    _description = "Больничные"
    _order = "date desc"

    name = fields.Char(u'Наименование', compute='_get_name', store=True )
    date = fields.Date(string='Дата документа', readonly=True)
    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")

    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    number_1c = fields.Char(string='Код 1С', readonly=True)
    employee_guid_1c = fields.Char(string='guid сотрудника 1C', readonly=True)
    posted = fields.Boolean(string='Проведен?', readonly=True)

    employee_id = fields.Many2one("hr.employee", string="Сотрудник HR", readonly=True)

    @api.depends("employee_id")
    def _get_name(self):
        for line in self:
            if line.employee_id:
                line.name = line.employee_id.name



class HrTransferDoc(models.Model):
    _name = "hr.transfer_doc"
    _description = "Переводы сотрудников"
    _order = "date desc"

    name = fields.Char(u'Наименование', compute='_get_name', store=True )
    date = fields.Date(string='Дата документа', readonly=True)
    start_date = fields.Date(string="Начало")
    end_date = fields.Date(string="Окончание")

    guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    number_1c = fields.Char(string='Код 1С', readonly=True)
    employee_guid_1c = fields.Char(string='guid сотрудника 1C', readonly=True)
    posted = fields.Boolean(string='Проведен?', readonly=True)

    old_job_title = fields.Char(string='Старая должность', compute='_get_old', store=True)
    old_department_id = fields.Many2one("hr.department", string="Старое подразделение", compute='_get_old', store=True)
    
    job_title = fields.Char(string='Должность')
    department_id = fields.Many2one("hr.department", string="Подразделение")


    employee_id = fields.Many2one("hr.employee", string="Сотрудник HR", readonly=True)

    is_multi_transfer = fields.Boolean(string='Групповой перевод', readonly=True)

    @api.depends("employee_id")
    def _get_name(self):
        for line in self:
            if line.employee_id:
                line.name = line.employee_id.name

    @api.depends("job_title", "department_id")
    def _get_old(self):
        for line in self:
            old_transfer = self.search([
                ('date', '<', line.date),
                ('posted', '=', True),
                ('employee_id', '=', line.employee_id.id),
            ], limit=1)
            
            if len(old_transfer)>0:
                line.old_job_title = old_transfer.job_title
                line.old_department_id = old_transfer.department_id
            else:
                recruitment = self.env['hr.recruitment_doc'].search([
                    ('posted', '=', True),
                    ('employee_id', '=', line.employee_id.id),
                ], limit=1)
                if len(recruitment)>0:
                    line.old_job_title = recruitment.job_title
                    line.old_department_id = recruitment.department_id.id

