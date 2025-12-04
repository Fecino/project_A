# -*- coding: utf-8 -*-


from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.tools.mail import is_html_empty
import uuid

class CRMScentopia(models.Model):
    _inherit = 'crm.lead'

    uuid = fields.Char(string='UUID')
    # avatar_img = fields.Many2one('scentopia.avatar', string='Avatar Image')
    no_of_employees = fields.Integer(string='No of Employees')
    designation = fields.Char(string='Designation')
    email_opt_out = fields.Char(string='Email Opt Out')
    fax = fields.Char(string='Fax')
    annual_revenue = fields.Monetary(string='Annual Revenue', currency_field='company_currency', tracking=True, default=0.0)
    reason_of_loss = fields.Html(string='Reason of Loss')
    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('uuid'):
                vals['uuid'] = str(uuid.uuid4())
        return super(CRMScentopia, self).create(vals_list)
        
class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    def action_lost_reason_apply(self):
        """Mark lead as lost and apply the loss reason"""
        self.ensure_one()
        if not is_html_empty(self.lost_feedback):
            self.lead_ids._track_set_log_message(
                Markup('<div style="margin-bottom: 4px;"><p>%s:</p>%s<br /></div>') % (
                    _('Lost Comment'),
                    self.lost_feedback
                )
            )
        # Inherit and add reason_of_loss parameter
        res = self.lead_ids.action_set_lost(
            lost_reason_id=self.lost_reason_id.id,
            reason_of_loss=self.lost_feedback
        )
        return res
    
