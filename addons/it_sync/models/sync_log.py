
from odoo import fields, models, api
from datetime import datetime

class SyncLog(models.Model):
    _name = "sync.log"
    _description = "Журнал синхронизаций"
    _order = "date desc"

    date = fields.Datetime(string='Дата')
    obj = fields.Char(u'Объект', readonly=True) #Объект который создал запись self.__class__.__name__
    name = fields.Char(u'Наименование', readonly=True) #Наименование объекта self.__class__._description
    result = fields.Text(string='Результат', readonly=True)
    is_error = fields.Boolean(string='С ошибкой')

    # @api.model
    # def create(self, vals):
    #     if not 'name' in vals:
    #         vals['name'] = self.env[obj]._description
            
    #     return super(AdSyncLog, self).create(vals)