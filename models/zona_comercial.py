from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SurtecnicaZonaComercial(models.Model):
    """Zona en la que se hace la visita.

    Por qué un modelo propio y no la provincia nativa (res.country.state): las zonas con
    las que trabajan son más finas que la provincia y no coinciden con ella. En la planilla
    conviven 'Valle de Uco', 'Chilecito La Rioja', 'Poman' y 'Aimogasta' con 'Mendoza' y
    'Buenos Aires'; y hay zonas que cruzan provincias ('Nquen y R. N', 'Santa Fe y E.Rios').
    Forzar eso dentro de la provincia obligaría a repartir a mano lo que ellos ya tienen
    resuelto con su propio criterio.

    El vínculo con la provincia queda como dato opcional, para poder agrupar por provincia
    sin perder la zona.
    """

    _name = "surtecnica.zona.comercial"
    _description = "Zona comercial"
    _order = "sequence, name"

    name = fields.Char(string="Zona", required=True, translate=False)
    sequence = fields.Integer(string="Secuencia", default=10)
    active = fields.Boolean(string="Activo", default=True)
    state_id = fields.Many2one(
        "res.country.state",
        string="Provincia",
        help="Opcional. Sirve para agrupar por provincia sin perder el detalle de la zona.",
    )
    partner_ids = fields.One2many(
        "res.partner", "zona_comercial_id", string="Clientes de la zona"
    )
    partner_count = fields.Integer(
        string="Clientes", compute="_compute_partner_count"
    )
    note = fields.Char(string="Observaciones")

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Ya existe una zona con ese nombre."),
    ]

    @api.depends("partner_ids")
    def _compute_partner_count(self):
        # Por qué read_group y no len(partner_ids): con muchos clientes por zona, cargar
        # el one2many completo para contarlo trae todos los registros al ORM sin necesidad.
        data = self.env["res.partner"]._read_group(
            [("zona_comercial_id", "in", self.ids)],
            groupby=["zona_comercial_id"],
            aggregates=["__count"],
        )
        contados = {zona.id: cantidad for zona, cantidad in data}
        for registro in self:
            registro.partner_count = contados.get(registro.id, 0)

    @api.constrains("name")
    def _check_name(self):
        for registro in self:
            if not (registro.name or "").strip():
                raise ValidationError(_("La zona necesita un nombre."))
