# ============================================================
# CONTEXTO OPERATIVO - CREACIÓN DE DF_MAESTRO Y GRÁFICOS EDA0
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.ticker import FuncFormatter


# ============================================================
# 1. RUTAS
# ============================================================

ruta_data_limpios = Path(r"..\data_limpios")
ruta_graficos = Path(r"..\graficos")
ruta_graficos.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. CONFIGURACIÓN VISUAL
# ============================================================

plt.style.use("dark_background")

COLOR_FONDO = "#111827"
COLOR_PANEL = "#1f2937"
COLOR_TEXTO = "#f9fafb"
COLOR_GRID = "#6b7280"

ORDEN_TURNOS = ["M", "T", "N"]
ORDEN_PERIODOS = ["P1", "P2", "P3", "P4", "P5", "P6"]

ETIQUETAS_TURNOS = {
    "M": "Mañana\n06-14h",
    "T": "Tarde\n14-22h",
    "N": "Noche\n22-06h"
}

COLORES_TURNO = {
    "M": "#38bdf8",
    "T": "#facc15",
    "N": "#a78bfa"
}

COLORES_PERIODOS = {
    "P1": "#ef4444",
    "P2": "#f97316",
    "P3": "#facc15",
    "P4": "#22c55e",
    "P5": "#14b8a6",
    "P6": "#3b82f6"
}


def formato_miles(x, pos):
    return f"{x:,.0f}"


def aplicar_estilo(ax):
    ax.set_facecolor(COLOR_PANEL)
    ax.grid(True, alpha=0.22, color=COLOR_GRID)
    ax.tick_params(colors=COLOR_TEXTO)
    ax.xaxis.label.set_color(COLOR_TEXTO)
    ax.yaxis.label.set_color(COLOR_TEXTO)
    ax.title.set_color(COLOR_TEXTO)

    for spine in ax.spines.values():
        spine.set_color("#374151")


def guardar_grafico(nombre_archivo):
    plt.tight_layout()
    plt.savefig(
        ruta_graficos / nombre_archivo,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# ============================================================
# 3. CARGA DE DATASETS LIMPIOS
# ============================================================

df_consumo_hora = pd.read_csv(ruta_data_limpios / "df_consumo_2024_horario_estudio_limpio.csv")
df_periodos_limpio = pd.read_csv(ruta_data_limpios / "df_periodos_peninsula_limpio.csv")
df_tarifa = pd.read_csv(ruta_data_limpios / "df_tarifa_completa_2024_limpio.csv")


# ============================================================
# 4. CONVERSIÓN DE FECHAS
# ============================================================

# Es necesario porque al leer desde CSV las fechas entran como texto.
# Sin esta conversión no podremos calcular la semana del año.

df_consumo_hora["datetime_hora"] = pd.to_datetime(df_consumo_hora["datetime_hora"])
df_consumo_hora["fecha"] = pd.to_datetime(df_consumo_hora["fecha"])


# ============================================================
# 5. CREACIÓN DEL DATASET MAESTRO
# ============================================================

# Primero cruzamos consumo horario con periodos tarifarios.
# Clave: mes + tipo_semana + hora_periodo

df_maestro = df_consumo_hora.merge(
    df_periodos_limpio,
    on=["mes", "tipo_semana", "hora_periodo"],
    how="left"
)

# Después cruzamos con la tarifa completa.
# Clave: mes + periodo_tarifario

df_maestro = df_maestro.merge(
    df_tarifa,
    on=["mes", "periodo_tarifario"],
    how="left"
)


# ============================================================
# 6. CÁLCULO DE COSTE VARIABLE ESTIMADO
# ============================================================

# Coste usado en el EDA:
# consumo_kwh x (energia_regulada_eur_kwh + fnee_eur_kwh)
#
# No es una factura eléctrica real completa.
# No incluye potencia contratada, excesos, reactiva penalizable,
# impuestos completos, alquileres ni otros conceptos.

df_maestro["precio_variable_parcial_eur_kwh"] = (
    df_maestro["energia_regulada_eur_kwh"]
    + df_maestro["fnee_eur_kwh"]
)

df_maestro["coste_estimado_parcial_eur"] = (
    df_maestro["consumo_kwh"]
    * df_maestro["precio_variable_parcial_eur_kwh"]
)


# ============================================================
# 7. ORDEN Y VARIABLES AUXILIARES
# ============================================================

df_maestro["turno"] = pd.Categorical(
    df_maestro["turno"],
    categories=ORDEN_TURNOS,
    ordered=True
)

df_maestro["periodo_tarifario"] = pd.Categorical(
    df_maestro["periodo_tarifario"],
    categories=ORDEN_PERIODOS,
    ordered=True
)

# Semana secuencial del año.
# La necesitamos para el gráfico semanal por turno.

df_maestro["semana_anio"] = (
    (df_maestro["fecha"].dt.dayofyear - 1) // 7
) + 1

# MWh para gráficos agregados.
# El dataset mantiene consumo_kwh como unidad principal.

df_maestro["consumo_mwh"] = df_maestro["consumo_kwh"] / 1000


# ============================================================
# 8. SELECCIÓN DE COLUMNAS DEL DATASET MAESTRO
# ============================================================

columnas_maestro = [
    "datetime_hora",
    "fecha",
    "dia",
    "mes",
    "mes_nombre",
    "dia_semana_2024",
    "tipo_semana",
    "hora_periodo",
    "turno",
    "periodo_tarifario",
    "tramo_horario",
    "hora_inicio",
    "hora_fin",
    "tipo_carga",
    "consumo_kwh",
    "consumo_mwh",
    "potencia_media_kw",
    "reactiva_retrasada_kvarh",
    "reactiva_adelantada_kvarh",
    "CO2(tCO2)",
    "factor_potencia_retrasada",
    "factor_potencia_adelantada",
    "potencia_eur_kw_anio",
    "energia_regulada_eur_kwh",
    "exceso_potencia_eur_kw_dia",
    "reactiva_095_eur_kvarh",
    "reactiva_080_eur_kvarh",
    "iee_perc",
    "iva_perc",
    "alq_trif_eur_dia",
    "bs_eur_dia",
    "fnee_eur_kwh",
    "tasa_mun_perc",
    "precio_variable_parcial_eur_kwh",
    "coste_estimado_parcial_eur",
    "semana_anio"
]

df_maestro = df_maestro[columnas_maestro]


# ============================================================
# 9. GUARDADO DEL DATASET MAESTRO
# ============================================================

df_maestro.to_csv(
    ruta_data_limpios / "df_maestro.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# BLOQUE 0 - CONTEXTO OPERATIVO GENERAL
# ============================================================


# ============================================================
# GRÁFICO 1 - CONSUMO TOTAL: LABORABLE VS FIN DE SEMANA
# ============================================================

consumo_tipo_semana = (
    df_maestro
    .groupby("tipo_semana", as_index=False)
    .agg(consumo_mwh=("consumo_mwh", "sum"))
)

consumo_tipo_semana["tipo_semana"] = consumo_tipo_semana["tipo_semana"].replace({
    "Weekday": "Laborables",
    "Weekend": "Fines de semana"
})

fig, ax = plt.subplots(figsize=(9, 5.5))
fig.patch.set_facecolor(COLOR_FONDO)

barras = ax.bar(
    consumo_tipo_semana["tipo_semana"],
    consumo_tipo_semana["consumo_mwh"],
    color=["#38bdf8", "#a78bfa"],
    edgecolor="white",
    linewidth=1,
    alpha=0.92
)

aplicar_estilo(ax)

ax.set_title("Consumo total: laborables vs fines de semana", fontsize=15, weight="bold")
ax.set_xlabel("")
ax.set_ylabel("Consumo total (MWh)")
ax.yaxis.set_major_formatter(FuncFormatter(formato_miles))

for barra in barras:
    altura = barra.get_height()
    ax.text(
        barra.get_x() + barra.get_width() / 2,
        altura,
        f"{altura:,.0f} MWh",
        ha="center",
        va="bottom",
        fontsize=10,
        color=COLOR_TEXTO,
        weight="bold"
    )

guardar_grafico("eda0_01_consumo_laborable_vs_fin_semana.png")


# ============================================================
# GRÁFICO 2 - CONSUMO TOTAL POR TURNO
# ============================================================

consumo_turno = (
    df_maestro
    .groupby("turno", observed=False, as_index=False)
    .agg(consumo_mwh=("consumo_mwh", "sum"))
    .sort_values("turno")
)

fig, ax = plt.subplots(figsize=(9, 5.5))
fig.patch.set_facecolor(COLOR_FONDO)

barras = ax.bar(
    consumo_turno["turno"].astype(str).map(ETIQUETAS_TURNOS),
    consumo_turno["consumo_mwh"],
    color=[COLORES_TURNO[t] for t in consumo_turno["turno"].astype(str)],
    edgecolor="white",
    linewidth=1,
    alpha=0.92
)

aplicar_estilo(ax)

ax.set_title("Consumo total por turno", fontsize=15, weight="bold")
ax.set_xlabel("")
ax.set_ylabel("Consumo total (MWh)")
ax.yaxis.set_major_formatter(FuncFormatter(formato_miles))

for barra in barras:
    altura = barra.get_height()
    ax.text(
        barra.get_x() + barra.get_width() / 2,
        altura,
        f"{altura:,.0f} MWh",
        ha="center",
        va="bottom",
        fontsize=10,
        color=COLOR_TEXTO,
        weight="bold"
    )

guardar_grafico("eda0_02_consumo_total_por_turno.png")


# ============================================================
# GRÁFICO 3 - CONSUMO SEMANAL POR TURNO
# ============================================================

consumo_semana_turno = (
    df_maestro
    .groupby(["semana_anio", "turno"], observed=False, as_index=False)
    .agg(consumo_mwh=("consumo_mwh", "sum"))
)

tabla_semana_turno = (
    consumo_semana_turno
    .pivot(index="semana_anio", columns="turno", values="consumo_mwh")
    .fillna(0)
)

tabla_semana_turno = tabla_semana_turno[ORDEN_TURNOS]

fig, ax = plt.subplots(figsize=(16, 6))
fig.patch.set_facecolor(COLOR_FONDO)

bottom = np.zeros(len(tabla_semana_turno))

for turno in ORDEN_TURNOS:
    ax.bar(
        tabla_semana_turno.index,
        tabla_semana_turno[turno],
        bottom=bottom,
        label=ETIQUETAS_TURNOS[turno].replace("\n", " "),
        color=COLORES_TURNO[turno],
        edgecolor=COLOR_FONDO,
        linewidth=0.3,
        alpha=0.92
    )
    bottom += tabla_semana_turno[turno].values

aplicar_estilo(ax)

ax.set_title("Consumo semanal por turno durante 2024", fontsize=15, weight="bold")
ax.set_xlabel("Semana del año")
ax.set_ylabel("Consumo semanal (MWh)")
ax.set_xticks(range(1, int(df_maestro["semana_anio"].max()) + 1, 2))
ax.yaxis.set_major_formatter(FuncFormatter(formato_miles))

legend = ax.legend(
    title="Turno",
    facecolor=COLOR_PANEL,
    edgecolor="#374151",
    framealpha=0.95
)

plt.setp(legend.get_texts(), color=COLOR_TEXTO)
plt.setp(legend.get_title(), color=COLOR_TEXTO)

guardar_grafico("eda0_03_consumo_semanal_por_turno.png")


# ============================================================
# GRÁFICO 4 - CONSUMO MEDIO POR HORA DEL DÍA
# ============================================================

consumo_hora = (
    df_maestro
    .groupby("hora_periodo", as_index=False)
    .agg(consumo_medio_kwh=("consumo_kwh", "mean"))
)

fig, ax = plt.subplots(figsize=(12, 5.5))
fig.patch.set_facecolor(COLOR_FONDO)

ax.plot(
    consumo_hora["hora_periodo"],
    consumo_hora["consumo_medio_kwh"],
    marker="o",
    linewidth=2,
    color="#38bdf8"
)

aplicar_estilo(ax)

ax.set_title("Consumo medio horario durante el año", fontsize=15, weight="bold")
ax.set_xlabel("Hora del día")
ax.set_ylabel("Consumo medio horario (kWh)")
ax.set_xticks(range(1, 25))

guardar_grafico("eda0_04_consumo_medio_por_hora.png")


# ============================================================
# GRÁFICO 5 - PESO DEL CONSUMO Y DEL COSTE POR PERIODO
# ============================================================

resumen_periodo = (
    df_maestro
    .groupby("periodo_tarifario", observed=False, as_index=False)
    .agg(
        consumo_kwh=("consumo_kwh", "sum"),
        coste_estimado_parcial_eur=("coste_estimado_parcial_eur", "sum")
    )
    .sort_values("periodo_tarifario")
)

resumen_periodo["porcentaje_consumo"] = (
    resumen_periodo["consumo_kwh"]
    / resumen_periodo["consumo_kwh"].sum()
    * 100
)

resumen_periodo["porcentaje_coste"] = (
    resumen_periodo["coste_estimado_parcial_eur"]
    / resumen_periodo["coste_estimado_parcial_eur"].sum()
    * 100
)

x = np.arange(len(resumen_periodo))
ancho = 0.38

fig, ax = plt.subplots(figsize=(11, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

barras_consumo = ax.bar(
    x - ancho / 2,
    resumen_periodo["porcentaje_consumo"],
    width=ancho,
    label="% consumo",
    color="#38bdf8",
    edgecolor="white",
    linewidth=0.8,
    alpha=0.92
)

barras_coste = ax.bar(
    x + ancho / 2,
    resumen_periodo["porcentaje_coste"],
    width=ancho,
    label="% coste estimado",
    color="#f97316",
    edgecolor="white",
    linewidth=0.8,
    alpha=0.92
)

aplicar_estilo(ax)

ax.set_title("Peso del consumo y del coste estimado por periodo tarifario", fontsize=15, weight="bold")
ax.set_xlabel("Periodo tarifario")
ax.set_ylabel("Porcentaje sobre el total (%)")
ax.set_xticks(x)
ax.set_xticklabels(resumen_periodo["periodo_tarifario"].astype(str))

legend = ax.legend(
    facecolor=COLOR_PANEL,
    edgecolor="#374151",
    framealpha=0.95
)

plt.setp(legend.get_texts(), color=COLOR_TEXTO)

for barras in [barras_consumo, barras_coste]:
    for barra in barras:
        altura = barra.get_height()
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            altura,
            f"{altura:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLOR_TEXTO,
            weight="bold"
        )

guardar_grafico("eda0_05_consumo_vs_coste_parcial_por_periodo.png")


# ============================================================
# RESULTADO EN CONSOLA
# ============================================================

print("df_maestro.csv generado correctamente.")
print("Gráficos del bloque 0 generados correctamente:")
print("- eda0_01_consumo_laborable_vs_fin_semana.png")
print("- eda0_02_consumo_total_por_turno.png")
print("- eda0_03_consumo_semanal_por_turno.png")
print("- eda0_04_consumo_medio_por_hora.png")
print("- eda0_05_consumo_vs_coste_parcial_por_periodo.png")