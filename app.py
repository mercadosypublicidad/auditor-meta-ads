import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="Auditor Multi-Canal BI", page_icon="📈", layout="wide")

st.title("📊 Auditoría BI: Meta & Google Ads")
st.sidebar.header("Configuración de Análisis")

# 1. Selector de Plataforma
plataforma = st.sidebar.selectbox("Selecciona la Plataforma", ["Meta Ads", "Google Ads"])

archivo_subido = st.file_uploader(f"Sube el reporte CSV de {plataforma}", type=['csv'])

def diagnosticar_google(subset, z):
    # Lógica específica para Google Ads
    ctr_col = next((c for c in subset.columns if 'ctr' in c.lower()), None)
    if z > 2:
        return "ALERTA: CPC Inusual (Competencia alta)"
    if ctr_col and subset[ctr_col].iloc[0] < subset[ctr_col].mean():
        return "ALERTA: Relevancia baja en Búsqueda"
    return "ESTABLE: Subasta normal"

def diagnosticar_meta(subset, z):
    # Tu lógica ya probada de Meta Ads
    frecuencia_col = next((c for c in subset.columns if 'frecuencia' in c.lower()), None)
    frec = subset[frecuencia_col].sum() / subset.shape[0] if frecuencia_col else 0
    if z > 2:
        if frec > 3.5: return f"FATIGA: Frecuencia ({frec:.1f}x)"
        return "SUBASTA ALTA: Costo elevado"
    return "ESTABLE: Operación normal"

if archivo_subido:
    try:
        df = pd.read_csv(archivo_subido, encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")

        # Definir métrica y columnas según plataforma
        if plataforma == "Google Ads":
            metrica_costo = next((c for c in df.columns if 'cpc' in c.lower() or 'coste' in c.lower()), df.columns[0])
            col_id = next((c for c in df.columns if 'campaña' in c.lower() or 'campaign' in c.lower()), df.columns[0])
        else:
            metrica_costo = 'Costo por resultados'
            col_id = next((c for c in df.columns if 'nombre' in c.lower()), df.columns[0])

        # Procesamiento
        top_items = df.groupby(col_id)['Importe gastado (MXN)' if plataforma == "Meta Ads" else df.columns[-1]].sum().nlargest(4).index
        
        st.subheader(f"Resultados de {plataforma}")
        cols = st.columns(len(top_items))

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        plt.subplots_adjust(hspace=0.5)

        for i, (item, ax) in enumerate(zip(top_items, axes.flatten())):
            subset = df[df[col_id] == item].dropna(subset=[metrica_costo])
            if len(subset) > 2:
                m, s, h = subset[metrica_costo].mean(), subset[metrica_costo].std(), subset[metrica_costo].iloc[0]
                z = (h - m) / s if s > 0 else 0
                
                msg = diagnosticar_google(subset, z) if plataforma == "Google Ads" else diagnosticar_meta(subset, z)
                color = '#E74C3C' if z > 2 else '#3498DB'
                
                x = np.linspace(m - 4*s, m + 4*s, 100)
                ax.plot(x, norm.pdf(x, m, s), color=color, lw=2)
                ax.fill_between(x, norm.pdf(x, m, s), alpha=0.1, color=color)
                ax.axvline(h, color='black', lw=2)
                ax.set_title(f"{item[:20]}...\nZ: {z:.2f} | {msg}", fontsize=9, color=color)
        
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: Asegúrate de que las columnas coincidan con {plataforma}.")
