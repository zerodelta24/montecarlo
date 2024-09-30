import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.title('Simulación de Monte Carlo para Operaciones Financieras')
st.write('Esta aplicación permite realizar una simulación de Monte Carlo basada en tus datos históricos de operaciones.')

# Capital inicial
capital_inicial = st.number_input('Capital Inicial (USD)', value=10000.0, min_value=0.0)

# Tope de stop loss (umbral de riesgo de ruina)
stop_loss = st.number_input('Tope de Stop Loss (USD)', value=1500.0, min_value=0.0)

# Número de simulaciones
N = st.number_input('Número de Simulaciones', min_value=1, value=1000, step=1)

# Número de operaciones por simulación
M = st.number_input('Número de Operaciones por Simulación', min_value=1, value=500, step=1)

# Subir archivo de operaciones históricas
archivo = st.file_uploader('Subir Archivo CSV con Operaciones Históricas', type=['csv'])

if st.button('Ejecutar Simulación'):
    if archivo is not None:
        try:
            # Leer el archivo CSV
            datos = pd.read_csv(archivo, encoding='utf-8')

            # Verificar que las columnas necesarias existen
            if 'Benef./Pérdida USD' in datos.columns:
                # Convertir la columna de fecha a datetime si existe
                if 'Fecha/hora' in datos.columns:
                    datos['Fecha/hora'] = pd.to_datetime(datos['Fecha/hora'], errors='coerce')
                    datos = datos.dropna(subset=['Fecha/hora'])
                else:
                    st.warning('La columna "Fecha/hora" no se encontró. Continuando sin convertir fechas.')

                # Asegurarse de que la columna 'Benef./Pérdida USD' es numérica
                datos['Benef./Pérdida USD'] = pd.to_numeric(datos['Benef./Pérdida USD'], errors='coerce')
                datos = datos.dropna(subset=['Benef./Pérdida USD'])

                # Verificar que existen suficientes datos para la simulación
                if len(datos) == 0:
                    st.error('No hay datos válidos en la columna "Benef./Pérdida USD" después de procesar el archivo.')
                else:
                    # Calcular el retorno promedio y la desviación estándar
                    retorno_promedio = datos['Benef./Pérdida USD'].mean()
                    desviacion_estandar = datos['Benef./Pérdida USD'].std()

                    st.write(f'**Retorno Promedio:** {retorno_promedio:.2f} USD')
                    st.write(f'**Desviación Estándar:** {desviacion_estandar:.2f} USD')

                    # Verificar que la desviación estándar no sea cero
                    if desviacion_estandar == 0:
                        st.error('La desviación estándar es cero. No se puede realizar la simulación.')
                    else:
                        # Realizar la simulación de Monte Carlo
                        simulaciones = np.random.normal(retorno_promedio, desviacion_estandar, (int(N), int(M)))
                        retornos_acumulados = simulaciones.cumsum(axis=1)
                        capital_final = capital_inicial + retornos_acumulados[:, -1]

                        # Calcular el riesgo de ruina ajustado al tope de stop loss
                        ruinas = 0
                        for i in range(int(N)):
                            serie_capital = capital_inicial + retornos_acumulados[i]
                            if np.any(serie_capital < stop_loss):
                                ruinas += 1
                        riesgo_de_ruina = ruinas / int(N)
                        st.write(f'**Riesgo de Ruina (capital cae por debajo de ${stop_loss}):** {riesgo_de_ruina * 100:.2f}%')

                        # Calcular el drawdown máximo para cada simulación
                        max_drawdowns = []
                        for i in range(int(N)):
                            serie = capital_inicial + retornos_acumulados[i]
                            pico_acumulado = np.maximum.accumulate(serie)
                            drawdowns = (pico_acumulado - serie) / pico_acumulado
                            max_drawdown = np.max(drawdowns)
                            max_drawdowns.append(max_drawdown)
                        max_drawdowns = np.array(max_drawdowns)
                        mediana_drawdown = np.median(max_drawdowns)
                        st.write(f'**Mediana del Drawdown Máximo:** {mediana_drawdown * 100:.2f}%')

                        # Calcular el retorno promedio anual
                        retornos_totales = retornos_acumulados[:, -1]
                        retorno_promedio_anual = np.mean(retornos_totales)
                        st.write(f'**Retorno Promedio Anual:** {retorno_promedio_anual:.2f} USD')

                        # Visualizar los resultados
                        st.subheader('Distribución del Capital Final')
                        fig1, ax1 = plt.subplots()
                        ax1.hist(capital_final, bins=50, edgecolor='black')
                        ax1.set_xlabel('Capital Final (USD)')
                        ax1.set_ylabel('Frecuencia')
                        st.pyplot(fig1)

                        st.subheader('Distribución de los Drawdowns Máximos')
                        fig2, ax2 = plt.subplots()
                        ax2.hist(max_drawdowns * 100, bins=50, edgecolor='black')
                        ax2.set_xlabel('Drawdown Máximo (%)')
                        ax2.set_ylabel('Frecuencia')
                        st.pyplot(fig2)
            else:
                st.error('El archivo CSV debe contener una columna llamada "Benef./Pérdida USD". Las columnas encontradas son:')
                st.write(datos.columns.tolist())
        except Exception as e:
            st.error(f'Ocurrió un error al procesar el archivo: {e}')
    else:
        st.error('Por favor, sube un archivo CSV con tus operaciones históricas.')

st.markdown("""
### Formato del Archivo CSV
El archivo debe contener al menos las siguientes columnas:

- **Fecha/hora:** (opcional) Fecha y hora de cada operación.
- **Benef./Pérdida USD:** Ganancia o pérdida de cada operación en USD.

Asegúrate de que los nombres de las columnas sean exactamente como se indica.
""")
