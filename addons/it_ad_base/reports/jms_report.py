# -*- coding: utf-8 -*-
import xlwt
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import date, timedelta, datetime


class JMSReport(models.TransientModel):
    _name = "jms.report"
    _description = "JMS отчеты"

    name = fields.Char(u'Пользователь')
    date_start = fields.Date(string='Начало')
    date_end = fields.Date(string='Окончание')
    summary_data = fields.Char('Name', size=256)
    file_name = fields.Binary('JMS отчет', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                            default='choose')

    def jms_report_wizard_action(self):
        #self.result = self.env['jms.connect'].sudo().report(self.date_start, self.date_end)
        #reload(sys)
        #sys.setdefaultencoding("utf-8")

        company_name = 's;kljfglkj'
        file_name = 'JMSReport.xls'
        workbook = xlwt.Workbook(encoding="UTF-8")
        format0 = xlwt.easyxf(
            'font:height 500,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;')
        formathead2 = xlwt.easyxf(
            'font:height 250,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;')
        format1 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour gray25;align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;')
        format2 = xlwt.easyxf('font:bold True;align: horiz left')
        format3 = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;')
        
        formatDate = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;', num_format_str='DD.MM.YYYY')
        
        formatDateTime = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;', num_format_str='DD.MM.YYYY HH:MM')
        
        formatTime = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;', num_format_str='HH:MM')

        formatInt1 = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black,\
                                left thin, right thin, top thin, bottom thin;', num_format_str='# ##0.0')

                                
        sheet = workbook.add_sheet("Отчет")
        sheet.col(0).width = int(11 * 260)
        sheet.col(1).width = int(30 * 260)
        sheet.col(2).width = int(40 * 260)
        sheet.col(3).width = int(10 * 260)
        sheet.row(0).height_mismatch = True
        sheet.row(0).height = 150 * 4
        sheet.row(1).height_mismatch = True
        sheet.row(1).height = 150 * 2
        sheet.row(2).height_mismatch = True
        sheet.row(2).height = 150 * 3
        sheet.write_merge(0, 0, 0, 6, 'Отчет о времени нахождения сотрудников за ПК', format0)
        sheet.write_merge(1, 1, 0, 6, 'Период с :' + str(self.date_start) + ' по ' + str(self.date_end), formathead2)
        #sheet.write_merge(2, 2, 0, 3, 'Company : ' + company_name, formathead2)
        sheet.write(3, 0, 'Дата', format1)
        sheet.write(3, 1, 'ФИО', format1)
        sheet.write(3, 2, 'Должность', format1)
        sheet.write(3, 3, 'Кол-во событий', format1)
        sheet.write(3, 4, 'Первое', format1)
        sheet.write(3, 5, 'Последнее', format1)
        sheet.write(3, 6, 'Отработано, ч', format1)

        users_list_id = self.env['jms.event_log'].sudo().read_group([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('users_id', '!=', False),
        ], fields=['users_id'], groupby=['users_id'])

        
        users_list = []
        for data in users_list_id:
            if data['users_id']:
                d_id, obj = data['users_id']
                users_list.append(d_id)

        n = 3
        for user_id in users_list:
            current_date = self.date_start
            while current_date<=self.date_end:
                start_day =  datetime(
                    year=current_date.year, 
                    month=current_date.month,
                    day=current_date.day,
                    hour=0,
                    minute=0,
                    second=0
                )
                end_day =  datetime(
                    year=current_date.year, 
                    month=current_date.month,
                    day=current_date.day,
                    hour=23,
                    minute=59,
                    second=59
                )
                event_list = self.env['jms.event_log'].sudo().search([
                    ('date', '>=', start_day),
                    ('date', '<=', end_day),
                    ('users_id', '=', user_id),
                ], order='date asc')

                print('++++', current_date, event_list)
                t_delta = 0
                t_first = False
                t_last = False
                t_start = False
                t_end = False
                for line in event_list:
                    if not t_first and line.event_name == 'Подключение':
                        t_first = line.date
                    if not t_start and line.event_name == 'Подключение':
                        t_start = line.date
                        t_end = False
                    if not t_end and t_start and line.event_name == 'Отключение':
                        t_end = line.date
                        t_delta += (t_end - t_start).total_seconds() / 60.0 /60.0
                        t_start = False
                        t_end = False

                    if line.event_name == 'Отключение':
                        t_last = line.date

                if t_first:
                    t_first = t_first + timedelta(hours=5)
                else:
                    t_first = 0    
                if t_last:
                    t_last = t_last + timedelta(hours=5)
                else:
                    t_last = 0
                if len(event_list)>0:
                    print("+++t_first", t_first)
                    print("+++t_last", t_last)
                    n+=1
                    sheet.write(n, 0, current_date, formatDate)
                    sheet.write(n, 1, event_list[0].users_id.name, format3)
                    sheet.write(n, 2, event_list[0].users_id.title, format3)
                    sheet.write(n, 3, len(event_list), format3)
                    sheet.write(n, 4, t_first, formatTime)
                    sheet.write(n, 5, t_last, formatTime)
                    sheet.write(n, 6, t_delta, formatInt1)
                
                current_date = current_date + timedelta(days=1)
           

        # Лист со всеми данными
        sheet = workbook.add_sheet("Данные")
        sheet.col(0).width = int(20 * 260)
        sheet.col(1).width = int(20 * 260)
        sheet.col(2).width = int(40 * 260)
        sheet.col(3).width = int(40 * 260)
        sheet.col(4).width = int(20 * 260)
        sheet.col(5).width = int(40 * 260)
      
        sheet.write(0, 0, 'Дата', format1)
        sheet.write(0, 1, 'Событие', format1)
        sheet.write(0, 2, 'ФИО', format1)
        sheet.write(0, 3, 'Должность', format1)
        sheet.write(0, 4, 'Имя ПК', format1)
        sheet.write(0, 5, 'Имя пользователя', format1)

        event_list = self.env['jms.event_log'].sudo().search([
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ], order='date asc')

        n=0
        for line in event_list:
            date = line.date
            if date:
                date = date + timedelta(hours=5)
            else:
                date = 0

            name = title = ''
            users_id = line.users_id
            if users_id:
                name = users_id.name
                title = users_id.title


            n+=1
            sheet.write(n, 0, date, formatDateTime)
            sheet.write(n, 1, line.event_name, format3)
            sheet.write(n, 2, name, format3)
            sheet.write(n, 3, title, format3)
            sheet.write(n, 4, line.pc_name, format3)
            sheet.write(n, 5, line.name, format3)






        fp = BytesIO()
        workbook.save(fp)
        self.write(
            {'state': 'get', 'file_name': base64.encodestring(fp.getvalue()), 'summary_data': file_name})
        fp.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jms.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
        }