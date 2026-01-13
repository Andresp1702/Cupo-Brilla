import streamlit as st
import pandas as pd

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
    # Usamos base_2.xlsx como en tu código. 
    # Asegúrate que el archivo esté en la carpeta del repositorio.
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

        # --- CORRECCIÓN: LIMPIEZA DE TELÉFONO ---
        if pd.notna(telefono_raw):
            t_str = str(telefono_raw)
            # Si Excel trajo decimales (ej: 310555.0), los quitamos
            if t_str.endswith('.0'):
                t_str = t_str[:-2]
            # Dejamos SOLO dígitos (elimina comas, espacios, puntos)
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

        # --- FILTRO POR CIUDAD ---
        ciudades_disponibles = datos_cliente['Localidad'].unique()
        
        ciudades_seleccionadas = st.multiselect(
            "📍 Filtrar por Ciudad/Localidad:",
            options=ciudades_disponibles,
            default=ciudades_disponibles
        )

        # Filtramos según selección
        datos_visualizar = datos_cliente[datos_cliente['Localidad'].isin(ciudades_seleccionadas)]

        if not datos_visualizar.empty:
            # --- CÁLCULOS ---
            total_asignado = datos_visualizar['CupoAsignado'].sum()
            total_usado = datos_visualizar['CupoUsado'].sum()
            total_disponible = datos_visualizar['CupoDisponible'].sum()
            cantidad_predios = len(datos_visualizar)

            # --- VISUALIZACIÓN DE MÉTRICAS ---
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)

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

            # --- LÓGICA LINEA ÚLTIMA COMPRA ---
            # Verificamos cuántas líneas de compra diferentes hay en la selección
            lineas_unicas = datos_visualizar['LineaUltimaCompra'].astype(str).unique()
            
            mostrar_linea_en_tabla = True # Por defecto la mostramos
            
            # Si solo hay UNA línea única (y no es 'nan'), la mostramos afuera
            if len(lineas_unicas) == 1 and lineas_unicas[0].lower() != 'nan':
                st.info(f"🛒 **Última Línea de Compra (General):** {lineas_unicas[0]}")
                mostrar_linea_en_tabla = False # La quitamos de la tabla para no repetir

            # --- TABLA DETALLADA ---
            st.subheader("📋 Detalle de Contratos")
            
            # Definimos las columnas base
            columnas_a_mostrar = [
                'Contrato',  # <--- Agregado Contrato
                'Localidad', 
                'Subcategoria', 
                'Ubicacion', 
                'CupoAsignado', 
                'CupoUsado',
                'CupoDisponible'
            ]
            
            # Si las líneas son diferentes, agregamos la columna a la tabla
            if mostrar_linea_en_tabla:
                # La insertamos en una posición específica (ej: después de Ubicacion)
                columnas_a_mostrar.insert(4, 'LineaUltimaCompra')

            # Verificamos que las columnas existan
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

