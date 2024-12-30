import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium import Popup

st.set_page_config(page_title="Dashboard de Óptica", layout="wide")

# Título y subtítulo
st.title("Dashboard de Óptica")
st.subheader("Visualiza los datos clave de ventas, stock y rendimiento de las sucursales")

# Datos simulados (se generan una vez para evitar parpadeos)
st.session_state.setdefault('sucursales', ['Rosario', 'Capital Federal', 'San Nicolás - Savio', 'San Nicolás - Nación'])
st.session_state.setdefault('ventas', np.random.randint(50, 200, size=4))
st.session_state.setdefault('stock', np.random.randint(100, 500, size=4))

sucursales = st.session_state['sucursales']
ventas = st.session_state['ventas']
stock = st.session_state['stock']

# Crear un DataFrame para ventas y stock
data = pd.DataFrame({
    'Sucursal': sucursales,
    'Ventas': ventas,
    'Stock': stock
})

# Ubicaciones de sucursales
ubicaciones = pd.DataFrame({
    'Sucursal': ['Rosario', 'Capital Federal', 'San Nicolás - Savio', 'San Nicolás - Nación'],
    'Dirección': ['Mitre 1100, Rosario, Santa Fe', 'Corrientes 1200, Capital Federal', 'Av. Savio y Nación, San Nicolás', 'Nación 400, San Nicolás'],
    'Latitud': [-32.94682, -34.60372, -33.33750, -33.33720],
    'Longitud': [-60.63932, -58.38162, -60.22655, -60.23000]
})

# Sidebar para opciones
st.sidebar.header("Opciones de visualización")
visualizar_stock = st.sidebar.checkbox("Mostrar Stock", value=True)
visualizar_ventas = st.sidebar.checkbox("Mostrar Ventas", value=True)

# KPIs principales
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
kpi_col1.metric("Ventas Totales", f"{data['Ventas'].sum()} unidades")
kpi_col2.metric("Stock Total", f"{data['Stock'].sum()} unidades")
kpi_col3.metric("Cantidad de Sucursales", len(sucursales))

# Gráficos
st.markdown("### Rendimiento por sucursal")
chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    st.markdown("#### Ventas por Sucursal")
    fig, ax = plt.subplots()
    ax.bar(data['Sucursal'], data['Ventas'], color='skyblue')
    ax.set_ylabel("Ventas")
    ax.set_title("Ventas por Sucursal")
    st.pyplot(fig)

with chart_col2:
    st.markdown("#### Stock por Sucursal")
    if visualizar_stock:
        fig, ax = plt.subplots()
        ax.bar(data['Sucursal'], data['Stock'], color='orange')
        ax.set_ylabel("Stock")
        ax.set_title("Stock por Sucursal")
        st.pyplot(fig)

with chart_col3:
    st.markdown("#### Distribución de Ventas")
    fig, ax = plt.subplots()
    ax.pie(data['Ventas'], labels=data['Sucursal'], autopct='%1.1f%%', explode=[0.1]*len(sucursales), startangle=90, colors=plt.cm.tab20c.colors)
    ax.set_title("Porcentaje de Ventas por Sucursal")
    st.pyplot(fig)

# Mapa de sucursales
st.markdown("### Mapa de Sucursales")
mapa = folium.Map(location=[-33.0, -60.0], zoom_start=6)
for _, row in ubicaciones.iterrows():
    match = data[data['Sucursal'] == row['Sucursal']]
    if not match.empty:
        ventas_sucursal = match['Ventas'].values[0]
        stock_sucursal = match['Stock'].values[0]
        popup_content = f"<b>{row['Sucursal']}</b><br>Dirección: {row['Dirección']}<br>Ventas: {ventas_sucursal} unidades<br>Stock: {stock_sucursal} unidades"
        popup = Popup(popup_content, max_width=300)
        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=popup,
            tooltip=row['Sucursal']
        ).add_to(mapa)

st_folium(mapa, width=700, height=500)

# Tablas
st.markdown("### Detalles por sucursal")
st.table(data if visualizar_ventas and visualizar_stock else data[['Sucursal', 'Ventas'] if visualizar_ventas else ['Sucursal', 'Stock']])

# Mensaje final
st.sidebar.info("Selecciona o deselecciona las métricas para personalizar el tablero.")
