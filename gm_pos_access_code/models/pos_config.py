from odoo import models, api, _, fields
from odoo.http import request


class PosConfig(models.Model):
    _inherit = 'pos.config'

    generate_access_code = fields.Boolean(string='Generate Access Code', default=False)

    def open_custom_ui(self):
        """Open custom POS UI interface - 100% identical to original POS
        
        Returns action URL to custom POS interface that renders exactly like /pos/ui
        """
        self.ensure_one()
        
        # Create session if needed (same logic as original open_ui)
        if not self.current_session_id:
            self.env['pos.session'].create({'user_id': self.env.uid, 'config_id': self.id})
            
        path = '/gm_pos/web' if self._force_http() else '/gm_pos/ui'
        pos_url = path + '?config_id=%d&from_backend=True' % self.id
        debug = request and request.session.debug
        if debug:
            pos_url += '&debug=%s' % debug
            
        return {
            'type': 'ir.actions.act_url',
            'url': pos_url,
            'target': 'self',
        }