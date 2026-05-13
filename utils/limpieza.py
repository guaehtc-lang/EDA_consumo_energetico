import pandas as pd


# ============================================================
# LIMPIEZA DEL DATASET DE CONSUMO INDUSTRIAL
# ============================================================

# El dataset original contiene datos cada 15 minutos de 2018.
# En este proyecto se utiliza como patrón industrial de consumo
# y se adapta a un calendario simulado de 2024.


# ============================================================
# 1. CARGA DEL DATASET ORIGINAL
# ============================================================

df_consumo = pd.read_csv(r"..\data\Steel_industry_data.csv")


# ============================================================
# 2. RENOMBRADO DE COLUMNAS
# ============================================================

columnas_consumo = {
    "date": "fecha_original",
    "Usage_kWh": "consumo_kwh",
    "Lagging_Current_Reactive.Power_kVarh": "reactiva_retrasada_kvarh",
    "Leading_Current_Reactive_Power_kVarh": "reactiva_adelantada_kvarh",
    "CO2(tCO2)": "CO2(tCO2)",
    "Lagging_Current_Power_Factor": "factor_potencia_retrasada",
    "Leading_Current_Power_Factor": "factor_potencia_adelantada",
    "NSM": "segundos_desde_medianoche",
    "WeekStatus": "tipo_semana_original",
    "Day_of_week": "dia_semana_original",
    "Load_Type": "tipo_carga"
}

df_consumo = df_consumo.rename(columns=columnas_consumo)


# ============================================================
# 3. CONVERSIÓN DE FECHA ORIGINAL Y ORDENACIÓN
# ============================================================

df_consumo["datetime_original"] = pd.to_datetime(
    df_consumo["fecha_original"],
    dayfirst=True
)

df_consumo = (
    df_consumo
    .sort_values("datetime_original")
    .reset_index(drop=True)
)


# ============================================================
# 4. ASIGNACIÓN DEL CALENDARIO SIMULADO 2024
# ============================================================

# El dataset original tiene 365 días:
# 365 días x 24 horas x 4 registros/hora = 35.040 filas.
#
# Se asigna el patrón original al calendario 2024 desde el
# 01/01/2024 hasta el 30/12/2024.
#
# El 31/12/2024 se añadirá después como día sintético.

df_consumo["datetime_2024_simulado"] = pd.date_range(
    start="2024-01-01 00:00:00",
    periods=len(df_consumo),
    freq="15min"
)


# ============================================================
# 5. CREACIÓN SIMPLE DEL 31/12/2024 SINTÉTICO
# ============================================================

# Para completar el año 2024 se copia el patrón del primer día
# del dataset original: 01/01/2018.
#
# Como cada día tiene 96 registros de 15 minutos:
# 24 horas x 4 registros/hora = 96 filas.
#
# Es decir:
# - copiamos las primeras 96 filas,
# - les cambiamos la fecha simulada a 31/12/2024,
# - las añadimos al final del dataset.

df_31d = df_consumo.iloc[:96].copy()

df_31d["datetime_2024_simulado"] = pd.date_range(
    start="2024-12-31 00:00:00",
    periods=96,
    freq="15min"
)


# ============================================================
# 6. UNIÓN DEL CONSUMO SIMULADO CON EL DÍA SINTÉTICO
# ============================================================

df_consumo_2024 = pd.concat(
    [df_consumo, df_31d],
    ignore_index=True
)

df_consumo_2024 = (
    df_consumo_2024
    .sort_values("datetime_2024_simulado")
    .reset_index(drop=True)
)


# ============================================================
# 7. CREACIÓN DE VARIABLES TEMPORALES
# ============================================================

df_consumo_2024["fecha"] = (
    df_consumo_2024["datetime_2024_simulado"].dt.normalize()
)

df_consumo_2024["hora"] = (
    df_consumo_2024["datetime_2024_simulado"].dt.hour
)

df_consumo_2024["dia"] = (
    df_consumo_2024["datetime_2024_simulado"].dt.day
)

df_consumo_2024["mes"] = (
    df_consumo_2024["datetime_2024_simulado"].dt.month
)

df_consumo_2024["dia_semana_2024"] = (
    df_consumo_2024["datetime_2024_simulado"].dt.day_name()
)

df_consumo_2024["tipo_semana"] = (
    df_consumo_2024["datetime_2024_simulado"]
    .dt.dayofweek
    .apply(lambda x: "Weekday" if x < 5 else "Weekend")
)


# ============================================================
# 8. CREACIÓN DE COLUMNA TURNO
# ============================================================

# M = Mañana: 06:00 a 13:59
# T = Tarde: 14:00 a 21:59
# N = Noche: 22:00 a 05:59

def asignar_turno(hora):
    if 6 <= hora < 14:
        return "M"
    elif 14 <= hora < 22:
        return "T"
    else:
        return "N"


df_consumo_2024["turno"] = (
    df_consumo_2024["hora"].apply(asignar_turno)
)


# ============================================================
# 9. SELECCIÓN DEL DATAFRAME DE ESTUDIO A 15 MINUTOS
# ============================================================

# Conservamos solo las columnas útiles para el análisis.
# Se eliminan las columnas originales de fecha de 2018 para evitar confusión.

columnas_estudio_15min = [
    "datetime_2024_simulado",
    "fecha",
    "hora",
    "turno",
    "dia",
    "mes",
    "dia_semana_2024",
    "tipo_semana",
    "tipo_carga",
    "consumo_kwh",
    "reactiva_retrasada_kvarh",
    "reactiva_adelantada_kvarh",
    "CO2(tCO2)",
    "factor_potencia_retrasada",
    "factor_potencia_adelantada",
    "segundos_desde_medianoche"
]

df_consumo_2024_estudio = (
    df_consumo_2024[columnas_estudio_15min]
    .copy()
)


# ============================================================
# 10. GUARDADO DEL DATASET DE ESTUDIO A 15 MINUTOS
# ============================================================

df_consumo_2024_estudio.to_csv(
    r"..\data_limpios\df_consumo_2024_15min_estudio_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 11. CREACIÓN DE HORA_PERIODO
# ============================================================

# 00:00, 00:15, 00:30, 00:45 -> hora_periodo = 1
# 01:00, 01:15, 01:30, 01:45 -> hora_periodo = 2
# ...
# 23:00, 23:15, 23:30, 23:45 -> hora_periodo = 24

df_consumo_2024_estudio["hora_periodo"] = (
    df_consumo_2024_estudio["hora"] + 1
)


# ============================================================
# 12. AGRUPACIÓN HORARIA
# ============================================================

# Pasamos de datos de 15 minutos a datos horarios.
#
# Criterio:
# - consumo_kwh: suma
# - reactiva_retrasada_kvarh: suma
# - reactiva_adelantada_kvarh: suma
# - CO2(tCO2): suma
# - factores de potencia: media
# - variables categóricas: primer valor de la hora

df_consumo_hora = (
    df_consumo_2024_estudio
    .groupby(["fecha", "hora_periodo"], as_index=False)
    .agg({
        "dia": "first",
        "mes": "first",
        "dia_semana_2024": "first",
        "tipo_semana": "first",
        "turno": "first",
        "tipo_carga": "first",
        "consumo_kwh": "sum",
        "reactiva_retrasada_kvarh": "sum",
        "reactiva_adelantada_kvarh": "sum",
        "CO2(tCO2)": "sum",
        "factor_potencia_retrasada": "mean",
        "factor_potencia_adelantada": "mean"
    })
)


# ============================================================
# 13. CREACIÓN DE DATETIME_HORA Y POTENCIA MEDIA HORARIA
# ============================================================

# En una fila horaria:
# consumo_kwh en 1 hora equivale a potencia media horaria en kW.

df_consumo_hora["datetime_hora"] = (
    df_consumo_hora["fecha"]
    + pd.to_timedelta(df_consumo_hora["hora_periodo"] - 1, unit="h")
)

df_consumo_hora["potencia_media_kw"] = (
    df_consumo_hora["consumo_kwh"]
)


# ============================================================
# 14. DATASET HORARIO FINAL
# ============================================================

columnas_horario = [
    "datetime_hora",
    "fecha",
    "hora_periodo",
    "turno",
    "dia",
    "mes",
    "dia_semana_2024",
    "tipo_semana",
    "tipo_carga",
    "consumo_kwh",
    "potencia_media_kw",
    "reactiva_retrasada_kvarh",
    "reactiva_adelantada_kvarh",
    "CO2(tCO2)",
    "factor_potencia_retrasada",
    "factor_potencia_adelantada"
]

df_consumo_2024_horario_estudio_limpio = (
    df_consumo_hora[columnas_horario]
    .copy()
)


# ============================================================
# 15. GUARDADO DEL DATASET HORARIO LIMPIO
# ============================================================

df_consumo_2024_horario_estudio_limpio.to_csv(
    r"..\data_limpios\df_consumo_2024_horario_estudio_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)


# ======================================================================================================
# ======================================================================================================
# ======================================================================================================
# ======================================================================================================

# ============================================================
# LIMPIEZA DEL DATASET DE PERIODOS TARIFARIOS PENÍNSULA
# ============================================================

# El archivo original tiene este formato:
# Time | Jan | Feb | ... | Dec | Weekend
#
# Para cruzarlo con el consumo horario necesitamos una fila por:
# mes + tipo_semana + hora_periodo


# ============================================================
# 1. CARGA DEL DATASET ORIGINAL DE PERIODOS
# ============================================================

df_periodos = pd.read_csv(r"..\data\periodos_peninsula.csv")


# ============================================================
# 2. DICCIONARIO DE MESES
# ============================================================

mapa_meses = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
}

columnas_meses = list(mapa_meses.keys())


# ============================================================
# 3. PERIODOS DE LUNES A VIERNES
# ============================================================

# Las columnas Jan-Dec representan los periodos de días laborables.
# Las pasamos de formato ancho a formato largo.

df_weekday = df_periodos.melt(
    id_vars="Time",
    value_vars=columnas_meses,
    var_name="mes_texto",
    value_name="periodo_tarifario"
)

df_weekday["mes"] = df_weekday["mes_texto"].map(mapa_meses)
df_weekday["tipo_semana"] = "Weekday"


# ============================================================
# 4. PERIODOS DE FIN DE SEMANA
# ============================================================

# La columna Weekend aplica igual para todos los meses.
# Creamos una tabla de meses y la cruzamos con las 24 horas de Weekend.

df_meses = pd.DataFrame({
    "mes_texto": list(mapa_meses.keys()),
    "mes": list(mapa_meses.values())
})

df_weekend = (
    df_periodos[["Time", "Weekend"]]
    .rename(columns={"Weekend": "periodo_tarifario"})
    .merge(df_meses, how="cross")
)

df_weekend["tipo_semana"] = "Weekend"


# ============================================================
# 5. UNIÓN DE LABORABLES Y FINES DE SEMANA
# ============================================================

df_periodos_limpio = pd.concat(
    [df_weekday, df_weekend],
    ignore_index=True
)


# ============================================================
# 6. CREACIÓN DE HORA_INICIO, HORA_FIN Y HORA_PERIODO
# ============================================================

df_periodos_limpio[["hora_inicio", "hora_fin"]] = (
    df_periodos_limpio["Time"]
    .str.split("-", expand=True)
    .astype(int)
)

df_periodos_limpio["hora_periodo"] = (
    df_periodos_limpio["hora_inicio"] + 1
)


# ============================================================
# 7. LIMPIEZA Y RENOMBRADO DE COLUMNAS
# ============================================================

df_periodos_limpio["periodo_tarifario"] = (
    df_periodos_limpio["periodo_tarifario"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df_periodos_limpio = df_periodos_limpio.rename(columns={
    "Time": "tramo_horario"
})


# ============================================================
# 8. SELECCIÓN Y ORDENACIÓN FINAL
# ============================================================

df_periodos_limpio = df_periodos_limpio[
    [
        "mes",
        "mes_texto",
        "tipo_semana",
        "hora_periodo",
        "hora_inicio",
        "hora_fin",
        "tramo_horario",
        "periodo_tarifario"
    ]
]

df_periodos_limpio = (
    df_periodos_limpio
    .sort_values(["mes", "tipo_semana", "hora_periodo"])
    .reset_index(drop=True)
)


# ============================================================
# 9. GUARDADO DEL DATASET LIMPIO DE PERIODOS
# ============================================================

df_periodos_limpio.to_csv(
    r"..\data_limpios\df_periodos_peninsula_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# LIMPIEZA DEL DATASET DE CLIMA 2024
# ============================================================

# Este archivo contiene datos climáticos diarios medios de España en 2024.
# Se utilizará para el análisis exploratorio entre clima, consumo diario
# y coste energético parcial.


# ============================================================
# 1. CARGA DEL DATASET DE CLIMA 2024
# ============================================================

df_clima = pd.read_csv(r"..\data\clima_aemet_espana_media_diaria_2024.csv")


# ============================================================
# 2. RENOMBRADO DE COLUMNAS
# ============================================================

df_clima_2024_limpio = df_clima.rename(columns={
    "fecha": "fecha",
    "tmed": "temperatura_media",
    "tmin": "temperatura_minima",
    "tmax": "temperatura_maxima",
    "prec": "precipitacion",
    "velmedia": "viento_medio",
    "racha": "racha_viento",
    "sol": "horas_sol",
    "presMax": "presion_maxima",
    "presMin": "presion_minima",
    "num_estaciones": "num_estaciones"
}).copy()


# ============================================================
# 3. CONVERSIÓN DE FECHA A DATETIME
# ============================================================

df_clima_2024_limpio["fecha"] = pd.to_datetime(
    df_clima_2024_limpio["fecha"]
)


# ============================================================
# 4. CREACIÓN DE COLUMNAS TEMPORALES
# ============================================================

df_clima_2024_limpio["dia"] = df_clima_2024_limpio["fecha"].dt.day
df_clima_2024_limpio["mes"] = df_clima_2024_limpio["fecha"].dt.month
df_clima_2024_limpio["dia_semana"] = df_clima_2024_limpio["fecha"].dt.day_name()
df_clima_2024_limpio["dia_anio"] = df_clima_2024_limpio["fecha"].dt.dayofyear


# ============================================================
# 5. REORDENACIÓN FINAL DE COLUMNAS
# ============================================================

columnas_clima_ordenadas = [
    "fecha",
    "dia",
    "mes",
    "dia_semana",
    "dia_anio",
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

df_clima_2024_limpio = df_clima_2024_limpio[columnas_clima_ordenadas]


# ============================================================
# 6. GUARDADO DEL DATASET LIMPIO DE CLIMA
# ============================================================

df_clima_2024_limpio.to_csv(
    r"..\data_limpios\df_clima_2024_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# LIMPIEZA DEL DATASET DE TARIFA COMPLETA 2024
# ============================================================

# El archivo original contiene conceptos económicos por mes:
# - potencia por periodo P1-P6
# - energía regulada por periodo P1-P6
# - excesos de potencia por periodo P1-P6
# - conceptos generales: reactiva, impuestos, alquiler, FNEE, etc.
#
# Para cruzarlo con df_maestro necesitamos una fila por:
# mes + periodo_tarifario


# ============================================================
# 1. CARGA DEL DATASET ORIGINAL DE TARIFA COMPLETA
# ============================================================

df_tarifa = pd.read_csv(r"..\data\tarifa_completa_2024.csv")


# ============================================================
# 2. CREACIÓN DEL NÚMERO DE MES
# ============================================================

mapa_meses_tarifa = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12
}

df_tarifa["mes"] = df_tarifa["Mes"].map(mapa_meses_tarifa)
df_tarifa["mes_nombre"] = df_tarifa["Mes"]


# ============================================================
# 3. TABLA DE POTENCIA EN FORMATO LARGO
# ============================================================

df_potencia = df_tarifa.melt(
    id_vars=["mes", "mes_nombre"],
    value_vars=[
        "Pot_P1_EUR/kWaño",
        "Pot_P2_EUR/kWaño",
        "Pot_P3_EUR/kWaño",
        "Pot_P4_EUR/kWaño",
        "Pot_P5_EUR/kWaño",
        "Pot_P6_EUR/kWaño"
    ],
    var_name="periodo_tarifario",
    value_name="potencia_eur_kw_anio"
)

df_potencia["periodo_tarifario"] = (
    df_potencia["periodo_tarifario"]
    .str.extract(r"(P[1-6])")
)


# ============================================================
# 4. TABLA DE ENERGÍA REGULADA EN FORMATO LARGO
# ============================================================

df_energia = df_tarifa.melt(
    id_vars=["mes", "mes_nombre"],
    value_vars=[
        "EneReg_P1_EUR/kWh",
        "EneReg_P2_EUR/kWh",
        "EneReg_P3_EUR/kWh",
        "EneReg_P4_EUR/kWh",
        "EneReg_P5_EUR/kWh",
        "EneReg_P6_EUR/kWh"
    ],
    var_name="periodo_tarifario",
    value_name="energia_regulada_eur_kwh"
)

df_energia["periodo_tarifario"] = (
    df_energia["periodo_tarifario"]
    .str.extract(r"(P[1-6])")
)


# ============================================================
# 5. TABLA DE EXCESOS DE POTENCIA EN FORMATO LARGO
# ============================================================

df_excesos = df_tarifa.melt(
    id_vars=["mes", "mes_nombre"],
    value_vars=[
        "Exc_tp_P1_EUR/kWdia",
        "Exc_tp_P2_EUR/kWdia",
        "Exc_tp_P3_EUR/kWdia",
        "Exc_tp_P4_EUR/kWdia",
        "Exc_tp_P5_EUR/kWdia",
        "Exc_tp_P6_EUR/kWdia"
    ],
    var_name="periodo_tarifario",
    value_name="exceso_potencia_eur_kw_dia"
)

df_excesos["periodo_tarifario"] = (
    df_excesos["periodo_tarifario"]
    .str.extract(r"(P[1-6])")
)


# ============================================================
# 6. TABLA DE CONCEPTOS GENERALES
# ============================================================

# Estos conceptos son mensuales y no dependen de P1-P6.
# Para poder cruzarlos después, se replican para cada periodo.

df_conceptos = df_tarifa[
    [
        "mes",
        "mes_nombre",
        "React_095_EUR/kVArh",
        "React_080_EUR/kVArh",
        "IEE_perc",
        "IVA_perc",
        "Alq_Trif_EUR/dia",
        "BS_EUR/dia",
        "FNEE_EUR/kWh",
        "TasaMun_perc"
    ]
].copy()

df_periodos_tarifa = pd.DataFrame({
    "periodo_tarifario": ["P1", "P2", "P3", "P4", "P5", "P6"]
})

df_conceptos = df_conceptos.merge(
    df_periodos_tarifa,
    how="cross"
)

df_conceptos = df_conceptos.rename(columns={
    "React_095_EUR/kVArh": "reactiva_095_eur_kvarh",
    "React_080_EUR/kVArh": "reactiva_080_eur_kvarh",
    "IEE_perc": "iee_perc",
    "IVA_perc": "iva_perc",
    "Alq_Trif_EUR/dia": "alq_trif_eur_dia",
    "BS_EUR/dia": "bs_eur_dia",
    "FNEE_EUR/kWh": "fnee_eur_kwh",
    "TasaMun_perc": "tasa_mun_perc"
})


# ============================================================
# 7. UNIÓN DE TODAS LAS TABLAS DE TARIFA
# ============================================================

df_tarifa_completa_2024_limpio = df_potencia.merge(
    df_energia,
    on=["mes", "mes_nombre", "periodo_tarifario"],
    how="left"
)

df_tarifa_completa_2024_limpio = df_tarifa_completa_2024_limpio.merge(
    df_excesos,
    on=["mes", "mes_nombre", "periodo_tarifario"],
    how="left"
)

df_tarifa_completa_2024_limpio = df_tarifa_completa_2024_limpio.merge(
    df_conceptos,
    on=["mes", "mes_nombre", "periodo_tarifario"],
    how="left"
)


# ============================================================
# 8. ORDENACIÓN FINAL
# ============================================================

df_tarifa_completa_2024_limpio = (
    df_tarifa_completa_2024_limpio
    .sort_values(["mes", "periodo_tarifario"])
    .reset_index(drop=True)
)


# ============================================================
# 9. GUARDADO DEL DATASET LIMPIO DE TARIFA COMPLETA
# ============================================================

df_tarifa_completa_2024_limpio.to_csv(
    r"..\data_limpios\df_tarifa_completa_2024_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)