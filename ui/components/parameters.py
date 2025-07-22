#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente de configuración de parámetros para el RPA Nubox.
"""

import streamlit as st
import datetime
from utils.date_utils import should_use_monthly_extraction, generate_monthly_date_ranges, get_month_name_es

def render_parameters_section():
    """Renderiza la sección de configuración de parámetros del reporte."""
    st.markdown('<h2 class="section-header">📊 Configuración del Reporte</h2>', unsafe_allow_html=True)
    
    # Configuración de fechas
    fecha_desde, fecha_hasta = _render_date_section()
    
    # Dropdowns dinámicos
    dropdown_selections, selected_accounts, selected_companies = _render_dropdown_section()
    
    # Mostrar resumen de configuración múltiple
    _render_multiple_summary(selected_companies, selected_accounts, fecha_desde, fecha_hasta)
    
    return fecha_desde, fecha_hasta, dropdown_selections, selected_accounts, selected_companies

def _render_date_section():
    """Renderiza la sección de configuración de fechas."""
    st.markdown("### 📅 Período del Reporte")
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_desde = st.date_input(
            "Fecha desde", 
            value=datetime.date(2025, 1, 1),
            help="Fecha de inicio del reporte"
        )
    
    with col2:
        fecha_hasta = st.date_input(
            "Fecha hasta", 
            value=datetime.date.today(),
            help="Fecha de fin del reporte"
        )
    
    # Mostrar información sobre modo mensual
    _render_monthly_mode_info(fecha_desde, fecha_hasta)
    
    return fecha_desde, fecha_hasta

def _render_monthly_mode_info(fecha_desde, fecha_hasta):
    """Renderiza información sobre el modo de extracción mensual."""
    if fecha_desde and fecha_hasta:
        delta_days = (fecha_hasta - fecha_desde).days
        use_monthly = should_use_monthly_extraction(fecha_desde, fecha_hasta)
        
        if use_monthly:
            monthly_ranges = generate_monthly_date_ranges(fecha_desde, fecha_hasta)
            
            st.info(f"""
            🗓️ **Modo Mensual Activado**
            
            Rango detectado: {delta_days} días  
            Se generarán **{len(monthly_ranges)} reportes mensuales** automáticamente:
            """)
            
            # Mostrar vista previa de los meses
            months_preview = []
            for i, (start, end) in enumerate(monthly_ranges[:5], 1):  # Mostrar máximo 5
                month_name = get_month_name_es(start)
                months_preview.append(f"{i}. {month_name}: {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}")
            
            for preview in months_preview:
                st.text(preview)
            
            if len(monthly_ranges) > 5:
                st.text(f"... y {len(monthly_ranges) - 5} meses adicionales")
            
            st.warning("⚠️ Las extracciones mensuales pueden tomar considerablemente más tiempo.")
        else:
            st.success(f"✅ **Modo Estándar** - Rango: {delta_days} días (se extraerá como un solo reporte)")

def _render_dropdown_section():
    """Renderiza la sección de dropdowns dinámicos."""
    # Verificar si las opciones están cargadas
    if not st.session_state.get('dropdown_options_loaded', False):
        st.warning("⚠️ Primero debes inicializar el RPA para cargar las opciones disponibles.")
        return {}, [], []
    
    dropdown_options = st.session_state.get('dropdown_options', {})
    dropdown_selections = {}
    selected_accounts = []
    selected_companies = []
    
    st.markdown("### 🔽 Filtros del Reporte")
    
    # Debug: Mostrar estructura de dropdown_options
    if st.checkbox("🔍 Mostrar debug de opciones", value=False):
        st.json(dropdown_options)
    
    for dropdown_name, dropdown_config in dropdown_options.items():
        # Extraer opciones basándose en el formato de datos
        if isinstance(dropdown_config, dict) and "options" in dropdown_config:
            options = dropdown_config["options"]
        elif isinstance(dropdown_config, list):
            options = dropdown_config
        else:
            st.warning(f"Formato no reconocido para {dropdown_name}: {type(dropdown_config)}")
            continue
        
        if not options:
            continue
        
        if dropdown_name == "Empresa":
            selected_companies, dropdown_selections[dropdown_name] = _render_company_selection(
                options, None, dropdown_selections, dropdown_name
            )
        elif dropdown_name == "Cuenta Contable":
            selected_accounts, dropdown_selections[dropdown_name] = _render_account_selection(
                options, None, dropdown_selections, dropdown_name, selected_companies
            )
        else:
            dropdown_selections[dropdown_name] = _render_other_dropdown(
                dropdown_name, options, None, dropdown_selections
            )
    
    return dropdown_selections, selected_accounts, selected_companies

def _render_multiple_summary(selected_companies, selected_accounts, fecha_desde, fecha_hasta):
    """Renderiza el resumen de configuración múltiple incluyendo información mensual."""
    if selected_companies and selected_accounts:
        total_combinations = len(selected_companies) * len(selected_accounts)
        
        # Calcular si habrá extracciones mensuales
        use_monthly = should_use_monthly_extraction(fecha_desde, fecha_hasta) if fecha_desde and fecha_hasta else False
        monthly_count = len(generate_monthly_date_ranges(fecha_desde, fecha_hasta)) if use_monthly else 1
        
        total_extractions = total_combinations * monthly_count
        
        st.markdown("---")
        st.markdown("### 📊 Resumen de Configuración")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Empresas", len(selected_companies))
        
        with col2:
            st.metric("Cuentas", len(selected_accounts))
        
        with col3:
            st.metric("Combinaciones", total_combinations)
        
        with col4:
            if use_monthly:
                st.metric("Total Extracciones", total_extractions, delta=f"{monthly_count} meses")
            else:
                st.metric("Total Extracciones", total_extractions)
        
        # Información detallada
        if use_monthly:
            st.info(f"""
            🗓️ **Procesamiento Mensual Configurado**
            - {total_combinations} combinaciones × {monthly_count} meses = **{total_extractions} extracciones totales**
            - Tiempo estimado: ~{total_extractions * 2}-{total_extractions * 3} minutos
            """)
        else:
            st.info(f"""
            📊 **Procesamiento Estándar**
            - {total_combinations} combinaciones en un solo período
            - Tiempo estimado: ~{total_combinations * 2}-{total_combinations * 3} minutos
            """)
        
        # Lista de empresas y cuentas seleccionadas
        with st.expander("Ver selecciones detalladas"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Empresas seleccionadas:**")
                for empresa in selected_companies:
                    st.text(f"• {empresa}")
            
            with col2:
                st.markdown("**Cuentas seleccionadas:**")
                for cuenta in selected_accounts:
                    st.text(f"• {cuenta}")

def _render_company_selection(options, current_selected, dropdown_selections, dropdown_name):
    """Renderiza la selección de empresas (simple o múltiple)."""
    st.markdown(f"#### 🏢 {dropdown_name}")
    
    # Modo de selección
    selection_mode = st.radio(
        "Modo de selección",
        ["Una empresa", "Múltiples empresas"],
        key=f"{dropdown_name}_mode",
        horizontal=True
    )
    
    if selection_mode == "Una empresa":
        selected = st.selectbox(
            f"Seleccionar {dropdown_name}",
            options,
            key=f"{dropdown_name}_single"
        )
        return [selected] if selected else [], selected
    else:
        selected = st.multiselect(
            f"Seleccionar {dropdown_name}s",
            options,
            key=f"{dropdown_name}_multi"
        )
        return selected, selected

def _render_account_selection(options, current_selected, dropdown_selections, dropdown_name, selected_companies):
    """Renderiza la selección de cuentas contables (simple o múltiple)."""
    st.markdown(f"#### 💰 {dropdown_name}")
    
    if not selected_companies:
        st.warning("⚠️ Primero selecciona al menos una empresa")
        return [], None
    
    # Modo de selección
    selection_mode = st.radio(
        "Modo de selección de cuentas",
        ["Una cuenta", "Múltiples cuentas"],
        key=f"{dropdown_name}_mode",
        horizontal=True
    )
    
    if selection_mode == "Una cuenta":
        selected = st.selectbox(
            f"Seleccionar {dropdown_name}",
            options,
            key=f"{dropdown_name}_single"
        )
        return [selected] if selected else [], selected
    else:
        selected = st.multiselect(
            f"Seleccionar {dropdown_name}s",
            options,
            key=f"{dropdown_name}_multi"
        )
        return selected, selected

def _render_other_dropdown(dropdown_name, options, current_selected, dropdown_selections):
    """Renderiza otros dropdowns estándar."""
    return st.selectbox(
        dropdown_name,
        options,
        key=f"{dropdown_name}_dropdown"
    )