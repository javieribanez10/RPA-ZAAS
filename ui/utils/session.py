#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Manejo del estado de sesión de Streamlit para el RPA Nubox.
"""

import streamlit as st

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
    if 'dropdown_options_loaded' not in st.session_state:
        st.session_state.dropdown_options_loaded = False
    if 'report_generated' not in st.session_state:
        st.session_state.report_generated = False

def clear_session_state():
    """Limpia completamente el estado de la sesión."""
    # Cerrar servicio si existe
    if st.session_state.get('nubox_service'):
        try:
            st.session_state.nubox_service.close()
        except:
            pass
    
    # Limpiar estado
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def reset_process_state():
    """Reinicia solo el estado del proceso, manteniendo la configuración."""
    keys_to_reset = ['logged_in', 'navigation_complete', 'report_generated']
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

def get_session_status():
    """Retorna el estado actual de la sesión."""
    return {
        'logged_in': st.session_state.get('logged_in', False),
        'navigation_complete': st.session_state.get('navigation_complete', False),
        'dropdown_options_loaded': st.session_state.get('dropdown_options_loaded', False),
        'report_generated': st.session_state.get('report_generated', False),
        'nubox_service_active': st.session_state.get('nubox_service') is not None
    }