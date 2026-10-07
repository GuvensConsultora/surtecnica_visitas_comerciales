from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class VisitaRubro(models.Model):
    """Rubro del cliente visitado (agro, bodega, ingeniería…): una lista predeterminada que
    arma el equipo comercial, y el vendedor elige uno en cada visita.

    Por qué un catálogo propio y no las etiquetas de contacto: ésas las usan otros
    circuitos, como el pañol, y mezclarlas contamina los dos filtros. Pedido de comercial
    del 28/09/2026: el rubro lo elige el vendedor en la visita (29/09); las etiquetas
    libres van aparte, en ``surtecnica.visita.etiqueta``.
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
