#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente de sidebar para configuración del RPA Nubox.
"""

import streamlit as st
from ui.utils.session import get_session_status

def render_sidebar():
    """Renderiza la configuración en la barra lateral."""
    st.sidebar.markdown("## ⚙️ Configuración")
    
    # Configuración del navegador
    st.sidebar.markdown("### Navegador")
    headless = st.sidebar.checkbox(
        "Modo headless (sin ventana)", 
        value=True, 
        help="Ejecutar el navegador en segundo plano"
    )
    timeout = st.sidebar.slider(
        "Timeout (segundos)", 
        min_value=10, 
        max_value=60, 
        value=30,
        help="Tiempo máximo de espera para operaciones"
    )
    
    # Información del sistema
    st.sidebar.markdown("### 📋 Estado del Sistema")
    status = get_session_status()
    
    if status['logged_in']:
        st.sidebar.success("✅ Conectado a Nubox")
    else:
        st.sidebar.error("❌ No conectado")
    
    if status['navigation_complete']:
        st.sidebar.success("✅ Navegación completada")
    else:
        st.sidebar.warning("⏳ Esperando navegación")
    
    if status['dropdown_options_loaded']:
        st.sidebar.success("✅ Parámetros cargados")
    else:
        st.sidebar.warning("⏳ Parámetros pendientes")
    
    return headless, timeout