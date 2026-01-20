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
    # Usamos base_2.xlsx
    df = pd.read_excel("base_2.xlsx", dtype={'Identificacion': str, 'Contrato': str})
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo 'base_2.xlsx'. Asegúrate de subirlo al repositorio.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Error al leer el archivo: {e}")
    st.stop()

# --- INTERFAZ DE BÚSQUEDA ---
st.divider()
cedula_input = st.text_input("Digita la Cédula del Cliente:", placeholder="Ej: 100589...")

# --- LÓGICA DE FILTRADO ---
if cedula_input:
    # Limpiamos espacios
    cedula_limpia = cedula_input.strip()
    
    # Filtramos el DF
    datos_cliente = df[df['Identificacion'] == cedula_limpia]

    if not datos_cliente.empty:
        # --- DATOS GENERALES DEL CLIENTE ---
        nombre = datos_cliente['NombreSuscriptor'].iloc[0]
        telefono_raw = datos_cliente['UltimoTelefono'].iloc[0]
        segmento = datos_cliente['SegmentoClienteRFM'].iloc[0]

        # --- LIMPIEZA DE TELÉFONO ---
        if pd.notna(telefono_raw):
            t_str = str(telefono_raw)
            if t_str.endswith('.0'):
                t_str = t_str[:-2]
            telefono_str = ''.join(filter(str.isdigit, t_str))
        else:
            telefono_str = "No registrado"

        segmento_str = str(segmento) if pd.notna(segmento) else "Sin segmento"

        st.success(f"✅ Cliente: {nombre}")
        
        # Información extra
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.info(f"📞 **Teléfono:** {telefono_str}")
        with info_col2:
            st.info(f"📊 **Segmento RFM:** {segmento_str}")

        st.divider()

        # --- FILTRO POR CIUDAD (Multiselect) ---
        ciudades_disponibles = datos_cliente['Localidad'].unique()
        
        ciudades_seleccionadas = st.multiselect(
            "📍 Filtrar por Ciudad/Localidad:",
            options=ciudades_disponibles,
            default=ciudades_disponibles
        )

        # Filtramos según selección
        datos_visualizar = datos_cliente[datos_cliente['Localidad'].isin(ciudades_seleccionadas)]

        if not datos_visualizar.empty:
            # --- CÁLCULOS ESTÁNDAR ---
            total_asignado = datos_visualizar['CupoAsignado'].sum()
            total_usado = datos_visualizar['CupoUsado'].sum()
            total_disponible = datos_visualizar['CupoDisponible'].sum()
            cantidad_predios = len(datos_visualizar)

            # --- CÁLCULO CUPO DISPONIBLE REAL (Top 2 Contratos) ---
            # 1. Ordenamos por Cupo Disponible de mayor a menor
            # 2. Tomamos los primeros 2 registros (.head(2))
            # 3. Sumamos
            cupo_real_top2 = datos_visualizar.sort_values(
                by='CupoDisponible', ascending=False
            ).head(2)['CupoDisponible'].sum()

            # --- VISUALIZACIÓN DE MÉTRICAS (5 Columnas ahora) ---
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

            # Cupo Total (Suma de todo)
            m_col4.metric("✅ Disponible", f"${total_disponible:,.0f}")
            
            # NUEVA METRICA: Cupo Real (Suma Top 2)
            # Usamos un ícono diferente para resaltar (⭐)
            m_col5.metric("⭐ Cupo Real (Max 2)", f"${cupo_real_top2:,.0f}")
            
            st.divider()

            # =========================================================
            # LÓGICA ESPECIAL: LOCALIDAD Y LÍNEA DE COMPRA
            # =========================================================

            # 1. Análisis de LOCALIDAD
            localidades_unicas = datos_visualizar['Localidad'].unique()
            mostrar_localidad_tabla = True 

            if len(localidades_unicas) == 1:
                st.info(f"📍 **Localidad (General):** {localidades_unicas[0]}")
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

            # --- TABLA DETALLADA ---
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

            st.dataframe(
                datos_visualizar[cols_existentes], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Debes seleccionar al menos una ciudad para ver los datos.")

    else:
        st.warning(f"⚠️ La cédula {cedula_limpia} no se encuentra en la base de datos.")

