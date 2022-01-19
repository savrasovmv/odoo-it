from odoo import fields, models, api, _

class TransferUse(models.Model):
    _name = "sklad.transfer_use"
    _description = "Передача в пользование"
    _order = "date desc"

    name = fields.Char('Номер', copy=False, readonly=True, default=lambda x: _('New'))
    date = fields.Datetime('Дата', copy=False, default=fields.Datetime.now)

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
    _order = "date desc"

    name = fields.Char(u'Наименование', related="assets_id.name", store=True, readonly=True)
    assets_id = fields.Many2one('sklad.assets', string='Актив')
    serial_number = fields.Char('Серийный номер', related='assets_id.serial_number', store=True, readonly=True)


    transfer_use_id = fields.Many2one('sklad.transfer_use', string='Передача в пользование')



class TransferUseProduct(models.Model):
    _name = "sklad.transfer_use_product_line"
    _description = "Строки Номенклатура, Передача в пользование"
    _order = "date desc"

    name = fields.Char(u'Наименование', related="product_id.name", store=True, readonly=True)
    product_id = fields.Many2one('sklad.product', string='Номенклатура')
    qty = fields.Float('Кол-во', default=0.0, digits=(10, 3), copy=False)


    transfer_use_id = fields.Many2one('sklad.transfer_use', string='Передача в пользование')




