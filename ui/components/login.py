#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente de login para el RPA Nubox.
"""

import streamlit as st

def render_login_section():
    """Renderiza la sección de login."""
    st.markdown('<h2 class="section-header">🔐 Credenciales de Nubox</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input(
            "RUT de usuario", 
            placeholder="12345678-9",
            help="Ingresa tu RUT sin puntos, con guión"
        )
    
    with col2:
        password = st.text_input(
            "Contraseña", 
            type="password",
            help="Tu contraseña de Nubox"
        )
    
    # URL personalizada (avanzado)
    with st.expander("⚙️ Configuración avanzada"):
        custom_url = st.text_input(
            "URL de Nubox (opcional)", 
            value="https://web.nubox.com/Login/Account/Login?ReturnUrl=%2FSistemaLogin",
            help="URL personalizada de login"
        )
    
    return username, password, custom_url