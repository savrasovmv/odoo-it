from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SkladProduct(models.Model):
    _name = "sklad.product"
    _description = "Номенклатура"
    _order = "name"

    name = fields.Char('Наименование')
    product_uom_id = fields.Many2one('sklad.product_uom', string='Единица измерения')
    product_category_id = fields.Many2one('sklad.product_category', string='Категория номенклатуры')

    # 1С
    # guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    code_1c = fields.Char(string='Код 1С', readonly=True, groups="base.group_erp_manager, base.group_system")


class SkladProductCategory(models.Model):
    _name = "sklad.product_category"
    _description = "Категории номенклатуры"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Наименование', index=True, required=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('sklad.product_category', 'Родительская категория', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('sklad.product_category', 'parent_id', 'Дочернии категории')
    

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Вы не можете создавать рекурсивные категории.'))
        return True

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    


class SkladProductUom(models.Model):
    _name = "sklad.product_uom"
    _description = "Единицы измерения"
    _order = "name"

    name = fields.Char('Наименование')

    # 1С
    # guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    code_1c = fields.Char(string='Код 1С', readonly=True, groups="base.group_erp_manager, base.group_system")