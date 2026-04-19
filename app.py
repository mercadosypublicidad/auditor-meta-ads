import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# 1. Configuración de la página web
st.set_page_config(page_title="Auditor BI Meta Ads", page_icon="📊", layout="wide")

st.title("📊 Auditoría Estratégica Universal")
st.markdown("Sube el reporte CSV de Meta Ads para obtener un diagnóstico automático de fatiga y rendimiento.")

# 2. El botón "mágico" para subir archivos directamente en la web
archivo_subido = st.file_uploader("Arrastra tu archivo CSV aquí", type=['csv'])

def diagnosticar_causa(subset):
    clics_col = next((c for c in subset.columns if 'clics' in c.lower()), None)
    impresiones_col = next((c for c in subset.columns if 'impresiones' in c.lower()), None)
    alcance_col = next((c for c in subset.columns if 'alcance' in c.lower()), None)

    ctr = 0
    if clics_col and impresiones_col:
        total_clics = subset[clics_col].sum()
        total_imp = subset[impresiones_col].sum()
        ctr = (total_clics / total_imp) * 100 if total_imp > 0 else 0

    frecuencia = 0
    if impresiones_col and alcance_col:
        total_imp = subset[impresiones_col].sum()
        total_alc = subset[alcance_col].sum()
        frecuencia = total_imp / total_alc if total_alc > 0 else 0
    
    m, s, h = subset['Costo por resultados'].mean(), subset['Costo por resultados'].std(), subset['Costo por resultados'].iloc[0]
    z = (h - m) / s if s > 0 else 0

    if z > 2:
        if frecuencia > 3.5:
            return f"FATIGA: Frecuencia excesiva ({frecuencia:.1f}x)"
        if ctr > 0 and ctr < 0.8:
            return f"BAJA RELEVANCIA: CTR pobre ({ctr:.2f}%)"
        return "SUBASTA ALTA: Competencia fuerte"
    elif z < -1:
        return "ÓPTIMO: Rendimiento superior"
    
    return "ESTABLE: Costo normal"

# 3. Lógica principal que solo corre si hay un archivo
if archivo_subido is not None:
    try:
        # Carga inteligente
        df = pd.read_csv(archivo_subido, encoding='utf-8-sig')
        df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")
        
        posibles_id = ['Nombre de la campaña', 'Nombre del conjunto de anuncios', 'Nombre del anuncio']
        col_id = next((c for c in posibles_id if c in df.columns), df.columns[0])
        
        df['Inicio del informe'] = pd.to_datetime(df['Inicio del informe'])
        
        top_4 = df.groupby(col_id)['Importe gastado (MXN)'].sum().nlargest(4).index
        items = sorted(top_4)

        g_total = df['Importe gastado (MXN)'].sum()
        leads_t = df['Resultados'].sum()
        cpl_g = g_total / leads_t if leads_t > 0 else 0

        # --- SECCIÓN VISUAL WEB ---
        st.divider()
        
        # Tarjetas de métricas tipo Dashboard
        col1, col2, col3 = st.columns(3)
        col1.metric("Inversión Total", f"${g_total:,.2f}")
        col2.metric("Leads Generados", f"{int(leads_t)}")
        col3.metric("CPL Global", f"${cpl_g:.2f}")
        
        st.caption(f"Análisis desglosado por: **{col_id}**")

        # Gráficas
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        plt.subplots_adjust(hspace=0.4, wspace=0.3)
        
        df_datos = df.dropna(subset=['Costo por resultados'])
        
        for i, ax in enumerate(axes.flatten()):
            if i < len(items):
                nombre = items[i]
                subset = df_datos[df_datos[col_id] == nombre]
                
                if not subset.empty and len(subset) > 2:
                    m, s, h = subset['Costo por resultados'].mean(), subset['Costo por resultados'].std(), subset['Costo por resultados'].iloc[0]
                    z = (h - m) / s if s > 0 else 0
                    
                    diagnostico = diagnosticar_causa(subset)
                    color = '#E74C3C' if z > 2 else '#3498DB'
                    
                    x = np.linspace(m - 4*s, m + 4*s, 100)
                    ax.plot(x, norm.pdf(x, m, s), color=color, lw=2.5)
                    ax.fill_between(x, norm.pdf(x, m, s), alpha=0.1, color=color)
                    ax.axvline(h, color='black', lw=2)
                    
                    ax.set_title(f"{str(nombre)[:25]}...\nZ: {z:.2f} | {diagnostico}", 
                                 fontsize=10, fontweight='bold', color=color)
                else:
                    ax.text(0.5, 0.5, "Esperando datos...", ha='center', color='gray')
                ax.grid(True, alpha=0.1)
                ax.set_yticklabels([]) # Limpiamos el eje Y para diseño más web
            else:
                ax.set_visible(False)
        
        # Le decimos a Streamlit que pinte la figura de Matplotlib
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo: {e}. Revisa que sea un CSV válido de Meta Ads.")