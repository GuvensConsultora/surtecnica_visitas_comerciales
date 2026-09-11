from odoo import fields, models, tools


class SurtecnicaVisitaResumen(models.Model):
    """Reemplaza la hoja "Resumen de visitas": una fila por comercial y por mes.

    Es una vista SQL de sólo lectura (_auto = False): no guarda nada, se recalcula al
    abrirla a partir de las visitas cargadas. Así no hay dos fuentes que puedan diferir.

    Decisiones que no son obvias:
    - Los meses SIN visitas aparecen con 0. Si no, el promedio sólo contaría los meses
      buenos y un mes vacío nunca figuraría como meta incumplida. Cada comercial tiene
      meses desde su primera visita hasta el mes actual (o hasta su última visita, si el
      usuario está archivado, para que un ex comercial no sume ceros para siempre).
    - El mes se toma en la zona horaria del comercial: una visita del 31 a las 22 h no
      puede caer en el mes siguiente por estar guardada en UTC.
    - Un mismo número se expone en dos campos (cantidad y promedio) porque cada campo
      tiene un solo agregador: sumado da el total, promediado da el promedio mensual.
    """

    _name = "surtecnica.visita.resumen"
    _description = "Resumen mensual de visitas comerciales"
    _auto = False
    _order = "mes desc, user_id"
    _rec_name = "user_id"

    user_id = fields.Many2one("res.users", string="Comercial", readonly=True)
    mes = fields.Date(string="Mes", readonly=True)
    cantidad = fields.Integer(string="Visitas", readonly=True, group_operator="sum")
    promedio = fields.Float(string="Promedio mensual", readonly=True,
                            group_operator="avg", digits=(16, 1))
    participacion = fields.Float(
        string="Participación en el mes (%)", readonly=True, group_operator="avg",
        digits=(16, 1),
        help="Qué parte de las visitas del mes hizo este comercial. Al agrupar varios "
        "meses muestra el promedio de esas participaciones.",
    )
    meta = fields.Integer(string="Meta", readonly=True, group_operator="avg")
    cumplimiento = fields.Float(
        string="Cumplimiento de la meta (%)", readonly=True, group_operator="avg",
        digits=(16, 1),
        help="Visitas del mes sobre la meta del comercial. Vacío si no tiene meta cargada.",
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH visitas AS (
                    SELECT e.user_id,
                           date_trunc('month', e.start AT TIME ZONE 'UTC'
                                      AT TIME ZONE COALESCE(p.tz, 'UTC'))::date AS mes,
                           count(*) AS cantidad
                      FROM calendar_event e
                      JOIN res_users u ON u.id = e.user_id
                      JOIN res_partner p ON p.id = u.partner_id
                     WHERE e.es_visita_comercial
                       AND e.active
                     GROUP BY 1, 2
                ), rango AS (
                    SELECT v.user_id,
                           min(v.mes) AS desde,
                           CASE WHEN u.active
                                THEN date_trunc('month', now())::date
                                ELSE max(v.mes) END AS hasta
                      FROM visitas v
                      JOIN res_users u ON u.id = v.user_id
                     GROUP BY v.user_id, u.active
                ), grilla AS (
                    SELECT r.user_id, gs::date AS mes
                      FROM rango r,
                           generate_series(r.desde, r.hasta, interval '1 month') gs
                ), total_mes AS (
                    SELECT mes, sum(cantidad) AS total FROM visitas GROUP BY mes
                )
                SELECT row_number() OVER (ORDER BY g.mes, g.user_id) AS id,
                       g.user_id,
                       g.mes,
                       COALESCE(v.cantidad, 0) AS cantidad,
                       COALESCE(v.cantidad, 0)::float AS promedio,
                       CASE WHEN t.total > 0
                            THEN 100.0 * COALESCE(v.cantidad, 0) / t.total END
                           AS participacion,
                       m.visitas_minimas AS meta,
                       CASE WHEN m.visitas_minimas > 0
                            THEN 100.0 * COALESCE(v.cantidad, 0) / m.visitas_minimas END
                           AS cumplimiento
                  FROM grilla g
                  LEFT JOIN visitas v ON v.user_id = g.user_id AND v.mes = g.mes
                  LEFT JOIN total_mes t ON t.mes = g.mes
                  LEFT JOIN surtecnica_meta_visitas m
                         ON m.user_id = g.user_id AND m.active
            )
        """)
