from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import werkzeug
from odoo.http import request


class ItAuthSignupHome(AuthSignupHome):

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        return  werkzeug.utils.redirect('/') #request.redirect('/') 

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        return  werkzeug.utils.redirect('/')
