import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium import Popup

# Configuración de la página
st.set_page_config(page_title="Dashboard de Óptica", layout="wide")

# Función para gestionar acceso de usuarios
def gestionar_acceso():
    st.sidebar.title("Acceso de Usuario")
    usuario = st.sidebar.text_input("Usuario")
    nivel_acceso = st.sidebar.selectbox("Nivel de Acceso", [1, 2, 3, 4, 5])
    if st.sidebar.button("Iniciar Sesión"):
        if usuario:
            st.session_state['usuario'] = usuario
            st.session_state['nivel_acceso'] = nivel_acceso
            st.sidebar.success(f"Acceso concedido: Nivel {nivel_acceso}")
        else:
            st.sidebar.error("Por favor, ingrese un usuario.")

# Inicializar estado de sesión
if 'usuario' not in st.session_state:
    gestionar_acceso()
    st.stop()

# Verificar nivel de acceso
nivel_acceso = st.session_state['nivel_acceso']
mostrar_valores_monetarios = nivel_acceso >= 5

# Título y subtítulo
st.title("Dashboard de Óptica")
st.subheader(f"Usuario: {st.session_state['usuario']} (Nivel {nivel_acceso})")

# Datos simulados (se generan una vez para evitar parpadeos)
st.session_state.setdefault('sucursales', ['Rosario', 'Capital Federal', 'San Nicolás - Savio', 'San Nicolás - Nación'])
st.session_state.setdefault('modelos', ['Modelo A', 'Modelo B', 'Modelo C', 'Modelo D', 'Modelo E'])
st.session_state.setdefault('ventas', np.random.randint(50, 200, size=(4, 5)))
st.session_state.setdefault('stock', np.random.randint(100, 500, size=(4, 5)))
st.session_state.setdefault('compras', np.random.randint(20, 100, size=(4, 5)))
st.session_state.setdefault('devoluciones', np.random.randint(5, 50, size=(4, 5)))

# Colores asignados a las sucursales
sucursal_colores = {
    'Rosario': 'blue',
    'Capital Federal': 'green',
    'San Nicolás - Savio': 'orange',
    'San Nicolás - Nación': 'red'
}

# Colores asignados a las métricas
metrica_colores = {
    'Ventas': 'lightblue',
    'Stock': 'lightgreen',
    'Compras': 'lightsalmon',
    'Devoluciones': 'lightcoral'
}

sucursales = st.session_state['sucursales']
modelos = st.session_state['modelos']
ventas = st.session_state['ventas']
stock = st.session_state['stock']
compras = st.session_state['compras']
devoluciones = st.session_state['devoluciones']

# Crear un DataFrame para los datos
data = pd.DataFrame({
    'Sucursal': np.repeat(sucursales, len(modelos)),
    'Modelo': np.tile(modelos, len(sucursales)),
    'Ventas': ventas.flatten(),
    'Stock': stock.flatten(),
    'Compras': compras.flatten(),
    'Devoluciones': devoluciones.flatten()
})

# Filtrar datos según nivel de acceso
if nivel_acceso == 1:
    data = data.drop(columns=['Ventas', 'Compras'])

# Ubicaciones de sucursales
ubicaciones = pd.DataFrame({
    'Sucursal': ['Rosario', 'Capital Federal', 'San Nicolás - Savio', 'San Nicolás - Nación'],
    'Dirección': ['Mitre 1100, Rosario, Santa Fe', 'Corrientes 1200, Capital Federal', 'Av. Savio y Nación, San Nicolás', 'Nación 400, San Nicolás'],
    'Latitud': [-32.94682, -34.60372, -33.33750, -33.33720],
    'Longitud': [-60.63932, -58.38162, -60.22655, -60.23000]
})

# Sidebar para opciones
st.sidebar.header("Filtros")
# Filtro de sucursales
sucursal_seleccionada = st.sidebar.multiselect("Seleccionar sucursales:", options=sucursales, default=sucursales)
# Filtro de modelos
modelo_seleccionado = st.sidebar.multiselect("Seleccionar modelos:", options=modelos, default=modelos)
# Filtro de métricas
metricas_seleccionadas = st.sidebar.multiselect("Seleccionar métricas:", options=['Ventas', 'Stock', 'Compras', 'Devoluciones'], default=['Ventas', 'Stock'])

# Filtrar datos
data_filtrada = data[(data['Sucursal'].isin(sucursal_seleccionada)) & (data['Modelo'].isin(modelo_seleccionado))]

# KPIs por métrica y adicionales
st.markdown("### KPIs por Métrica")
kpi_cols = st.columns(len(metricas_seleccionadas) + 3)
for i, metrica in enumerate(metricas_seleccionadas):
    kpi_value = data_filtrada[metrica].sum()
    if nivel_acceso == 1 and metrica in ['Ventas', 'Compras']:
        kpi_value = "N/A"
    kpi_cols[i].metric(f"{metrica} Totales", f"{kpi_value} unidades")
kpi_cols[len(metricas_seleccionadas)].metric("Promedio Ventas", f"{data_filtrada['Ventas'].mean():.2f} unidades" if mostrar_valores_monetarios else "N/A")
kpi_cols[len(metricas_seleccionadas) + 1].metric("Stock Promedio", f"{data_filtrada['Stock'].mean():.2f} unidades")
kpi_cols[len(metricas_seleccionadas) + 2].metric("Ratio Ventas/Devoluciones", f"{(data_filtrada['Ventas'].sum() / max(data_filtrada['Devoluciones'].sum(), 1)):.2f}" if mostrar_valores_monetarios else "N/A")

# Gráficos en una fila con tres columnas
st.markdown("### Gráficos")
graph_col1, graph_col2, graph_col3 = st.columns(3)

with graph_col1:
    st.markdown("#### Rendimiento por Sucursal y Métrica")
    fig, ax = plt.subplots(figsize=(6, 4))
    for metrica in metricas_seleccionadas:
        sucursal_data = data_filtrada.groupby('Sucursal')[metrica].sum()
        ax.bar(sucursal_data.index, sucursal_data, label=metrica, color=metrica_colores[metrica], alpha=0.7)
    ax.set_title("Por Sucursal")
    ax.set_ylabel("Unidades")
    ax.legend(title="Métricas")
    st.pyplot(fig)

with graph_col2:
    st.markdown("#### Rendimiento por Modelo y Métrica")
    fig, ax = plt.subplots(figsize=(6, 4))
    for metrica in metricas_seleccionadas:
        modelo_data = data_filtrada.groupby('Modelo')[metrica].sum()
        ax.bar(modelo_data.index, modelo_data, label=metrica, color=metrica_colores[metrica], alpha=0.7)
    ax.set_title("Por Modelo")
    ax.set_ylabel("Unidades")
    ax.legend(title="Métricas")
    st.pyplot(fig)

with graph_col3:
    st.markdown("#### Distribución por Sucursal")
    fig, ax = plt.subplots(figsize=(6, 4))
    for metrica in metricas_seleccionadas:
        sucursal_data = data_filtrada.groupby('Sucursal')[metrica].sum()
        explode = [0.1] * len(sucursal_data)
        ax.pie(sucursal_data, labels=sucursal_data.index, autopct='%1.1f%%', startangle=90, colors=[sucursal_colores[s] for s in sucursal_data.index], explode=explode)
    ax.set_title("Distribución")
    st.pyplot(fig)

# Mapa de sucursales
st.markdown("### Mapa de Sucursales")
mapa = folium.Map(location=[-33.0, -60.0], zoom_start=6)
for _, row in ubicaciones[ubicaciones['Sucursal'].isin(sucursal_seleccionada)].iterrows():
    sucursal_data = data_filtrada[data_filtrada['Sucursal'] == row['Sucursal']]
    popup_content = "<br>".join([f"{metrica}: {sucursal_data[metrica].sum()} unidades" for metrica in metricas_seleccionadas])
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=folium.Popup(f"<b>{row['Sucursal']}</b><br>{popup_content}", max_width=300),
        tooltip=row['Sucursal'],
        icon=folium.Icon(color=sucursal_colores[row['Sucursal']])
    ).add_to(mapa)

st_folium(mapa, width=700, height=500)

# Tabla de datos filtrados
st.markdown("### Detalles por Sucursal y Modelo")
st.dataframe(data_filtrada[['Sucursal', 'Modelo'] + metricas_seleccionadas])

# Mensaje final
st.sidebar.info("Usa los filtros para personalizar los datos mostrados.")
