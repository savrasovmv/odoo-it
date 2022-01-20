from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SkladLocation(models.Model):
    _name = "sklad.location"
    _description = "Местонахождения"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Наименование', index=True, required=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('sklad.location', 'Родительское место', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('sklad.location', 'parent_id', 'Дочернии места')
    

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (location.parent_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    @api.constrains('parent_id')
    def _check_location_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Вы не можете создавать рекурсивные места.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

   

