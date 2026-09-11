from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CalendarEvent(models.Model):
    """La visita comercial se apoya en el evento de calendario nativo.

    Por qué acá y no en un modelo propio: calendar.event ya tiene fecha, responsable,
    cliente, observaciones y el vínculo con la oportunidad de CRM, y ya está en la app
    Calendario que el comercial abre desde el celular. Un modelo nuevo obligaría a cargar
    la visita dos veces —una para la agenda, otra para el informe— y esa doble carga es
    exactamente lo que devuelve a la gente a la planilla.

    Sólo se agregan campos; no se redefine ninguno nativo.
    """

    _inherit = "calendar.event"

    es_visita_comercial = fields.Boolean(
        string="Es visita comercial",
        default=False,
        index=True,
        help="Marca el evento para que entre en el informe de visitas comerciales. "
        "Los eventos de agenda que no son visitas quedan fuera del informe.",
    )
    cliente_id = fields.Many2one(
        "res.partner",
        string="Cliente visitado",
        index=True,
        help="A quién se visitó. No se usa el partner_id nativo porque ese campo es "
        "'Scheduled by': un related no almacenado de user_id.partner_id, o sea el "
        "organizador, no el cliente. Sin campo propio no se puede filtrar ni agrupar.",
    )
    tipo_visita_id = fields.Many2one(
        "calendar.event.type",
        string="Tipo de visita",
        default=lambda self: self._default_tipo_visita_id(),
        help="Reunión, Contacto, Llamado o Video llamada.",
    )

    @api.model
    def _default_tipo_visita_id(self):
        """Reunión por defecto: es lo que ocurre en 1.081 de las 1.198 visitas con tipo
        cargado en la planilla. Un default acertado evita un click en casi todos los
        casos; el que hizo un llamado lo cambia."""
        return self.env.ref(
            "surtecnica_visitas_comerciales.tipo_visita_reunion",
            raise_if_not_found=False,
        )
    zona_comercial_id = fields.Many2one(
        "surtecnica.zona.comercial",
        string="Zona",
        compute="_compute_zona_comercial_id",
        store=True,
        readonly=False,
        index=True,
        help="Se completa sola con la zona del cliente. Se puede cambiar si la visita "
        "se hizo en otra zona.",
    )

    @api.depends("cliente_id")
    def _compute_zona_comercial_id(self):
        # readonly=False: se propone la zona del cliente, pero el comercial manda.
        # Si el evento ya tiene zona cargada a mano, no se pisa.
        for evento in self:
            if evento.cliente_id.zona_comercial_id and not evento.zona_comercial_id:
                evento.zona_comercial_id = evento.cliente_id.zona_comercial_id
            elif not evento.zona_comercial_id:
                evento.zona_comercial_id = False

    @api.onchange("cliente_id", "es_visita_comercial")
    def _onchange_cliente_id_visita(self):
        """Propone el título para no obligar a escribirlo. `name` es requerido en el
        nativo y pedirle al comercial que invente un título en cada visita es fricción
        pura: la visita ya se identifica por cliente y fecha."""
        for evento in self:
            if evento.es_visita_comercial and evento.cliente_id and not evento.name:
                evento.name = _("Visita a %s") % evento.cliente_id.display_name

    @api.model_create_multi
    def create(self, vals_list):
        # Mismo default que el onchange, para las visitas que entran por importador o
        # por API, donde el onchange no corre (ver B.27: lo que la UI estampa hay que
        # estamparlo explícitamente).
        for vals in vals_list:
            if vals.get("es_visita_comercial") and not vals.get("name") and vals.get("cliente_id"):
                partner = self.env["res.partner"].browse(vals["cliente_id"])
                vals["name"] = _("Visita a %s") % partner.display_name
        return super().create(vals_list)

    @api.constrains("es_visita_comercial", "cliente_id")
    def _check_visita_comercial(self):
        """Lo mínimo para que el informe sirva: sin cliente, la visita no se puede
        atribuir a nadie. El tipo NO se exige: viene con Reunión por defecto, que es
        lo que ocurre en 9 de cada 10 casos."""
        for evento in self:
            if evento.es_visita_comercial and not evento.cliente_id:
                raise ValidationError(
                    _("Para registrar una visita comercial hace falta indicar el cliente.")
                )
