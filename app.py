import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="Auditor Multi-Canal BI", page_icon="📈", layout="wide")

st.title("📊 Auditoría BI: Meta & Google Ads")
st.markdown("Analizador de anomalías estadísticas para optimización de presupuestos.")

# 1. Configuración de Plataforma
plataforma = st.sidebar.selectbox("Selecciona la Plataforma", ["Meta Ads", "Google Ads"])
archivo_subido = st.file_uploader(f"Sube el reporte CSV de {plataforma}", type=['csv'])

def diagnosticar(z, plataforma, frecuencia=0):
    if plataforma == "Google Ads":
        if z > 1.5: return "COSTO ALTO: Revisar competencia"
        if z < -1: return "EFICIENTE: Buen rendimiento"
    else:
        if z > 2 and frecuencia > 3.5: return "FATIGA: Cambiar creativos"
        if z > 1.5: return "COSTO ELEVADO"
    return "ESTABLE"

if archivo_subido:
    try:
        # --- CARGA Y LIMPIEZA AUTOMÁTICA ---
        if plataforma == "Google Ads":
            df = pd.read_csv(archivo_subido, encoding='utf-8-sig', skiprows=2)
            df.columns = df.columns.str.strip()
            # Limpiar filas de totales y nulas
            df = df.dropna(subset=[df.columns[1]])
            df = df[~df.iloc[:, 0].astype(str).str.contains("Total", case=False)]
            
            # Convertir monedas (comas a puntos)
            for col in df.columns:
                if any(x in col.lower() for x in ['coste', 'cpc', 'costo']):
                    df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
            
            metrica_costo = next((c for c in df.columns if 'cpc' in c.lower() or 'coste' in c.lower()), df.columns[0])
            col_id = next((c for c in df.columns if 'campaña' in c.lower()), df.columns[1])
        else:
            df = pd.read_csv(archivo_subido, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            metrica_costo = 'Costo por resultados'
            col_id = next((c for c in df.columns if 'nombre' in c.lower()), df.columns[0])

        # --- CÁLCULO DE BENCHMARK (Cuenta vs Campaña) ---
        # Calculamos la media y desviación de TODA la tabla para comparar
        m_global = df[metrica_costo].mean()
        s_global = df[metrica_costo].std() if df[metrica_costo].std() > 0 else 1
        
        st.subheader(f"Análisis de Desviación: {plataforma}")
        
        # Grid de resultados
        top_items = df.sort_values(by=metrica_costo, ascending=False).head(4)
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        plt.subplots_adjust(hspace=0.6)

        for i, (index, row) in enumerate(top_items.iterrows()):
            ax = axes.flatten()[i]
            nombre = row[col_id]
            valor_actual = row[metrica_costo]
            
            # Z-Score comparando esta campaña contra el promedio del archivo
            z = (valor_actual - m_global) / s_global
            
            # Gráfica de distribución
            x = np.linspace(m_global - 4*s_global, m_global + 4*s_global, 100)
            y = norm.pdf(x, m_global, s_global)
            
            color = '#E74C3C' if z > 1 else '#3498DB'
            ax.plot(x, y, color=color, lw=2)
            ax.fill_between(x, y, alpha=0.1, color=color)
            ax.axvline(valor_actual, color='black', linestyle='--', lw=2, label='Tu Campaña')
            ax.axvline(m_global, color='gray', linestyle=':', label='Promedio Cuenta')
            
            status = diagnosticar(z, plataforma)
            ax.set_title(f"{nombre[:20]}\nZ: {z:.2f} | {status}", fontsize=10, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)

        st.pyplot(fig)
        
        # Tabla de depuración para tu control
        with st.expander("Ver datos procesados"):
            st.dataframe(df[[col_id, metrica_costo]])

    except Exception as e:
        st.error(f"Error técnico: {e}. Asegúrate de subir el archivo 'Informe de campaña' original.")
