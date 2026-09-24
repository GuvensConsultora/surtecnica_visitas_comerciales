from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class VisitaRubro(models.Model):
    """Etiquetas propias de la visita comercial: proyecto, importante, proveedor que entra en
    la cotización, lo que defina el equipo comercial.

    Por qué un catálogo propio y no las etiquetas de contacto: esas describen al cliente
    (su industria) y las usan otros circuitos, como el pañol; éstas describen la visita.
    Mezclarlas contamina los dos filtros. Pedido de comercial del 24/09/2026.
    """

    _name = "surtecnica.visita.rubro"
    _description = "Rubro de visita comercial"
    _order = "name"

    name = fields.Char(string="Rubro", required=True, translate=False)
    color = fields.Integer(string="Color")
    active = fields.Boolean(string="Activo", default=True)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Ya existe un rubro con ese nombre."),
    ]

    @api.constrains("name")
    def _check_name(self):
        # El unique de SQL distingue mayúsculas: sin este control conviven "Importante" e
        # "importante", que es justo lo que pasó con las etiquetas de contacto.
        for registro in self:
            nombre = (registro.name or "").strip()
            if not nombre:
                raise ValidationError(_("El rubro necesita un nombre."))
            repetido = self.with_context(active_test=False).search(
                [("id", "!=", registro.id), ("name", "=ilike", nombre)], limit=1
            )
            if repetido:
                raise ValidationError(
                    _("Ya existe el rubro «%s». Usá ése en vez de crear otro.") % repetido.name
                )
