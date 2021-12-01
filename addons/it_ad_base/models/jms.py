
# -*- coding: utf-8 -*-

from odoo import fields, models, api

class JMSEventLog(models.Model):
    _name = "jms.event_log"
    _description = "JMS события"
    _order = "date desc"

    name = fields.Char(u'Пользователь')
    date = fields.Datetime(string='Дата', readonly=True)
    pc_name = fields.Char(u'Имя ПК')
    event_id = fields.Integer(string='id события')
    event_name = fields.Char(string='Имя события')
    users_id = fields.Many2one("ad.users", string="Пользователь AD")
    jms_id = fields.Integer(string='id jms')


    