/** @odoo-module **/

/*
 * Gráfico de barras que muestra la cantidad de cada barra siempre visible,
 * sin tener que pasar el mouse (pedido de Matías, 05/11/2026).
 *
 * No toca el gráfico estándar de Odoo: es una vista aparte
 * (js_class="surtecnica_graph_cantidades") que sólo usan los gráficos de Visitas.
 * Hereda el renderizador nativo y le agrega un plugin de Chart.js que escribe
 * el número después de dibujar las barras.
 */

import { registry } from "@web/core/registry";
import { cookie } from "@web/core/browser/cookie";
import { graphView } from "@web/views/graph/graph_view";
import { GraphRenderer } from "@web/views/graph/graph_renderer";

// Alto mínimo (px) de un tramo apilado para escribirle el número adentro.
const ALTO_MINIMO_TRAMO = 14;

function formatearCantidad(valor) {
    if (Number.isInteger(valor)) {
        return String(valor);
    }
    return valor.toLocaleString("es-AR", { maximumFractionDigits: 2 });
}

const pluginCantidades = {
    id: "surtecnica_cantidades",
    afterDatasetsDraw(chart, _args, opciones) {
        const { ctx } = chart;
        const oscuro = opciones.oscuro;
        ctx.save();
        ctx.font = "bold 12px sans-serif";
        ctx.textAlign = "center";
        // Con una sola serie de barras visible no hay nada apilado: el número va arriba.
        const seriesVisibles = chart.data.datasets.filter(
            (d, i) => d.type !== "line" && chart.isDatasetVisible(i)
        ).length;
        const apilado = opciones.apilado && seriesVisibles > 1;
        chart.data.datasets.forEach((dataset, i) => {
            // La línea de tendencia punteada no lleva número: sólo las barras.
            if (dataset.type === "line" || !chart.isDatasetVisible(i)) {
                return;
            }
            const meta = chart.getDatasetMeta(i);
            meta.data.forEach((barra, j) => {
                const valor = dataset.data[j];
                if (!valor) {
                    return;
                }
                const texto = formatearCantidad(valor);
                const { x, y, base } = barra.getProps(["x", "y", "base"], true);
                if (apilado) {
                    // Barras apiladas: el número va en el centro de su tramo.
                    const alto = Math.abs(base - y);
                    if (alto < ALTO_MINIMO_TRAMO) {
                        return;
                    }
                    ctx.fillStyle = "#ffffff";
                    ctx.textBaseline = "middle";
                    ctx.fillText(texto, x, (y + base) / 2);
                } else {
                    // Barras simples: el número va arriba de la barra.
                    ctx.fillStyle = oscuro ? "#e5e7eb" : "#374151";
                    ctx.textBaseline = "bottom";
                    ctx.fillText(texto, x, y - 4);
                }
            });
        });
        ctx.restore();
    },
};

export class GraphRendererCantidades extends GraphRenderer {
    getChartConfig() {
        const config = super.getChartConfig();
        if (config.type !== "bar") {
            return config;
        }
        const options = config.options;
        // Lugar arriba para que el número de la barra más alta no quede cortado.
        options.layout = { ...(options.layout || {}), padding: { top: 20 } };
        options.plugins = {
            ...options.plugins,
            surtecnica_cantidades: {
                apilado: Boolean(this.model.metaData.stacked),
                oscuro: cookie.get("color_scheme") === "dark",
            },
        };
        config.plugins = [...(config.plugins || []), pluginCantidades];
        return config;
    }
}

registry.category("views").add("surtecnica_graph_cantidades", {
    ...graphView,
    Renderer: GraphRendererCantidades,
});
