from odoo import _, fields, models


class ResPartner(models.Model):
    """La zona vive en el cliente, no en cada visita.

    Por qué: la zona es un atributo del cliente, no del encuentro — el mismo cliente
    está siempre en la misma zona. Cargándola una vez por cliente, las visitas la
    heredan solas y el comercial no la tipea nunca. Es también lo que permite mirar la
    cartera por zona, no sólo las visitas.
    """

    _inherit = "res.partner"

    zona_comercial_id = fields.Many2one(
        "surtecnica.zona.comercial",
        string="Zona comercial",
        index=True,
        help="Zona en la que se atiende a este cliente. Las visitas la toman de acá.",
    )
    visita_count = fields.Integer(
        string="Visitas", compute="_compute_visita_count"
    )

    def _compute_visita_count(self):
        # Sólo cuenta las marcadas como visita comercial: la agenda general no es cartera.
        data = self.env["calendar.event"]._read_group(
            [("cliente_id", "in", self.ids), ("es_visita_comercial", "=", True)],
            groupby=["cliente_id"],
            aggregates=["__count"],
        )
        contados = {partner.id: cantidad for partner, cantidad in data}
        for registro in self:
            registro.visita_count = contados.get(registro.id, 0)

    def action_ver_visitas(self):
        """Smart button: abre las visitas de este cliente ya filtradas y con el cliente
        precargado, para que registrar la próxima sea un click desde su ficha."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Visitas a %s") % self.display_name,
            "res_model": "calendar.event",
            "view_mode": "tree,form,pivot,calendar",
            "domain": [
                ("cliente_id", "=", self.id),
                ("es_visita_comercial", "=", True),
            ],
            "context": {
                "default_cliente_id": self.id,
                "default_es_visita_comercial": True,
                "default_zona_comercial_id": self.zona_comercial_id.id,
            },
        }
