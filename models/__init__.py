from . import zona_comercial
from . import visita_rubro
from . import calendar_event
from . import res_partner
# El orden importa: la vista SQL del resumen lee la tabla de metas, que tiene que
# existir antes de que se cree la vista.
from . import meta_visitas
from . import visita_resumen
