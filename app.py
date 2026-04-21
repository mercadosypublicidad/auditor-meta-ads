import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import textwrap # NUEVO: Librería para envolver textos largos

st.set_page_config(page_title="Auditor Multi-Canal BI", page_icon="📈", layout="wide")

st.title("📊 Auditoría BI: Meta & Google Ads")
st.markdown("Analizador de anomalías estadísticas para optimización de presupuestos.")

# --- CONTROLES DE LA BARRA LATERAL ---
st.sidebar.header("⚙️ Controles de Auditoría")
plataforma = st.sidebar.selectbox("Selecciona la Plataforma", ["Meta Ads", "Google Ads"])

nivel_analisis = st.sidebar.radio("Nivel de Análisis", ["Campaña", "Anuncio"])
solo_activas = st.sidebar.checkbox("🟢 Mostrar solo activas", value=True, help="Oculta campañas pausadas o finalizadas.")

st.sidebar.divider()
archivo_subido = st.sidebar.file_uploader(f"Sube el reporte de {plataforma}", type=['csv'])

def diagnosticar(z, plataforma, frecuencia=0):
    if plataforma == "Google Ads":
        if z > 1.5: return "COSTO ALTO: Revisar subasta"
        if z < -1: return "EFICIENTE: Buen rendimiento"
    else:
        if z > 2 and frecuencia > 3.5: return "FATIGA: Cambiar creativo"
        if z > 1.5: return "COSTO ELEVADO"
    return "ESTABLE"

if archivo_subido:
    try:
        # --- CARGA Y LIMPIEZA AUTOMÁTICA ---
        if plataforma == "Google Ads":
            df = pd.read_csv(archivo_subido, encoding='utf-8-sig', skiprows=2)
            df.columns = df.columns.str.strip()
            df = df.dropna(subset=[df.columns[1]])
            df = df[~df.iloc[:, 0].astype(str).str.contains("Total", case=False)]
            
            for col in df.columns:
                if any(x in col.lower() for x in ['coste', 'cpc', 'costo']):
                    df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
            
            metrica_costo = next((c for c in df.columns if 'cpc' in c.lower() or 'coste' in c.lower()), df.columns[0])
            col_estado = next((c for c in df.columns if 'estado' in c.lower()), None)

        else:
            df = pd.read_csv(archivo_subido, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            
            metrica_costo = next((c for c in df.columns if 'cost' in c.lower() and 'resultado' in c.lower()), df.columns[0])
            df[metrica_costo] = pd.to_numeric(df[metrica_costo].astype(str).str.replace(',', '.'), errors='coerce')
            df = df.dropna(subset=[metrica_costo])
            
            col_estado = next((c for c in df.columns if 'entrega' in c.lower() or 'estado' in c.lower()), None)

        # --- APLICAR FILTRO DE ACTIVAS ---
        if solo_activas and col_estado:
            df = df[df[col_estado].astype(str).str.contains('active|activa|apto|habilitada|curso', case=False, na=False)]
            if len(df) == 0:
                st.warning("⚠️ No hay datos activos en este reporte. Intenta apagar el filtro de 'Mostrar solo activas'.")
                st.stop()

        # --- DETECCIÓN DINÁMICA DE NIVEL ---
        if nivel_analisis == "Campaña":
            col_id = next((c for c in df.columns if 'campaña' in c.lower()), df.columns[1] if plataforma=="Google Ads" else df.columns[0])
        else:
            col_id = next((c for c in df.columns if 'anuncio' in c.lower() and 'conjunto' not in c.lower() and 'presupuesto' not in c.lower()), None)
            if not col_id:
                st.warning("⚠️ No se encontró la columna de Anuncios. ¿Aseguraste descargar el CSV desde la pestaña de 'Anuncios'? Cambiando a vista de Campaña automáticamente.")
                col_id = next((c for c in df.columns if 'campaña' in c.lower()), df.columns[1])
                nivel_analisis = "Campaña"

        # --- CÁLCULO DE BENCHMARK ---
        df_agrupado = df.groupby(col_id)[metrica_costo].mean().reset_index()
        
        m_global = df_agrupado[metrica_costo].mean()
        s_global = df_agrupado[metrica_costo].std() if df_agrupado[metrica_costo].std() > 0 else 1
        
        st.subheader(f"Comparativa de {nivel_analisis}s ({plataforma})")
        
        top_items = df_agrupado.sort_values(by=metrica_costo, ascending=False).head(4)
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10)) # Aumenté un poco el alto de la figura
        plt.subplots_adjust(hspace=0.7) # Aumenté el espacio entre gráficas para que quepa el texto largo

        for i, (index, row) in enumerate(top_items.iterrows()):
            ax = axes.flatten()[i]
            nombre = row[col_id]
            valor_actual = row[metrica_costo]
            
            z = (valor_actual - m_global) / s_global
            
            x = np.linspace(m_global - 4*s_global, m_global + 4*s_global, 100)
            y = norm.pdf(x, m_global, s_global)
            
            color = '#E74C3C' if z > 1 else '#3498DB'
            ax.plot(x, y, color=color, lw=2)
            ax.fill_between(x, y, alpha=0.1, color=color)
            
            ax.axvline(valor_actual, color='black', linestyle='--', lw=2, label=f'Costo Actual: ${valor_actual:.2f}')
            ax.axvline(m_global, color='gray', linestyle=':', label=f'Promedio Cuenta: ${m_global:.2f}')
            ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
            
            status = diagnosticar(z, plataforma)
            
            # --- LA MEJORA VISUAL: ENVOLVER TEXTO EN VEZ DE CORTARLO ---
            nombre_envuelto = "\n".join(textwrap.wrap(str(nombre), width=45))
            ax.set_title(f"{nombre_envuelto}\nZ: {z:.2f} | {status}", fontsize=9, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)

        st.pyplot(fig)
        
        with st.expander("Ver tabla de datos limpios"):
            st.dataframe(df_agrupado[[col_id, metrica_costo]])

    except Exception as e:
        st.error(f"Error técnico: {e}. Revisa el archivo subido.")
