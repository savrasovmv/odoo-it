from odoo import fields, models, api, _

class TransferUse(models.Model):
    _name = "sklad.transfer_use"
    _description = "Передача в пользование"
    _order = "date desc"

    name = fields.Char('Номер', copy=False, readonly=True, default=lambda x: _('New'))
    date = fields.Datetime('Дата', copy=False, default=fields.Datetime.now, required=True)

    mol_id = fields.Many2one('hr.employee', string='МОЛ')
    recipient_id = fields.Many2one('hr.employee', string='Получатель')


    location_id = fields.Many2one('sklad.location', string='Текущее место')
    location_dist_id = fields.Many2one('sklad.location', string='Место назначение')


    assets_line_ids = fields.One2many('sklad.transfer_use_assets_line', 'transfer_use_id', string='Строки Активов')
    product_line_ids = fields.One2many('sklad.transfer_use_product_line', 'transfer_use_id', string='Строки Номенклатуры')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sklad.transfer_use') or _('New')
        return super(TransferUse, self).create(vals)


class TransferUseAssets(models.Model):
    _name = "sklad.transfer_use_assets_line"
    _description = "Строки Активов, Передача в пользование"
    _order = "id"

    name = fields.Char(u'Наименование', related="assets_id.name", store=True, readonly=True)
    assets_id = fields.Many2one('sklad.assets', string='Актив', required=True)
    serial_number = fields.Char('Серийный номер', related='assets_id.serial_number', store=True, readonly=True)
    mol_id = fields.Many2one('hr.employee', string='МОЛ', related="transfer_use_id.mol_id", store=True)
    recipient_id = fields.Many2one('hr.employee', string='Получатель', related="transfer_use_id.recipient_id", store=True)
    location_id = fields.Many2one('sklad.location', string='Текущее место', related="transfer_use_id.location_id", store=True)
    location_dist_id = fields.Many2one('sklad.location', string='Место назначение', related="transfer_use_id.location_dist_id", store=True)


    transfer_use_id = fields.Many2one('sklad.transfer_use', string='Передача в пользование')



class TransferUseProduct(models.Model):
    _name = "sklad.transfer_use_product_line"
    _description = "Строки Номенклатура, Передача в пользование"
    _order = "id"

    name = fields.Char(u'Наименование', related="product_id.name", store=True, readonly=True)
    product_id = fields.Many2one('sklad.product', string='Номенклатура', required=True)
    product_uom_id = fields.Many2one('sklad.product_uom', string='Единица измерения', related="product_id.product_uom_id", store=True)
    qty = fields.Float('Кол-во', default=0.0, digits=(10, 3), copy=False)


    transfer_use_id = fields.Many2one('sklad.transfer_use', string='Передача в пользование')




