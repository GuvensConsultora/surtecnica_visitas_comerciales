from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SurtecnicaMetaVisitas(models.Model):
    """Mínimo de visitas por mes que se espera de cada comercial.

    Por qué un modelo propio y no un campo en res.users: el dato es del circuito de
    visitas, no del usuario; así el módulo se desinstala sin dejar columnas en una tabla
    nativa. Viene VACÍO: la planilla sólo dice "Dana: Mínimo 20 visitas mensuales", y la
    meta de cada comercial la define la empresa, no nosotros.
    """

    _name = "surtecnica.meta.visitas"
    _description = "Meta mensual de visitas por comercial"
    _order = "user_id"
    _rec_name = "user_id"

    user_id = fields.Many2one("res.users", string="Comercial", required=True,
                              ondelete="cascade")
    visitas_minimas = fields.Integer(string="Visitas mínimas por mes", required=True)
    active = fields.Boolean(string="Activo", default=True)

    _sql_constraints = [
        ("user_uniq", "unique (user_id)", "Ese comercial ya tiene una meta cargada."),
    ]

    @api.constrains("visitas_minimas")
    def _check_visitas_minimas(self):
        for registro in self:
            if registro.visitas_minimas <= 0:
                raise ValidationError(_("La meta tiene que ser de al menos una visita."))
