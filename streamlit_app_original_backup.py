#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interfaz web con Streamlit para el RPA de Nubox.
Permite configurar parámetros de reportes de forma amigable.
"""

import streamlit as st
import pandas as pd
import datetime
import time
import sys
import os
import io
import logging
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from services.nubox_service import NuboxService
from config.settings import setup_config
from utils.logger import setup_logger

# Configurar logger global
logger = logging.getLogger("nubox_rpa.streamlit")

# Configuración de la página
st.set_page_config(
    page_title="RPA Nubox - Extractor de Reportes",
    page_icon="📊",
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
    .status-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inicializa el estado de la sesión de Streamlit."""
    if 'nubox_service' not in st.session_state:
        st.session_state.nubox_service = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'navigation_complete' not in st.session_state:
        st.session_state.navigation_complete = False
    if 'dropdown_options' not in st.session_state:
        st.session_state.dropdown_options = {}
    if 'report_generated' not in st.session_state:
        st.session_state.report_generated = False

def sidebar_configuration():
    """Configuración en la barra lateral."""
    st.sidebar.markdown("## ⚙️ Configuración")
    
    # Configuración del navegador
    st.sidebar.markdown("### Navegador")
    headless = st.sidebar.checkbox("Modo headless (sin ventana)", value=True, 
                                  help="Ejecutar el navegador en segundo plano")
    timeout = st.sidebar.slider("Timeout (segundos)", min_value=10, max_value=60, value=30,
                               help="Tiempo máximo de espera para operaciones")
    
    # Información del sistema
    st.sidebar.markdown("### 📋 Estado del Sistema")
    if st.session_state.logged_in:
        st.sidebar.success("✅ Conectado a Nubox")
    else:
        st.sidebar.error("❌ No conectado")
    
    if st.session_state.navigation_complete:
        st.sidebar.success("✅ Navegación completada")
    else:
        st.sidebar.warning("⏳ Esperando navegación")
    
    return headless, timeout

def login_section():
    """Sección de login."""
    st.markdown('<h2 class="section-header">🔐 Credenciales de Nubox</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("RUT de usuario", placeholder="12345678-9",
                                help="Ingresa tu RUT sin puntos, con guión")
    
    with col2:
        password = st.text_input("Contraseña", type="password",
                                help="Tu contraseña de Nubox")
    
    # URL personalizada (avanzado)
    with st.expander("⚙️ Configuración avanzada"):
        custom_url = st.text_input("URL de Nubox (opcional)", 
                                  value="https://web.nubox.com/Login/Account/Login?ReturnUrl=%2FSistemaLogin",
                                  help="URL personalizada de login")
    
    return username, password, custom_url

def report_parameters_section():
    """Sección de configuración de parámetros del reporte."""
    st.markdown('<h2 class="section-header">📊 Configuración del Reporte</h2>', unsafe_allow_html=True)
    
    # Configuración de fechas
    st.markdown("### 📅 Período del Reporte")
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input("Fecha desde", 
                                   value=datetime.date(2025, 1, 1),
                                   help="Fecha de inicio del reporte")
    
    with col2:
        fecha_hasta = st.date_input("Fecha hasta", 
                                   value=datetime.date.today(),
                                   help="Fecha de fin del reporte")
    
    # Dropdowns dinámicos
    st.markdown("### 🔽 Configuración de Parámetros")
    
    dropdown_selections = {}
    selected_accounts = []  # Para manejar múltiples cuentas
    selected_companies = []  # Para manejar múltiples empresas
    
    if st.session_state.dropdown_options:
        for dropdown_name, dropdown_info in st.session_state.dropdown_options.items():
            options = dropdown_info.get('options', [])
            current_selected = dropdown_info.get('selected', '')
            
            # Tratamiento especial para "Empresa" - permitir selección múltiple
            if dropdown_name == "Empresa":
                st.markdown("#### 🏢 Selección de Empresas")
                
                # Opción para seleccionar múltiples empresas
                multi_company_mode = st.checkbox(
                    "🏭 Generar reportes para múltiples empresas",
                    value=False,
                    help="Activa esta opción para seleccionar varias empresas y generar reportes para cada una",
                    key="multi_company_checkbox"
                )
                
                if multi_company_mode:
                    # Multiselect para empresas
                    selected_companies = st.multiselect(
                        "**Selecciona las empresas**",
                        options=options,
                        default=[current_selected] if current_selected in options else [],
                        help="Puedes seleccionar múltiples empresas. Se generarán reportes para cada combinación empresa-cuenta.",
                        key="multiselect_empresa"
                    )
                    
                    # Información sobre cuántos reportes se generarán (esto se actualizará después de seleccionar cuentas)
                    if selected_companies:
                        st.info(f"ℹ️ Empresas seleccionadas: **{len(selected_companies)}**")
                        
                        # Mostrar vista previa de las empresas seleccionadas
                        with st.expander("👀 Vista previa de empresas seleccionadas"):
                            for i, company in enumerate(selected_companies, 1):
                                st.write(f"{i}. {company}")
                        
                        # Para compatibilidad, usar la primera empresa como selección principal
                        dropdown_selections[dropdown_name] = selected_companies[0]
                    else:
                        st.warning("⚠️ Selecciona al menos una empresa.")
                        # Si no hay selección, usar la opción por defecto
                        dropdown_selections[dropdown_name] = current_selected
                        selected_companies = [current_selected] if current_selected else []
                else:
                    # Modo de una sola empresa (original)
                    try:
                        default_index = options.index(current_selected) if current_selected in options else 0
                    except ValueError:
                        default_index = 0
                    
                    selected_option = st.selectbox(
                        f"**{dropdown_name}**",
                        options=options,
                        index=default_index,
                        help=f"Selecciona una opción para {dropdown_name}",
                        key="selectbox_empresa"
                    )
                    
                    dropdown_selections[dropdown_name] = selected_option
                    selected_companies = [selected_option]  # Una sola empresa
                    
            # Tratamiento especial para "Cuenta Contable" - permitir selección múltiple
            elif dropdown_name == "Cuenta Contable":
                st.markdown("#### 💰 Selección de Cuentas Contables")
                
                # Opción para seleccionar múltiples cuentas
                multi_account_mode = st.checkbox(
                    "🔢 Generar reportes para múltiples cuentas",
                    value=False,
                    help="Activa esta opción para seleccionar varias cuentas y generar un reporte por cada una",
                    key="multi_account_checkbox"
                )
                
                if multi_account_mode:
                    # Multiselect para cuentas
                    selected_accounts = st.multiselect(
                        "**Selecciona las cuentas contables**",
                        options=options,
                        default=[current_selected] if current_selected in options else [],
                        help="Puedes seleccionar múltiples cuentas. Se generará un reporte por cada cuenta.",
                        key="multiselect_cuenta_contable"
                    )
                    
                    # Información sobre cuántos reportes se generarán
                    if selected_accounts:
                        # Calcular total de reportes basado en empresas y cuentas seleccionadas
                        total_reports = len(selected_companies) * len(selected_accounts)
                        st.info(f"ℹ️ Se generarán **{total_reports}** reportes total ({len(selected_companies)} empresas × {len(selected_accounts)} cuentas).")
                        
                        # Mostrar vista previa de las cuentas seleccionadas
                        with st.expander("👀 Vista previa de cuentas seleccionadas"):
                            for i, account in enumerate(selected_accounts, 1):
                                st.write(f"{i}. {account}")
                        
                        # Para compatibilidad, usar la primera cuenta como selección principal
                        dropdown_selections[dropdown_name] = selected_accounts[0]
                    else:
                        st.warning("⚠️ Selecciona al menos una cuenta contable.")
                        # Si no hay selección, usar la opción por defecto
                        dropdown_selections[dropdown_name] = current_selected
                        selected_accounts = [current_selected] if current_selected else []
                else:
                    # Modo de una sola cuenta (original)
                    try:
                        default_index = options.index(current_selected) if current_selected in options else 0
                    except ValueError:
                        default_index = 0
                    
                    selected_option = st.selectbox(
                        f"**{dropdown_name}**",
                        options=options,
                        index=default_index,
                        help=f"Selecciona una opción para {dropdown_name}",
                        key="selectbox_cuenta_contable"
                    )
                    
                    dropdown_selections[dropdown_name] = selected_option
                    selected_accounts = [selected_option]  # Una sola cuenta
            else:
                # Para otros dropdowns, mantener comportamiento original
                try:
                    default_index = options.index(current_selected) if current_selected in options else 0
                except ValueError:
                    default_index = 0
                
                selected_option = st.selectbox(
                    f"**{dropdown_name}**",
                    options=options,
                    index=default_index,
                    help=f"Selecciona una opción para {dropdown_name}",
                    key=f"dropdown_{dropdown_name.lower().replace(' ', '_')}"
                )
                
                dropdown_selections[dropdown_name] = selected_option
    else:
        st.info("ℹ️ Los parámetros se cargarán después de conectar con Nubox y navegar al reporte.")
    
    # Validaciones por defecto si no hay selecciones
    if not selected_accounts and st.session_state.dropdown_options:
        # Si no hay cuentas seleccionadas pero tenemos opciones, usar la primera como fallback
        cuenta_info = st.session_state.dropdown_options.get("Cuenta Contable", {})
        if cuenta_info.get('options'):
            selected_accounts = [cuenta_info['options'][0]]
            dropdown_selections["Cuenta Contable"] = cuenta_info['options'][0]
    
    if not selected_companies and st.session_state.dropdown_options:
        # Si no hay empresas seleccionadas pero tenemos opciones, usar la primera como fallback
        empresa_info = st.session_state.dropdown_options.get("Empresa", {})
        if empresa_info.get('options'):
            selected_companies = [empresa_info['options'][0]]
            dropdown_selections["Empresa"] = empresa_info['options'][0]
    
    # Mostrar resumen de la configuración múltiple si aplica
    if len(selected_companies) > 1 or len(selected_accounts) > 1:
        st.markdown("### 📋 Resumen de Configuración Múltiple")
        
        total_reports = len(selected_companies) * len(selected_accounts)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏢 Empresas", len(selected_companies))
        with col2:
            st.metric("💰 Cuentas", len(selected_accounts))
        with col3:
            st.metric("📊 Total Reportes", total_reports)
        
        if total_reports > 10:
            st.warning(f"⚠️ Se generarán {total_reports} reportes. Este proceso puede tomar considerable tiempo.")
        elif total_reports > 5:
            st.info(f"ℹ️ Se generarán {total_reports} reportes. El proceso será automático.")
        else:
            st.success(f"✅ Se generarán {total_reports} reportes.")
    
    return fecha_desde, fecha_hasta, dropdown_selections, selected_accounts, selected_companies

def progress_section():
    """Sección de progreso y logs."""
    st.markdown('<h2 class="section-header">📈 Progreso</h2>', unsafe_allow_html=True)
    
    # Contenedor para el progreso
    progress_container = st.container()
    
    # Contenedor para logs
    log_container = st.expander("📝 Ver logs detallados", expanded=False)
    
    return progress_container, log_container

def execute_rpa_process(username, password, custom_url, fecha_desde, fecha_hasta, 
                       dropdown_selections, selected_accounts, headless, timeout, progress_container, log_container):
    """Ejecuta el proceso RPA completo, con soporte para múltiples cuentas."""
    
    try:
        # Configurar logger
        logger = setup_logger()
        config = setup_config()
        
        # Determinar si es procesamiento múltiple
        is_multiple_accounts = len(selected_accounts) > 1
        
        with progress_container:
            # Barra de progreso general
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Paso 1: Inicializar servicio
            status_text.text("🔄 Inicializando servicio Nubox...")
            progress_bar.progress(5)
            
            if not st.session_state.nubox_service:
                st.session_state.nubox_service = NuboxService(headless=headless, timeout=timeout)
            
            with log_container:
                st.text("✅ Servicio Nubox inicializado")
            
            # Paso 2: Login
            if not st.session_state.logged_in:
                status_text.text("🔐 Iniciando sesión en Nubox...")
                progress_bar.progress(15)
                
                login_success = st.session_state.nubox_service.login(username, password, custom_url)
                
                if login_success:
                    st.session_state.logged_in = True
                    with log_container:
                        st.text("✅ Login exitoso")
                    
                    st.success("🎉 ¡Conectado exitosamente a Nubox!")
                else:
                    with log_container:
                        st.text("❌ Error en login")
                    st.error("❌ Error al conectar con Nubox. Verifica tus credenciales.")
                    return False
            
            # Paso 3: Navegación
            if not st.session_state.navigation_complete:
                status_text.text("🧭 Navegando al reporte Mayor...")
                progress_bar.progress(25)
                
                navigation_success = st.session_state.nubox_service.navigate_to_report()
                
                if navigation_success:
                    st.session_state.navigation_complete = True
                    with log_container:
                        st.text("✅ Navegación completada")
                    
                    # Cargar opciones de dropdowns
                    status_text.text("📋 Cargando opciones de parámetros...")
                    progress_bar.progress(35)
                    
                    load_dropdown_options()
                    
                    with log_container:
                        st.text("✅ Opciones de parámetros cargadas")
                    
                    st.success("🎯 ¡Navegación completada! Ahora puedes configurar los parámetros del reporte.")
                    st.rerun()
                    
                else:
                    with log_container:
                        st.text("❌ Error en navegación")
                    st.error("❌ Error al navegar al reporte. Intenta nuevamente.")
                    return False
            
            # Verificar que tengamos parámetros de configuración
            if not st.session_state.navigation_complete or not dropdown_selections:
                st.warning("⚠️ Primero debes completar la navegación y configurar los parámetros.")
                return False
            
            # Preparar parámetros base
            base_params = {
                'fecha_desde': fecha_desde.strftime("%d/%m/%Y"),
                'fecha_hasta': fecha_hasta.strftime("%d/%m/%Y"),
                'dropdown_selections': dropdown_selections
            }
            
            # Procesar según el modo (una cuenta o múltiples)
            if is_multiple_accounts:
                # MODO MÚLTIPLES CUENTAS
                status_text.text(f"📊 Procesando {len(selected_accounts)} cuentas contables...")
                progress_bar.progress(45)
                
                with log_container:
                    st.text(f"🔢 Iniciando procesamiento de {len(selected_accounts)} cuentas")
                    for i, account in enumerate(selected_accounts, 1):
                        st.text(f"  {i}. {account}")
                
                # Llamar al método de extracción múltiple
                results = st.session_state.nubox_service.extract_multiple_reports_by_account(
                    base_params, selected_accounts
                )
                
                progress_bar.progress(95)
                
                # Procesar y mostrar resultados múltiples
                if results and '_summary' in results:
                    summary = results['_summary']
                    
                    with log_container:
                        st.text(f"✅ Extracción completada:")
                        st.text(f"  - Total de cuentas: {summary['total_accounts']}")
                        st.text(f"  - Exitosas: {summary['successful_extractions']}")
                        st.text(f"  - Fallidas: {summary['failed_extractions']}")
                        st.text(f"  - Tasa de éxito: {summary['success_rate']:.1f}%")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ ¡Proceso de múltiples reportes completado!")
                    
                    # Mostrar resultados múltiples
                    show_multiple_results(results, selected_accounts)
                    
                    return True
                else:
                    with log_container:
                        st.text("❌ Error en la extracción de reportes múltiples")
                    st.error("❌ No se pudieron extraer los reportes.")
                    return False
                    
            else:
                # MODO UNA SOLA CUENTA
                status_text.text("⚙️ Configurando parámetros del reporte...")
                progress_bar.progress(50)
                
                # Configurar parámetros usando el método automatizado
                config_success = configure_parameters_programmatically(base_params, log_container)
                
                if config_success:
                    with log_container:
                        st.text("✅ Parámetros configurados correctamente")
                    progress_bar.progress(75)
                else:
                    with log_container:
                        st.text("❌ Error al configurar parámetros")
                    st.error("❌ Error al configurar parámetros del reporte.")
                    return False
                
                # Generar y extraer reporte único
                status_text.text("📊 Generando y extrayendo reporte...")
                progress_bar.progress(90)
                
                report_data = st.session_state.nubox_service.extract_report()
                
                if isinstance(report_data, tuple):
                    df, file_path = report_data
                else:
                    df = report_data
                    file_path = None
                
                progress_bar.progress(100)
                status_text.text("✅ ¡Proceso completado!")
                
                with log_container:
                    st.text("✅ Reporte extraído exitosamente")
                
                st.session_state.report_generated = True
                
                # Mostrar resultados únicos
                show_results(df, file_path)
                
                return True
            
    except Exception as e:
        with log_container:
            st.text(f"❌ Error general: {str(e)}")
        st.error(f"❌ Error durante la ejecución: {str(e)}")
        return False

def load_dropdown_options():
    """Extrae las opciones de dropdowns dinámicamente desde Nubox."""
    try:
        # Extraer opciones reales de la página de Nubox
        if st.session_state.nubox_service:
            logger.info("Extrayendo opciones de dropdowns de la página de Nubox")
            dropdown_options = st.session_state.nubox_service.extract_dropdown_options()
            
            if dropdown_options:
                st.session_state.dropdown_options = dropdown_options
                logger.info(f"Opciones de dropdowns extraídas exitosamente: {len(dropdown_options)} dropdowns")
                return True
            else:
                logger.warning("No se pudieron extraer opciones reales, usando opciones de respaldo")
                # Fallback con opciones simuladas si no se pueden extraer
                st.session_state.dropdown_options = {
                    "Empresa": {
                        "options": [
                            "051, VERSE CONSULTORES LTDA",
                            "205, INSTITUTO DE CAP. Y GESTION SPA", 
                            "282, SUGA SPA",
                            "527, PUNTO HUMANO SPA",
                            "586, SERV. EMPRESARIALES INSERT PRO SPA",
                            "689, DELSO SPA",
                            "796, INVERSIONES LAS TRALCAS SPA",
                            "838, SERV. ASESORIAS EMP. NRED SPA",
                            "903, COMERCIALIZADORA INSERT S.A.",
                            "904, UAU TELECOM SPA",
                            "905, Paulo Subiabre Cepeda E. Individual",
                            "906, SELYT SPA"
                        ],
                        "selected": "051, VERSE CONSULTORES LTDA",
                        "name": "ComboEmpresa",
                        "index": 0
                    },
                    "Tipo de Reporte": {
                        "options": [
                            "ANALISIS POR CUENTA",
                            "BORRADOR", 
                            "OFICIAL SIN NOMBRE",
                            "OFICIAL CON NOMBRE"
                        ],
                        "selected": "ANALISIS POR CUENTA",
                        "name": "ComboTipoReporte",
                        "index": 1
                    },
                    "Formato de Salida": {
                        "options": ["PDF", "EXCEL"],
                        "selected": "PDF",
                        "name": "ComboFormato",
                        "index": 2
                    },
                    "Cuenta Contable": {
                        "options": [
                            "1101-01 CUENTA CAJA",
                            "1101-02 BANCO SANTANDER",
                            "1101-03 BANCO BCI",
                            "1104-01 CLIENTES NACIONALES",
                            "5101-01 VENTAS POR SERVICIO",
                            "4201-01 ARRIENDOS OFICINAS"
                        ],
                        "selected": "1101-01 CUENTA CAJA",
                        "name": "ComboCodigoSubcuenta",
                        "index": 3
                    },
                    "Incluir Subcuentas": {
                        "options": ["NO", "SI"],
                        "selected": "NO",
                        "name": "ComboIncluirSubcuentas",
                        "index": 4
                    }
                }
                logger.info("Usando opciones de respaldo predefinidas")
                return True
        else:
            logger.error("Servicio Nubox no disponible para extraer opciones")
            return False
    except Exception as e:
        logger.error(f"Error cargando opciones de dropdowns: {str(e)}")
        st.error(f"Error cargando opciones de dropdowns: {str(e)}")
        return False

def configure_parameters_programmatically(params, log_container):
    """Configura los parámetros del reporte de forma programática."""
    try:
        # Crear un objeto de parámetros que el servicio pueda usar
        service_params = {
            'fecha_desde': params['fecha_desde'],  # Cambiar de 'nueva_fecha_desde' a 'fecha_desde'
            'fecha_hasta': params.get('fecha_hasta'),  # Cambiar de 'nueva_fecha_hasta' a 'fecha_hasta'
            'dropdown_selections': params['dropdown_selections']
        }
        
        with log_container:
            st.text(f"📅 Configurando fecha desde: {params['fecha_desde']}")
            if params.get('fecha_hasta'):
                st.text(f"📅 Configurando fecha hasta: {params['fecha_hasta']}")
            for dropdown, selection in params['dropdown_selections'].items():
                st.text(f"🔽 {dropdown}: {selection}")
        
        # Llamar al método programático del servicio
        success = st.session_state.nubox_service.set_report_parameters_programmatic(service_params)
        
        if success:
            with log_container:
                st.text("✅ Configuración programática completada exitosamente")
        else:
            with log_container:
                st.text("❌ Error en la configuración programática")
        
        return success
        
    except Exception as e:
        with log_container:
            st.text(f"❌ Error configurando parámetros: {str(e)}")
        return False

def show_multiple_results(results, selected_accounts):
    """Muestra los resultados de múltiples reportes extraídos con exportación automática a MongoDB."""
    st.markdown('<h2 class="section-header">📊 Resultados de Múltiples Reportes</h2>', unsafe_allow_html=True)
    
    if not results or '_summary' not in results:
        st.error("❌ No se obtuvieron resultados válidos de los reportes múltiples.")
        return
    
    summary = results['_summary']
    
    # Mostrar resumen general
    st.markdown("### 📈 Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Cuentas", summary['total_accounts'])
    with col2:
        st.metric("✅ Exitosas", summary['successful_extractions'])
    with col3:
        st.metric("❌ Fallidas", summary['failed_extractions'])
    with col4:
        st.metric("📈 Tasa de Éxito", f"{summary['success_rate']:.1f}%")
    
    # Mostrar estado visual
    if summary['success_rate'] >= 80:
        st.success(f"🎉 ¡Excelente! Se procesaron exitosamente {summary['successful_extractions']} de {summary['total_accounts']} cuentas.")
    elif summary['success_rate'] >= 50:
        st.warning(f"⚠️ Se procesaron {summary['successful_extractions']} de {summary['total_accounts']} cuentas. Revisa las que fallaron.")
    else:
        st.error(f"❌ Solo se procesaron {summary['successful_extractions']} de {summary['total_accounts']} cuentas exitosamente.")
    
    # Separar resultados exitosos y fallidos
    successful_results = []
    failed_results = []
    
    for account in selected_accounts:
        if account in results and account != '_summary':
            result = results[account]
            if result.get('success', False):
                successful_results.append((account, result))
            else:
                failed_results.append((account, result))
    
    # EXPORTACIÓN AUTOMÁTICA A MONGODB PARA REPORTES MÚLTIPLES
    if successful_results:
        st.markdown("### 🚀 Exportación Automática a MongoDB")
        
        with st.spinner(f"Exportando {len(successful_results)} reportes a MongoDB..."):
            try:
                from services.mongodb_client import NuboxMongoClient
                
                mongo_client = NuboxMongoClient()
                export_summary = {
                    'total_reportes': len(successful_results),
                    'exportados_exitosos': 0,
                    'exportados_fallidos': 0,
                    'document_ids': [],
                    'errores': []
                }
                
                # Exportar cada reporte exitoso
                for account, result in successful_results:
                    try:
                        df = result.get('data')
                        if df is not None and not df.empty:
                            # Extraer información de la empresa desde los atributos del DataFrame
                            company_info = df.attrs.get('company_info', {}) if hasattr(df, 'attrs') else {}
                            
                            # Preparar metadatos específicos para esta cuenta
                            report_metadata = {
                                'archivo_origen': os.path.basename(result.get('file_path', '')) or 'streamlit_multiple_extraction',
                                'cuenta_contable': account,  # Usar la cuenta específica
                                'fecha_extraccion': datetime.datetime.now().isoformat(),
                                'parametros_streamlit': {
                                    'formato_salida': 'EXCEL',
                                    'include_subcuentas': st.session_state.get('dropdown_options', {}).get('Incluir Subcuentas', {}).get('selected', 'NO'),
                                    'procesamiento_multiple': True,
                                    'total_cuentas_procesadas': len(successful_results)
                                }
                            }
                            
                            # Exportar a MongoDB
                            export_result = mongo_client.export_nubox_dataframe(
                                df=df,
                                company_info=company_info,
                                report_metadata=report_metadata
                            )
                            
                            if export_result['success']:
                                export_summary['exportados_exitosos'] += 1
                                export_summary['document_ids'].append({
                                    'cuenta': account,
                                    'document_id': export_result['document_id'],
                                    'filas': export_result['exported_rows']
                                })
                            else:
                                export_summary['exportados_fallidos'] += 1
                                export_summary['errores'].append({
                                    'cuenta': account,
                                    'errores': export_result['errors']
                                })
                        else:
                            export_summary['exportados_fallidos'] += 1
                            export_summary['errores'].append({
                                'cuenta': account,
                                'errores': ['DataFrame vacío o no disponible']
                            })
                            
                    except Exception as e:
                        export_summary['exportados_fallidos'] += 1
                        export_summary['errores'].append({
                            'cuenta': account,
                            'errores': [str(e)]
                        })
                
                mongo_client.disconnect()
                
                # Mostrar resultado de la exportación masiva
                if export_summary['exportados_exitosos'] > 0:
                    st.success(f"✅ **{export_summary['exportados_exitosos']} reportes exportados exitosamente a MongoDB**")
                    
                    # Mostrar detalles de la exportación múltiple
                    with st.expander("📋 Detalles de la Exportación Masiva", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("📊 Reportes Exportados", export_summary['exportados_exitosos'])
                        with col2:
                            st.metric("❌ Fallos de Exportación", export_summary['exportados_fallidos'])
                        with col3:
                            total_filas = sum(doc['filas'] for doc in export_summary['document_ids'])
                            st.metric("📝 Total Filas", total_filas)
                        with col4:
                            st.metric("📅 Fecha", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
                        
                        st.write("**IDs de Documentos Exportados:**")
                        for doc_info in export_summary['document_ids']:
                            st.write(f"- **{doc_info['cuenta']}**: `{doc_info['document_id']}` ({doc_info['filas']} filas)")
                        
                        st.write(f"**Colección**: `test-nubox`")
                        st.write(f"**Base de Datos**: `buk-data`")
                        
                        if export_summary['errores']:
                            st.write("**Errores de Exportación:**")
                            for error_info in export_summary['errores']:
                                st.write(f"- **{error_info['cuenta']}**: {', '.join(error_info['errores'])}")
                
                else:
                    st.error("❌ **No se pudo exportar ningún reporte a MongoDB**")
                    if export_summary['errores']:
                        st.write("**Errores encontrados:**")
                        for error_info in export_summary['errores']:
                            st.write(f"- **{error_info['cuenta']}**: {', '.join(error_info['errores'])}")
                
            except ImportError:
                st.warning("⚠️ Cliente MongoDB no disponible. Instalar con: `pip install pymongo`")
            except Exception as e:
                st.error(f"❌ Error durante la exportación masiva: {str(e)}")
    
    # Mostrar resultados exitosos
    if successful_results:
        st.markdown("### ✅ Reportes Exitosos")
        
        # Crear tabs para cada reporte exitoso
        tab_names = []
        tab_data = []
        
        for i, (account, result) in enumerate(successful_results):
            # Crear nombre corto para la tab
            account_code = result.get('account_code', f'cuenta_{i+1}')
            tab_names.append(f"📊 {account_code}")
            tab_data.append((account, result))
        
        if len(tab_names) > 0:
            tabs = st.tabs(tab_names)
            
            for i, (tab, (account, result)) in enumerate(zip(tabs, tab_data)):
                with tab:
                    st.markdown(f"**Cuenta:** {account}")
                    
                    # Métricas del reporte individual
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📊 Filas", result.get('rows_count', 0))
                    with col2:
                        st.metric("📋 Columnas", result.get('columns_count', 0))
                    with col3:
                        file_status = "Descargado" if result.get('file_path') else "En memoria"
                        st.metric("📁 Archivo", file_status)
                    
                    # Mostrar preview de los datos si están disponibles
                    df = result.get('data')
                    if df is not None and not df.empty:
                        st.markdown("**Vista previa de los datos:**")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        # Botones de descarga para este reporte
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Descargar CSV
                            csv_data = df.to_csv(index=False)
                            account_code = result.get('account_code', combination_key.replace(' ', '_'))
                            st.download_button(
                                label="💾 Descargar CSV",
                                data=csv_data,
                                file_name=f"reporte_{account_code}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key=f"csv_{combination_key}"
                            )
                        
                        with col2:
                            # Descargar Excel
                            excel_buffer = io.BytesIO()
                            df.to_excel(excel_buffer, index=False, engine='openpyxl')
                            excel_data = excel_buffer.getvalue()
                            
                            st.download_button(
                                label="📊 Descargar Excel",
                                data=excel_data,
                                file_name=f"reporte_{account_code}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"excel_{combination_key}"
                            )
                    else:
                        st.info("ℹ️ No hay datos para mostrar, pero el archivo fue descargado exitosamente.")
                    
                    # Mostrar información del archivo descargado
                    file_path = result.get('file_path')
                    if file_path and file_path != "Descarga no encontrada":
                        st.info(f"📁 Archivo descargado en: {file_path}")
    
    # Mostrar resultados fallidos
    if failed_results:
        st.markdown("### ❌ Reportes Fallidos")
        
        with st.expander(f"Ver detalles de {len(failed_results)} reportes fallidos", expanded=len(successful_results) == 0):
            for account, result in failed_results:
                error_msg = result.get('error', 'Error desconocido')
                st.error(f"**{account}**: {error_msg}")
    
    # Opción para descargar resumen completo
    st.markdown("### 📋 Descarga del Resumen Completo")
    
    if successful_results:
        # Crear DataFrame combinado con información de resumen
        summary_data = []
        
        for account, result in successful_results + failed_results:
            summary_data.append({
                'Cuenta': account,
                'Código': result.get('account_code', ''),
                'Estado': 'Exitoso' if result.get('success', False) else 'Fallido',
                'Filas': result.get('rows_count', 0),
                'Columnas': result.get('columns_count', 0),
                'Archivo': result.get('file_path', '') if result.get('file_path') and result.get('file_path') != "Descarga no encontrada" else '',
                'Error': result.get('error', '') if not result.get('success', False) else ''
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar resumen en CSV
            summary_csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📄 Descargar Resumen CSV",
                data=summary_csv,
                file_name=f"resumen_reportes_multiples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Descargar resumen en Excel
            summary_excel_buffer = io.BytesIO()
            summary_df.to_excel(summary_excel_buffer, index=False, engine='openpyxl')
            summary_excel_data = summary_excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Resumen Excel",
                data=summary_excel_data,
                file_name=f"resumen_reportes_multiples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Mostrar tabla de resumen
        st.markdown("**Vista previa del resumen:**")
        st.dataframe(summary_df, use_container_width=True)

def show_results(df, file_path=None):
    """Muestra los resultados del reporte extraído con análisis mejorado y exportación automática a MongoDB."""
    st.markdown('<h2 class="section-header">📊 Resultados del Reporte</h2>', unsafe_allow_html=True)
    
    if not df.empty:
        # Exportación automática a MongoDB
        st.markdown("### 🚀 Exportación Automática a MongoDB")
        
        with st.spinner("Exportando datos a MongoDB..."):
            try:
                from services.mongodb_client import NuboxMongoClient
                
                # Extraer información de la empresa desde los atributos del DataFrame
                company_info = df.attrs.get('company_info', {}) if hasattr(df, 'attrs') else {}
                
                # Preparar metadatos del reporte
                report_metadata = {
                    'archivo_origen': os.path.basename(file_path) if file_path else 'streamlit_extraction',
                    'cuenta_contable': st.session_state.get('dropdown_options', {}).get('Cuenta Contable', {}).get('selected', ''),
                    'fecha_extraccion': datetime.datetime.now().isoformat(),
                    'parametros_streamlit': {
                        'formato_salida': 'EXCEL',
                        'include_subcuentas': st.session_state.get('dropdown_options', {}).get('Incluir Subcuentas', {}).get('selected', 'NO')
                    }
                }
                
                # Crear cliente MongoDB y exportar
                mongo_client = NuboxMongoClient()
                export_result = mongo_client.export_nubox_dataframe(
                    df=df,
                    company_info=company_info,
                    report_metadata=report_metadata
                )
                
                if export_result['success']:
                    st.success(f"✅ **Datos exportados exitosamente a MongoDB**")
                    
                    # Mostrar detalles de la exportación en un expandidor
                    with st.expander("📋 Detalles de la Exportación", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("📊 Filas Exportadas", export_result['exported_rows'])
                        with col2:
                            st.metric("🏢 Empresa", company_info.get('Nombre', 'N/A'))
                        with col3:
                            st.metric("📅 Fecha", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
                        
                        st.write(f"**ID del Documento**: `{export_result['document_id']}`")
                        st.write(f"**Colección**: `{export_result['collection_name']}`")
                        st.write(f"**Base de Datos**: `nubox-data`")
                        
                        if company_info:
                            st.write("**Información de Empresa Exportada**:")
                            for key, value in company_info.items():
                                st.write(f"- **{key}**: {value}")
                else:
                    st.error("❌ **Error en la exportación a MongoDB**")
                    if export_result['errors']:
                        st.write("**Errores encontrados**:")
                        for error in export_result['errors']:
                            st.write(f"- {error}")
                
                mongo_client.disconnect()
                
            except ImportError:
                st.warning("⚠️ Cliente MongoDB no disponible. Instalar con: `pip install pymongo`")
            except Exception as e:
                st.error(f"❌ Error durante la exportación: {str(e)}")

        # Mostrar información del DataFrame
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Filas", len(df))
        with col2:
            st.metric("📋 Columnas", len(df.columns))
        with col3:
            if file_path:
                st.metric("📁 Archivo", "Descargado")
            else:
                st.metric("📁 Archivo", "En memoria")
        with col4:
            # Calcular tamaño estimado en MB
            size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            st.metric("💾 Tamaño", f"{size_mb:.2f} MB")

        # Análisis rápido del DataFrame
        st.markdown("### 📈 Análisis Rápido")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Información de tipos de datos
            with st.expander("🔍 Tipos de Datos"):
                types_info = df.dtypes.value_counts()
                for dtype, count in types_info.items():
                    st.write(f"**{dtype}**: {count} columnas")
        
        with col2:
            # Información de valores nulos
            with st.expander("❌ Valores Nulos"):
                null_counts = df.isnull().sum()
                null_cols = null_counts[null_counts > 0]
                if len(null_cols) > 0:
                    for col, count in null_cols.items():
                        percentage = (count / len(df)) * 100
                        st.write(f"**{col}**: {count} ({percentage:.1f}%)")
                else:
                    st.write("✅ No hay valores nulos")

        # Filtros para el DataFrame
        st.markdown("### 🔍 Filtros y Exploración")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por número de filas a mostrar
            rows_to_show = st.selectbox(
                "Filas a mostrar",
                options=[10, 20, 50, 100, "Todas"],
                index=1
            )
        
        with col2:
            # Filtro por columnas
            all_columns = df.columns.tolist()
            selected_columns = st.multiselect(
                "Seleccionar columnas",
                options=all_columns,
                default=all_columns[:10] if len(all_columns) > 10 else all_columns
            )
        
        with col3:
            # Opción de búsqueda
            search_term = st.text_input(
                "Buscar en los datos",
                placeholder="Ingresa término de búsqueda..."
            )

        # Aplicar filtros
        filtered_df = df.copy()
        
        if selected_columns:
            filtered_df = filtered_df[selected_columns]
        
        if search_term:
            # Buscar en todas las columnas de texto
            mask = False
            for col in filtered_df.select_dtypes(include=['object', 'string']).columns:
                mask |= filtered_df[col].astype(str).str.contains(search_term, case=False, na=False)
            
            if mask.any():
                filtered_df = filtered_df[mask]
                st.info(f"🔍 Se encontraron {len(filtered_df)} filas que contienen '{search_term}'")
            else:
                st.warning(f"⚠️ No se encontraron resultados para '{search_term}'")

        # Mostrar preview de los datos filtrados
        st.markdown("### 👀 Vista previa de los datos")
        
        if rows_to_show == "Todas":
            display_df = filtered_df
        else:
            display_df = filtered_df.head(rows_to_show)
        
        # Mostrar el DataFrame con mejor formato
        st.dataframe(
            display_df, 
            use_container_width=True,
            height=min(400, len(display_df) * 35 + 50)  # Altura dinámica
        )
        
        # Información adicional del filtrado
        if len(filtered_df) != len(df):
            st.info(f"📊 Mostrando {len(display_df)} de {len(filtered_df)} filas filtradas (total: {len(df)} filas)")
        else:
            st.info(f"📊 Mostrando {len(display_df)} de {len(df)} filas totales")

        # Análisis estadístico básico para columnas numéricas
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) > 0:
            st.markdown("### 📊 Estadísticas Descriptivas")
            
            with st.expander("Ver estadísticas numéricas", expanded=False):
                st.dataframe(df[numeric_columns].describe(), use_container_width=True)

        # Opciones de descarga mejoradas
        st.markdown("### 💾 Opciones de Descarga")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Botón para descargar CSV completo
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="💾 Descargar CSV Completo",
                data=csv_data,
                file_name=f"reporte_nubox_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Botón para descargar Excel completo
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Excel Completo",
                data=excel_data,
                file_name=f"reporte_nubox_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            # Botón para descargar datos filtrados
            if len(filtered_df) != len(df) and not filtered_df.empty:
                filtered_csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="🔍 Descargar Filtrados CSV",
                    data=filtered_csv,
                    file_name=f"reporte_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Información adicional si hay archivo descargado
        if file_path:
            st.markdown("### 📁 Información del Archivo")
            st.info(f"📁 El archivo original también fue descargado en: {file_path}")
            
            # Mostrar información adicional del archivo
            try:
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                st.write(f"**Tamaño del archivo**: {file_size:.2f} MB")
                st.write(f"**Formato**: {os.path.splitext(file_path)[1].upper()}")
            except:
                pass

    else:
        st.markdown("### ⚠️ Problema con la Extracción")
        
        # Mostrar información detallada del error
        if file_path and file_path.startswith("Archivo inválido:"):
            st.error("❌ **Archivo descargado inválido**")
            
            # Mostrar alerta específica sobre el problema de formato
            st.warning("🚨 **Problema detectado**: El archivo tiene una extensión .xls pero su contenido no coincide con el formato Excel esperado.")
            
            st.markdown("""
            **Lo que está pasando**:
            - Nubox generó un archivo con extensión `.xls` 
            - Sin embargo, el contenido del archivo no es Excel válido
            - Probablemente contiene HTML (página de error) o datos corruptos
            - macOS detecta esta inconsistencia y muestra la alerta de seguridad
            
            **Posibles causas**:
            - Nubox devolvió una página de error en lugar del reporte
            - La sesión de Nubox expiró durante la generación
            - Los parámetros del reporte no son válidos
            - Problemas temporales en el servidor de Nubox
            - Límites de datos excedidos en el reporte
            """)
            
            # Mostrar la ruta del archivo problemático
            actual_path = file_path.replace("Archivo inválido: ", "")
            st.info(f"📁 Archivo problemático: `{os.path.basename(actual_path)}`")
            
            # Crear análisis detallado del archivo
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Analizar Contenido del Archivo", key="analyze_file"):
                    try:
                        file_size = os.path.getsize(actual_path) / 1024  # KB
                        
                        with open(actual_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(2000)  # Primeros 2000 caracteres
                        
                        st.markdown("### 📋 Análisis del Archivo")
                        st.write(f"**Tamaño**: {file_size:.2f} KB")
                        st.write(f"**Nombre**: {os.path.basename(actual_path)}")
                        
                        # Detectar tipo de contenido
                        if '<html' in content.lower():
                            st.error("🌐 **Tipo detectado**: Página HTML")
                            st.write("El archivo contiene código HTML en lugar de datos Excel.")
                            
                            # Buscar títulos o mensajes específicos
                            import re
                            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                            if title_match:
                                st.write(f"**Título de la página**: {title_match.group(1)}")
                            
                        elif 'error' in content.lower():
                            st.error("🚫 **Tipo detectado**: Mensaje de error")
                            
                            # Buscar mensajes de error específicos
                            error_keywords = ['error', 'timeout', 'session', 'expired', 'invalid']
                            found_errors = [word for word in error_keywords if word in content.lower()]
                            if found_errors:
                                st.write(f"**Palabras de error encontradas**: {', '.join(found_errors)}")
                        
                        elif file_size < 1:
                            st.warning("📄 **Tipo detectado**: Archivo muy pequeño o vacío")
                        
                        else:
                            st.info("❓ **Tipo detectado**: Contenido desconocido")
                        
                        # Mostrar contenido en un expandidor
                        with st.expander("Ver contenido del archivo", expanded=False):
                            st.code(content[:1000], language="html")
                            if len(content) > 1000:
                                st.write(f"... y {len(content) - 1000} caracteres más")
                        
                    except Exception as e:
                        st.error(f"No se pudo analizar el archivo: {str(e)}")
            
            with col2:
                if st.button("🔧 Soluciones Recomendadas", key="solutions"):
                    st.markdown("### 🛠️ Pasos para Resolver")
                    
                    solutions = [
                        "1. **Verificar sesión**: Asegúrate de que tu sesión en Nubox sigue activa",
                        "2. **Validar parámetros**: Confirma que las fechas y filtros sean correctos",
                        "3. **Reducir alcance**: Prueba con un rango de fechas más pequeño",
                        "4. **Cambiar formato**: En Nubox, selecciona 'PDF' en lugar de 'Excel'",
                        "5. **Reintentar**: Espera unos minutos y vuelve a intentar",
                        "6. **Limpiar cookies**: Borra las cookies del navegador para Nubox"
                    ]
                    
                    for solution in solutions:
                        st.write(solution)
                    
                    st.info("💡 **Consejo**: Si el problema persiste, es probable que sea un problema temporal de Nubox.")
            
            # Botones de acción
            st.markdown("### 🎯 Acciones Disponibles")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🗑️ Eliminar Archivo", key="delete_file"):
                    try:
                        os.remove(actual_path)
                        st.success("✅ Archivo eliminado")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar: {str(e)}")
            
            with col2:
                if st.button("📁 Abrir Carpeta", key="open_folder"):
                    import subprocess
                    subprocess.run(["open", str(Path.home() / "Downloads")])
                    st.info("📂 Carpeta de descargas abierta")
            
            with col3:
                if st.button("🔄 Reintentar", key="retry"):
                    st.rerun()
            
            with col4:
                if st.button("🆕 Proceso Nuevo", key="new_process"):
                    # Limpiar estado y reiniciar
                    for key in list(st.session_state.keys()):
                        if key.startswith(('logged_in', 'navigation_complete', 'report_generated')):
                            del st.session_state[key]
                    st.rerun()
        elif file_path and file_path.startswith("Error de lectura:"):
            st.error("❌ **Error al leer el archivo Excel**")
            st.markdown("""
            **Problema**: El archivo se descargó pero no se puede leer como Excel.
            
            **Posibles soluciones**:
            1. Verificar que el archivo no esté corrupto
            2. Intentar abrirlo manualmente en Excel
            3. Cambiar el formato de salida a PDF y luego convertir
            4. Contactar soporte de Nubox si el problema persiste
            """)
            
            actual_path = file_path.replace("Error de lectura: ", "")
            st.info(f"📁 Archivo descargado: `{actual_path}`")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📁 Abrir Carpeta de Descargas"):
                    import subprocess
                    subprocess.run(["open", str(Path.home() / "Downloads")])
            
            with col2:
                if st.button("🔄 Reintentar Extracción"):
                    st.rerun()
                    
        elif file_path == "Descarga no encontrada":
            st.error("❌ **No se encontró archivo descargado**")
            st.markdown("""
            **Problema**: No se detectó ningún archivo Excel reciente en la carpeta de descargas.
            
            **Posibles causas**:
            - La descarga no se completó
            - El archivo se guardó en otra ubicación
            - El proceso de generación falló en Nubox
            - Bloqueador de pop-ups impidió la descarga
            """)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📁 Verificar Descargas"):
                    # Mostrar archivos recientes en Downloads
                    downloads_folder = Path.home() / "Downloads"
                    excel_files = list(downloads_folder.glob("*.xls*"))
                    
                    if excel_files:
                        # Ordenar por fecha de modificación
                        excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        
                        st.markdown("**Archivos Excel encontrados:**")
                        for file in excel_files[:5]:  # Mostrar solo los 5 más recientes
                            mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                            st.write(f"- `{file.name}` (modificado: {mtime.strftime('%d/%m/%Y %H:%M')})")
                    else:
                        st.warning("No se encontraron archivos Excel en la carpeta de descargas.")
            
            with col2:
                if st.button("⏱️ Esperar y Reintentar"):
                    with st.spinner("Esperando 30 segundos más para la descarga..."):
                        time.sleep(30)
                    st.rerun()
            
            with col3:
                if st.button("🔄 Reintentar Proceso"):
                    st.rerun()
        else:
            st.warning("⚠️ No se pudieron extraer datos del reporte. Revisa los logs para más información.")
            
            # Información de diagnóstico
            with st.expander("🔧 Información de Diagnóstico"):
                st.markdown("""
                **Pasos de diagnóstico**:
                1. Verifica que estés conectado a Nubox
                2. Confirma que los parámetros del reporte son válidos
                3. Asegúrate de que no hay bloqueadores de descarga
                4. Revisa los logs detallados para errores específicos
                """)
            
            # Opciones de recuperación
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Reintentar Extracción"):
                    st.rerun()
            
            with col2:
                if st.button("🧭 Verificar Navegación"):
                    if st.session_state.get('nubox_service'):
                        try:
                            # Tomar captura de pantalla para diagnóstico
                            st.session_state.nubox_service.browser_manager.take_screenshot("diagnostico_estado_actual.png")
                            st.success("✅ Captura de diagnóstico guardada en la carpeta logs/")
                        except:
                            st.error("❌ No se pudo tomar captura de diagnóstico")
                    else:
                        st.warning("⚠️ Servicio Nubox no disponible")
            
            with col3:
                if st.button("🆕 Reiniciar Todo"):
                    # Limpiar completamente el estado
                    if st.session_state.get('nubox_service'):
                        st.session_state.nubox_service.close()
                    
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    
                    st.success("🔄 Estado reiniciado. Recarga la página para empezar de nuevo.")
                    st.rerun()

def initialize_rpa_process(username, password, custom_url, headless, timeout, progress_container, log_container):
    """Inicializa el proceso RPA: login y navegación hasta cargar los dropdowns."""
    try:
        # Configurar logger
        logger = setup_logger()
        config = setup_config()
        
        with progress_container:
            # Barra de progreso para inicialización
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Paso 1: Inicializar servicio
            status_text.text("🔄 Inicializando servicio Nubox...")
            progress_bar.progress(10)
            
            if not st.session_state.nubox_service:
                st.session_state.nubox_service = NuboxService(headless=headless, timeout=timeout)
            
            with log_container:
                st.text("✅ Servicio Nubox inicializado")
            
            # Paso 2: Login
            if not st.session_state.logged_in:
                status_text.text("🔐 Iniciando sesión en Nubox...")
                progress_bar.progress(30)
                
                login_success = st.session_state.nubox_service.login(username, password, custom_url)
                
                if login_success:
                    st.session_state.logged_in = True
                    with log_container:
                        st.text("✅ Login exitoso")
                else:
                    with log_container:
                        st.text("❌ Error en login")
                    st.error("❌ Error al conectar con Nubox. Verifica tus credenciales.")
                    return False
            
            # Paso 3: Navegación
            if not st.session_state.navigation_complete:
                status_text.text("🧭 Navegando al reporte Mayor...")
                progress_bar.progress(60)
                
                navigation_success = st.session_state.nubox_service.navigate_to_report()
                
                if navigation_success:
                    st.session_state.navigation_complete = True
                    with log_container:
                        st.text("✅ Navegación completada")
                    
                    # Cargar opciones de dropdowns
                    status_text.text("📋 Cargando opciones de parámetros...")
                    progress_bar.progress(80)
                    
                    load_dropdown_options()
                    
                    with log_container:
                        st.text("✅ Opciones de parámetros cargadas")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ ¡Inicialización completada!")
                    
                    return True
                else:
                    with log_container:
                        st.text("❌ Error en navegación")
                    st.error("❌ Error al navegar al reporte. Intenta nuevamente.")
                    return False
            
            return True
            
    except Exception as e:
        with log_container:
            st.text(f"❌ Error en inicialización: {str(e)}")
        st.error(f"❌ Error durante la inicialización: {str(e)}")
        return False

def extract_report_process(fecha_desde, fecha_hasta, dropdown_selections, selected_accounts, selected_companies, progress_container, log_container):
    """Extrae el reporte con los parámetros configurados."""
    try:
        # Determinar el tipo de procesamiento
        is_multiple_accounts = len(selected_accounts) > 1
        is_multiple_companies = len(selected_companies) > 1
        is_multiple_processing = is_multiple_accounts or is_multiple_companies
        
        with progress_container:
            # Barra de progreso para extracción
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Preparar parámetros base
            base_params = {
                'fecha_desde': fecha_desde.strftime("%d/%m/%Y"),
                'fecha_hasta': fecha_hasta.strftime("%d/%m/%Y"),
                'dropdown_selections': dropdown_selections
            }
            
            # Procesar según el modo
            if is_multiple_processing:
                # MODO MÚLTIPLE (empresas y/o cuentas)
                total_combinations = len(selected_companies) * len(selected_accounts)
                status_text.text(f"📊 Procesando {total_combinations} combinaciones ({len(selected_companies)} empresas × {len(selected_accounts)} cuentas)...")
                progress_bar.progress(20)
                
                with log_container:
                    st.text(f"🔢 Iniciando procesamiento múltiple:")
                    st.text(f"  - Empresas: {len(selected_companies)}")
                    st.text(f"  - Cuentas: {len(selected_accounts)}")
                    st.text(f"  - Total combinaciones: {total_combinations}")
                
                # Llamar al nuevo método de extracción múltiple por empresas y cuentas
                results = st.session_state.nubox_service.extract_multiple_reports_by_company_and_account(
                    base_params, selected_companies, selected_accounts
                )
                
                progress_bar.progress(95)
                
                # Procesar y mostrar resultados múltiples
                if results and '_summary' in results:
                    summary = results['_summary']
                    
                    with log_container:
                        st.text(f"✅ Extracción completada:")
                        st.text(f"  - Total combinaciones: {summary.get('total_combinaciones', total_combinations)}")
                        st.text(f"  - Exitosas: {summary['successful_extractions']}")
                        st.text(f"  - Fallidas: {summary['failed_extractions']}")
                        st.text(f"  - Tasa de éxito: {summary['success_rate']:.1f}%")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ ¡Proceso múltiple completado!")
                    
                    # Mostrar resultados múltiples con nueva función
                    show_multiple_company_account_results(results, selected_companies, selected_accounts)
                    
                    return True
                else:
                    with log_container:
                        st.text("❌ Error en la extracción múltiple")
                    st.error("❌ No se pudieron extraer los reportes.")
                    return False
                    
            else:
                # MODO UNA SOLA COMBINACIÓN
                status_text.text("⚙️ Configurando parámetros del reporte...")
                progress_bar.progress(25)
                
                # Configurar parámetros usando el método automatizado
                config_success = configure_parameters_programmatically(base_params, log_container)
                
                if config_success:
                    with log_container:
                        st.text("✅ Parámetros configurados correctamente")
                    progress_bar.progress(50)
                else:
                    with log_container:
                        st.text("❌ Error al configurar parámetros")
                    st.error("❌ Error al configurar parámetros del reporte.")
                    return False
                
                # Generar y extraer reporte único
                status_text.text("📊 Generando y extrayendo reporte...")
                progress_bar.progress(75)
                
                report_data = st.session_state.nubox_service.extract_report()
                
                if isinstance(report_data, tuple):
                    df, file_path = report_data
                else:
                    df = report_data
                    file_path = None
                
                progress_bar.progress(100)
                status_text.text("✅ ¡Extracción completada!")
                
                with log_container:
                    st.text("✅ Reporte extraído exitosamente")
                
                st.session_state.report_generated = True
                
                # Mostrar resultados únicos
                show_results(df, file_path)
                
                return True

    except Exception as e:
        with log_container:
            st.text(f"❌ Error en extracción: {str(e)}")
        st.error(f"❌ Error durante la extracción: {str(e)}")
        return False

def show_multiple_company_account_results(results, selected_companies, selected_accounts):
    """Muestra los resultados de múltiples reportes extraídos para empresas y cuentas con exportación automática a MongoDB."""
    st.markdown('<h2 class="section-header">📊 Resultados de Múltiples Empresas y Cuentas</h2>', unsafe_allow_html=True)
    
    if not results or '_summary' not in results:
        st.error("❌ No se obtuvieron resultados válidos de los reportes múltiples.")
        return
    
    summary = results['_summary']
    
    # Mostrar resumen general
    st.markdown("### 📈 Resumen General")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🏢 Empresas", len(selected_companies))
    with col2:
        st.metric("💰 Cuentas", len(selected_accounts))
    with col3:
        st.metric("📊 Total Combinaciones", summary.get('total_combinaciones', len(selected_companies) * len(selected_accounts)))
    with col4:
        st.metric("✅ Exitosas", summary['successful_extractions'])
    with col5:
        st.metric("📈 Tasa de Éxito", f"{summary['success_rate']:.1f}%")
    
    # Mostrar estado visual mejorado
    total_expected = len(selected_companies) * len(selected_accounts)
    if summary['success_rate'] >= 80:
        st.success(f"🎉 ¡Excelente! Se procesaron exitosamente {summary['successful_extractions']} de {total_expected} combinaciones empresa-cuenta.")
    elif summary['success_rate'] >= 50:
        st.warning(f"⚠️ Se procesaron {summary['successful_extractions']} de {total_expected} combinaciones. Revisa las que fallaron.")
    else:
        st.error(f"❌ Solo se procesaron {summary['successful_extractions']} de {total_expected} combinaciones exitosamente.")
    
    # Separar resultados exitosos y fallidos
    successful_results = []
    failed_results = []
    
    # El formato de results ahora incluye combinaciones empresa-cuenta
    for combination_key, result in results.items():
        if combination_key != '_summary':
            if result.get('success', False):
                successful_results.append((combination_key, result))
            else:
                failed_results.append((combination_key, result))
    
    # EXPORTACIÓN AUTOMÁTICA A MONGODB PARA REPORTES MÚLTIPLES
    if successful_results:
        st.markdown("### 🚀 Exportación Automática a MongoDB")
        
        with st.spinner(f"Exportando {len(successful_results)} reportes a MongoDB..."):
            try:
                from services.mongodb_client import NuboxMongoClient
                
                mongo_client = NuboxMongoClient()
                export_summary = {
                    'total_reportes': len(successful_results),
                    'exportados_exitosos': 0,
                    'exportados_fallidos': 0,
                    'document_ids': [],
                    'errores': []
                }
                
                # Exportar cada reporte exitoso
                for combination_key, result in successful_results:
                    try:
                        df = result.get('data')
                        if df is not None and not df.empty:
                            # Extraer información de la empresa desde los atributos del DataFrame
                            company_info = df.attrs.get('company_info', {}) if hasattr(df, 'attrs') else {}
                            
                            # Preparar metadatos específicos para esta combinación
                            report_metadata = {
                                'archivo_origen': os.path.basename(result.get('file_path', '')) or 'streamlit_multiple_extraction',
                                'empresa': result.get('company', ''),
                                'cuenta_contable': result.get('account', ''),
                                'combinacion': combination_key,
                                'fecha_extraccion': datetime.datetime.now().isoformat(),
                                'parametros_streamlit': {
                                    'formato_salida': 'EXCEL',
                                    'include_subcuentas': st.session_state.get('dropdown_options', {}).get('Incluir Subcuentas', {}).get('selected', 'NO'),
                                    'procesamiento_multiple': True,
                                    'total_empresas': len(selected_companies),
                                    'total_cuentas': len(selected_accounts),
                                    'total_combinaciones': len(successful_results)
                                }
                            }
                            
                            # Exportar a MongoDB
                            export_result = mongo_client.export_nubox_dataframe(
                                df=df,
                                company_info=company_info,
                                report_metadata=report_metadata
                            )
                            
                            if export_result['success']:
                                export_summary['exportados_exitosos'] += 1
                                export_summary['document_ids'].append({
                                    'combinacion': combination_key,
                                    'empresa': result.get('company', ''),
                                    'cuenta': result.get('account', ''),
                                    'document_id': export_result['document_id'],
                                    'filas': export_result['exported_rows']
                                })
                            else:
                                export_summary['exportados_fallidos'] += 1
                                export_summary['errores'].append({
                                    'combinacion': combination_key,
                                    'errores': export_result['errors']
                                })
                        else:
                            export_summary['exportados_fallidos'] += 1
                            export_summary['errores'].append({
                                'combinacion': combination_key,
                                'errores': ['DataFrame vacío o no disponible']
                            })
                            
                    except Exception as e:
                        export_summary['exportados_fallidos'] += 1
                        export_summary['errores'].append({
                            'combinacion': combination_key,
                            'errores': [str(e)]
                        })
                
                mongo_client.disconnect()
                
                # Mostrar resultado de la exportación masiva
                if export_summary['exportados_exitosos'] > 0:
                    st.success(f"✅ **{export_summary['exportados_exitosos']} reportes exportados exitosamente a MongoDB**")
                    
                    # Mostrar detalles de la exportación múltiple
                    with st.expander("📋 Detalles de la Exportación Masiva", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("📊 Reportes Exportados", export_summary['exportados_exitosos'])
                        with col2:
                            st.metric("❌ Fallos de Exportación", export_summary['exportados_fallidos'])
                        with col3:
                            total_filas = sum(doc['filas'] for doc in export_summary['document_ids'])
                            st.metric("📝 Total Filas", total_filas)
                        with col4:
                            st.metric("📅 Fecha", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
                        
                        st.write("**IDs de Documentos Exportados:**")
                        for doc_info in export_summary['document_ids']:
                            st.write(f"- **{doc_info['empresa']} - {doc_info['cuenta']}**: `{doc_info['document_id']}` ({doc_info['filas']} filas)")
                        
                        st.write(f"**Colección**: `test-nubox`")
                        st.write(f"**Base de Datos**: `nubox-data`")
                        
                        if export_summary['errores']:
                            st.write("**Errores de Exportación:**")
                            for error_info in export_summary['errores']:
                                st.write(f"- **{error_info['combinacion']}**: {', '.join(error_info['errores'])}")
                
                else:
                    st.error("❌ **No se pudo exportar ningún reporte a MongoDB**")
                    if export_summary['errores']:
                        st.write("**Errores encontrados:**")
                        for error_info in export_summary['errores']:
                            st.write(f"- **{error_info['combinacion']}**: {', '.join(error_info['errores'])}")
                
            except ImportError:
                st.warning("⚠️ Cliente MongoDB no disponible. Instalar con: `pip install pymongo`")
            except Exception as e:
                st.error(f"❌ Error durante la exportación masiva: {str(e)}")
    
    # Mostrar resultados exitosos organizados por empresa
    if successful_results:
        st.markdown("### ✅ Reportes Exitosos")
        
        # Organizar resultados por empresa
        results_by_company = {}
        for combination_key, result in successful_results:
            company = result.get('company', 'Empresa desconocida')
            if company not in results_by_company:
                results_by_company[company] = []
            results_by_company[company].append((combination_key, result))
        
        # Crear tabs por empresa
        if results_by_company:
            company_tabs = st.tabs([f"🏢 {company.split(',')[0].strip()}" for company in results_by_company.keys()])
            
            for company_tab, (company, company_results) in zip(company_tabs, results_by_company.items()):
                with company_tab:
                    st.markdown(f"**Empresa:** {company}")
                    st.markdown(f"**Reportes generados:** {len(company_results)}")
                    
                    # Sub-tabs para cada cuenta dentro de la empresa
                    if len(company_results) > 1:
                        account_tab_names = []
                        for combination_key, result in company_results:
                            account = result.get('account', 'Cuenta desconocida')
                            account_code = account.split(' ')[0] if ' ' in account else account
                            account_tab_names.append(f"💰 {account_code}")
                        
                        account_tabs = st.tabs(account_tab_names)
                        
                        for account_tab, (combination_key, result) in zip(account_tabs, company_results):
                            with account_tab:
                                _show_individual_report_result(combination_key, result)
                    else:
                        # Solo una cuenta, mostrar directamente
                        combination_key, result = company_results[0]
                        _show_individual_report_result(combination_key, result)
    
    # Mostrar resultados fallidos
    if failed_results:
        st.markdown("### ❌ Reportes Fallidos")
        
        with st.expander(f"Ver detalles de {len(failed_results)} reportes fallidos", expanded=len(successful_results) == 0):
            for combination_key, result in failed_results:
                error_msg = result.get('error', 'Error desconocido')
                company = result.get('company', 'Empresa desconocida')
                account = result.get('account', 'Cuenta desconocida')
                st.error(f"**{company} - {account}**: {error_msg}")
    
    # Opción para descargar resumen completo
    st.markdown("### 📋 Descarga del Resumen Completo")
    
    if successful_results or failed_results:
        # Crear DataFrame combinado con información de resumen
        summary_data = []
        
        for combination_key, result in successful_results + failed_results:
            summary_data.append({
                'Combinación': combination_key,
                'Empresa': result.get('company', ''),

                'Cuenta': result.get('account', ''),
                'Código Cuenta': result.get('account_code', ''),
                'Estado': 'Exitoso' if result.get('success', False) else 'Fallido',
                'Filas': result.get('rows_count', 0),
                'Columnas': result.get('columns_count', 0),
                'Archivo': result.get('file_path', '') if result.get('file_path') and result.get('file_path') != "Descarga no encontrada" else '',
                'Error': result.get('error', '') if not result.get('success', False) else ''
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar resumen en CSV
            summary_csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📄 Descargar Resumen CSV",
                data=summary_csv,
                file_name=f"resumen_reportes_multiples_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Descargar resumen en Excel
            summary_excel_buffer = io.BytesIO()
            summary_df.to_excel(summary_excel_buffer, index=False, engine='openpyxl')
            summary_excel_data = summary_excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Resumen Excel",
                data=summary_excel_data,
                file_name=f"resumen_reportes_multiples_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Mostrar tabla de resumen
        st.markdown("**Vista previa del resumen:**")
        st.dataframe(summary_df, use_container_width=True)

def _show_individual_report_result(combination_key, result):
    """Función auxiliar para mostrar un resultado individual de reporte."""
    account = result.get('account', 'Cuenta desconocida')
    
    # Métricas del reporte individual
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Filas", result.get('rows_count', 0))
    with col2:
        st.metric("📋 Columnas", result.get('columns_count', 0))
    with col3:
        file_status = "Descargado" if result.get('file_path') else "En memoria"
        st.metric("📁 Archivo", file_status)
    
    # Mostrar preview de los datos si están disponibles
    df = result.get('data')
    if df is not None and not df.empty:
        st.markdown("**Vista previa de los datos:**")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Botones de descarga para este reporte
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar CSV
            csv_data = df.to_csv(index=False)
            account_code = result.get('account_code', combination_key.replace(' ', '_'))
            st.download_button(
                label="💾 Descargar CSV",
                data=csv_data,
                file_name=f"reporte_{account_code}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"csv_{combination_key}"
            )
        
        with col2:
            # Descargar Excel
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Excel",
                data=excel_data,
                file_name=f"reporte_{account_code}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{combination_key}"
            )
    else:
        st.info("ℹ️ No hay datos para mostrar, pero el archivo fue descargado exitosamente.")
    
    # Mostrar información del archivo descargado
    file_path = result.get('file_path')
    if file_path and file_path != "Descarga no encontrada":
        st.info(f"📁 Archivo descargado en: {file_path}")

def main():
    """Función principal de la aplicación Streamlit."""
    
    # Inicializar estado de la sesión
    initialize_session_state()
    
    # Título principal
    st.markdown('<h1 class="main-header">🤖 RPA Nubox - Extractor de Reportes</h1>', unsafe_allow_html=True)
    
    # Sidebar con configuración
    headless, timeout = sidebar_configuration()
    
    # Sección de login
    username, password, custom_url = login_section()
    
    # Sección de parámetros del reporte
    fecha_desde, fecha_hasta, dropdown_selections, selected_accounts, selected_companies = report_parameters_section()
    
    # Sección de progreso
    progress_container, log_container = progress_section()
    
    # Botones de control principal
    st.markdown('<h2 class="section-header">🎮 Control del Proceso</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Botón para inicializar (login + navegación)
        if st.button("🚀 Inicializar RPA", type="primary", use_container_width=True):
            if username and password:
                success = initialize_rpa_process(
                    username, password, custom_url, headless, timeout, 
                    progress_container, log_container
                )
                if success:
                    st.success("✅ RPA inicializado. Ahora puedes configurar parámetros y extraer reportes.")
                    st.rerun()
            else:
                st.error("❌ Por favor ingresa usuario y contraseña.")
    
    with col2:
        # Botón para extraer reportes (solo activo si está inicializado)
        extract_disabled = not (st.session_state.logged_in and st.session_state.navigation_complete)
        
        if st.button("📊 Extraer Reportes", disabled=extract_disabled, use_container_width=True):
            if dropdown_selections and (selected_accounts or selected_companies):
                success = extract_report_process(
                    fecha_desde, fecha_hasta, dropdown_selections, 
                    selected_accounts, selected_companies,
                    progress_container, log_container
                )
                if success:
                    st.balloons()
            else:
                st.error("❌ Primero configura los parámetros del reporte.")
    
    with col3:
        # Botón para reiniciar todo
        if st.button("🔄 Reiniciar Todo", use_container_width=True):
            # Cerrar servicio si existe
            if st.session_state.get('nubox_service'):
                try:
                    st.session_state.nubox_service.close()
                except:
                    pass
            
            # Limpiar estado
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.success("🔄 Estado reiniciado. Recargando página...")
            time.sleep(1)
            st.rerun()
    
    # Información adicional en el footer
    st.markdown("---")
    st.markdown("### 📋 Estado del Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        login_status = "✅ Conectado" if st.session_state.logged_in else "❌ Desconectado"
        st.info(f"**Login**: {login_status}")
    
    with col2:
        nav_status = "✅ Completada" if st.session_state.navigation_complete else "⏳ Pendiente"
        st.info(f"**Navegación**: {nav_status}")
    
    with col3:
        params_status = "✅ Cargados" if st.session_state.dropdown_options else "⏳ Pendientes"
        st.info(f"**Parámetros**: {params_status}")
    
    with col4:
        report_status = "✅ Generado" if st.session_state.report_generated else "⏳ Pendiente"
        st.info(f"**Reporte**: {report_status}")
    
    # Información de ayuda
    with st.expander("ℹ️ Ayuda y Consejos"):
        st.markdown("""
        ### 🔧 Cómo usar el RPA Nubox
        
        1. **Inicializar**: Ingresa tus credenciales y haz clic en "Inicializar RPA"
        2. **Configurar**: Una vez inicializado, selecciona empresas y cuentas
        3. **Extraer**: Haz clic en "Extraer Reportes" para procesar
        4. **Descargar**: Los resultados se mostrarán con opciones de descarga
        
        ### 🎯 Consejos para mejor rendimiento
        
        - **Modo headless**: Mantén activado para mejor rendimiento
        - **Timeout**: Aumenta si tienes conexión lenta
        - **Múltiples reportes**: El sistema procesa automáticamente en lotes
        - **MongoDB**: Los datos se exportan automáticamente
        
        ### 🚨 Solución de problemas
        
        - **Error de login**: Verifica credenciales y conexión
        - **Archivos inválidos**: Reinicia e intenta con menos reportes
        - **Navegación fallida**: Aumenta el timeout
        - **Proceso lento**: Usa modo headless y reduce combinaciones
        """)

if __name__ == "__main__":
    main()