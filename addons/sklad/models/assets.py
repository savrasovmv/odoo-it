from odoo import api, fields, models


class SkladAssets(models.Model):
    _name = "sklad.assets"
    _description = "Активы"
    _order = "name"

    name = fields.Char('Наименование')
    invetory_number = fields.Char('Инвентарный номер')
    serial_number = fields.Char('Серийный номер')
    bar_code = fields.Char('Штрих-код')

    # 1С
    # guid_1c = fields.Char(string='guid1C', readonly=True, groups="base.group_erp_manager, base.group_system")
    code_1c = fields.Char(string='Код 1С', readonly=True, groups="base.group_erp_manager, base.group_system")
    nomen_1c = fields.Boolean('В 1С как номенклатура?', default=True, help="Если установлен, то этот актив из справочника 1С Номенклатура, иначе из Основного средства") 


    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s [%s]' % (rec.name,rec.serial_number)))
        return result

