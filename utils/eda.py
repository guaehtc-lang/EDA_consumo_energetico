# ============================================================
# EDA - ANÁLISIS EXPLORATORIO DEL CONSUMO ENERGÉTICO
# ============================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from matplotlib.ticker import FuncFormatter

# ============================================================
# 1. RUTAS
# ============================================================
ruta_data_limpios = Path(r"..\data_limpios")
ruta_graficos = Path(r"..\graficos")
ruta_graficos.mkdir(parents=True, exist_ok=True)

# ============================================================
# 2. CONFIGURACIÓN VISUAL GENERAL
# ============================================================
plt.style.use("dark_background")

COLOR_FONDO   = "#111827"
COLOR_PANEL   = "#1f2937"
COLOR_TEXTO   = "#f9fafb"
COLOR_GRID    = "#6b7280"
COLOR_CONSUMO = "#38bdf8"
COLOR_COSTE   = "#f97316"
COLOR_TEMP    = "#facc15"
COLOR_VIENTO  = "#a78bfa"

ORDEN_PERIODOS = ["P1", "P2", "P3", "P4", "P5", "P6"]
ORDEN_TURNOS   = ["M", "T", "N"]

COLORES_PERIODOS = {
    "P1": "#ef4444",
    "P2": "#f97316",
    "P3": "#facc15",
    "P4": "#22c55e",
    "P5": "#14b8a6",
    "P6": "#3b82f6"
}

COLORES_TURNOS = {
    "M": "#38bdf8",
    "T": "#facc15",
    "N": "#a78bfa"
}

ETIQUETAS_TURNOS = {
    "M": "Mañana\n06-14h",
    "T": "Tarde\n14-22h",
    "N": "Noche\n22-06h"
}


def aplicar_estilo(ax):
    """Aplica el estilo visual común a todos los gráficos."""
    ax.set_facecolor(COLOR_PANEL)
    ax.grid(True, alpha=0.22, color=COLOR_GRID)
    ax.tick_params(colors=COLOR_TEXTO)
    ax.xaxis.label.set_color(COLOR_TEXTO)
    ax.yaxis.label.set_color(COLOR_TEXTO)
    ax.title.set_color(COLOR_TEXTO)
    for spine in ax.spines.values():
        spine.set_color("#374151")


def guardar_grafico(nombre_archivo):
    """Guarda el gráfico actual en la carpeta de gráficos."""
    plt.tight_layout()
    plt.savefig(
        ruta_graficos / nombre_archivo,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


def formato_miles(x, pos):
    return f"{x:,.0f}"


def formato_eur_kwh(x, pos):
    return f"{x:.3f}"


# ============================================================
# 3. CARGA DE DATOS
# ============================================================
df_maestro = pd.read_csv(ruta_data_limpios / "df_maestro.csv")
df_clima   = pd.read_csv(ruta_data_limpios / "df_clima_2024_limpio.csv")

df_maestro["datetime_hora"] = pd.to_datetime(df_maestro["datetime_hora"])
df_maestro["fecha"]         = pd.to_datetime(df_maestro["fecha"])
df_clima["fecha"]           = pd.to_datetime(df_clima["fecha"])

df_maestro = (
    df_maestro
    .sort_values("datetime_hora")
    .reset_index(drop=True)
)

df_maestro["periodo_tarifario"] = pd.Categorical(
    df_maestro["periodo_tarifario"],
    categories=ORDEN_PERIODOS,
    ordered=True
)

df_maestro["turno"] = pd.Categorical(
    df_maestro["turno"],
    categories=ORDEN_TURNOS,
    ordered=True
)


# ============================================================
# H1 - CLIMA, CONSUMO Y COSTE ESTIMADO
# ============================================================
# Hipótesis:
# El consumo eléctrico diario puede variar en función de la
# temperatura exterior, especialmente en días de frío o calor intenso.

# ============================================================
# H1.1 - CREACIÓN DEL DATASET DIARIO CONSUMO + CLIMA
# ============================================================
df_consumo_diario = (
    df_maestro
    .groupby("fecha", as_index=False)
    .agg(
        dia=("dia", "first"),
        mes=("mes", "first"),
        mes_nombre=("mes_nombre", "first"),
        dia_semana_2024=("dia_semana_2024", "first"),
        tipo_semana=("tipo_semana", "first"),
        consumo_kwh=("consumo_kwh", "sum"),
        coste_estimado_parcial_eur=("coste_estimado_parcial_eur", "sum"),
        potencia_media_diaria_kw=("potencia_media_kw", "mean"),
        potencia_max_horaria_kw=("potencia_media_kw", "max"),
        reactiva_retrasada_kvarh=("reactiva_retrasada_kvarh", "sum"),
        reactiva_adelantada_kvarh=("reactiva_adelantada_kvarh", "sum"),
        CO2_tCO2=("CO2(tCO2)", "sum"),
        factor_potencia_retrasada=("factor_potencia_retrasada", "mean"),
        factor_potencia_adelantada=("factor_potencia_adelantada", "mean")
    )
)

df_consumo_diario["coste_unitario_parcial_eur_kwh"] = (
    df_consumo_diario["coste_estimado_parcial_eur"]
    / df_consumo_diario["consumo_kwh"]
)

columnas_clima = [
    "fecha",
    "temperatura_media",
    "temperatura_minima",
    "temperatura_maxima",
    "precipitacion",
    "viento_medio",
    "racha_viento",
    "horas_sol",
    "presion_maxima",
    "presion_minima",
    "num_estaciones"
]

df_consumo_clima = df_consumo_diario.merge(
    df_clima[columnas_clima],
    on="fecha",
    how="left"
)


def asignar_estacion(mes):
    if mes in [12, 1, 2]:
        return "Invierno"
    elif mes in [3, 4, 5]:
        return "Primavera"
    elif mes in [6, 7, 8]:
        return "Verano"
    else:
        return "Otoño"


df_consumo_clima["estacion"] = df_consumo_clima["mes"].apply(asignar_estacion)

p10_temp = df_consumo_clima["temperatura_media"].quantile(0.10)
p90_temp = df_consumo_clima["temperatura_media"].quantile(0.90)


def clasificar_temperatura(temp):
    if temp <= p10_temp:
        return "Frío"
    elif temp >= p90_temp:
        return "Caluroso"
    else:
        return "Normal"


df_consumo_clima["tipo_temperatura"] = (
    df_consumo_clima["temperatura_media"].apply(clasificar_temperatura)
)

df_consumo_clima.to_csv(
    ruta_data_limpios / "df_consumo_clima_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# H1.2 - CONSUMO DIARIO Y TEMPERATURA MEDIA
# ============================================================
fig, ax1 = plt.subplots(figsize=(15, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

ax1.plot(
    df_consumo_clima["fecha"],
    df_consumo_clima["consumo_kwh"],
    color=COLOR_CONSUMO,
    linewidth=1.8,
    label="Consumo diario"
)
aplicar_estilo(ax1)
ax1.set_title(
    "Consumo diario y temperatura media durante 2024",
    fontsize=15, weight="bold"
)
ax1.set_xlabel("Fecha")
ax1.set_ylabel("Consumo diario (kWh)", color=COLOR_CONSUMO)
ax1.tick_params(axis="y", labelcolor=COLOR_CONSUMO)
ax1.yaxis.set_major_formatter(FuncFormatter(formato_miles))

ax2 = ax1.twinx()
ax2.plot(
    df_consumo_clima["fecha"],
    df_consumo_clima["temperatura_media"],
    color=COLOR_TEMP,
    linewidth=1.5,
    alpha=0.85,
    label="Temperatura media"
)
ax2.set_ylabel("Temperatura media (°C)", color=COLOR_TEMP)
ax2.tick_params(axis="y", labelcolor=COLOR_TEMP)
ax2.spines["right"].set_color("#374151")

lineas_1, etiquetas_1 = ax1.get_legend_handles_labels()
lineas_2, etiquetas_2 = ax2.get_legend_handles_labels()
legend = ax1.legend(
    lineas_1 + lineas_2,
    etiquetas_1 + etiquetas_2,
    facecolor=COLOR_PANEL,
    edgecolor="#374151",
    framealpha=0.95,
    loc="upper left"
)
plt.setp(legend.get_texts(), color=COLOR_TEXTO)
guardar_grafico("h1_01_consumo_diario_temperatura_media.png")


# ============================================================
# H1.3 - SCATTER CONSUMO VS TEMPERATURA
# ============================================================
df_h1_temp = df_consumo_clima[
    ["temperatura_media", "consumo_kwh"]
].dropna().copy()

x_temp   = df_h1_temp["temperatura_media"]
y_consumo = df_h1_temp["consumo_kwh"]

pendiente, intercepto = np.polyfit(x_temp, y_consumo, 1)
x_linea = np.linspace(x_temp.min(), x_temp.max(), 100)
y_linea = pendiente * x_linea + intercepto

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(COLOR_FONDO)

ax.scatter(
    x_temp, y_consumo,
    s=45, alpha=0.72,
    color=COLOR_CONSUMO,
    edgecolors="white",
    linewidths=0.35
)
ax.plot(
    x_linea, y_linea,
    color=COLOR_COSTE,
    linewidth=2.2,
    label="Tendencia lineal"
)
aplicar_estilo(ax)
ax.set_title(
    "Relación exploratoria: consumo diario vs temperatura media",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Temperatura media diaria (°C)")
ax.set_ylabel("Consumo diario (kWh)")
ax.yaxis.set_major_formatter(FuncFormatter(formato_miles))

legend = ax.legend(facecolor=COLOR_PANEL, edgecolor="#374151", framealpha=0.95)
plt.setp(legend.get_texts(), color=COLOR_TEXTO)
guardar_grafico("h1_02_scatter_consumo_temperatura_media.png")


# ============================================================
# H1.4 - CONSUMO Y COSTE POR TIPO DE TEMPERATURA
# ============================================================
orden_temp = ["Frío", "Normal", "Caluroso"]

resumen_temp = (
    df_consumo_clima
    .groupby("tipo_temperatura", as_index=False)
    .agg(
        dias=("fecha", "count"),
        temperatura_media=("temperatura_media", "mean"),
        consumo_medio_diario_kwh=("consumo_kwh", "mean"),
        coste_medio_diario_eur=("coste_estimado_parcial_eur", "mean"),
        coste_unitario_medio_eur_kwh=("coste_unitario_parcial_eur_kwh", "mean"),
        viento_medio=("viento_medio", "mean")
    )
)

resumen_temp["tipo_temperatura"] = pd.Categorical(
    resumen_temp["tipo_temperatura"],
    categories=orden_temp,
    ordered=True
)
resumen_temp = resumen_temp.sort_values("tipo_temperatura")

x     = np.arange(len(resumen_temp))
ancho = 0.38

fig, ax1 = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor(COLOR_FONDO)

barras_consumo = ax1.bar(
    x - ancho / 2,
    resumen_temp["consumo_medio_diario_kwh"],
    width=ancho,
    color=COLOR_CONSUMO,
    edgecolor="white",
    linewidth=0.8,
    alpha=0.9,
    label="Consumo medio diario"
)
aplicar_estilo(ax1)
ax1.set_ylabel("Consumo medio diario (kWh)", color=COLOR_CONSUMO)
ax1.tick_params(axis="y", labelcolor=COLOR_CONSUMO)
ax1.yaxis.set_major_formatter(FuncFormatter(formato_miles))

ax2 = ax1.twinx()
barras_coste = ax2.bar(
    x + ancho / 2,
    resumen_temp["coste_medio_diario_eur"],
    width=ancho,
    color=COLOR_COSTE,
    edgecolor="white",
    linewidth=0.8,
    alpha=0.9,
    label="Coste estimado medio diario"
)
ax2.set_ylabel("Coste estimado medio diario (€)", color=COLOR_COSTE)
ax2.tick_params(axis="y", labelcolor=COLOR_COSTE)
ax2.spines["right"].set_color("#374151")

ax1.set_xticks(x)
ax1.set_xticklabels(resumen_temp["tipo_temperatura"])
ax1.set_xlabel("Tipo de temperatura")
ax1.set_title(
    "Consumo y coste estimado medio según temperatura",
    fontsize=15, weight="bold"
)

for barra in barras_consumo:
    altura = barra.get_height()
    ax1.text(
        barra.get_x() + barra.get_width() / 2, altura,
        f"{altura:,.0f}",
        ha="center", va="bottom", fontsize=9, color=COLOR_TEXTO
    )

for barra in barras_coste:
    altura = barra.get_height()
    ax2.text(
        barra.get_x() + barra.get_width() / 2, altura,
        f"{altura:,.0f}€",
        ha="center", va="bottom", fontsize=9, color=COLOR_TEXTO
    )

lineas_1, etiquetas_1 = ax1.get_legend_handles_labels()
lineas_2, etiquetas_2 = ax2.get_legend_handles_labels()
legend = ax1.legend(
    lineas_1 + lineas_2,
    etiquetas_1 + etiquetas_2,
    facecolor=COLOR_PANEL,
    edgecolor="#374151",
    framealpha=0.95,
    loc="upper left"
)
plt.setp(legend.get_texts(), color=COLOR_TEXTO)
guardar_grafico("h1_03_consumo_coste_por_tipo_temperatura.png")


# ============================================================
# H1.5 - COSTE UNITARIO VS TEMPERATURA
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(COLOR_FONDO)

sns.scatterplot(
    data=df_consumo_clima,
    x="temperatura_media",
    y="coste_unitario_parcial_eur_kwh",
    hue="estacion",
    size="consumo_kwh",
    sizes=(35, 160),
    alpha=0.78,
    edgecolor="white",
    linewidth=0.35,
    ax=ax
)
aplicar_estilo(ax)
ax.set_title(
    "Coste unitario estimado vs temperatura media",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Temperatura media diaria (°C)")
ax.set_ylabel("Coste unitario estimado (€/kWh)")
ax.yaxis.set_major_formatter(FuncFormatter(formato_eur_kwh))

legend = ax.legend(facecolor=COLOR_PANEL, edgecolor="#374151", framealpha=0.95, loc="best")
plt.setp(legend.get_texts(), color=COLOR_TEXTO)
plt.setp(legend.get_title(), color=COLOR_TEXTO)
guardar_grafico("h1_04_coste_unitario_temperatura_media.png")


# ============================================================
# H1.6 - COSTE UNITARIO VS VIENTO
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(COLOR_FONDO)

sns.scatterplot(
    data=df_consumo_clima,
    x="viento_medio",
    y="coste_unitario_parcial_eur_kwh",
    hue="estacion",
    size="consumo_kwh",
    sizes=(35, 160),
    alpha=0.78,
    edgecolor="white",
    linewidth=0.35,
    ax=ax
)
aplicar_estilo(ax)
ax.set_title(
    "Coste unitario estimado vs viento medio",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Viento medio diario")
ax.set_ylabel("Coste unitario estimado (€/kWh)")
ax.yaxis.set_major_formatter(FuncFormatter(formato_eur_kwh))

legend = ax.legend(facecolor=COLOR_PANEL, edgecolor="#374151", framealpha=0.95, loc="best")
plt.setp(legend.get_texts(), color=COLOR_TEXTO)
plt.setp(legend.get_title(), color=COLOR_TEXTO)
guardar_grafico("h1_05_coste_unitario_viento_medio.png")


# ============================================================
# H1.7 - MATRIZ DE CORRELACIÓN
# ============================================================
variables_corr = [
    "consumo_kwh",
    "coste_estimado_parcial_eur",
    "coste_unitario_parcial_eur_kwh",
    "temperatura_media",
    "temperatura_minima",
    "temperatura_maxima",
    "precipitacion",
    "viento_medio",
    "racha_viento",
    "horas_sol"
]

corr_h1 = df_consumo_clima[variables_corr].corr()

fig, ax = plt.subplots(figsize=(11, 8))
fig.patch.set_facecolor(COLOR_FONDO)

sns.heatmap(
    corr_h1,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.4,
    linecolor="#111827",
    cbar_kws={"label": "Correlación"},
    ax=ax
)
ax.set_facecolor(COLOR_PANEL)
ax.set_title(
    "Matriz de correlación: consumo, coste estimado y clima",
    fontsize=15, weight="bold"
)
ax.tick_params(colors=COLOR_TEXTO)
cbar = ax.collections[0].colorbar
cbar.ax.yaxis.label.set_color(COLOR_TEXTO)
cbar.ax.tick_params(colors=COLOR_TEXTO)
guardar_grafico("h1_06_matriz_correlacion_consumo_coste_clima.png")


# ============================================================
# H2 - CONSUMO EN PERIODOS TARIFARIOS CAROS
# ============================================================
resumen_h2 = (
    df_maestro
    .groupby("periodo_tarifario", observed=False, as_index=False)
    .agg(
        horas=("datetime_hora", "count"),
        consumo_total_kwh=("consumo_kwh", "sum"),
        consumo_medio_horario_kwh=("consumo_kwh", "mean"),
        potencia_media_kw=("potencia_media_kw", "mean")
    )
    .sort_values("periodo_tarifario")
    .reset_index(drop=True)
)

resumen_h2["consumo_total_mwh"] = resumen_h2["consumo_total_kwh"] / 1000
resumen_h2["porcentaje_consumo"] = (
    resumen_h2["consumo_total_kwh"]
    / resumen_h2["consumo_total_kwh"].sum()
    * 100
)


# ============================================================
# H2.1 - CONSUMO MEDIO HORARIO POR PERIODO
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

colores = [
    COLORES_PERIODOS[periodo]
    for periodo in resumen_h2["periodo_tarifario"].astype(str)
]

barras = ax.bar(
    resumen_h2["periodo_tarifario"].astype(str),
    resumen_h2["consumo_medio_horario_kwh"],
    color=colores,
    edgecolor="white",
    linewidth=0.9,
    alpha=0.92
)
aplicar_estilo(ax)
ax.set_title(
    "Consumo medio horario por periodo tarifario",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Periodo tarifario")
ax.set_ylabel("Consumo medio horario (kWh)")

for barra in barras:
    altura = barra.get_height()
    ax.text(
        barra.get_x() + barra.get_width() / 2, altura,
        f"{altura:,.1f}",
        ha="center", va="bottom", fontsize=10,
        color=COLOR_TEXTO, weight="bold"
    )
guardar_grafico("h2_03_consumo_medio_horario_por_periodo.png")


# ============================================================
# H2.2 - BOXPLOT CONSUMO HORARIO POR PERIODO
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

sns.boxplot(
    data=df_maestro,
    x="periodo_tarifario",
    y="consumo_kwh",
    order=ORDEN_PERIODOS,
    hue="periodo_tarifario",
    palette=COLORES_PERIODOS,
    width=0.58,
    linewidth=1.3,
    fliersize=2.5,
    legend=False,
    ax=ax
)
aplicar_estilo(ax)
ax.set_title(
    "Distribución del consumo horario por periodo tarifario",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Periodo tarifario")
ax.set_ylabel("Consumo horario (kWh)")
guardar_grafico("h2_04_boxplot_consumo_por_periodo.png")


# ============================================================
# H3 - RELACIÓN ENTRE CONSUMO Y COSTE ESTIMADO
# ============================================================
resumen_h3 = (
    df_maestro
    .groupby("periodo_tarifario", observed=False, as_index=False)
    .agg(
        horas=("datetime_hora", "count"),
        consumo_total_kwh=("consumo_kwh", "sum"),
        coste_estimado_total_eur=("coste_estimado_parcial_eur", "sum")
    )
    .sort_values("periodo_tarifario")
    .reset_index(drop=True)
)

resumen_h3["porcentaje_consumo"] = (
    resumen_h3["consumo_total_kwh"]
    / resumen_h3["consumo_total_kwh"].sum()
    * 100
)
resumen_h3["porcentaje_coste"] = (
    resumen_h3["coste_estimado_total_eur"]
    / resumen_h3["coste_estimado_total_eur"].sum()
    * 100
)
resumen_h3["coste_unitario_estimado_eur_kwh"] = (
    resumen_h3["coste_estimado_total_eur"]
    / resumen_h3["consumo_total_kwh"]
)
resumen_h3["diferencia_peso_coste_vs_consumo"] = (
    resumen_h3["porcentaje_coste"] - resumen_h3["porcentaje_consumo"]
)


# ============================================================
# H3.1 - PESO DEL CONSUMO VS PESO DEL COSTE
# ============================================================
x     = np.arange(len(resumen_h3))
ancho = 0.38

fig, ax = plt.subplots(figsize=(11, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

barras_consumo = ax.bar(
    x - ancho / 2,
    resumen_h3["porcentaje_consumo"],
    width=ancho,
    label="% consumo",
    color=COLOR_CONSUMO,
    edgecolor="white",
    linewidth=0.8,
    alpha=0.92
)
barras_coste = ax.bar(
    x + ancho / 2,
    resumen_h3["porcentaje_coste"],
    width=ancho,
    label="% coste estimado",
    color=COLOR_COSTE,
    edgecolor="white",
    linewidth=0.8,
    alpha=0.92
)
aplicar_estilo(ax)
ax.set_title(
    "Peso del consumo y del coste estimado por periodo tarifario",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Periodo tarifario")
ax.set_ylabel("Porcentaje sobre el total (%)")
ax.set_xticks(x)
ax.set_xticklabels(resumen_h3["periodo_tarifario"].astype(str))

legend = ax.legend(facecolor=COLOR_PANEL, edgecolor="#374151", framealpha=0.95)
plt.setp(legend.get_texts(), color=COLOR_TEXTO)

for barras in [barras_consumo, barras_coste]:
    for barra in barras:
        altura = barra.get_height()
        ax.text(
            barra.get_x() + barra.get_width() / 2, altura,
            f"{altura:.1f}%",
            ha="center", va="bottom", fontsize=9,
            color=COLOR_TEXTO, weight="bold"
        )
guardar_grafico("h3_01_peso_consumo_vs_coste_por_periodo.png")


# ============================================================
# H3.2 - SCATTER CONSUMO HORARIO VS COSTE ESTIMADO
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor(COLOR_FONDO)

for periodo in ORDEN_PERIODOS:
    datos = df_maestro[df_maestro["periodo_tarifario"] == periodo]
    ax.scatter(
        datos["consumo_kwh"],
        datos["coste_estimado_parcial_eur"],
        s=28, alpha=0.55,
        color=COLORES_PERIODOS[periodo],
        edgecolors="white",
        linewidths=0.25,
        label=periodo
    )
aplicar_estilo(ax)
ax.set_title(
    "Relación entre consumo horario y coste estimado",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Consumo horario (kWh)")
ax.set_ylabel("Coste estimado horario (€)")

legend = ax.legend(
    title="Periodo",
    facecolor=COLOR_PANEL,
    edgecolor="#374151",
    framealpha=0.95
)
plt.setp(legend.get_texts(), color=COLOR_TEXTO)
plt.setp(legend.get_title(), color=COLOR_TEXTO)
guardar_grafico("h3_02_scatter_consumo_vs_coste_parcial.png")


# ============================================================
# H3.3 - COSTE UNITARIO ESTIMADO POR PERIODO
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

colores = [
    COLORES_PERIODOS[periodo]
    for periodo in resumen_h3["periodo_tarifario"].astype(str)
]

barras = ax.bar(
    resumen_h3["periodo_tarifario"].astype(str),
    resumen_h3["coste_unitario_estimado_eur_kwh"],
    color=colores,
    edgecolor="white",
    linewidth=0.9,
    alpha=0.92
)
aplicar_estilo(ax)
ax.set_title(
    "Coste unitario estimado por periodo tarifario",
    fontsize=15, weight="bold"
)
ax.set_xlabel("Periodo tarifario")
ax.set_ylabel("Coste unitario estimado (€/kWh)")

for barra in barras:
    altura = barra.get_height()
    ax.text(
        barra.get_x() + barra.get_width() / 2, altura,
        f"{altura:.4f}",
        ha="center", va="bottom", fontsize=10,
        color=COLOR_TEXTO, weight="bold"
    )
guardar_grafico("h3_03_coste_unitario_parcial_por_periodo.png")


# ============================================================
# H4 - IMPACTO DE ADELANTAR 2 HORAS EL CONSUMO
# ============================================================
df_h4 = (
    df_maestro
    .sort_values("datetime_hora")
    .reset_index(drop=True)
    .copy()
)

df_h4["consumo_escenario_2h"] = df_h4["consumo_kwh"].shift(-2)
df_h4.loc[df_h4.index[-2:], "consumo_escenario_2h"] = (
    df_h4["consumo_kwh"].iloc[:2].values
)

df_h4["coste_actual_eur"] = (
    df_h4["consumo_kwh"] * df_h4["precio_variable_parcial_eur_kwh"]
)
df_h4["coste_escenario_2h_eur"] = (
    df_h4["consumo_escenario_2h"] * df_h4["precio_variable_parcial_eur_kwh"]
)
df_h4["diferencia_coste_2h_eur"] = (
    df_h4["coste_escenario_2h_eur"] - df_h4["coste_actual_eur"]
)

coste_actual_total       = df_h4["coste_actual_eur"].sum()
coste_escenario_2h_total = df_h4["coste_escenario_2h_eur"].sum()
diferencia_total_eur     = coste_escenario_2h_total - coste_actual_total
porcentaje_variacion     = diferencia_total_eur / coste_actual_total * 100


# ============================================================
# H4.1 - CONSUMO MEDIO POR TURNO
# ============================================================
resumen_turno_h4 = (
    df_h4
    .groupby("turno", observed=False, as_index=False)
    .agg(
        consumo_medio_horario_kwh=("consumo_kwh", "mean"),
        consumo_total_kwh=("consumo_kwh", "sum"),
        coste_actual_total_eur=("coste_actual_eur", "sum"),
        coste_escenario_2h_total_eur=("coste_escenario_2h_eur", "sum")
    )
    .sort_values("turno")
    .reset_index(drop=True)
)

resumen_turno_h4["ahorro_escenario_2h_eur"] = (
    resumen_turno_h4["coste_actual_total_eur"]
    - resumen_turno_h4["coste_escenario_2h_total_eur"]
)

fig, ax = plt.subplots(figsize=(10, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

barras = ax.bar(
    resumen_turno_h4["turno"].astype(str).map(ETIQUETAS_TURNOS),
    resumen_turno_h4["consumo_medio_horario_kwh"],
    color=[COLORES_TURNOS[t] for t in resumen_turno_h4["turno"].astype(str)],
    edgecolor="white",
    linewidth=0.9,
    alpha=0.92
)
aplicar_estilo(ax)
ax.set_title("Consumo medio horario por turno", fontsize=15, weight="bold")
ax.set_xlabel("")
ax.set_ylabel("Consumo medio horario (kWh)")

for barra in barras:
    altura = barra.get_height()
    ax.text(
        barra.get_x() + barra.get_width() / 2, altura,
        f"{altura:,.1f}",
        ha="center", va="bottom", fontsize=10,
        color=COLOR_TEXTO, weight="bold"
    )
guardar_grafico("h4_01_consumo_medio_por_turno.png")


# ============================================================
# H4.2 - COSTE ACTUAL VS ESCENARIO ADELANTANDO 2H
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

categorias = ["Actual", "Escenario\nadelanto 2h"]
valores    = [coste_actual_total, coste_escenario_2h_total]

barras = ax.bar(
    categorias, valores,
    color=[COLOR_CONSUMO, COLOR_COSTE],
    edgecolor="white",
    linewidth=1,
    alpha=0.92
)
aplicar_estilo(ax)
ax.set_title(
    "Coste estimado total: actual vs escenario adelantando 2 horas",
    fontsize=15, weight="bold"
)
ax.set_xlabel("")
ax.set_ylabel("Coste estimado total (€)")

for barra in barras:
    altura = barra.get_height()
    ax.text(
        barra.get_x() + barra.get_width() / 2, altura,
        f"{altura:,.2f} €",
        ha="center", va="bottom", fontsize=10,
        color=COLOR_TEXTO, weight="bold"
    )

texto_resultado = (
    f"Diferencia: {diferencia_total_eur:,.2f} €\n"
    f"Variación: {porcentaje_variacion:.2f} %"
)
ax.text(
    0.98, 0.95,
    texto_resultado,
    transform=ax.transAxes,
    ha="right", va="top", fontsize=10, color=COLOR_TEXTO,
    bbox=dict(
        boxstyle="round,pad=0.4",
        facecolor=COLOR_PANEL,
        edgecolor="#374151",
        alpha=0.95
    )
)
guardar_grafico("h4_02_coste_actual_vs_escenario_2h.png")


# ============================================================
# H4.3 - DIFERENCIA DE COSTE POR PERIODO
# ============================================================
resumen_periodo_h4 = (
    df_h4
    .groupby("periodo_tarifario", observed=False, as_index=False)
    .agg(
        coste_actual_total_eur=("coste_actual_eur", "sum"),
        coste_escenario_2h_total_eur=("coste_escenario_2h_eur", "sum")
    )
    .sort_values("periodo_tarifario")
    .reset_index(drop=True)
)

resumen_periodo_h4["diferencia_coste_eur"] = (
    resumen_periodo_h4["coste_escenario_2h_total_eur"]
    - resumen_periodo_h4["coste_actual_total_eur"]
)

fig, ax = plt.subplots(figsize=(11, 5.8))
fig.patch.set_facecolor(COLOR_FONDO)

colores_diferencia = [
    "#ef4444" if valor > 0 else "#22c55e"
    for valor in resumen_periodo_h4["diferencia_coste_eur"]
]

barras = ax.bar(
    resumen_periodo_h4["periodo_tarifario"].astype(str),
    resumen_periodo_h4["diferencia_coste_eur"],
    color=colores_diferencia,
    edgecolor="white",
    linewidth=0.9,
    alpha=0.92
)
aplicar_estilo(ax)
ax.axhline(0, color="white", linewidth=1, alpha=0.7)
ax.set_title(
    "Diferencia de coste estimado por periodo tarifario\n"
    "(escenario adelantando 2 horas - escenario actual)",
    fontsize=14, weight="bold"
)
ax.set_xlabel("Periodo tarifario")
ax.set_ylabel("Diferencia de coste (€)")

for barra in barras:
    altura = barra.get_height()
    ax.text(
        barra.get_x() + barra.get_width() / 2, altura,
        f"{altura:,.2f}",
        ha="center",
        va="bottom" if altura >= 0 else "top",
        fontsize=9, color=COLOR_TEXTO, weight="bold"
    )
guardar_grafico("h4_03_diferencia_coste_por_periodo_escenario_2h.png")


# ============================================================
# RESULTADOS EN CONSOLA
# ============================================================
print("EDA ejecutado correctamente.")
print("Dataset generado: df_consumo_clima_limpio.csv")
print("\nGráficos generados:")
print("- h1_01_consumo_diario_temperatura_media.png")
print("- h1_02_scatter_consumo_temperatura_media.png")
print("- h1_03_consumo_coste_por_tipo_temperatura.png")
print("- h1_04_coste_unitario_temperatura_media.png")
print("- h1_05_coste_unitario_viento_medio.png")
print("- h1_06_matriz_correlacion_consumo_coste_clima.png")
print("- h2_03_consumo_medio_horario_por_periodo.png")
print("- h2_04_boxplot_consumo_por_periodo.png")
print("- h3_01_peso_consumo_vs_coste_por_periodo.png")
print("- h3_02_scatter_consumo_vs_coste_parcial.png")
print("- h3_03_coste_unitario_parcial_por_periodo.png")
print("- h4_01_consumo_medio_por_turno.png")
print("- h4_02_coste_actual_vs_escenario_2h.png")
print("- h4_03_diferencia_coste_por_periodo_escenario_2h.png")
print("\nResumen H2:")
print(resumen_h2.round(2))
print("\nResumen H3:")
print(resumen_h3.round(4))
print("\nResumen H4 global:")
print(f"Coste actual estimado:        {coste_actual_total:,.2f} €")
print(f"Coste escenario adelanto 2h:  {coste_escenario_2h_total:,.2f} €")
print(f"Diferencia:                   {diferencia_total_eur:,.2f} €")
print(f"Variación porcentual:         {porcentaje_variacion:.2f} %")

# ============================================================
# H1.7 - TENDENCIA NORMALIZADA CONSUMO VS TEMPERATURA
# ============================================================

# Este gráfico no sustituye a H1_01.
# Muestra una comparación visual de tendencias temporales.
#
# Se normalizan consumo y temperatura entre 0 y 1 para poder
# compararlas en el mismo eje.
#
# Después se ajusta una curva polinómica de grado 2 a cada variable.
# La lectura debe ser exploratoria: muestra tendencia temporal,
# no causalidad directa.

df_h1_tendencia = df_consumo_clima.copy()

df_h1_tendencia = (
    df_h1_tendencia
    .sort_values("fecha")
    .reset_index(drop=True)
)

df_h1_tendencia["dia_indice"] = np.arange(len(df_h1_tendencia))

df_h1_tendencia["consumo_norm"] = (
    (df_h1_tendencia["consumo_kwh"] - df_h1_tendencia["consumo_kwh"].min())
    / (df_h1_tendencia["consumo_kwh"].max() - df_h1_tendencia["consumo_kwh"].min())
)

df_h1_tendencia["temperatura_norm"] = (
    (df_h1_tendencia["temperatura_media"] - df_h1_tendencia["temperatura_media"].min())
    / (df_h1_tendencia["temperatura_media"].max() - df_h1_tendencia["temperatura_media"].min())
)

x_h1 = df_h1_tendencia["dia_indice"]

coef_consumo = np.polyfit(
    x_h1,
    df_h1_tendencia["consumo_norm"],
    2
)

coef_temperatura = np.polyfit(
    x_h1,
    df_h1_tendencia["temperatura_norm"],
    2
)

curva_consumo = np.poly1d(coef_consumo)
curva_temperatura = np.poly1d(coef_temperatura)

x_h1_suave = np.linspace(
    x_h1.min(),
    x_h1.max(),
    500
)

y_consumo_suave = curva_consumo(x_h1_suave)
y_temperatura_suave = curva_temperatura(x_h1_suave)

fechas_suaves = pd.date_range(
    start=df_h1_tendencia["fecha"].min(),
    end=df_h1_tendencia["fecha"].max(),
    periods=len(x_h1_suave)
)

fig, ax = plt.subplots(figsize=(15, 6))
fig.patch.set_facecolor(COLOR_FONDO)
ax.set_facecolor(COLOR_PANEL)

ax.scatter(
    df_h1_tendencia["fecha"],
    df_h1_tendencia["consumo_norm"],
    s=14,
    alpha=0.18,
    color=COLOR_CONSUMO,
    label="Consumo diario normalizado"
)

ax.scatter(
    df_h1_tendencia["fecha"],
    df_h1_tendencia["temperatura_norm"],
    s=14,
    alpha=0.18,
    color=COLOR_TEMP,
    label="Temperatura media normalizada"
)

ax.plot(
    fechas_suaves,
    y_consumo_suave,
    color=COLOR_CONSUMO,
    linewidth=3,
    label="Tendencia consumo grado 2"
)

ax.plot(
    fechas_suaves,
    y_temperatura_suave,
    color=COLOR_TEMP,
    linewidth=3,
    label="Tendencia temperatura grado 2"
)

ax.set_title(
    "Tendencias normalizadas de consumo y temperatura",
    fontsize=15,
    weight="bold",
    color=COLOR_TEXTO
)

ax.set_xlabel("Fecha", color=COLOR_TEXTO)
ax.set_ylabel("Valor normalizado 0-1", color=COLOR_TEXTO)

ax.grid(True, alpha=0.22, color=COLOR_GRID)
ax.tick_params(colors=COLOR_TEXTO)

for spine in ax.spines.values():
    spine.set_color("#374151")

legend = ax.legend(
    facecolor=COLOR_PANEL,
    edgecolor="#374151",
    framealpha=0.95,
    loc="upper left"
)

plt.setp(legend.get_texts(), color=COLOR_TEXTO)

guardar_grafico("h1_07_tendencia_consumo_temperatura_normalizada.png")
