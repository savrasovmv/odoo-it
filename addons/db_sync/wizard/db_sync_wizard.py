import logging
import threading
import time
from xmlrpc.client import ServerProxy
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.tools import format_datetime

_logger = logging.getLogger(__name__)


class RPCProxyOne(object):
    def __init__(self, server, ressource):
        """Class to store one RPC proxy server."""
        self.server = server
        local_url = "%s:%d/xmlrpc/2/common" % (
            server.server_url,
            server.server_port,
        )
        rpc = ServerProxy(local_url)
        self.uid = rpc.login(server.db_name, server.login, server.password)
        local_url = "%s:%d/xmlrpc/2/object" % (
            server.server_url,
            server.server_port,
        )
        self.rpc = ServerProxy(local_url)
        self.ressource = ressource

    def __getattr__(self, name):
        return lambda *args, **kwargs: self.rpc.execute(
            self.server.db_name,
            self.uid,
            self.server.password,
            self.ressource,
            name,
            *args
        )


class RPCProxy(object):
    """Class to store RPC proxy server."""

    def __init__(self, server):
        self.server = server

    def test_connection(self):
        local_url = "%s:%d/xmlrpc/2/common" % (
            self.server.server_url,
            self.server.server_port,
        )
        try:
            rpc = ServerProxy(local_url)
            v = rpc.version()
            return v
        except:
            return False
        



    def get(self, ressource):
        return RPCProxyOne(self.server, ressource)



class DbSyncWizard(models.TransientModel):
    """Форма действия синхронизации"""

    _name = "db.sync_wizard"
    _description = "Форма действия синхронизации"

    server_id = fields.Many2one(
        "db.sync_server", "Сервер", required=True
    )

    user_id = fields.Many2one(
        "res.users", "Отправить результат", default=lambda self: self.env.user
    )

    result = fields.Text(string='Результат', default='')
    text_error = fields.Text(string='Текст ошибок', default='')
    text_create = fields.Text(string='Результат создания', default='')
    text_update = fields.Text(string='Результат обновления', default='')

    count_error = fields.Integer(string='Кол-во ошибок', default=0)
    count_create = fields.Integer(string='Кол-во созданных объектов', default=0)
    count_update = fields.Integer(string='Кол-во обновленных объектов', default=0)
    
    count_check_del_line = fields.Integer(string='Удалено строк obj_sync', default=0)
    count_check_del_remote = fields.Integer(string='Удалено в Удаленной БД', default=0)
    count_check_create_remote = fields.Integer(string='Создано в Удаленной БД', default=0)

    is_check_obj = fields.Boolean(string='Проверять существование объекта в удаленной базе')

    
    def get_remote_id_by_local_id(self, obj_id):
        """Ищит была ли ранее синхронизация, возвращает id запись удаленной базы"""
        s = self.env['db.sync_obj'].search([
            ('model', '=', obj_id._name),
            ('local_id', '=', obj_id.id),
        ], limit=1)

        if len(s)>0:
            return s.remote_id
        return False

    def transform_many2one(self, obj_id, field_id):
        """Возвращает Id записи поля many2one соответствующее Id на удаленном сервере"""
        mo_obj_id = obj_id[field_id.name]
        return self.get_remote_id_by_local_id(mo_obj_id)
        



    def create_sync_vals(self, sync_model_id, obj_id):
        list_sync_field = sync_model_id.get_sync_field()
        for field in list_sync_field:
            pass 

    def create_sync_obj(self, sync_model_id, local_id, remote_id):
        """Создает в модели db.sync_obj новую запись соответствия ID серверов"""
       
        self.env['db.sync_obj'].create({
            'sync_model_id': sync_model_id.id,
            'local_id': local_id,
            'remote_id': remote_id
        })

    
    
    def sync_obj(self, sync_model_id, obj_id, is_check=False):
        """Синхронизация конкретных объектов модели
            is_check - признак выполнения проверки
        """

        _logger.debug("Синхронизация объекта %s",  obj_id)
        pool_dist = RPCProxy(self.server_id)
        dist_obj_id = self.get_remote_id_by_local_id(obj_id)

        sync_field_id = sync_model_id.get_sync_field()
        print("++++ sync_field_id", sync_field_id)

        vals = {}
        for field_id in sync_field_id:
            #or 'one2many' or 'many2many'
            if field_id.ttype == 'many2one':
                # Если поле объекта содержит значение
                if obj_id[field_id.name]:
                    mo_obj_id = self.transform_many2one(obj_id, field_id)
                 
                    if mo_obj_id:
                        vals[field_id.name] = mo_obj_id
                    else:
                        _logger.debug("Не найдена запись для поля m2o %s объекта %s" % (field_id.name, obj_id))
                        self.text_error  = "Не найдена запись для поля m2o %s объекта %s \n" % (field_id.name, obj_id)
                        self.count_error += 1
                else:
                    vals[field_id.name] = False
                    

            else:
                vals[field_id.name] = obj_id[field_id.name]

        if len(vals)==0:
            _logger.debug("Нет значений vals для объекта %s" % (obj_id))
            self.text_error  = "Нет значений vals для объекта %s \n" % (obj_id)
            self.count_error += 1
            return       
                

        # Проверять существутет ли объект в Удаленной БД
        # Если не проверять и объекта в УдБД не существует, то при обновлении объекта методом write объект в удаленной базе не создаться
        # Если проверять то это дополнительный вызов, что увеличивает нагрузку
        if dist_obj_id and (self.is_check_obj or is_check):
            _logger.debug("Проверка существования объекта %s в удаленной БД по id= %s " % (obj_id, dist_obj_id))
            res = pool_dist.get(sync_model_id.ir_model_id.model).search([['id', '=', dist_obj_id]])
            if len(res) == 0:
                _logger.debug("Не найден объекта %s в удаленной БД по id= %s " % (obj_id, dist_obj_id))
                _logger.debug("Удаляем зпись в Синхронизированные объекты(db.sync_obj) объекта %s" % (obj_id,))
                dist_obj_id = False
                # Удалить не верную запись
                s = self.env['db.sync_obj'].search([
                    ('model', '=', obj_id._name),
                    ('local_id', '=', obj_id.id),
                ],).unlink()



        if dist_obj_id:
            _logger.debug("Обновление объекта %s в удаленной БД с id= %s и vals=%s" % (obj_id, dist_obj_id, vals))
            res = pool_dist.get(sync_model_id.ir_model_id.model).write([dist_obj_id], vals)
            self.text_update += '%s %s -> %s \n' % (obj_id, obj_id.display_name, dist_obj_id)
            self.count_update += 1
        else:
            
            # list_field_by_search = sync_model_id.field_by_search.split(' ')
            # domain = []
            # for field in list_field_by_search:
            #     if isinstance(obj_id._fields[field], fields.Many2one):
            #         field_value = self.get_remote_id_by_local_id(obj_id[field])
            #     else:
            #         field_value = obj_id[field]
            #     domain.append((field, '=', field_value))

            list_field_by_search = sync_model_id.get_search_field()
            domain = []
            for field in list_field_by_search:
                field_value = False
                if field.ttype == 'many2one':
                    field_value = self.get_remote_id_by_local_id(obj_id[field])
                else:
                    field_value = obj_id[field.name]
                
                if field_value:
                    domain.append((field.name, '=', field_value))
                else:
                    _logger.debug("Для поля %s не найдено значение, поле не добавлено в домен поиска" % (field.name))
            if len(domain)==0:
                _logger.debug("Нет полей поиска соответствий для модели %s" % (sync_model_id))
                self.text_error  = "Нет полей поиска соответствий для модели %s \n" % (sync_model_id)
                self.count_error += 1
                return 

            _logger.debug("Поиск объекта  %s в удаленной БД по полям %s" % (obj_id, domain))
            
            remote_obj = pool_dist.get(sync_model_id.ir_model_id.model).search(domain, limit=1)

            _logger.debug("remote_obj %s" % (remote_obj))

            if remote_obj:
                new_id = remote_obj[0]
                _logger.debug("Найден. Обновление объекта %s в удаленной БД с id= %s" % (obj_id, new_id))
                pool_dist.get(sync_model_id.ir_model_id.model).write([new_id], vals)
                self.count_update += 1
                self.text_update += '%s %s -> %s \n' % (obj_id, obj_id.display_name, new_id)

                
            else:
                _logger.debug("Не найден. Создание нового объекта %s в удаленной БД " % (obj_id, ))
                new_id = pool_dist.get(sync_model_id.ir_model_id.model).create(vals)
                _logger.debug("Создан новый объекта %s в удаленной БД с id = %s" % (obj_id, new_id))
                self.count_create += 1
                self.text_create += '%s %s -> %s \n' % (obj_id, obj_id.display_name, new_id)



            self.create_sync_obj(sync_model_id, obj_id.id, new_id)


    def sync_model(self, sync_model_id):
        """Синхронизация модели. Выборка объектов для синхронизации, запус синхронизации записей"""
        
        _logger.debug("Синхронизация модели. Выборка объектов для синхронизации, запус синхронизации записей")

        sync_date = fields.Datetime.now()
        pool_dist = RPCProxy(self.server_id)
        module = pool_dist.get("ir.module.module")
        model_obj = sync_model_id.ir_model_id.model
        module_id = module.search(
            [("name", "ilike", "db_sync"), ("state", "=", "installed")]
        )
        if not module_id and (sync_model_id.action == "Pull" or sync_model_id.action == "PullPush"):
            raise ValidationError(
                _(
                    """Для синхронизации объектов с типом/
                          Pull или PullPush /
                          необходимо установить модуль синхронизации/
                          на удаленный сервер"""
                )
            )
        
        sync_obj_ids = sync_model_id.get_sync_obj_ids()
        _logger.debug("Объектов для синхронизации:  %s", len(sync_obj_ids))

        for obj_id in sync_obj_ids:
            self.sync_obj(sync_model_id, obj_id)

        sync_model_id.sync_date = sync_date





    def start_sync(self):
        """Начало синхронизации. Выборка моделей для синхронизации и их синхронизация"""
        self.ensure_one()
        _logger.debug("Начало синхронизации. Выборка моделей для синхронизации и их синхронизация")

        self.text_update=self.text_create=self.text_error=''

        for sync_model_id in self.server_id.sync_model_ids:
            _logger.debug("Начало синхронизации модели  %s, порядок %s" % (sync_model_id.name, sync_model_id.sequence))
            self.sync_model(sync_model_id)


        self.create_log()


    def create_log(self):
        if self.user_id:
            log = self.env["db.sync_log"]
            self.result = """
                Результаты обновления: \n
                Обновлено: %s, \n
                Создано: %s, \n
                Ошибок: %s, \n
                Текст ошибок: \n
                %s \n \n
                ------------------------------------ \n
                Подробности: \n
                ------------------------------------ \n
                Обновлены объекты: \n 
                %s, \n
                Созданы объекты: \n
                %s, \n

            
            """ % (
                self.count_update,
                self.count_create,
                self.count_error,
                self.text_error if self.text_error else '',
                self.text_update if self.text_update else '',
                self.text_create if self.text_create else '',
            )
            
            log.create(
                {
                    "name": "Отчет о синхронизации",
                    "date": fields.Datetime.now(),
                    "server_id": self.server_id.id,
                    "result": self.result,
                    "is_error": False if self.count_error==0 else True
                }
            )


    def start_sync_action(self):
        """События Wizard начать синхронизацию"""

        _logger.debug("События Wizard начать синхронизацию")

        _logger.debug("Проверка доступности удаленного сервера %s", self.server_id.name)
        pool_dist = RPCProxy(self.server_id)
        _logger.debug("Запрос версии сервера")
        res = pool_dist.test_connection()
        if res:
            _logger.debug("Версия сервера %s", res)
        else:
            _logger.warning("Ошибка подключения к удаленному серверу %s", self.server_id.name)
            self.text_error  = "Ошибка подключения к удаленному серверу %s \n", self.server_id.name
            self.count_error += 1

            log = self.env["db.sync_log"]
            
            log.create(
                {
                    "name": "Отчет о синхронизации",
                    "date": fields.Datetime.now(),
                    "server_id": self.server_id.id,
                    "result": "Ошибка подключения к удаленному серверу",
                    "is_error": True
                }
            )
            self.result = "Ошибка подключения к удаленному серверу"
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Прерванно'),
                    'message': self.result,
                    'type':'warning',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                },
            }
            return notification


        threaded_sync = threading.Thread(
            target=self.start_sync()
        )
        threaded_sync.start()

        return {
				'name': 'Результат',
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'db.sync_wizard',
				'target':'new',
				'context':{
							'default_result':self.result,
							} 
				}

        # id2 = self.env.ref("db_sync.db_sync_finish_wizard").id
        # return {
        #     "binding_view_types": "form",
        #     "view_mode": "form",
        #     "res_model": "db.sync_wizard",
        #     "views": [(id2, "form")],
        #     "view_id": False,
        #     "type": "ir.actions.act_window",
        #     "target": "new",
        # }





    def check_sync_model(self, sync_model_id):
        """Проверка модели"""

        pool_dist = RPCProxy(self.server_id)

        # ----------------------------------------------
        # Проверка локальных объектов
        # ----------------------------------------------

        obj_ids = self.env['db.sync_obj'].search([
            ('sync_model_id', '=', sync_model_id.id)
        ])

        local_ids = [k.local_id for k in obj_ids]
        domain = sync_model_id.get_defaul_domain()

        local_obj_ids = self.env[sync_model_id.model].search(domain + [('id', 'in', local_ids)])
        db_local_ids = [k.id for k in local_obj_ids]

        # Список id существующей в Синхронизированные объекты db.sync_obj, но не существующие в текущей БД
        # Очищаем список и удаляем объекты в удаленной БД если они существуют
        list_del_local = list(set(local_ids) - set(db_local_ids))

        if len(list_del_local)>0:
            # Нахоим ID удаленной БД для последующего удаления
            search_del_obj_ids = self.env['db.sync_obj'].search([
                ('sync_model_id', '=', sync_model_id.id),
                ('local_id', 'in', list_del_local)
            ])
            list_del_remote_ids = [k.remote_id for k in search_del_obj_ids]
            
            self.count_check_del_line += len(search_del_obj_ids) 
            self.count_check_del_remote += len(list_del_remote_ids) 

            # Выбираем существующие в УдБД объекты входящие в список для удаления
            remote_ids = pool_dist.get(sync_model_id.model).search([('id', 'in', list_del_remote_ids)])
            # Удаляем записи в БД
            pool_dist.get(sync_model_id.model).unlink(remote_ids)
            search_del_obj_ids.unlink()




        # ----------------------------------------------
        # Проверка объектов в УдБД
        # ----------------------------------------------
        obj_ids = self.env['db.sync_obj'].search([
            ('sync_model_id', '=', sync_model_id.id)
        ])

        remote_ids = [k.remote_id for k in obj_ids]

        db_remote_ids = pool_dist.get(sync_model_id.model).search([('id', 'in', remote_ids)])

        # Список id существующей в Синхронизированные объекты db.sync_obj, но не существующие в Удаленной БД
        # Создаем объекты в удаленной БД если они отсутствуют
        list_create_remote_obj_id = list(set(remote_ids) - set(db_remote_ids))

        if len(list_create_remote_obj_id)>0:
            # Нахоим объекты которые нужно создать в УдБД
            search_create_obj_ids = self.env['db.sync_obj'].search([
                ('sync_model_id', '=', sync_model_id.id),
                ('remote_id', 'in', list_create_remote_obj_id)
            ])

            # Id объектов которые необходимо создать в УдБД
            local_ids = [k.local_id for k in search_create_obj_ids]

            # Получаем конкретные объекты модели для синхронизации
            sync_obj_ids = self.env[sync_model_id.model].search([('id', 'in', local_ids)])

            # Синхронизируем
            for obj_id in sync_obj_ids:
                self.sync_obj(sync_model_id, obj_id, True)




    def start_check_sync(self):
        """Выборка моделий для проверки. Запуск процедуры проверки модели"""

        self.text_update=self.text_create=self.text_error=''

        for sync_model_id in self.server_id.sync_model_ids:
            _logger.debug("Проверка модели  %s, порядок %s" % (sync_model_id.name, sync_model_id.sequence))
            self.check_sync_model(sync_model_id)
        
        self.create_log_check()





    def start_check_sync_action(self):
        """События Wizard Проверяет синхронизированные объекты и восстанавляивает в случае отсутствия"""

        _logger.debug("События Wizard начать проверку синхронизированных объектов")

        _logger.debug("Проверка доступности удаленного сервера %s", self.server_id.name)
        pool_dist = RPCProxy(self.server_id)
        _logger.debug("Запрос версии сервера")
        res = pool_dist.test_connection()
        if res:
            _logger.debug("Версия сервера %s", res)
        else:
            _logger.warning("Ошибка подключения к удаленному серверу %s", self.server_id.name)
            self.text_error  = "Ошибка подключения к удаленному серверу %s \n", self.server_id.name
            self.count_error += 1

            log = self.env["db.sync_log"]
            
            log.create(
                {
                    "name": "Отчет о проверке",
                    "date": fields.Datetime.now(),
                    "server_id": self.server_id.id,
                    "result": "Ошибка подключения к удаленному серверу",
                    "is_error": True
                }
            )
            self.result = "Ошибка подключения к удаленному серверу"
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Прерванно'),
                    'message': self.result,
                    'type':'warning',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                },
            }
            return notification


        threaded_sync = threading.Thread(
            target=self.start_check_sync()
        )
        threaded_sync.start()

        return {
				'name': 'Результат',
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'db.sync_wizard',
				'target':'new',
				'context':{
							'default_result':self.result,
							} 
				}

    def create_log_check(self):
        if self.user_id:
            log = self.env["db.sync_log"]
            self.result = """
                Результаты проверки: \n
                Удалено строк Синхронизированные объекты db.sync_obj: %s, \n
                Удалено в Удаленной БД: %s, \n
                Создано в Удаленной БД: %s, \n
                Ошибок: %s, \n
                Текст ошибок: \n
                %s \n
                ------------------------------------ \n
                Подробности: \n
                ------------------------------------ \n
                Обновлены объекты: \n 
                %s, \n
                Созданы объекты: \n
                %s, \n
            
            """ % (
                self.count_check_del_line,
                self.count_check_del_remote,
                self.count_create,
                self.count_error,
                self.text_error if self.text_error else '',
                self.text_update if self.text_update else '',
                self.text_create if self.text_create else '',
            )
            
            log.create(
                {
                    "name": "Отчет о проверки",
                    "date": fields.Datetime.now(),
                    "server_id": self.server_id.id,
                    "result": self.result,
                    "is_error": False if self.count_error==0 else True
                }
            )