from odoo import api, fields, models


class SkladAssets(models.Model):
    _name = "sklad.assets"
    _description = "Активы"
    _order = "name"

    name = fields.Char('Наименование')
    invetory_number = fields.Char('Инвентарный номер', copy=False)
    serial_number = fields.Char('Серийный номер', copy=False)
    bar_code = fields.Char('Штрих-код', copy=False)

    assets_category_id = fields.Many2one('sklad.assets_category', string='Категория актива')
    date_acquisition = fields.Date('Дата приобретения')
    original_value  = fields.Float('Стоимость', digits=(10,2))

    # 1С
    # guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    code_1c = fields.Char(string='Код 1С', readonly=True, groups="base.group_erp_manager, base.group_system", copy=False)
    nomen_1c = fields.Boolean('В 1С как номенклатура?', default=True, help="Если установлен, то этот актив из справочника 1С Номенклатура, иначе из Основного средства") 


    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s [%s]' % (rec.name,rec.serial_number)))
        return result



class SkladAssetsCategory(models.Model):
    _name = "sklad.assets_category"
    _description = "Категории активов"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Наименование', index=True, required=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('sklad.assets_category', 'Родительская категория', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('sklad.assets_category', 'parent_id', 'Дочернии категории')
    

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