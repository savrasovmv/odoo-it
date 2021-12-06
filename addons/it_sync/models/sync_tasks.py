# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime



class SyncTasks(models.Model):
    _name = "sync.tasks"
    _description = "Задачи синхронизации"
    _order = "name"

    name = fields.Char(u'Наименование', required=True)
    date = fields.Datetime(string='Дата')
    obj_create = fields.Char(u'Модель')
    obj_create_name = fields.Char(u'Имя модели')
    obj_create_id = fields.Integer(u'Id объекта')
    obj_data = fields.Text(string='Данные объекта')
    is_completed = fields.Boolean(string='Выполнена?', default=False)
    is_canceled = fields.Boolean(string='Отменить?', default=False)
    is_updated = fields.Boolean(string='Обновить?', default=False)

    result = fields.Text(string='Результат', default='')
    obj_url = fields.Char(string='Ссылка на объект', compute='_get_url')

    def _get_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            rec.obj_url = '%s/web#id=%s&model=%s&view_type=form' % (base_url, rec.obj_create_id, rec.obj_create)

    

    def get_task(self, obj):
        return self.search([
            ('obj_create', '=', obj._name),
            ('obj_create_id', '=', obj.id),
            ])


    def create_task(self, obj):

        standart_vals = {
            'obj_create': obj._name,
            'obj_create_name': obj._description,
            'obj_create_id': obj.id,
            'obj_data': obj.read(),
        }

        doc_vals = {}

        current_task = self.get_task(obj)

        if obj._name == 'hr.recruitment_doc':
            doc_vals = {
                'name': 'Создать пользователя',
                'date': obj.service_start_date,
            }

        if obj._name == 'hr.termination_doc':
            doc_vals = {
                'name': 'Удалить пользователя',
                'date': obj.service_termination_date,
            }

        if obj._name == 'hr.transfer_doc':
            doc_vals = {
                'name': 'Перевод пользователя',
                'date': obj.start_date,
            }
        
        vals = {**standart_vals, **doc_vals}
        if current_task:
            current_task.write(vals)
            if current_task.is_completed:
                current_task.is_updated = True

        else:
            self.create(vals)



    def update_task(self, obj):
        current_task = self.get_task(obj)

        standart_vals = {
            'obj_create': obj._name,
            'obj_create_name': obj._description,
            'obj_create_id': obj.id,
            'obj_data': current_task.obj_data + '\n' + obj.read(),

        }
        doc_vals = {}


        if obj._name == 'hr.recruitment_doc':
            doc_vals = {
                'name': 'Создать пользователя',
                'date': obj.service_start_date,
            }

        if obj._name == 'hr.termination_doc':
            doc_vals = {
                'name': 'Удалить пользователя',
                'date': obj.service_termination_date,
            }

        if obj._name == 'hr.transfer_doc':
            doc_vals = {
                'name': 'Перевод пользователя',
                'date': obj.start_date,
            }
        

        vals = {**standart_vals, **doc_vals}
        if obj.posted and not current_task:
            self.create(vals)
        elif obj.posted and current_task:
            # t = self.browse(self.id)
            current_task.write(vals)
            if current_task.is_completed:
                current_task.is_updated = True
            if current_task.is_canceled:
                current_task.is_canceled = False

        
        if not obj.posted and current_task:
            if current_task.is_completed:
                current_task.is_canceled = True
            else:
                current_task.unlink()

    

    def do_tasks_action(self):

       
        if not self.is_completed or self.is_canceled or self.is_updated:
            if self.obj_create == 'hr.recruitment_doc':
                # create user AD
                doc = self.env[self.obj_create].sudo().browse(self.obj_create_id)
                if doc:
                    self.env['ad.connect'].sudo().ldap_create_user(doc.employee_id)



            if self.obj_create == 'hr.termination_doc':
                # disabled user AD
                pass
            if self.obj_create == 'hr.transfer_doc':
                # update user AD
                pass
            
        

    def do_list_tasks_action(self):
        
        date = datetime.today()

        search_task = self.search([
            ('date', '<=', date),
            '|','|',
            ('is_completed', '=', False),
            ('is_updated', '=', True),
            ('is_canceled', '=', True),
        ])

        for line in search_task:
            line.do_tasks_action()
        
        
                
    def send_mail(self):
        mail_template = self.env.ref('it_sync.tasks_user_create_email_template')
        mail_template.send_mail(self.id, force_send=True)

                
    