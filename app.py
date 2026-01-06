import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Consulta de Cupos", layout="centered")

# --- TÍTULO Y DESCRIPCIÓN ---
st.title("🔍 Buscador de Cupos y Predios")
st.markdown("Ingrese el número de cédula para consultar el detalle de contratos y cupos disponibles.")

# --- CARGAR DATOS ---
# Usamos @st.cache_data para que el archivo se cargue una vez y la app sea rápida
@st.cache_data
def cargar_datos():
    # CAMBIA 'tu_archivo.xlsx' por el nombre real de tu archivo
    # Asegúrate de usar la hoja donde está el detalle (fila por contrato), NO el resumen
    df = pd.read_excel("base.xlsx") 
    
    # Aseguramos que la cédula sea texto para evitar problemas de búsqueda
    df['Identificacion'] = df['Identificacion'].astype(str)
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo de Excel. Asegúrate de subirlo al repositorio.")
    st.stop()

# --- INTERFAZ DE BÚSQUEDA ---
cedula_input = st.text_input("Digita la Cédula del Cliente:", placeholder="Ej: 100589...")

# --- LÓGICA DE FILTRADO ---
if cedula_input:
    # Filtramos el DF principal buscando la cédula
    # .str.strip() elimina espacios en blanco accidentales
    datos_cliente = df[df['Identificacion'].str.strip() == cedula_input.strip()]

    if not datos_cliente.empty:
        st.success(f"✅ Cliente encontrado: {datos_cliente['NombreSuscriptor'].iloc[0]}")
        
        st.divider() # Línea divisoria visual

        # --- FILTRO POR CIUDAD (MULTISELECT) ---
        # Obtenemos las ciudades únicas de ESTE cliente
        ciudades_disponibles = datos_cliente['Localidad'].unique()
        
        # Widget para seleccionar (por defecto selecciona todas)
        ciudades_seleccionadas = st.multiselect(
            "📍 Filtrar por Ciudad/Localidad:",
            options=ciudades_disponibles,
            default=ciudades_disponibles
        )

        # Filtramos los datos según la selección del usuario
        datos_visualizar = datos_cliente[datos_cliente['Localidad'].isin(ciudades_seleccionadas)]

        # --- CÁLCULOS DINÁMICOS ---
        total_cupo = datos_visualizar['CupoDisponible'].sum()
        cantidad_predios = len(datos_visualizar)

        # --- MOSTRAR MÉTRICAS (TARJETAS) ---
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🏠 Predios Seleccionados", f"{cantidad_predios}")
        with col2:
            # Formateamos como moneda ($)
            st.metric("💰 Cupo Disponible Total", f"${total_cupo:,.0f}")

        # --- MOSTRAR TABLA DETALLADA ---
        st.subheader("📋 Detalle de Contratos")
        
        # Seleccionamos solo las columnas relevantes para mostrar
        columnas_a_mostrar = ['Localidad', 'Ubicacion', 'CupoAsignado', 'CupoDisponible']
        st.dataframe(datos_visualizar[columnas_a_mostrar], use_container_width=True)

    else:

        st.warning("⚠️ No se encontró ninguna información para la cédula ingresada.")
