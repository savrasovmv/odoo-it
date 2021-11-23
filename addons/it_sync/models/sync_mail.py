# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime



class SyncMail(models.Model):
    _name = "sync.mail"
    _description = "Почта синхронизации"
    _order = "name"

    name = fields.Char(u'Наименование', required=True)
    date = fields.Datetime(string='Дата')
    email_from = fields.Char(u'email_from')
    email_to = fields.Char(u'email_to')
    subject = fields.Char(u'subject')
    auto_delete = fields.Char(u'auto_delete')
    body_html = fields.Char(u'body_html')
    
                
    def send_mail(self, email_values={}):
        mail_template = self.env.ref('it_sync.tasks_user_create_email_template')
        mail_template.with_context(email_values).send_mail(self.id, force_send=True)

                
    