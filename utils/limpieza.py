import pandas as pd


# ============================================================
# 1. CARGA DEL DATASET ORIGINAL DE CONSUMO INDUSTRIAL
# ============================================================

df_consumo = pd.read_csv(r"..\data\Steel_industry_data.csv")


# ============================================================
# 2. TRADUCCIÓN DE COLUMNAS DEL DATASET INDUSTRIAL
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
    "WeekStatus": "tipo_semana",
    "Day_of_week": "dia_semana",
    "Load_Type": "tipo_carga"
}

df_consumo = df_consumo.rename(columns=columnas_consumo)


# ============================================================
# 3. CONVERSIÓN DE LA FECHA ORIGINAL A FORMATO DATETIME
# ============================================================

df_consumo["datetime_original"] = pd.to_datetime(
    df_consumo["fecha_original"],
    dayfirst=True,
    errors="coerce"
)


# ============================================================
# 4. ORDENACIÓN CRONOLÓGICA SEGÚN LA FECHA ORIGINAL
# ============================================================

df_consumo = df_consumo.sort_values("datetime_original").reset_index(drop=True)


# ============================================================
# 5. CREACIÓN DEL CALENDARIO COMPLETO DE 2024 A 15 MINUTOS
# ============================================================

calendario_2024_15min = pd.date_range(
    start="2024-01-01 00:00:00",
    end="2024-12-31 23:45:00",
    freq="15min"
)


# ============================================================
# 6. ASIGNACIÓN DEL CONSUMO ORIGINAL AL CALENDARIO 2024
#    MANTENIENDO LA CORRESPONDENCIA DEL DÍA DE LA SEMANA
# ============================================================

# El dataset original tiene 35.040 registros:
# 365 días x 96 registros diarios de 15 minutos.
# Se asignan esos registros a los primeros 35.040 intervalos de 2024.
# Esto cubre desde el 01/01/2024 hasta el 30/12/2024.

calendario_consumo_real = calendario_2024_15min[:len(df_consumo)]

df_consumo["datetime_2024_simulado"] = calendario_consumo_real
df_consumo["origen_dato"] = "simulado_2024"


# ============================================================
# 7. CREACIÓN DE COLUMNAS TEMPORALES BÁSICAS SOBRE EL CONSUMO SIMULADO
# ============================================================

df_consumo["fecha"] = df_consumo["datetime_2024_simulado"].dt.normalize()
df_consumo["hora"] = df_consumo["datetime_2024_simulado"].dt.hour
df_consumo["dia"] = df_consumo["datetime_2024_simulado"].dt.day
df_consumo["mes"] = df_consumo["datetime_2024_simulado"].dt.month
df_consumo["dia_semana_2024"] = df_consumo["datetime_2024_simulado"].dt.day_name()


# ============================================================
# 8. SELECCIÓN DEL 01/01/2018 COMO PATRÓN PARA EL 31/12/2024
# ============================================================

# El 31/12/2024 se crea como día sintético.
# Se usa el patrón de consumo del 01/01/2018 como aproximación de día de baja actividad/parada.

df_1_enero_original = df_consumo.loc[
    df_consumo["datetime_original"].dt.date == pd.to_datetime("2018-01-01").date()
].copy()


# ============================================================
# 9. CREACIÓN DEL CALENDARIO DEL 31/12/2024 A 15 MINUTOS
# ============================================================

calendario_31d = pd.date_range(
    start="2024-12-31 00:00:00",
    end="2024-12-31 23:45:00",
    freq="15min"
)


# ============================================================
# 10. CREACIÓN DEL DATASET SINTÉTICO DEL 31/12/2024
# ============================================================

df_31d = df_1_enero_original.copy()

# Asignamos la fecha simulada del 31/12/2024
df_31d["datetime_2024_simulado"] = calendario_31d

# Marcamos el origen del dato sintético
df_31d["fecha_original"] = "sintetico_31_diciembre_base_2018_01_01"
df_31d["datetime_original"] = pd.NaT
df_31d["origen_dato"] = "sintetico_31_diciembre"

# Recalculamos segundos desde medianoche
df_31d["segundos_desde_medianoche"] = (
    df_31d["datetime_2024_simulado"].dt.hour * 3600
    + df_31d["datetime_2024_simulado"].dt.minute * 60
)

# Etiquetamos el día según el calendario 2024.
# El 31/12/2024 fue martes y día entre semana.
df_31d["tipo_semana"] = "Weekday"
df_31d["dia_semana"] = "Tuesday"


# ============================================================
# 11. UNIÓN DEL DATASET SIMULADO CON EL 31/12/2024 SINTÉTICO
# ============================================================

df_consumo_2024 = pd.concat(
    [df_consumo, df_31d],
    ignore_index=True
)


# ============================================================
# 12. ORDENACIÓN FINAL DEL DATASET DE CONSUMO 2024
# ============================================================

df_consumo_2024 = (
    df_consumo_2024
    .sort_values("datetime_2024_simulado")
    .reset_index(drop=True)
)


# ============================================================
# 13. RECÁLCULO FINAL DE COLUMNAS TEMPORALES SOBRE EL DATASET COMPLETO
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


# ============================================================
# 14. REORDENACIÓN FINAL DE COLUMNAS
# ============================================================

columnas_ordenadas = [
    "fecha_original",
    "consumo_kwh",
    "reactiva_retrasada_kvarh",
    "reactiva_adelantada_kvarh",
    "CO2(tCO2)",
    "factor_potencia_retrasada",
    "factor_potencia_adelantada",
    "segundos_desde_medianoche",
    "tipo_semana",
    "dia_semana",
    "tipo_carga",
    "datetime_original",
    "datetime_2024_simulado",
    "fecha",
    "hora",
    "dia",
    "mes",
    "dia_semana_2024",
    "origen_dato"
]

df_consumo_2024 = df_consumo_2024[columnas_ordenadas]

# ============================================================
# CREACIÓN DEL DATAFRAME DE ESTUDIO PARA EL EDA
# ============================================================

# Creamos un nuevo DataFrame solo con las columnas útiles para el análisis.
# A partir de este punto trabajaremos con fechas simuladas de 2024.
# Las columnas de fecha original 2018 se dejan fuera del DataFrame de estudio.

columnas_estudio = [
    "datetime_2024_simulado",
    "fecha",
    "hora",
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
    "segundos_desde_medianoche",
    "origen_dato"
]

df_consumo_2024_estudio = df_consumo_2024[columnas_estudio].copy()

# ============================================================
# 15. CREACIÓN DEL DATAFRAME DE ESTUDIO PARA EL EDA
# ============================================================

# Creamos un DataFrame de trabajo con las columnas necesarias para el análisis.
# A partir de este punto dejamos fuera las columnas de fecha original 2018.

columnas_estudio = [
    "datetime_2024_simulado",
    "fecha",
    "hora",
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
    "segundos_desde_medianoche",
    "origen_dato"
]

df_consumo_2024_estudio = df_consumo_2024[columnas_estudio].copy()


# ============================================================
# 16. CREACIÓN DE COLUMNA HORA_PERIODO
# ============================================================

# Creamos una hora de periodo de 1 a 24:
# 00:00, 00:15, 00:30, 00:45 -> hora_periodo = 1
# 01:00, 01:15, 01:30, 01:45 -> hora_periodo = 2
# ...
# 23:00, 23:15, 23:30, 23:45 -> hora_periodo = 24

df_consumo_2024_estudio["hora_periodo"] = (
    df_consumo_2024_estudio["hora"] + 1
)


# ============================================================
# 17. AGRUPACIÓN HORARIA POR FECHA Y HORA_PERIODO
# ============================================================

# Pasamos de datos cada 15 minutos a datos horarios.
# Las energías se suman.
# Los factores de potencia se promedian.
# Las variables categóricas se conservan con el primer valor de cada hora.

df_consumo_hora = (
    df_consumo_2024_estudio
    .groupby(["fecha", "hora_periodo"], as_index=False)
    .agg({
        "dia": "first",
        "mes": "first",
        "dia_semana_2024": "first",
        "tipo_semana": "first",
        "tipo_carga": "first",
        "consumo_kwh": "sum",
        "reactiva_retrasada_kvarh": "sum",
        "reactiva_adelantada_kvarh": "sum",
        "CO2(tCO2)": "sum",
        "factor_potencia_retrasada": "mean",
        "factor_potencia_adelantada": "mean",
        "origen_dato": "first"
    })
)


# ============================================================
# 18. CREACIÓN DE DATETIME_HORA
# ============================================================

# Creamos una columna datetime representativa de cada hora.
# hora_periodo = 1 corresponde a las 00:00.
# hora_periodo = 24 corresponde a las 23:00.

df_consumo_hora["datetime_hora"] = (
    df_consumo_hora["fecha"]
    + pd.to_timedelta(df_consumo_hora["hora_periodo"] - 1, unit="h")
)


# ============================================================
# 19. REORDENACIÓN DEL DATAFRAME HORARIO
# ============================================================

columnas_hora_ordenadas = [
    "datetime_hora",
    "fecha",
    "hora_periodo",
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
    "origen_dato"
]

df_consumo_hora = df_consumo_hora[columnas_hora_ordenadas]


# ============================================================
# 20. CREACIÓN DEL DATAFRAME FINAL LIMPIO
# ============================================================

# Este será el dataset limpio de consumo horario que usaremos en el EDA.

df_consumo_2024_horario_estudio_limpio = df_consumo_hora.copy()


# ============================================================
# 21. GUARDADO DEL DATASET LIMPIO EN CSV
# ============================================================

# Guardamos el CSV limpio en la carpeta data_limpios.
# La carpeta data_limpios debe existir previamente dentro del proyecto.

df_consumo_2024_horario_estudio_limpio.to_csv(
    r"..\data_limpios\df_consumo_2024_horario_estudio_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# 1. CARGA DEL NUEVO DATASET DE PERIODOS TARIFARIOS
# ============================================================

df_periodos = pd.read_csv(r"..\data\periodos_peninsula.csv")

df_periodos.head()

# ============================================================
# 3. DICCIONARIO DE MESES
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

# ============================================================
# 4. TRANSFORMACIÓN DE LUNES A VIERNES A FORMATO LARGO
# ============================================================

columnas_meses = list(mapa_meses.keys())

df_periodos_weekday = df_periodos.melt(
    id_vars="Time",
    value_vars=columnas_meses,
    var_name="mes_texto",
    value_name="periodo_tarifario"
)

df_periodos_weekday["mes"] = df_periodos_weekday["mes_texto"].map(mapa_meses)
df_periodos_weekday["tipo_semana"] = "Weekday"

df_periodos_weekday.head()

# ============================================================
# 5. TRANSFORMACIÓN DE FINES DE SEMANA A FORMATO LARGO
# ============================================================

filas_weekend = []

for mes_texto, mes_numero in mapa_meses.items():
    df_temp = df_periodos[["Time", "Weekend"]].copy()
    df_temp["mes_texto"] = mes_texto
    df_temp["mes"] = mes_numero
    df_temp["tipo_semana"] = "Weekend"
    df_temp = df_temp.rename(columns={"Weekend": "periodo_tarifario"})
    filas_weekend.append(df_temp)

df_periodos_weekend = pd.concat(filas_weekend, ignore_index=True)

df_periodos_weekend.head()

# ============================================================
# 6. UNIÓN DE WEEKDAY Y WEEKEND
# ============================================================

df_periodos_limpio = pd.concat(
    [df_periodos_weekday, df_periodos_weekend],
    ignore_index=True
)

df_periodos_limpio.head()

# ============================================================
# 7. CREACIÓN DE HORA_INICIO, HORA_FIN Y HORA_PERIODO
# ============================================================

df_periodos_limpio[["hora_inicio", "hora_fin"]] = (
    df_periodos_limpio["Time"]
    .str.split("-", expand=True)
    .astype(int)
)

df_periodos_limpio["hora_periodo"] = df_periodos_limpio["hora_inicio"] + 1

df_periodos_limpio.head()

# ============================================================
# 8. REORDENACIÓN FINAL DE COLUMNAS
# ============================================================

df_periodos_limpio = df_periodos_limpio[
    [
        "mes",
        "mes_texto",
        "tipo_semana",
        "hora_periodo",
        "hora_inicio",
        "hora_fin",
        "Time",
        "periodo_tarifario"
    ]
]

df_periodos_limpio = df_periodos_limpio.sort_values(
    ["mes", "tipo_semana", "hora_periodo"]
).reset_index(drop=True)

df_periodos_limpio.head()

# ============================================================
# 14. GUARDADO DEL DATASET LIMPIO DE PERIODOS
# ============================================================

df_periodos_limpio.to_csv(
    r"..\data_limpios\df_periodos_peninsula_limpio.csv",
    index=False,
    encoding="utf-8-sig"
)


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
    df_clima_2024_limpio["fecha"],
    errors="coerce"
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