#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componentes de UI para autenticación
Formulario de login minimalista tipo modal
"""

import streamlit as st
from services.supabase_auth import SupabaseAuth
from typing import Optional, Dict

def render_login_form() -> Optional[Dict]:
    """
    Renderizar formulario de login minimalista tipo modal
    
    Returns:
        Optional[Dict]: Datos del usuario si login exitoso
    """
    # Espaciado superior
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Centrar el modal - MUCHO MÁS ANCHO
    col1, col2, col3 = st.columns([0.5, 2, 0.5])
    
    with col2:
        # Formulario dentro de un contenedor
        with st.container():
            # Título centrado con mejor diseño
            st.markdown("""
            <div style="text-align: center; margin-bottom: 2.5rem;">
                <h1 style="color: #2c3e50; font-weight: 300; margin: 0; font-size: 2.5rem;">🔐</h1>
                <h2 style="color: #34495e; font-weight: 400; margin: 0.5rem 0 0 0; font-size: 1.8rem;">Iniciar Sesión</h2>
                <p style="color: #7f8c8d; margin: 0.5rem 0 0 0; font-size: 1rem;">Accede al sistema NUBOX DBViewer</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Formulario
            auth = SupabaseAuth()
            
            with st.form("login_form", clear_on_submit=False):
                # Email con mejor espaciado
                st.markdown("**📧 Email**")
                email = st.text_input(
                    "Email",
                    placeholder="tu@email.com",
                    label_visibility="collapsed"
                )
                
                # Espaciado entre campos
                st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
                
                # Password con mejor espaciado
                st.markdown("**🔒 Contraseña**")
                password = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="••••••••••",
                    label_visibility="collapsed"
                )
                
                # Espaciado antes del botón
                st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                
                # Botón de login más grande
                login_button = st.form_submit_button(
                    "🚀 Ingresar al Sistema",
                    use_container_width=True,
                    type="primary"
                )
                
                # Lógica de autenticación
                if login_button:
                    if email and password:
                        with st.spinner("🔍 Verificando credenciales..."):
                            success, message, user_data = auth.login_user(email, password)
                        
                        if success:
                            st.success("✅ Login exitoso")
                            st.session_state.authenticated = True
                            st.session_state.user_data = user_data
                            st.rerun()
                            return user_data
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("⚠️ Por favor completa todos los campos")
    
    return None

def render_user_menu(user_data: Dict) -> bool:
    """Renderizar menú de usuario autenticado minimalista"""
    auth = SupabaseAuth()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Usuario")
        
        # Info del usuario
        st.write(f"**{user_data.get('full_name', 'Usuario')}**")
        st.write(f"{user_data.get('email', '')}")
        
        # Botones
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Refrescar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("Salir", use_container_width=True):
                auth.logout_user()
                for key in ['authenticated', 'user_data']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
                return True
    
    return False

def check_authentication() -> Optional[Dict]:
    """Verificar si el usuario está autenticado"""
    # Verificar session state primero
    if st.session_state.get('authenticated') and st.session_state.get('user_data'):
        return st.session_state.user_data
    
    # Verificar sesión de Supabase
    auth = SupabaseAuth()
    user_data = auth.check_session()
    
    if user_data:
        st.session_state.authenticated = True
        st.session_state.user_data = user_data
        return user_data
    
    return None

def require_authentication():
    """Función para requerir autenticación - Muestra login minimalista"""
    user_data = check_authentication()
    
    if not user_data:
        # CSS mejorado - Modal más ancho y diseño moderno
        st.markdown("""
        <style>
        /* Ocultar elementos de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        .stDecoration {display: none;}
        
        /* Fondo limpio con gradiente */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        /* Contenedor principal centrado */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1000px !important;
        }
        
        /* Modal de login MÁS ANCHO */
        .stForm {
            background: white;
            border: none;
            border-radius: 15px;
            padding: 3rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            margin: 2rem auto;
            max-width: 700px !important;
            width: 100% !important;
        }
        
        /* Inputs más grandes y modernos */
        .stTextInput > div > div > input {
            border: 2px solid #e1e8ed !important;
            border-radius: 10px !important;
            padding: 16px 20px !important;
            font-size: 16px !important;
            background: #f8f9fa !important;
            color: #2c3e50 !important;
            transition: all 0.3s ease;
            height: 60px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea !important;
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
            background: white !important;
        }
        
        /* Placeholder text más visible */
        .stTextInput > div > div > input::placeholder {
            color: #95a5a6 !important;
            opacity: 1 !important;
            font-weight: 400;
        }
        
        /* Labels personalizados */
        .stMarkdown p {
            font-size: 16px !important;
            color: #2c3e50 !important;
            font-weight: 600 !important;
            margin-bottom: 8px !important;
        }
        
        /* Botón principal más grande y atractivo */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 18px 32px !important;
            font-size: 18px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease;
            width: 100% !important;
            height: 60px !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
        }
        
        /* Títulos mejorados */
        h1, h2 {
            color: #2c3e50 !important;
            font-weight: 300 !important;
        }
        
        /* Ocultar sidebar en login */
        .css-1d391kg {display: none;}
        .css-17eq0hr {display: none;}
        section[data-testid="stSidebar"] {display: none;}
        
        /* Asegurar que el contenedor sea visible */
        .stTextInput {
            visibility: visible !important;
        }
        
        /* Form container mejorado */
        [data-testid="stForm"] {
            background: white;
            border: none;
            border-radius: 15px;
            padding: 3rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            margin: 2rem auto;
            max-width: 700px !important;
            width: 100% !important;
        }
        
        /* Espaciado mejorado */
        .stMarkdown {
            margin-bottom: 0.5rem;
        }
        
        /* Mensajes de error y éxito */
        .stAlert {
            border-radius: 10px;
            padding: 1rem;
            font-size: 14px;
            margin: 1rem 0;
        }
        
        </style>
        """, unsafe_allow_html=True)
        
        user_data = render_login_form()
        
        if not user_data:
            st.stop()
    
    return user_data