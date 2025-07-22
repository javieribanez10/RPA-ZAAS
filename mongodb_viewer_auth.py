#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualizador Streamlit para datos extraídos de MongoDB desde test-nubox.
VERSIÓN CON AUTENTICACIÓN SUPABASE
Permite explorar y analizar los reportes contables almacenados solo a usuarios autenticados.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

# Importar componentes de autenticación
from ui.auth_components import require_authentication, render_user_menu

from services.mongodb_client import NuboxMongoClient

# Configuración de la página
st.set_page_config(
    page_title="DB Viewer - Nubox",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .data-summary {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_mongodb_data():
    """Carga datos desde MongoDB con caché."""
    try:
        mongo_client = NuboxMongoClient()
        
        if not mongo_client.connect():
            return None, "Error de conexión a MongoDB"
        
        # Obtener estadísticas generales
        stats = mongo_client.get_collection_stats()
        
        # Obtener todos los reportes (limitado para performance)
        collection = mongo_client.db[mongo_client.collection_name]
        cursor = collection.find({}).sort("metadata.fecha_extraccion", -1).limit(100)
        reportes = list(cursor)
        
        # Extraer lista de empresas disponibles para filtros
        empresas_disponibles = set()
        for reporte in reportes:
            empresa = reporte.get('empresa', {}).get('nombre', '')
            if empresa:
                empresas_disponibles.add(empresa)
        
        mongo_client.disconnect()
        
        return {"stats": stats, "reportes": reportes, "empresas_disponibles": sorted(empresas_disponibles)}, None
        
    except Exception as e:
        return None, str(e)

def apply_global_filters(data, filtros):
    """Aplica los filtros globales a los datos."""
    if not filtros or not data or not data.get("reportes"):
        return data
    
    reportes_filtrados = []
    
    fecha_desde = filtros.get('fecha_desde')
    fecha_hasta = filtros.get('fecha_hasta')
    fecha_filter_type = filtros.get('fecha_filter_type', 'Fecha de Extracción')
    empresas_seleccionadas = filtros.get('empresas', [])
    monto_minimo = filtros.get('monto_minimo', 0)
    
    for reporte in data["reportes"]:
        # Filtro por empresa
        empresa_nombre = reporte.get('empresa', {}).get('nombre', '')
        if empresas_seleccionadas and empresa_nombre not in empresas_seleccionadas:
            continue
        
        # Filtro por fecha
        fecha_coincide = False
        
        if fecha_filter_type == 'Fecha de Extracción':
            # Filtrar por fecha de extracción del reporte
            fecha_extraccion = reporte.get('metadata', {}).get('fecha_extraccion')
            if fecha_extraccion:
                try:
                    if isinstance(fecha_extraccion, str):
                        fecha_ext_date = datetime.datetime.fromisoformat(fecha_extraccion.replace('Z', '+00:00')).date()
                    else:
                        fecha_ext_date = fecha_extraccion.date()
                    
                    if fecha_desde <= fecha_ext_date <= fecha_hasta:
                        fecha_coincide = True
                except:
                    # Si hay error parseando la fecha, incluir el reporte
                    fecha_coincide = True
            else:
                fecha_coincide = True
        
        elif fecha_filter_type == 'Fecha de Movimientos':
            # Filtrar por fechas de los movimientos contables
            movimientos = reporte.get('movimientos', [])
            for movimiento in movimientos:
                fecha_mov = movimiento.get('fecha')
                if fecha_mov:
                    try:
                        if isinstance(fecha_mov, str):
                            fecha_mov_date = datetime.datetime.strptime(fecha_mov, '%Y-%m-%d').date()
                        else:
                            fecha_mov_date = fecha_mov.date()
                        
                        if fecha_desde <= fecha_mov_date <= fecha_hasta:
                            fecha_coincide = True
                            break
                    except:
                        continue
        
        if not fecha_coincide:
            continue
        
        # Filtro por monto mínimo
        if monto_minimo > 0:
            totales = reporte.get('reporte', {}).get('totales', {})
            total_debe = totales.get('total_debe', 0)
            total_haber = totales.get('total_haber', 0)
            monto_total = total_debe + total_haber
            
            if monto_total < monto_minimo:
                continue
        
        # Si pasa todos los filtros, incluir el reporte
        reportes_filtrados.append(reporte)
    
    # Crear nueva estructura de datos con reportes filtrados
    data_filtrada = {
        "stats": data["stats"],  # Mantener estadísticas generales
        "reportes": reportes_filtrados,
        "empresas_disponibles": data.get("empresas_disponibles", [])
    }
    
    return data_filtrada

def initialize_session_state():
    """Inicializa el estado de la sesión."""
    if 'selected_reporte' not in st.session_state:
        st.session_state.selected_reporte = None
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'dashboard'

def sidebar_controls(user_data):
    """Controles de la barra lateral con menú de usuario."""
    # Header con información del usuario autenticado
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
        text-align: center;
    ">
        <h3 style="margin: 0; color: white;">🔐 MongoDB Viewer</h3>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Acceso Autenticado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menú de usuario
    render_user_menu(user_data)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔧 Configuración")
    
    # Selector de vista
    view_mode = st.sidebar.radio(
        "Tipo de Vista",
        ["📊 Dashboard General", "📋 Explorador de Reportes", "💰 Análisis Financiero", "🔍 Búsqueda Avanzada"],
        key="view_selector"
    )
    
    # Mapear a valores simples
    view_mapping = {
        "📊 Dashboard General": "dashboard",
        "📋 Explorador de Reportes": "explorer", 
        "💰 Análisis Financiero": "financial",
        "🔍 Búsqueda Avanzada": "search"
    }
    
    st.session_state.view_mode = view_mapping[view_mode]
    
    # Controles de filtrado
    st.sidebar.markdown("### 🔍 Filtros Globales")
    
    # Filtros de fecha
    st.sidebar.markdown("#### 📅 Filtros de Fecha")
    
    # Tipo de filtro de fecha
    fecha_filter_type = st.sidebar.selectbox(
        "Tipo de fecha",
        ["Fecha de Extracción", "Fecha de Movimientos"],
        help="Filtrar por fecha de extracción del reporte o por fechas de los movimientos contables"
    )
    
    # Filtro por fecha de extracción/movimientos
    fecha_desde_global = st.sidebar.date_input(
        "📅 Desde",
        value=datetime.date(2025, 1, 1),
        help=f"Fecha inicial para filtrar por {fecha_filter_type.lower()}"
    )
    
    fecha_hasta_global = st.sidebar.date_input(
        "📅 Hasta", 
        value=datetime.date.today(),
        help=f"Fecha final para filtrar por {fecha_filter_type.lower()}"
    )
    
    # Validación de fechas
    if fecha_desde_global > fecha_hasta_global:
        st.sidebar.error("⚠️ La fecha 'desde' debe ser menor que la fecha 'hasta'")
        fecha_desde_global = fecha_hasta_global
    
    # Filtros adicionales
    st.sidebar.markdown("#### 🏢 Otros Filtros")
    
    # Filtro por empresa (se cargará dinámicamente)
    if 'empresas_disponibles' in st.session_state:
        empresas_global = st.sidebar.multiselect(
            "Empresas",
            options=st.session_state.empresas_disponibles,
            help="Selecciona empresas específicas (vacío = todas)"
        )
    else:
        empresas_global = []
    
    # Filtro por monto mínimo
    monto_minimo_global = st.sidebar.number_input(
        "💰 Monto mínimo",
        min_value=0.0,
        value=0.0,
        step=1000.0,
        help="Filtrar reportes con movimientos mayores a este monto"
    )
    
    # Botón para refrescar datos
    if st.sidebar.button("🔄 Refrescar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # Guardar filtros en session_state
    st.session_state.filtros_globales = {
        'fecha_filter_type': fecha_filter_type,
        'fecha_desde': fecha_desde_global,
        'fecha_hasta': fecha_hasta_global,
        'empresas': empresas_global,
        'monto_minimo': monto_minimo_global
    }
    
    return st.session_state.view_mode

def show_connection_status():
    """Muestra el estado de conexión a MongoDB."""
    try:
        mongo_client = NuboxMongoClient()
        connection_result = mongo_client.test_connection()
        
        if connection_result['connected']:
            st.success(f"✅ Conectado a MongoDB - Base de datos: `{connection_result['database_name']}` - Colección: `{connection_result['collection_name']}`")
        else:
            st.error(f"❌ Error de conexión: {connection_result.get('error', 'Error desconocido')}")
            return False
            
        mongo_client.disconnect()
        return True
        
    except Exception as e:
        st.error(f"❌ Error verificando conexión: {str(e)}")
        return False

# Importar las funciones originales del viewer (dashboard_view, explorer_view, etc.)
# Las copiamos aquí para mantener toda la funcionalidad
def dashboard_view(data):
    """Vista principal de dashboard."""
    st.markdown('<h2 class="section-header">📊 Dashboard General</h2>', unsafe_allow_html=True)
    
    stats = data["stats"]
    reportes = data["reportes"]
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📋 Total Reportes",
            stats.get('total_reportes', 0),
            help="Número total de reportes en la base de datos"
        )
    
    with col2:
        st.metric(
            "🏢 Empresas",
            stats.get('empresas_unicas', 0),
            help="Número de empresas diferentes"
        )
    
    with col3:
        st.metric(
            "📝 Total Movimientos",
            f"{stats.get('total_movimientos', 0):,}",
            help="Suma de todos los movimientos contables"
        )
    
    with col4:
        total_debe = stats.get('total_debe', 0)
        st.metric(
            "💰 Total DEBE",
            f"${total_debe:,.0f}",
            help="Suma total de movimientos DEBE"
        )
    
    # Información temporal
    if stats.get('primera_extraccion') and stats.get('ultima_extraccion'):
        col1, col2 = st.columns(2)
        
        with col1:
            primera = stats['primera_extraccion']
            if isinstance(primera, str):
                primera_str = primera
            else:
                primera_str = primera.strftime('%d/%m/%Y %H:%M')
            st.info(f"🕐 **Primera extracción**: {primera_str}")
        
        with col2:
            ultima = stats['ultima_extraccion']
            if isinstance(ultima, str):
                ultima_str = ultima
            else:
                ultima_str = ultima.strftime('%d/%m/%Y %H:%M')
            st.info(f"🕑 **Última extracción**: {ultima_str}")
    
    # Análisis de reportes recientes
    if reportes:
        st.markdown("### 📈 Análisis de Reportes Recientes")
        
        # Preparar datos para gráficos
        empresas_count = {}
        cuentas_count = {}
        movimientos_por_empresa = {}
        
        for reporte in reportes:
            # Contar por empresa
            empresa_nombre = reporte.get('empresa', {}).get('nombre', 'Sin nombre')
            empresas_count[empresa_nombre] = empresas_count.get(empresa_nombre, 0) + 1
            
            # Contar por cuenta
            cuenta = reporte.get('reporte', {}).get('cuenta_contable', 'Sin cuenta')
            cuentas_count[cuenta] = cuentas_count.get(cuenta, 0) + 1
            
            # Sumar movimientos por empresa
            num_movimientos = len(reporte.get('movimientos', []))
            if empresa_nombre not in movimientos_por_empresa:
                movimientos_por_empresa[empresa_nombre] = 0
            movimientos_por_empresa[empresa_nombre] += num_movimientos
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de reportes por empresa
            if empresas_count:
                df_empresas = pd.DataFrame(
                    list(empresas_count.items()),
                    columns=['Empresa', 'Reportes']
                ).sort_values('Reportes', ascending=True)
                
                fig_empresas = px.bar(
                    df_empresas,
                    x='Reportes',
                    y='Empresa',
                    orientation='h',
                    title="📊 Reportes por Empresa",
                    color='Reportes',
                    color_continuous_scale='Blues'
                )
                fig_empresas.update_layout(height=400)
                st.plotly_chart(fig_empresas, use_container_width=True)
        
        with col2:
            # Gráfico de cuentas más frecuentes
            if cuentas_count:
                # Tomar solo las top 10 cuentas
                top_cuentas = dict(sorted(cuentas_count.items(), key=lambda x: x[1], reverse=True)[:10])
                
                df_cuentas = pd.DataFrame(
                    list(top_cuentas.items()),
                    columns=['Cuenta', 'Reportes']
                )
                
                fig_cuentas = px.pie(
                    df_cuentas,
                    values='Reportes',
                    names='Cuenta',
                    title="💰 Top 10 Cuentas Contables"
                )
                fig_cuentas.update_traces(textposition='inside', textinfo='percent+label')
                fig_cuentas.update_layout(height=400)
                st.plotly_chart(fig_cuentas, use_container_width=True)
        
        # Timeline de extracciones
        st.markdown("### ⏱️ Timeline de Extracciones")
        
        fechas_extraccion = []
        for reporte in reportes:
            fecha_str = reporte.get('metadata', {}).get('fecha_extraccion')
            if fecha_str:
                try:
                    if isinstance(fecha_str, str):
                        fecha = datetime.datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    else:
                        fecha = fecha_str
                    fechas_extraccion.append(fecha.date())
                except:
                    pass
        
        if fechas_extraccion:
            df_timeline = pd.DataFrame(fechas_extraccion, columns=['Fecha'])
            df_timeline_count = df_timeline.groupby('Fecha').size().reset_index(name='Extracciones')
            
            fig_timeline = px.line(
                df_timeline_count,
                x='Fecha',
                y='Extracciones',
                title="📅 Extracciones por Día",
                markers=True
            )
            fig_timeline.update_layout(height=300)
            st.plotly_chart(fig_timeline, use_container_width=True)

def explorer_view(data):
    """Vista de explorador de reportes."""
    st.markdown('<h2 class="section-header">📋 Explorador de Reportes</h2>', unsafe_allow_html=True)
    
    reportes = data["reportes"]
    
    if not reportes:
        st.warning("⚠️ No se encontraron reportes en la base de datos.")
        return
    
    # Crear DataFrame para mostrar lista de reportes
    reportes_summary = []
    for i, reporte in enumerate(reportes):
        empresa = reporte.get('empresa', {})
        reporte_info = reporte.get('reporte', {})
        metadata = reporte.get('metadata', {})
        
        summary = {
            'Índice': i,
            'Empresa': empresa.get('nombre', 'Sin nombre'),
            'RUT': empresa.get('rut', 'Sin RUT'),
            'Cuenta Contable': reporte_info.get('cuenta_contable', 'Sin cuenta'),
            'Movimientos': len(reporte.get('movimientos', [])),
            'Total DEBE': reporte_info.get('totales', {}).get('total_debe', 0),
            'Total HABER': reporte_info.get('totales', {}).get('total_haber', 0),
            'Fecha Extracción': metadata.get('fecha_extraccion', 'Sin fecha')
        }
        reportes_summary.append(summary)
    
    df_reportes = pd.DataFrame(reportes_summary)
    
    # Filtros
    st.markdown("### 🔍 Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        empresas_disponibles = ['Todas'] + list(df_reportes['Empresa'].unique())
        empresa_filtro = st.selectbox("🏢 Empresa", empresas_disponibles)
    
    with col2:
        if empresa_filtro != 'Todas':
            cuentas_disponibles = ['Todas'] + list(df_reportes[df_reportes['Empresa'] == empresa_filtro]['Cuenta Contable'].unique())
        else:
            cuentas_disponibles = ['Todas'] + list(df_reportes['Cuenta Contable'].unique())
        cuenta_filtro = st.selectbox("💰 Cuenta Contable", cuentas_disponibles)
    
    with col3:
        min_movimientos = st.number_input("📝 Mín. Movimientos", min_value=0, value=0)
    
    # Aplicar filtros
    df_filtrado = df_reportes.copy()
    
    if empresa_filtro != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Empresa'] == empresa_filtro]
    
    if cuenta_filtro != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Cuenta Contable'] == cuenta_filtro]
    
    if min_movimientos > 0:
        df_filtrado = df_filtrado[df_filtrado['Movimientos'] >= min_movimientos]
    
    # Mostrar tabla filtrada
    st.markdown(f"### 📊 Reportes Encontrados ({len(df_filtrado)})")
    
    if not df_filtrado.empty:
        # Configurar columnas para mostrar
        columnas_mostrar = ['Empresa', 'Cuenta Contable', 'Movimientos', 'Total DEBE', 'Total HABER']
        
        # Formatear DataFrame para mostrar
        df_display = df_filtrado[columnas_mostrar].copy()
        df_display['Total DEBE'] = df_display['Total DEBE'].apply(lambda x: f"${x:,.0f}")
        df_display['Total HABER'] = df_display['Total HABER'].apply(lambda x: f"${x:,.0f}")
        
        # Mostrar tabla con selector simple
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Selector manual para ver detalles
        st.markdown("### 🔍 Ver Detalles de Reporte")
        
        # Crear opciones para el selectbox
        opciones_reportes = []
        for idx, row in df_filtrado.iterrows():
            empresa = row['Empresa']
            cuenta = row['Cuenta Contable']
            movimientos = row['Movimientos']
            opcion = f"{empresa} - {cuenta} ({movimientos} movimientos)"
            opciones_reportes.append((opcion, row['Índice']))
        
        if opciones_reportes:
            selected_option = st.selectbox(
                "Selecciona un reporte para ver detalles:",
                options=[opt[0] for opt in opciones_reportes],
                index=0,
                key="reporte_selector"
            )
            
            if selected_option:
                # Encontrar el índice del reporte seleccionado
                selected_idx = None
                for opcion, idx in opciones_reportes:
                    if opcion == selected_option:
                        selected_idx = idx
                        break
                
                if selected_idx is not None:
                    selected_reporte = reportes[selected_idx]
                    show_reporte_details(selected_reporte)
    else:
        st.info("ℹ️ No se encontraron reportes con los filtros aplicados.")

def financial_view(data):
    """Vista de análisis financiero."""
    st.markdown('<h2 class="section-header">💰 Análisis Financiero</h2>', unsafe_allow_html=True)
    
    reportes = data["reportes"]
    
    if not reportes:
        st.warning("⚠️ No se encontraron reportes para análisis.")
        return
    
    # Análisis de saldos por empresa
    st.markdown("### 📊 Análisis de Saldos por Empresa")
    
    saldos_empresa = {}
    movimientos_empresa = {}
    
    for reporte in reportes:
        empresa_nombre = reporte.get('empresa', {}).get('nombre', 'Sin nombre')
        totales = reporte.get('reporte', {}).get('totales', {})
        
        if empresa_nombre not in saldos_empresa:
            saldos_empresa[empresa_nombre] = {'debe': 0, 'haber': 0, 'saldo': 0}
            movimientos_empresa[empresa_nombre] = []
        
        debe = totales.get('total_debe', 0)
        haber = totales.get('total_haber', 0)
        saldo = debe - haber
        
        saldos_empresa[empresa_nombre]['debe'] += debe
        saldos_empresa[empresa_nombre]['haber'] += haber
        saldos_empresa[empresa_nombre]['saldo'] += saldo
        
        # Recopilar movimientos individuales
        for movimiento in reporte.get('movimientos', []):
            mov_debe = movimiento.get('debe', 0)
            mov_haber = movimiento.get('haber', 0)
            mov_fecha = movimiento.get('fecha')
            
            if mov_fecha:
                movimientos_empresa[empresa_nombre].append({
                    'fecha': mov_fecha,
                    'debe': mov_debe,
                    'haber': mov_haber,
                    'saldo': mov_debe - mov_haber
                })
    
    # Gráfico de saldos por empresa
    if saldos_empresa:
        df_saldos = pd.DataFrame.from_dict(saldos_empresa, orient='index').reset_index()
        df_saldos.columns = ['Empresa', 'DEBE', 'HABER', 'Saldo Neto']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de barras comparativo
            fig_comparativo = go.Figure(data=[
                go.Bar(name='DEBE', x=df_saldos['Empresa'], y=df_saldos['DEBE'], marker_color='lightcoral'),
                go.Bar(name='HABER', x=df_saldos['Empresa'], y=df_saldos['HABER'], marker_color='lightblue')
            ])
            
            fig_comparativo.update_layout(
                title="💰 DEBE vs HABER por Empresa",
                barmode='group',
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_comparativo, use_container_width=True)
        
        with col2:
            # Gráfico de saldo neto
            fig_saldo = px.bar(
                df_saldos,
                x='Empresa',
                y='Saldo Neto',
                title="📈 Saldo Neto por Empresa",
                color='Saldo Neto',
                color_continuous_scale=['red', 'white', 'green'],
                color_continuous_midpoint=0
            )
            fig_saldo.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_saldo, use_container_width=True)
    
    # Tabla resumen financiero
    st.markdown("### 📋 Resumen Financiero")
    
    if saldos_empresa:
        df_resumen = df_saldos.copy()
        df_resumen['DEBE'] = df_resumen['DEBE'].apply(lambda x: f"${x:,.0f}")
        df_resumen['HABER'] = df_resumen['HABER'].apply(lambda x: f"${x:,.0f}")
        df_resumen['Saldo Neto'] = df_resumen['Saldo Neto'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(df_resumen, use_container_width=True)
        
        # Métricas totales
        total_debe = sum(empresa['debe'] for empresa in saldos_empresa.values())
        total_haber = sum(empresa['haber'] for empresa in saldos_empresa.values())
        saldo_total = total_debe - total_haber
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💸 Total DEBE", f"${total_debe:,.0f}")
        with col2:
            st.metric("💰 Total HABER", f"${total_haber:,.0f}")
        with col3:
            delta_color = "normal" if saldo_total >= 0 else "inverse"
            st.metric("⚖️ Saldo Total", f"${saldo_total:,.0f}")

def search_view(data):
    """Vista de búsqueda avanzada."""
    st.markdown('<h2 class="section-header">🔍 Búsqueda Avanzada</h2>', unsafe_allow_html=True)
    
    reportes = data["reportes"]
    
    # Opciones de búsqueda
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 Criterios de Búsqueda")
        
        # Búsqueda por texto
        search_text = st.text_input("🔤 Buscar en glosas/comprobantes", placeholder="Ej: CENTRALIZACION, VENTA, etc.")
        
        # Búsqueda por rango de fechas
        fecha_desde = st.date_input("📅 Desde", value=datetime.date(2025, 1, 1))
        fecha_hasta = st.date_input("📅 Hasta", value=datetime.date.today())
        
        # Búsqueda por montos
        monto_min = st.number_input("💰 Monto mínimo", value=0.0, step=1000.0)
        monto_max = st.number_input("💰 Monto máximo", value=0.0, step=1000.0)
    
    with col2:
        st.markdown("#### 🏢 Filtros por Empresa")
        
        # Extraer todas las empresas
        empresas_disponibles = set()
        for reporte in reportes:
            empresa = reporte.get('empresa', {}).get('nombre', '')
            if empresa:
                empresas_disponibles.add(empresa)
        
        empresas_seleccionadas = st.multiselect(
            "Seleccionar empresas",
            options=sorted(empresas_disponibles),
            help="Deja vacío para buscar en todas las empresas"
        )
        
        # Filtro por tipo de movimiento
        tipo_movimiento = st.selectbox(
            "💸 Tipo de movimiento",
            ["Todos", "Solo DEBE", "Solo HABER", "Ambos (DEBE y HABER)"]
        )
    
    # Botón de búsqueda
    if st.button("🔍 Buscar", type="primary", use_container_width=True):
        resultados = perform_advanced_search(
            reportes, search_text, fecha_desde, fecha_hasta,
            monto_min, monto_max, empresas_seleccionadas, tipo_movimiento
        )
        
        if resultados:
            st.markdown(f"### 📊 Resultados de Búsqueda ({len(resultados)} movimientos encontrados)")
            
            # Convertir resultados a DataFrame
            df_resultados = pd.DataFrame(resultados)
            
            # Formatear columnas monetarias
            if 'debe' in df_resultados.columns:
                df_resultados['debe_formatted'] = df_resultados['debe'].apply(lambda x: f"${x:,.2f}")
            if 'haber' in df_resultados.columns:
                df_resultados['haber_formatted'] = df_resultados['haber'].apply(lambda x: f"${x:,.2f}")
            if 'saldo' in df_resultados.columns:
                df_resultados['saldo_formatted'] = df_resultados['saldo'].apply(lambda x: f"${x:,.2f}")
            
            # Seleccionar columnas para mostrar
            columnas_mostrar = ['fecha', 'empresa', 'cuenta', 'comprobante', 'glosa', 'debe_formatted', 'haber_formatted', 'saldo_formatted']
            columnas_existentes = [col for col in columnas_mostrar if col in df_resultados.columns]
            
            if columnas_existentes:
                st.dataframe(
                    df_resultados[columnas_existentes],
                    use_container_width=True,
                    height=400
                )
                
                # Estadísticas de resultados
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📝 Movimientos", len(resultados))
                
                with col2:
                    total_debe = sum(r.get('debe', 0) for r in resultados)
                    st.metric("💸 Total DEBE", f"${total_debe:,.0f}")
                
                with col3:
                    total_haber = sum(r.get('haber', 0) for r in resultados)
                    st.metric("💰 Total HABER", f"${total_haber:,.0f}")
                
                with col4:
                    saldo_neto = total_debe - total_haber
                    st.metric("⚖️ Saldo Neto", f"${saldo_neto:,.0f}")
                
                # Opciones de descarga
                st.markdown("### 💾 Descargar Resultados")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = df_resultados.to_csv(index=False)
                    st.download_button(
                        label="📄 Descargar CSV",
                        data=csv_data,
                        file_name=f"busqueda_avanzada_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Crear reporte JSON
                    reporte_json = {
                        'criterios_busqueda': {
                            'texto': search_text,
                            'fecha_desde': str(fecha_desde),
                            'fecha_hasta': str(fecha_hasta),
                            'monto_min': monto_min,
                            'monto_max': monto_max,
                            'empresas': empresas_seleccionadas,
                            'tipo_movimiento': tipo_movimiento
                        },
                        'resultados': resultados,
                        'estadisticas': {
                            'total_movimientos': len(resultados),
                            'total_debe': total_debe,
                            'total_haber': total_haber,
                            'saldo_neto': saldo_neto
                        }
                    }
                    
                    json_data = json.dumps(reporte_json, default=str, indent=2)
                    st.download_button(
                        label="📋 Descargar JSON",
                        data=json_data,
                        file_name=f"busqueda_avanzada_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        else:
            st.info("ℹ️ No se encontraron movimientos que coincidan con los criterios de búsqueda.")

def perform_advanced_search(reportes, search_text, fecha_desde, fecha_hasta, monto_min, monto_max, empresas_seleccionadas, tipo_movimiento):
    """Realiza búsqueda avanzada en los reportes."""
    resultados = []
    
    for reporte in reportes:
        empresa_nombre = reporte.get('empresa', {}).get('nombre', '')
        cuenta_contable = reporte.get('reporte', {}).get('cuenta_contable', '')
        
        # Filtro por empresa
        if empresas_seleccionadas and empresa_nombre not in empresas_seleccionadas:
            continue
        
        # Buscar en movimientos
        for movimiento in reporte.get('movimientos', []):
            # Extraer datos del movimiento
            fecha_mov = movimiento.get('fecha')
            comprobante = movimiento.get('comprobante', '')
            glosa = movimiento.get('glosa', '')
            debe = movimiento.get('debe', 0)
            haber = movimiento.get('haber', 0)
            saldo = movimiento.get('saldo', 0)
            
            # Filtro por texto
            if search_text:
                texto_busqueda = search_text.lower()
                if (texto_busqueda not in comprobante.lower() and 
                    texto_busqueda not in glosa.lower()):
                    continue
            
            # Filtro por fecha
            if fecha_mov:
                try:
                    if isinstance(fecha_mov, str):
                        fecha_mov_date = datetime.datetime.strptime(fecha_mov, '%Y-%m-%d').date()
                    else:
                        fecha_mov_date = fecha_mov.date()
                    
                    if fecha_mov_date < fecha_desde or fecha_mov_date > fecha_hasta:
                        continue
                except:
                    continue
            
            # Filtro por montos
            monto_total = debe + haber
            if monto_min > 0 and monto_total < monto_min:
                continue
            if monto_max > 0 and monto_total > monto_max:
                continue
            
            # Filtro por tipo de movimiento
            if tipo_movimiento == "Solo DEBE" and debe <= 0:
                continue
            elif tipo_movimiento == "Solo HABER" and haber <= 0:
                continue
            elif tipo_movimiento == "Ambos (DEBE y HABER)" and (debe <= 0 or haber <= 0):
                continue
            
            # Agregar a resultados
            resultado = {
                'fecha': fecha_mov,
                'empresa': empresa_nombre,
                'cuenta': cuenta_contable,
                'comprobante': comprobante,
                'glosa': glosa,
                'debe': debe,
                'haber': haber,
                'saldo': saldo
            }
            resultados.append(resultado)
    
    return resultados

def show_reporte_details(reporte):
    """Muestra detalles completos de un reporte."""
    # Información de la empresa
    empresa = reporte.get('empresa', {})
    st.markdown("#### 🏢 Información de la Empresa")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Nombre**: {empresa.get('nombre', 'N/A')}")
        st.write(f"**RUT**: {empresa.get('rut', 'N/A')}")
    
    with col2:
        st.write(f"**Representante Legal**: {empresa.get('representante_legal', 'N/A')}")
        st.write(f"**Giro Comercial**: {empresa.get('giro_comercial', 'N/A')}")
    
    # Información del reporte
    reporte_info = reporte.get('reporte', {})
    st.markdown("#### 📊 Información del Reporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Tipo**: {reporte_info.get('tipo', 'N/A')}")
        st.write(f"**Cuenta Contable**: {reporte_info.get('cuenta_contable', 'N/A')}")
    
    with col2:
        periodo = reporte_info.get('periodo', {})
        fecha_desde = periodo.get('fecha_desde', 'N/A')
        fecha_hasta = periodo.get('fecha_hasta', 'N/A')
        st.write(f"**Período**: {fecha_desde} - {fecha_hasta}")
    
    # Totales
    totales = reporte_info.get('totales', {})
    if totales:
        st.markdown("#### 💰 Totales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💸 Total DEBE", f"${totales.get('total_debe', 0):,.0f}")
        with col2:
            st.metric("💰 Total HABER", f"${totales.get('total_haber', 0):,.0f}")
        with col3:
            st.metric("📊 Saldo Final", f"${totales.get('saldo_final', 0):,.0f}")
        with col4:
            st.metric("📝 Movimientos", totales.get('total_movimientos', 0))
    
    # Movimientos
    movimientos = reporte.get('movimientos', [])
    if movimientos:
        st.markdown("#### 📋 Movimientos Contables")
        
        # Convertir movimientos a DataFrame
        df_movimientos = pd.DataFrame(movimientos)
        
        # Formatear columnas monetarias
        if 'debe' in df_movimientos.columns:
            df_movimientos['debe_formatted'] = df_movimientos['debe'].apply(lambda x: f"${x:,.2f}")
        if 'haber' in df_movimientos.columns:
            df_movimientos['haber_formatted'] = df_movimientos['haber'].apply(lambda x: f"${x:,.2f}")
        if 'saldo' in df_movimientos.columns:
            df_movimientos['saldo_formatted'] = df_movimientos['saldo'].apply(lambda x: f"${x:,.2f}")
        
        # Seleccionar columnas para mostrar
        columnas_mostrar = ['fecha', 'comprobante', 'glosa', 'debe_formatted', 'haber_formatted', 'saldo_formatted']
        columnas_existentes = [col for col in columnas_mostrar if col in df_movimientos.columns]
        
        if columnas_existentes:
            st.dataframe(
                df_movimientos[columnas_existentes],
                use_container_width=True,
                height=300
            )
        
        # Opciones de descarga para este reporte
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = df_movimientos.to_csv(index=False)
            empresa_nombre = empresa.get('nombre', 'empresa').replace(' ', '_')
            st.download_button(
                label="💾 Descargar CSV",
                data=csv_data,
                file_name=f"movimientos_{empresa_nombre}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Descargar reporte completo en JSON
            json_data = json.dumps(reporte, default=str, indent=2)
            st.download_button(
                label="📋 Descargar JSON",
                data=json_data,
                file_name=f"reporte_{empresa_nombre}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def main():
    """Función principal de la aplicación con autenticación."""
    # ✅ VERIFICAR AUTENTICACIÓN PRIMERO
    user_data = require_authentication()
    
    # Título con indicador de autenticación
    st.markdown('<h1 class="main-header">🔐 MongoDB Viewer - Reportes Nubox</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">Acceso Autenticado - Sistema RPA Integrado</p>', unsafe_allow_html=True)
    
    # Inicializar estado
    initialize_session_state()
    
    # Mostrar estado de conexión
    if not show_connection_status():
        st.stop()
    
    # Cargar datos
    data, error = load_mongodb_data()
    
    if error:
        st.error(f"❌ Error cargando datos: {error}")
        
        # Mostrar información de ayuda
        with st.expander("🔧 Información de Ayuda"):
            st.markdown("""
            ### Posibles soluciones:
            1. **Verificar conexión**: Asegúrate de que MongoDB esté disponible
            2. **Verificar credenciales**: Revisa la configuración de conexión
            3. **Instalar dependencias**: `pip install pymongo`
            4. **Ejecutar RPA primero**: Genera algunos reportes para visualizar
            """)
        st.stop()
    
    if not data or not data.get("reportes"):
        st.warning("⚠️ No hay datos disponibles en MongoDB.")
        
        st.markdown("""
        ### 💡 Para empezar:
        1. Ejecuta el RPA principal (`streamlit_app.py`) para generar reportes
        2. Los datos se exportarán automáticamente a MongoDB
        3. Regresa aquí para visualizar los datos extraídos
        """)
        st.stop()
    
    # Cargar empresas disponibles en session_state para los filtros
    if 'empresas_disponibles' not in st.session_state:
        st.session_state.empresas_disponibles = data.get("empresas_disponibles", [])
    
    # Controles de la barra lateral (con menú de usuario)
    view_mode = sidebar_controls(user_data)
    
    # Aplicar filtros globales después de que se hayan definido
    if hasattr(st.session_state, 'filtros_globales'):
        data = apply_global_filters(data, st.session_state.filtros_globales)
        
        # Mostrar información de filtros aplicados
        if st.session_state.filtros_globales:
            filtros_activos = []
            
            # Filtro de fecha
            fecha_desde = st.session_state.filtros_globales.get('fecha_desde')
            fecha_hasta = st.session_state.filtros_globales.get('fecha_hasta')
            fecha_tipo = st.session_state.filtros_globales.get('fecha_filter_type', 'Fecha de Extracción')
            
            if fecha_desde and fecha_hasta:
                filtros_activos.append(f"📅 {fecha_tipo}: {fecha_desde} - {fecha_hasta}")
            
            # Filtro de empresas
            empresas_filtro = st.session_state.filtros_globales.get('empresas', [])
            if empresas_filtro:
                filtros_activos.append(f"🏢 Empresas: {len(empresas_filtro)} seleccionadas")
            
            # Filtro de monto
            monto_min = st.session_state.filtros_globales.get('monto_minimo', 0)
            if monto_min > 0:
                filtros_activos.append(f"💰 Monto mínimo: ${monto_min:,.0f}")
            
            # Mostrar filtros activos
            if filtros_activos:
                st.info(f"🔍 **Filtros activos**: {' | '.join(filtros_activos)}")
    
    # Mostrar vista según selección
    if view_mode == "dashboard":
        dashboard_view(data)
    elif view_mode == "explorer":
        explorer_view(data)
    elif view_mode == "financial":
        financial_view(data)
    elif view_mode == "search":
        search_view(data)
    
    # Footer con información
    st.markdown("---")
    st.markdown("### 📋 Información del Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info(f"**Base de datos**: `nubox-data`")
    
    with col2:
        st.info(f"**Colección**: `test-nubox`")
    
    with col3:
        total_reportes = len(data.get('reportes', []))
        st.info(f"**Reportes mostrados**: {total_reportes}")
    
    with col4:
        total_empresas = len(data.get('empresas_disponibles', []))
        st.info(f"**Empresas disponibles**: {total_empresas}")

if __name__ == "__main__":
    main()