from odoo import api, fields, models


class Sklad(models.Model):
    _name = "sklad.sklad"
    _description = "Склады"
    _order = "name"

    name = fields.Char('Наименование')
    employee_id = fields.Many2one('hr.employee', string='МОЛ')
    user_id = fields.Many2one('res.user', string='Пользователь')
    location_id = fields.Many2one('sklad.location', string='Местонахождения')
   

