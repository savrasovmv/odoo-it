from odoo import fields, models, api
from odoo import tools
from odoo.tools import html2plaintext
import base64


class DbSyncServer(models.Model):
    """Модель настройка для подключения к внешнему серверу Odoo"""

    _name = "db.sync_server"
    _description = "Сервер для синхронизации"

    name = fields.Char("Имя", required=True)
    server_url = fields.Char("URL", required=True, help="Например https://test.domain.ru")
    server_port = fields.Integer("Порт", required=True, default=8069)
    db_name = fields.Char("Имя БД", required=True)
    login = fields.Char("Имя пользователя", required=True)
    password = fields.Char("Пароль", required=True, password=True)
    sync_model_ids = fields.One2many(
        "db.sync_model", "server_id", "Модели", ondelete="cascade"
    )

    def set_sequence_model_child(self, sequence):
        """Проход по моделям и установка Порядка для зависимых моделий ниже от зависимых"""
        child = False
        for sync_model in self.sync_model_ids:
            # print("++++sync_model", sync_model.name)
            if sync_model.sequence>sequence:
                if sync_model.relation_sync_model_ids:
                    
                    for rel_model in sync_model.relation_sync_model_ids:
                        # print("++++rel_model", rel_model.name)
                        pet = False
                        #  Проверяем не петля ли, т.е не взаимозависимые модели
                        for rel_rel in rel_model.relation_sync_model_id.relation_sync_model_ids:
                            if rel_rel.sync_model_id.id == sync_model.id:
                                pet = True

                        
                        # print("++++pet", pet)
                        # print("++++rel_model.relation_sync_model_id.sequence", rel_model.relation_sync_model_id.sequence)
                        # print("++++sync_model.sequence", sync_model.sequence)
                        # Если у зависимой модели порядок меньше или равен порядку связанной и не петля, то увелииваем порядок
                        if rel_model.relation_sync_model_id.sequence>=sync_model.sequence and not pet:
                            # print("++++child=True")
                            child = True
                            sync_model.sequence = rel_model.sync_model_id.sequence + 10
                            
        if child:
            return True
        else:
            return False
                    



    def set_sequence_model(self):
        """Установка корням порядка 1 дочерним 10 и запуск прохода по дочерним"""
        for sync_model in self.sync_model_ids:
            if not sync_model.relation_sync_model_ids:
                sync_model.sequence = 1 
            else:
                sync_model.sequence = 10
        
        n = 0
        child = True
        while child and n<1000:
            child = self.set_sequence_model_child(1)
            n+=1



class DbSyncModel(models.Model):
    """Модели БД для синхронизации"""

    _name = "db.sync_model"
    _description = "Модели синхронизации"
    _order = "sequence"

    name = fields.Char("Наименование", related="ir_model_id.name", store=True)
    model = fields.Char("Модель", related="ir_model_id.model", store=True)
    domain = fields.Char("Домен", required=True, default=[])
    server_id = fields.Many2one(
        "db.sync_server", "Сервер", ondelete="cascade", required=True
    )
    ir_model_id = fields.Many2one("ir.model", "Модель БД")
    field_by_search = fields.Char("Поля для поиска соответствия", required=True, default="name", help="Поля разделенные пробелами по которым будет идти поиск в начальной синхронизации")
    action = fields.Selection(
        [("Pull", "Pull"), ("Push", "Push"), ("PullPush", "PullPush")],
        "Тип сихронизации",
        required=True,
        default="Push",
    )
    sequence = fields.Integer("Порядок",default=10)
    count_sync_field = fields.Integer("Кол-во полей синхронизации", compute="_get_count_sync_field", store=True, default=0)
    active = fields.Boolean(default=True)
    is_create = fields.Boolean("Создавать записи?", default=False, help="Если не установлен, записи этой модели не будут создавать на удаленном сервере, будет только синхронизация с имеющимися записями")
    is_active_obj = fields.Boolean("Только активные?", default=False, help="Если установлен, в выборку будут поподать только активные (active) объекты. Если False то в поисковому домену будет добавлены также отключенные записи (active=False")
    sync_date = fields.Datetime("Последняя синхронизация")
    relation_sync_model_ids = fields.One2many(
        "db.sync_model_relation", "sync_model_id", "IDs зависит от моделей", ondelete="cascade"
    )
    field_ids = fields.One2many(
        "db.sync_model_field", "sync_model_id", "IDs полей модели", ondelete="cascade"
    )
    obj_ids = fields.One2many(
        "db.sync_obj", "sync_model_id", "IDs объектов синхронизации", ondelete="cascade"
    )
    field_ignored_ids = fields.One2many(
        "db.sync_model_field_ignored", "sync_model_id", "Игнорируемые поля объектов"
    )

    @api.depends('field_ids.is_sync')
    def _get_count_sync_field(self):
        """Расчет количество синхронизированных полей в модели"""
        for record in self:
            fields = record.field_ids.search([
                ('is_sync', '=', True),
                ('sync_model_id', '=', record.id),
            ])
            record.count_sync_field = len(fields)


    # @api.model
    def action_set_field_ids(self):
        self.field_ids.unlink()
        fields = self.env['ir.model.fields'].search([
            ('model_id', '=', self.ir_model_id.id)
        ])

        for f in fields:
            vals = {
                'ir_model_field_id': f.id,
                'sync_model_id': self.id,
            }
            if f.name == 'name':
                vals['is_sync'] = True
                vals['is_search'] = True

            if f.name == 'active' and not self.is_active_obj:
                vals['is_sync'] = True
           
            self.field_ids.create(vals)

    @api.model
    def get_sync_obj_ids(self, action=None):
        """Возвращает объекты модели для синхронизации"""

        domain = eval(self.domain)
        model_obj = self.env[self.ir_model_id.model]

        # print("++++++++++self._fields",model_obj._fields)
        # print("++++++++++self.fields_get()",model_obj.fields_get())

        # Если нужно синхронизовать в том числе отключенные объекты
        if not self.is_active_obj and 'active' in model_obj._fields:
            domain += [
                '|',
                ('active', '=', True),
                ('active', '=', False),
            ]
        if self.sync_date:
            w_date = domain + [("write_date", ">=", self.sync_date)]
            c_date = domain + [("create_date", ">=", self.sync_date)]
        else:
            w_date = c_date = domain
        
        obj_rec = model_obj.search(w_date)
        # obj_rec = model_obj.search(self.domain)

        obj_rec += model_obj.search(c_date)

        obj_rec = list(set(obj_rec)) #Удаляем дубликаты из списка

        return obj_rec

    @api.model
    def get_sync_field(self, action=None):
        """Возвращает поля отмеченные для синхронизаии """
        fields = self.field_ids.search([
            ('sync_model_id', '=', self.id),
            ('is_sync', '=', True),
        ])

        return fields

    @api.model
    def get_search_field(self):
        """Возвращает поля отмеченные как поисковые, по которым будет идти поиск в удаленной БД """
        fields = self.field_ids.search([
            ('sync_model_id', '=', self.id),
            ('is_search', '=', True),
        ])

        return fields

    def action_update_relation_model(self):
        """Создания зависимостей от моделей"""
        self.relation_sync_model_ids.unlink()
        for field in self.field_ids:
            if field.relation_sync_model_id:
                self.relation_sync_model_ids.create({
                    'sync_model_id': self.id,
                    'relation_sync_model_id': field.relation_sync_model_id.id,
                })


    
    def action_create_relation_model(self):
        """Создать связи с зависимыми моделями в строках полей"""
        fields = self.field_ids.search([
            ('relation', '!=', ''),
            ('is_sync', '=', True),
        ])

        for field in fields:
            print("++++",field)
            print("++++",field.ir_model_field_id)
            res = self.env['db.sync_model'].search([
                ('model', '=', field.relation)
            ])
            if res:
                print("=======", res)
                field.relation_sync_model_id = res.id
            else:
                print("-------",field.relation)
                ir_model = self.env['ir.model'].search([
                    ('model', '=', field.relation)
                ])
                if ir_model:
                    vals = {
                        'server_id': self.server_id.id,
                        'ir_model_id': ir_model.id,
                    }
                    new_id = self.env['db.sync_model'].create(vals)
                    field.relation_sync_model_id = new_id.id
                    print("++++new_id", new_id)
                else:
                    print("Модель в ir.model не найдена")
        
        self.action_update_relation_model()

class DbSyncModelRelation(models.Model):
    """Зависимости Модели БД для синхронизации"""

    _name = "db.sync_model_relation"
    _description = "Зависимости Модели БД для синхронизации"
    _order = "name"

    sync_model_id = fields.Many2one("db.sync_model", "Модель синхронизации", required=True, ondelete="cascade")
    relation_sync_model_id = fields.Many2one("db.sync_model", "Реляционная Модель синхронизации")

    name = fields.Char("Наименование", related="relation_sync_model_id.name", store=True)
    


class DbSyncModelField(models.Model):
    """Поля Модели БД для синхронизации"""

    _name = "db.sync_model_field"
    _description = "Поля Модели синхронизации"
    _order = "name"

    name = fields.Char("Наименование", related="ir_model_field_id.name", store=True)
    ir_model_field_id = fields.Many2one("ir.model.fields", "Поля модели БД")
    relation_sync_model_id = fields.Many2one("db.sync_model", "Реляционная Модель синхронизации", store=True)
    ttype = fields.Selection(string='Тип', related="ir_model_field_id.ttype", store=True)
    field_description = fields.Char(string='Описание поля', related="ir_model_field_id.field_description", store=True)
    relation = fields.Char(string='Связь с моделью', related="ir_model_field_id.relation", store=True)
    is_sync = fields.Boolean(string='Синхронизовать', default=False, help="Отмеченные поля будут обновляться")
    is_search = fields.Boolean(string='Поиск', default=False, help="По отмеченным полям будет идти поиск в удаленной БД для сопоставления объектов")
    is_create = fields.Boolean(string='Создавать', default=False, help="Создавать ли запись в случает отсутствия")

    sync_model_id = fields.Many2one("db.sync_model", "Модель синхронизации", required=True, ondelete="cascade")

    


class DbSyncModelFieldIgnored(models.Model):
    """Игнорируемые поля объектов"""

    _name = "db.sync_model_field_ignored"
    _description = "Игнорируемые поля объекта"

    name = fields.Char("Имя поля", required=True)
    sync_model_id = fields.Many2one(
        "db.sync_model", "Модель синхронизации", required=True, ondelete="cascade"
    )


class DbSyncObj(models.Model):
    """Строки Ids объектов синхронизации"""

    _name = "db.sync_obj"
    _description = "Синхронизированные объекты"

    name = fields.Char("Наименование", related="ir_model_id.name", store=True)
    model = fields.Char("Модель", related="ir_model_id.model", store=True)
    date = fields.Datetime(
        "Дата", required=True, default=lambda self: fields.Datetime.now()
    )
    ir_model_id = fields.Many2one("ir.model", "Модели БД", related="sync_model_id.ir_model_id")
    sync_model_id = fields.Many2one("db.sync_model", "Модель синхронизации", required=True, ondelete="cascade")
    local_id = fields.Integer("Local ID", readonly=True)
    remote_id = fields.Integer("Remote ID", readonly=True)

    def get_remote_id_by_local_id(self, sync_model_id, local_id):
        """Ищит была ли ранее синхронизация, возвращает id запись удаленной базы"""
        
        s = self.search([
            ('sync_model_id', '=', sync_model_id),
            ('local_id', '=', local_id),
        ], limit=1)
       
        if len(s)>0:
            return s.remote_id
        
        return False

        



class DbSyncLog(models.Model):
    """Результат синхронизации"""

    _name = "db.sync_log"
    _description = "Результат синхронизации"
    _order = "date desc"
    

    name = fields.Char(
        "Наименование", required=True,
    )
    date = fields.Datetime(string='Дата')
    server_id = fields.Many2one(
        "db.sync_server", "Сервер", required=True
    )
    result = fields.Text("Результат")
    is_error = fields.Boolean(string='Ошибка?', default=False)