{
    "name": "Sur Técnica - Visitas comerciales",
    "summary": "Registro de visitas de los comerciales por zona y tipo, con informe mensual",
    "description": """
Reemplaza la planilla 'Visitas Comerciales.xlsx' por registro en Odoo.

La visita se apoya en calendar.event (nativo), que ya tiene fecha, comercial, cliente,
observaciones y vínculo con la oportunidad de CRM. Este módulo agrega lo único que
faltaba: la zona y el tipo de visita, más un menú propio para que las visitas
comerciales no se mezclen con la agenda general.

El informe por comercial y mes sale de la vista pivot nativa: sin fórmulas que arrastrar.
    """,
    "version": "17.0.1.4.1",
    "author": "Yagüven C.G.",
    "website": "https://yaguven.com",
    "license": "LGPL-3",
    "category": "Sales/CRM",
    "depends": ["calendar", "crm", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/tipo_visita_data.xml",
        "data/zona_comercial_data.xml",
        "views/zona_comercial_views.xml",
        "views/visita_rubro_views.xml",
        "views/visita_etiqueta_views.xml",
        "views/calendar_event_views.xml",
        "views/res_partner_views.xml",
        "views/resumen_views.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "surtecnica_visitas_comerciales/static/src/js/graph_cantidades.js",
        ],
    },
    "installable": True,
    "auto_install": False,
}
