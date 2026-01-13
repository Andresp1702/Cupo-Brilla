import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Consulta de Cupos", layout="centered", page_icon="🔍")

# --- ESTILOS CSS (Opcional: Para mejorar la visualización de métricas) ---
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
    # CAMBIA 'base.xlsx' por el nombre real de tu archivo
    # Asegúrate de que las columnas existan tal cual en el Excel
    df = pd.read_excel("base_2.xlsx", dtype={'Identificacion': str})
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo 'base.xlsx'. Asegúrate de subirlo al repositorio.")
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
        # --- DATOS GENERALES DEL CLIENTE (Tomamos el primero encontrado) ---
        nombre = datos_cliente['NombreSuscriptor'].iloc[0]
        telefono = datos_cliente['UltimoTelefono'].iloc[0]
        segmento = datos_cliente['SegmentoClienteRFM'].iloc[0]

        # Manejo de valores nulos para mostrar texto limpio
        telefono_str = str(telefono) if pd.notna(telefono) else "No registrado"
        segmento_str = str(segmento) if pd.notna(segmento) else "Sin segmento"

        st.success(f"✅ Cliente: **{nombre}**")
        
        # Mostramos información extra en columnas pequeñas arriba
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

            # --- VISUALIZACIÓN DE MÉTRICAS (Lógica condicional) ---
            # Creamos 4 columnas potenciales
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)

            # Siempre mostramos la cantidad de predios
            m_col1.metric("🏠 Predios", f"{cantidad_predios}")

            # Solo mostramos Asignado si es mayor a 0
            if total_asignado > 0:
                m_col2.metric("💰 Asignado", f"${total_asignado:,.0f}")
            else:
                m_col2.empty() # Deja el espacio vacío o invisible

            # Solo mostramos Usado si es mayor a 0
            if total_usado > 0:
                m_col3.metric("📉 Usado", f"${total_usado:,.0f}")
            else:
                m_col3.empty()

            # Cupo Disponible (El más importante)
            m_col4.metric("✅ Disponible", f"${total_disponible:,.0f}")

            # --- TABLA DETALLADA ---
            st.subheader("📋 Detalle de Contratos y Compras")
            
            # Definimos las columnas que queremos ver en la tabla
            columnas_a_mostrar = [
                'Localidad', 
                'Subcategoria', 
                'Ubicacion', 
                'LineaUltimaCompra', 
                'CupoAsignado', 
                'CupoUsado',
                'CupoDisponible'
            ]
            
            # Verificamos que las columnas existan antes de mostrarlas para evitar errores
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

