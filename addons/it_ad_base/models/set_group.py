# -*- coding: utf-8 -*-

from odoo import fields, models, api

class SetGroup(models.Model):
    _name = "ad.set_group"
    _description = "Установка групп пользователям"
    _order = "name"

    name = fields.Char(u'Наименование', required=True)
    active = fields.Boolean('Active', default=True)

    ou_id = fields.Many2one("ad.ou", string="Подразделение")
    department_id = fields.Many2one("ad.department", string="Управление/отдел")

    set_group_line = fields.One2many('ad.set_group_line', 'set_group_id', string=u"Строка Установка групп пользователям")


class SetGroupLine(models.Model):
    _name = "ad.set_group_line"
    _description = "Строка Установка групп пользователям"
    _order = "name"

    name = fields.Char(u'Наименование', compute="_get_name")
    group_id = fields.Many2one("ad.group", string="Группа AD")

    set_group_id = fields.Many2one('ad.set_group',
		ondelete='cascade', string=u"Установка групп пользователям", required=True)

    @api.depends("group_id")
    def _get_name(self):
        self.name = self.group_id.name

     
