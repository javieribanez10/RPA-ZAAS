#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente de progreso y logs para el RPA Nubox.
"""

import streamlit as st

def render_progress_section():
    """Renderiza la sección de progreso y logs."""
    st.markdown('<h2 class="section-header">📈 Progreso</h2>', unsafe_allow_html=True)
    
    # Contenedor para el progreso
    progress_container = st.container()
    
    # Contenedor para logs
    log_container = st.expander("📝 Ver logs detallados", expanded=False)
    
    return progress_container, log_container