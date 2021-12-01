# -*- coding: utf-8 -*-

from odoo import fields, models, api
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, LEVEL
import json
import base64

from openpyxl import Workbook
import os, fnmatch
from openpyxl.styles import Alignment, Border, Side, PatternFill, Font


class Mailbox(models.Model):
    _name = "ad.mailbox"
    _inherit = 'mail.thread'
    _description = "Почтовый ящик"
    _order = "date desc"

    name = fields.Char(u'Наименование')
    # name = fields.Char(u'Наименование', compute="_get_name", store=True)
    # message_type = fields.Char(u'message_type')
    # message_id = fields.Char(u'message_id')
    email_from = fields.Char(u'email_from')
    # from_t = fields.Char(u'from')
    # cc = fields.Char(u'cc')
    recipients = fields.Char(string='Получатели')
    # to = fields.Char(string='Получатель')
    # references = fields.Char(string='references')
    # in_reply_to = fields.Char(string='in_reply_to')
    date = fields.Datetime(string='Дата')
    subject = fields.Char(string='Тема')
    body_text = fields.Text(string='Тело письма текст')
    body_html = fields.Html(string='Тело письма html')
    # attachments = fields.Binary(string='Вложения')

    # def _get_name(self):
    #     self.name = str(self.date) + self.subject
        
    @api.model 
    def message_new(self, msg, custom_values=None):
        if custom_values is None:
            custom_values = {}
        
        defaults = {

            'name': msg.get('subject') or "Not",
           
        }
        
        # defaults = {

        #     'message_type': msg.get('message_type') or "",
        #     'message_id': msg.get('message_id') or "",
        #     'email_from': msg.get('email_from') or "",
        #     'from_t': msg.get('from') or "",
        #     'cc': msg.get('cc') or "",
        #     'recipients': msg.get('recipients') or "",
        #     'to': msg.get('to') or "",
        #     'references': msg.get('references') or "",
        #     'in_reply_to': msg.get('in_reply_to') or "",
        #     'date': msg.get('date'),
        #     'subject': msg.get('subject') or "",
        #     'body_text': msg.get('body') or "",
        #     'body_html': msg.get('body') or "",
        #     'attachments': msg.get('attachments') or "",
        # }

        vals = {
            'email_from': msg.get('email_from') or "",
            'recipients': msg.get('recipients') or "",
            'date': msg.get('date'),
            'subject': msg.get('subject') or "",
            'body_text': msg.get('body') or "",
            'body_html': msg.get('body') or "",
            'name': "Входящее сообщение",
        }

        # self.message_post(self.body_text)

        #new_mailbox = self.create(vals)


        # print("+++++++++++ MESSAGE", defaults)
        # print("+++++++++++ MESSAGE", msg)

        #return new_mailbox
        # defaults.update(custom_values or {})
        res = super(Mailbox, self).message_new(msg, custom_values=vals)
        return res
    
    # @api.model
    # def create(self,vals):
    #     res=super(Mailbox,self.with_context(mail_create_nosubscribe=True)).create(vals)
    #     return res
    
    # def _creation_subtype(self):
    #     return self#.env.ref('uit_base.ad_mailbox_new')


# Пример полей сообщения
# {
#     +'message_type': 'email', 
#     +'message_id': '<e86a00cbff8f4bd2af295efdaf18073a@tmenergo.ru>', 
#     +'subject': 'Это тема письма', 
#     +'email_from': '"Саврасов Михаил Владимирович" <SavrasovMV@tmenergo.ru>', 
#     +'from': '"Саврасов Михаил Владимирович" <SavrasovMV@tmenergo.ru>',
#     +'cc': '', 
#     +'recipients': '"Саврасов Михаил Владимирович" <SavrasovMV@tmenergo.ru>', 
#     +'to': '"Саврасов Михаил Владимирович" <SavrasovMV@tmenergo.ru>', 
#     'references': '', 
#     'in_reply_to': '', 
#     'date': '2021-07-20 08:48:01', 
#     'body': '<html>\r\n<head>\r\n<meta http-equiv="Content-Type" content="text/html; charset=koi8-r">\r\n<style type="text/css" style="display:none;"><!-- P {margin-top:0;margin-bottom:0;} --></style>\r\n</head>\r\n<body dir="ltr">\r\n<div id="divtagdefaultwrapper" style="font-size:12pt;color:#000000;font-family:Calibri,Helvetica,sans-serif;" dir="ltr">\r\n<p>Тело письма</p>\r\n<div id="Signature">\r\n<div id="divtagdefaultwrapper" dir="ltr" style="font-size: 12pt; color: rgb(0, 0, 0); font-family: Calibri, Helvetica, sans-serif, EmojiFont, &quot;Apple Color Emoji&quot;, &quot;Segoe UI Emoji&quot;, NotoColorEmoji, &quot;Segoe UI Symbol&quot;, &quot;Android Emoji&quot;, EmojiSymbols;">\r\n<br>\r\n<p></p>\r\n</div>\r\n</div>\r\n</div>\r\n</body>\r\n</html>\r\n', 
    
#     'attachments': [], 
#     'bounced_email': False,
#     'bounced_partner': res.partner(), 
#     'bounced_msg_id': False, 
#     'bounced_message': mail.message(),
#     'author_id': 3
#     }

