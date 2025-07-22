#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interfaz web refactorizada con Streamlit para el RPA de Nubox.
Versión modular con responsabilidades separadas.
"""

import streamlit as st
import sys
import time
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

# Importar módulos refactorizados
from ui.utils.styles import apply_custom_styles
from ui.utils.session import initialize_session_state, clear_session_state, get_session_status
from ui.components.sidebar import render_sidebar
from ui.components.login import render_login_section
from ui.components.parameters import render_parameters_section
from ui.components.progress import render_progress_section
from ui.pages.results import show_results
from ui.pages.multiple_results import show_multiple_results, show_multiple_company_account_results
from ui.pages.monthly_results import show_monthly_results, show_monthly_download_options
from core.rpa_controller import RPAController
from core.extraction import ReportExtractor

# Configuración de la página
st.set_page_config(
    page_title="RPA Nubox - Extractor de Reportes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Función principal de la aplicación Streamlit refactorizada."""
    
    # Aplicar estilos personalizados
    apply_custom_styles()
    
    # Inicializar estado de la sesión
    initialize_session_state()
    
    # Título principal
    st.markdown('<h1 class="main-header">🤖 RPA Nubox - Extractor de Reportes</h1>', unsafe_allow_html=True)
    
    # Renderizar componentes de UI
    headless, timeout = render_sidebar()
    username, password, custom_url = render_login_section()
    fecha_desde, fecha_hasta, dropdown_selections, selected_accounts, selected_companies = render_parameters_section()
    progress_container, log_container = render_progress_section()
    
    # Crear instancias de controladores
    rpa_controller = RPAController()
    report_extractor = ReportExtractor()
    
    # Botones de control principal
    st.markdown('<h2 class="section-header">🎮 Control del Proceso</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Botón para inicializar (login + navegación)
        if st.button("🚀 Inicializar RPA", type="primary", use_container_width=True):
            if username and password:
                success = rpa_controller.initialize_rpa_process(
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
                result = report_extractor.extract_report_process(
                    fecha_desde, fecha_hasta, dropdown_selections, 
                    selected_accounts, selected_companies,
                    progress_container, log_container
                )
                
                if result:
                    # Determinar tipo de resultado y mostrar apropiadamente
                    if isinstance(result, dict) and any('month_name' in v for v in result.values() if isinstance(v, dict)):
                        # Resultado mensual
                        show_monthly_results(result)
                        show_monthly_download_options(result)
                        st.balloons()
                    elif isinstance(result, tuple) and len(result) == 2:
                        # Resultado simple (df, file_path)
                        df, file_path = result
                        show_results(df, file_path)
                        st.balloons()
                    elif isinstance(result, dict) and '_summary' in result:
                        # Resultado múltiple estándar
                        is_multiple_companies = len(selected_companies) > 1
                        if is_multiple_companies:
                            show_multiple_company_account_results(result, selected_companies, selected_accounts)
                        else:
                            show_multiple_results(result, selected_accounts)
                        st.balloons()
                    else:
                        st.error("❌ Tipo de resultado no reconocido.")
            else:
                st.error("❌ Primero configura los parámetros del reporte.")
    
    with col3:
        # Botón para reiniciar todo
        if st.button("🔄 Reiniciar Todo", use_container_width=True):
            clear_session_state()
            st.success("🔄 Estado reiniciado. Recargando página...")
            time.sleep(1)
            st.rerun()
    
    # Mostrar estado del sistema
    _render_system_status()
    
    # Información de ayuda
    _render_help_section()

def _render_system_status():
    """Renderiza el estado actual del sistema."""
    st.markdown("---")
    st.markdown("### 📋 Estado del Sistema")
    
    status = get_session_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        login_status = "✅ Conectado" if status['logged_in'] else "❌ Desconectado"
        st.info(f"**Login**: {login_status}")
    
    with col2:
        nav_status = "✅ Completada" if status['navigation_complete'] else "⏳ Pendiente"
        st.info(f"**Navegación**: {nav_status}")
    
    with col3:
        params_status = "✅ Cargados" if status['dropdown_options_loaded'] else "⏳ Pendientes"
        st.info(f"**Parámetros**: {params_status}")
    
    with col4:
        report_status = "✅ Generado" if status['report_generated'] else "⏳ Pendiente"
        st.info(f"**Reporte**: {report_status}")

def _render_help_section():
    """Renderiza la sección de ayuda."""
    with st.expander("ℹ️ Ayuda y Consejos"):
        st.markdown("""
        ### 🔧 Cómo usar el RPA Nubox
        
        1. **Inicializar**: Ingresa tus credenciales y haz clic en "Inicializar RPA"
        2. **Configurar**: Una vez inicializado, selecciona empresas y cuentas
        3. **Extraer**: Haz clic en "Extraer Reportes" para procesar
        4. **Descargar**: Los resultados se mostrarán con opciones de descarga
        
        ### 🗓️ Nuevas Funcionalidades - Extracciones Mensuales
        
        - **Activación automática**: Para rangos > 32 días
        - **Proceso por meses**: Enero a Julio = 7 reportes mensuales
        - **Compatibilidad total**: Funciona con múltiples empresas y cuentas
        - **Descarga consolidada**: ZIP y Excel unificado
        
        ### 🎯 Consejos para mejor rendimiento
        
        - **Modo headless**: Mantén activado para mejor rendimiento
        - **Timeout**: Aumenta si tienes conexión lenta
        - **Múltiples reportes**: El sistema procesa automáticamente en lotes
        - **MongoDB**: Los datos se exportan automáticamente
        - **Extracciones mensuales**: Ideal para análisis históricos largos
        
        ### 🚨 Solución de problemas
        
        - **Error de login**: Verifica credenciales y conexión
        - **Archivos inválidos**: Reinicia e intenta con menos reportes
        - **Navegación fallida**: Aumenta el timeout
        - **Proceso lento**: Usa modo headless y reduce combinaciones
        - **Extracciones mensuales largas**: Normal para rangos de varios meses
        
        ### 🆕 Arquitectura Refactorizada con Extracciones Mensuales
        
        Esta versión incluye:
        - **Componentes modulares**: UI separada en módulos reutilizables
        - **Separación de responsabilidades**: Lógica de negocio separada de la UI
        - **Extracciones mensuales automáticas**: Procesamiento inteligente por períodos
        - **Mejor mantenibilidad**: Código más limpio y organizado
        - **Escalabilidad mejorada**: Manejo eficiente de grandes volúmenes de datos
        - **Resultados consolidados**: Múltiples formatos de descarga y visualización
        """)

if __name__ == "__main__":
    main()