# -*- coding: utf-8 -*-

from odoo import fields, models, api
from ldap3 import Server, Connection, SUBTREE, MODIFY_REPLACE, LEVEL
import json
import base64

class SyncWizard(models.TransientModel):
    _name = 'jms.wizard'
    _description = "Wizard JMS"



    result = fields.Text(string='Результат')

    

    def return_result(self, error=False):
        """Возвращает ошибку или результат выполнения действия"""

        if error:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('Прерванно'),
                    'message': error,
                    'type':'warning',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                },
            }
            return notification
        else:
            return {
				'name': 'Message',
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'sync.wizard',
				'target':'new',
				'context':{
							'default_result':self.result,
							} 
				}


    def jms_wizard_action(self):
        self.result = self.env['jms.connect'].sudo().jms_connect()
        # try:
        #     self.result = self.env['jms.connect'].sudo().jms_connect()
        # except Exception as error:
        #     return self.return_result(error=error)
        
        # return self.return_result()

    

    