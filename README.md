
# EDA Consumo Energético Industrial

Proyecto de **Análisis Exploratorio de Datos (EDA)** aplicado al consumo eléctrico de una planta industrial, con el objetivo de identificar patrones de consumo, analizar periodos tarifarios P1–P6, explorar la relación con variables climáticas y estimar el impacto económico energético.

---

## Objetivo

Transformar datos de consumo eléctrico en información útil para entender el comportamiento energético industrial y orientar posibles decisiones de optimización, respondiendo preguntas como:

- ¿Cuándo consume más la planta y cómo se distribuye por turnos?
- ¿Qué peso tienen los periodos tarifarios P1–P6 en el consumo y en el coste?
- ¿Existe relación exploratoria entre clima y consumo?
- ¿Un cambio horario podría reducir el coste energético estimado?

---

## Hipótesis analizadas

| ID | Hipótesis |
|----|-----------|
| H1 | El consumo diario varía en función de la temperatura exterior |
| H2 | Una parte relevante del consumo se concentra en periodos tarifarios caros (P1–P2) |
| H3 | El coste no depende solo de los kWh, sino también del periodo tarifario en que se producen |
| H4 | Un cambio en los turnos u horarios de trabajo puede afectar al coste energético estimado |

---

## Estructura del proyecto

```text
EDA_consumo_energetico/
│
├── data/                        # Datos originales
│   ├── Steel_industry_data.csv
│   ├── periodos_peninsula.csv
│   ├── clima_aemet_espana_media_diaria_2024.csv
│   └── tarifa_completa_2024.csv
│
├── data_limpios/                # Datos limpios generados
│   ├── df_consumo_2024_15min_estudio_limpio.csv
│   ├── df_consumo_2024_horario_estudio_limpio.csv
│   ├── df_periodos_peninsula_limpio.csv
│   ├── df_clima_2024_limpio.csv
│   ├── df_tarifa_completa_2024_limpio.csv
│   ├── df_maestro.csv           # Dataset principal del análisis
│   └── df_consumo_clima_limpio.csv
│
├── graficos/                    # Gráficos generados durante el análisis
├── memoria/                     # Memoria del proyecto
├── notebooks/                   # Notebooks de prueba y validación
│   ├── test_limpieza.ipynb
│   └── test_eda.ipynb
├── utils/                       # Scripts principales
│   ├── limpieza.py
│   ├── contexto_operativo.py
│   └── eda.py
└── README.md
```

---

## Cómo ejecutar

Desde la raíz del proyecto, situarse en la carpeta `utils/` y ejecutar los scripts en orden:

```bash
cd utils
python limpieza.py         # Genera los datasets limpios en data_limpios/
python contexto_operativo.py  # Genera df_maestro.csv y gráficos de contexto
python eda.py              # EDA principal e hipótesis H1–H4
```

---

## Dataset principal

El archivo `df_maestro.csv` integra consumo horario, calendario 2024, turno, periodo tarifario, datos climáticos y coste energético estimado. Es el punto de entrada para todo el análisis.

---

## Coste energético estimado

El proyecto calcula un **coste estimado parcial** para comparar escenarios:

```
coste_estimado_parcial = consumo_kwh × (energia_regulada_eur_kwh + fnee_eur_kwh)
```

> ⚠️ Este cálculo es exploratorio y no representa una factura eléctrica real. No incluye potencia contratada, impuestos, penalizaciones ni otros conceptos contractuales.

---

## Librerías utilizadas

`pandas` · `numpy` · `matplotlib` · `seaborn` · `pathlib`

---

## Nota metodológica

El patrón de consumo original (dataset industrial base) se adapta metodológicamente al calendario 2024. El análisis debe interpretarse como un EDA exploratorio, no como una auditoría energética completa.