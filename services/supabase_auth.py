#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cliente de autenticación para Supabase
Maneja el login y autenticación de usuarios para el DB Viewer
"""

import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib
import time
from typing import Dict, Optional, Tuple

# Cargar variables de entorno
load_dotenv()

class SupabaseAuth:
    """Cliente de autenticación con Supabase"""
    
    def __init__(self):
        """Inicializar cliente Supabase"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            st.error("❌ Error: Configuración de Supabase no encontrada")
            st.stop()
        
        try:
            self.supabase: Client = create_client(self.url, self.key)
        except Exception as e:
            st.error(f"❌ Error conectando a Supabase: {str(e)}")
            st.stop()
    
    def register_user(self, email: str, password: str, full_name: str = "") -> Tuple[bool, str]:
        """
        Registrar nuevo usuario
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            full_name: Nombre completo (opcional)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Registrar usuario con Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            if response.user:
                return True, "Usuario registrado exitosamente. Revisa tu email para verificar la cuenta."
            else:
                return False, "Error en el registro"
                
        except Exception as e:
            return False, f"Error durante el registro: {str(e)}"
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Iniciar sesión de usuario
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, user_data)
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                user_data = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get("full_name", ""),
                    "last_sign_in": response.user.last_sign_in_at,
                    "access_token": response.session.access_token
                }
                return True, "Login exitoso", user_data
            else:
                return False, "Credenciales inválidas", None
                
        except Exception as e:
            return False, f"Error durante el login: {str(e)}", None
    
    def logout_user(self) -> bool:
        """
        Cerrar sesión del usuario
        
        Returns:
            bool: True si logout exitoso
        """
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            st.error(f"Error durante logout: {str(e)}")
            return False
    
    def reset_password(self, email: str) -> Tuple[bool, str]:
        """
        Enviar email de reset de contraseña
        
        Args:
            email: Email del usuario
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.supabase.auth.reset_password_email(email)
            return True, "Email de reset enviado exitosamente"
        except Exception as e:
            return False, f"Error enviando reset: {str(e)}"
    
    def check_session(self) -> Optional[Dict]:
        """
        Verificar sesión actual
        
        Returns:
            Optional[Dict]: Datos del usuario si hay sesión activa
        """
        try:
            session = self.supabase.auth.get_session()
            if session and session.user:
                return {
                    "id": session.user.id,
                    "email": session.user.email,
                    "full_name": session.user.user_metadata.get("full_name", ""),
                    "access_token": session.access_token
                }
            return None
        except:
            return None