# -*- coding: utf-8 -*-

from odoo import fields, models, api
import pyodbc 
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class JMSConnect(models.AbstractModel):
    _name = "jms.connect"
    _description = "Класс для работы с JMS"

    def jms_connect(self):
        """Подключается к JMS, возвращает объект Connection"""
        _logger.info("ldap_connect")
         #     #Подключение к серверу AD
        jms_server = self.env['ir.config_parameter'].sudo().get_param('jms_server')
        jms_driver = self.env['ir.config_parameter'].sudo().get_param('jms_driver')
        jms_database = self.env['ir.config_parameter'].sudo().get_param('jms_database')
        jms_user = self.env['ir.config_parameter'].sudo().get_param('jms_user')
        jms_password = self.env['ir.config_parameter'].sudo().get_param('jms_password')

        conn = pyodbc.connect('DRIVER='+jms_driver+';SERVER='+jms_server+';DATABASE='+jms_database+';UID='+jms_user+';PWD='+ jms_password)

        old = self.env['jms.event_log'].sudo().search([], limit=1, order='date desc')           
        if len(old)>0:
            date = old.date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date = "2021-10-01 00:00:00"
        cursor = conn.cursor()
        cursor.execute("""SELECT
                              				
                            e.EventDate
                            ,e.NotificationType
                            ,e.Arg4
                            ,w.NetBIOSName
                            ,e.id
                            FROM dbo.ClientEventLog as e
                            LEFT JOIN Workstation as w ON (w.id=e.WorkstationId)
                            WHERE (NotificationType=12 OR NotificationType=13) AND EventDate>{ts '%s'}
                """ % date)
        jms = self.env['jms.event_log'].sudo()
        for line in cursor:
            # print(i)
            event_name = 'Другое'
            if line[1]==12:
                event_name = 'Подключение'
            elif line[1]==13:
                event_name = 'Отключение'
            id = line[4]
            dname = line[2].split('\\') # DOMAIN\UserName
            username = dname[1] # UserName

            users_id = self.env['ad.users'].sudo().search([('username', 'ilike', username)], limit=1)

            vals = {
                'date': line[0],
                'event_id': line[1],
                'event_name': event_name,
                'name': line[2],
                'pc_name': line[3],
                'jms_id': line[4],
                'users_id': users_id.id if len(users_id)>0 else '',
            }
            search = self.env['jms.event_log'].sudo().search([('jms_id', '=', id)], limit=1, order='date desc') 
            if len(search)>0:
                jms.write(vals)
            else:
                jms.create(vals)


    # def report(self, date_start, date_end):
    #     pass

        