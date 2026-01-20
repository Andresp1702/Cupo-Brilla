import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Consulta de Cupos", layout="centered", page_icon="🔍")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# --- TÍTULO Y DESCRIPCIÓN ---
st.title("🔍 Buscador de Cupos y Predios")
st.markdown("Ingrese el número de cédula para consultar el perfil, contratos y cupos detallados.")

# --- CARGAR DATOS ---
@st.cache_data
def cargar_datos():
    # Usamos base_2.pkl.gz (la versión optimizada que creamos antes)
    df = pd.read_pickle("base_2.pkl.gz")
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo 'base_2.pkl.gz'. Asegúrate de subirlo al repositorio.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Error al leer el archivo: {e}")
    st.stop()

# --- INTERFAZ DE BÚSQUEDA ---
st.divider()
cedula_input = st.text_input("Digita la Cédula del Cliente:", placeholder="Ej: 100589...")

# --- LÓGICA DE FILTRADO ---
if cedula_input:
    cedula_limpia = cedula_input.strip()
    
    # Filtramos el DF por cédula
    datos_cliente = df[df['Identificacion'] == cedula_limpia]

    if not datos_cliente.empty:
        # --- DATOS GENERALES DEL CLIENTE ---
        nombre = datos_cliente['NombreSuscriptor'].iloc[0]
        telefono_raw = datos_cliente['UltimoTelefono'].iloc[0]
        segmento = datos_cliente['SegmentoClienteRFM'].iloc[0]

        # Limpieza de teléfono
        if pd.notna(telefono_raw):
            t_str = str(telefono_raw)
            if t_str.endswith('.0'):
                t_str = t_str[:-2]
            telefono_str = ''.join(filter(str.isdigit, t_str))
        else:
            telefono_str = "No registrado"

        segmento_str = str(segmento) if pd.notna(segmento) else "Sin segmento"

        st.success(f"✅ Cliente: {nombre}")
        
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.info(f"📞 **Teléfono:** {telefono_str}")
        with info_col2:
            st.info(f"📊 **Segmento RFM:** {segmento_str}")

        st.divider()

        # --- CAMBIO 1: LISTADO DE CIUDADES (SIN FILTRO INTERACTIVO) ---
        # Ya no usamos multiselect, solo mostramos dónde tiene predios
        ciudades_encontradas = datos_cliente['Localidad'].unique()
        texto_ciudades = ", ".join(ciudades_encontradas)
        
        st.markdown(f"📍 **Predios ubicados en:** {texto_ciudades}")

        # Como ya no hay filtro, los datos a visualizar son todos los del cliente
        datos_visualizar = datos_cliente.copy()

        # --- CÁLCULOS ESTÁNDAR ---
        total_asignado = datos_visualizar['CupoAsignado'].sum()
        total_usado = datos_visualizar['CupoUsado'].sum()
        total_disponible = datos_visualizar['CupoDisponible'].sum()
        cantidad_predios = len(datos_visualizar)

        # --- CÁLCULO CUPO DISPONIBLE REAL (Top 2 Contratos) ---
        # Identificamos cuáles son las filas del Top 2 para usarlas luego en el resaltado
        df_sorted = datos_visualizar.sort_values(by='CupoDisponible', ascending=False)
        top_2_indices = df_sorted.head(2).index.tolist() # Guardamos los ID de las filas ganadoras
        
        cupo_real_top2 = df_sorted.head(2)['CupoDisponible'].sum()

        # --- VISUALIZACIÓN DE MÉTRICAS ---
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

        m_col1.metric("🏠 Predios", f"{cantidad_predios}")

        if total_asignado > 0:
            m_col2.metric("💰 Asignado", f"${total_asignado:,.0f}")
        else:
            m_col2.empty()

        if total_usado > 0:
            m_col3.metric("📉 Usado", f"${total_usado:,.0f}")
        else:
            m_col3.empty()

        m_col4.metric("✅ Disponible", f"${total_disponible:,.0f}")
        m_col5.metric("⭐ Cupo Real (Max 2)", f"${cupo_real_top2:,.0f}")
        
        st.divider()

        # =========================================================
        # LÓGICA ESPECIAL: GRÁFICOS Y TABLAS
        # =========================================================

        # 1. Análisis de LOCALIDAD
        localidades_unicas = datos_visualizar['Localidad'].unique()
        mostrar_localidad_tabla = True 

        if len(localidades_unicas) == 1:
            mostrar_localidad_tabla = False
        else:
            st.subheader("📊 Distribución por Localidad")
            conteo_localidad = datos_visualizar['Localidad'].value_counts()
            total_loc = conteo_localidad.sum()
            
            labels_loc = [
                f'{l}: {v} ({(v/total_loc*100):.1f}%)' 
                for l, v in zip(conteo_localidad.index, conteo_localidad)
            ]

            fig, ax = plt.subplots(figsize=(6, 3))
            wedges, texts = ax.pie(
                conteo_localidad, 
                startangle=90,
                colors=plt.cm.Pastel1.colors, 
                wedgeprops={'edgecolor': 'white'}
            )
            ax.legend(wedges, labels_loc, title="Localidades", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            ax.axis('equal') 
            st.pyplot(fig, use_container_width=False)

        # 2. Análisis de LÍNEA DE COMPRA
        lineas_unicas = datos_visualizar['LineaUltimaCompra'].astype(str).unique()
        mostrar_linea_en_tabla = True 
        
        if len(lineas_unicas) == 1 and lineas_unicas[0].lower() != 'nan':
            st.info(f"🛒 **Última Línea de Compra (General):** {lineas_unicas[0]}")
            mostrar_linea_en_tabla = False 

        # --- TABLA DETALLADA CON ESTILOS (HIGHLIGHT) ---
        st.subheader("📋 Detalle de Contratos")
        
        columnas_a_mostrar = [
            'Contrato',  
            'Subcategoria', 
            'Ubicacion', 
            'CupoAsignado', 
            'CupoUsado',
            'CupoDisponible'
        ]
        
        if mostrar_localidad_tabla:
            columnas_a_mostrar.insert(1, 'Localidad')

        if mostrar_linea_en_tabla:
            posicion = 2 if mostrar_localidad_tabla else 1
            columnas_a_mostrar.insert(posicion, 'LineaUltimaCompra')

        cols_existentes = [c for c in columnas_a_mostrar if c in datos_visualizar.columns]
        
        # --- CAMBIO 2: APLICAR ESTILOS PARA RESALTAR ---
        # Definimos una función que pinte de color si el índice está en el TOP 2
        def resaltar_mayores(row):
            # Si el índice de la fila está en la lista de los top 2
            if row.name in top_2_indices:
                # Retorna negrilla y fondo verde claro para toda la fila
                return ['background-color: #d1e7dd; font-weight: bold; color: black'] * len(row)
            else:
                return [''] * len(row)

        # Aplicamos el estilo al DataFrame
        # Nota: Pandas Styler requiere un DF limpio, por eso usamos style.apply
        df_styled = datos_visualizar[cols_existentes].style.apply(resaltar_mayores, axis=1)

        # Formato de moneda para columnas específicas si existen
        format_dict = {}
        for col in ['CupoAsignado', 'CupoUsado', 'CupoDisponible']:
            if col in cols_existentes:
                format_dict[col] = "${:,.0f}" # Formato dinero sin decimales

        df_styled = df_styled.format(format_dict)

        st.dataframe(
            df_styled, 
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning(f"⚠️ La cédula {cedula_limpia} no se encuentra en la base de datos.")
