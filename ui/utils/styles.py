#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Estilos CSS personalizados para la aplicación Streamlit.
"""

import streamlit as st

def apply_custom_styles():
    """Aplica los estilos CSS personalizados a la aplicación."""
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