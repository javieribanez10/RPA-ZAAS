#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Página para mostrar resultados de extracciones mensuales.
"""

import streamlit as st
import pandas as pd
from utils.date_utils import format_date_for_nubox, get_month_name_es

def show_monthly_results(monthly_results):
    """Muestra los resultados de extracciones mensuales."""
    st.markdown("## 📅 Resultados de Extracciones Mensuales")
    
    # Resumen general
    successful_months = sum(1 for result in monthly_results.values() if result['success'])
    total_months = len(monthly_results)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Meses", total_months)
    with col2:
        st.metric("Meses Exitosos", successful_months)
    with col3:
        success_rate = (successful_months / total_months * 100) if total_months > 0 else 0
        st.metric("Tasa de Éxito", f"{success_rate:.1f}%")
    
    st.markdown("---")
    
    # Mostrar resultados por mes
    for month_key, month_data in monthly_results.items():
        month_name = month_data['month_name']
        year = month_data['year']
        date_range = month_data['date_range']
        result = month_data['result']
        success = month_data['success']
        
        # Expandir para cada mes
        with st.expander(f"{'✅' if success else '❌'} {month_name} {year} - {format_date_for_nubox(date_range[0])} a {format_date_for_nubox(date_range[1])}", expanded=success):
            if success:
                _show_monthly_success_result(month_name, year, result)
            else:
                st.error(f"❌ Error en la extracción de {month_name} {year}")
                if isinstance(result, str):
                    st.text(f"Detalle del error: {result}")

def _show_monthly_success_result(month_name, year, result):
    """Muestra el resultado exitoso de un mes específico."""
    if isinstance(result, dict) and '_summary' in result:
        # Resultado múltiple (empresas/cuentas)
        summary = result['_summary']
        
        st.success(f"✅ Extracción múltiple completada para {month_name} {year}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Combinaciones", summary.get('total_combinations', 0))
        with col2:
            st.metric("Exitosas", summary.get('successful_extractions', 0))
        with col3:
            st.metric("Fallidas", summary.get('failed_extractions', 0))
        
        # Mostrar detalles de cada combinación
        st.markdown("### Detalle por Combinación")
        for key, combination_result in result.items():
            if key != '_summary':
                _show_combination_detail(key, combination_result, month_name)
                
    elif isinstance(result, tuple) and len(result) == 2:
        # Resultado simple (DataFrame, file_path)
        df, file_path = result
        
        st.success(f"✅ Reporte extraído para {month_name} {year}")
        
        if not df.empty:
            st.metric("Filas extraídas", len(df))
            
            # Mostrar vista previa de los datos
            st.markdown("### Vista Previa de Datos")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Botón de descarga
            if file_path:
                with open(file_path, 'rb') as f:
                    st.download_button(
                        label=f"📥 Descargar {month_name} {year}",
                        data=f.read(),
                        file_name=f"reporte_{month_name}_{year}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.warning("No se encontraron datos en el reporte")
    else:
        st.info(f"Resultado procesado para {month_name} {year}")

def _show_combination_detail(combination_key, combination_result, month_name):
    """Muestra el detalle de una combinación específica."""
    if combination_result.get('success', False):
        with st.expander(f"✅ {combination_key}", expanded=False):
            data = combination_result.get('data', pd.DataFrame())
            file_path = combination_result.get('file_path')
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Filas", combination_result.get('rows_count', 0))
            with col2:
                st.metric("Columnas", combination_result.get('columns_count', 0))
            
            if not data.empty:
                st.dataframe(data.head(5), use_container_width=True)
                
                # Botón de descarga individual
                if file_path:
                    try:
                        with open(file_path, 'rb') as f:
                            st.download_button(
                                label=f"📥 Descargar {combination_key}",
                                data=f.read(),
                                file_name=f"{combination_key}_{month_name}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"download_{combination_key}_{month_name}"
                            )
                    except Exception as e:
                        st.warning(f"No se pudo generar el botón de descarga: {str(e)}")
    else:
        with st.expander(f"❌ {combination_key}", expanded=False):
            st.error(f"Error: {combination_result.get('error', 'Error desconocido')}")

def show_monthly_download_options(monthly_results):
    """Muestra opciones de descarga consolidada para todos los meses."""
    st.markdown("### 📦 Descargas Consolidadas")
    
    successful_results = {k: v for k, v in monthly_results.items() if v['success']}
    
    if successful_results:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Descargar Todos los Meses (ZIP)", use_container_width=True):
                _create_monthly_zip_download(successful_results)
        
        with col2:
            if st.button("📊 Consolidar en Excel", use_container_width=True):
                _create_consolidated_excel(successful_results)
    else:
        st.warning("No hay resultados exitosos para descargar")

def _create_monthly_zip_download(successful_results):
    """Crea un archivo ZIP con todos los reportes mensuales."""
    try:
        import zipfile
        import io
        import tempfile
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for month_key, month_data in successful_results.items():
                month_name = month_data['month_name']
                year = month_data['year']
                result = month_data['result']
                
                # Agregar archivos al ZIP según el tipo de resultado
                if isinstance(result, tuple) and len(result) == 2:
                    df, file_path = result
                    if file_path and not df.empty:
                        try:
                            with open(file_path, 'rb') as f:
                                zip_file.writestr(f"{month_name}_{year}.xlsx", f.read())
                        except Exception as e:
                            st.warning(f"No se pudo agregar {month_name} al ZIP: {str(e)}")
                
                elif isinstance(result, dict) and '_summary' in result:
                    # Para resultados múltiples, agregar cada combinación
                    for combo_key, combo_result in result.items():
                        if combo_key != '_summary' and combo_result.get('success'):
                            file_path = combo_result.get('file_path')
                            if file_path:
                                try:
                                    with open(file_path, 'rb') as f:
                                        safe_combo_key = combo_key.replace('/', '_').replace('\\', '_')
                                        zip_file.writestr(f"{month_name}_{year}_{safe_combo_key}.xlsx", f.read())
                                except Exception as e:
                                    st.warning(f"No se pudo agregar {combo_key} de {month_name} al ZIP: {str(e)}")
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📥 Descargar ZIP Completo",
            data=zip_buffer.getvalue(),
            file_name="reportes_mensuales_completos.zip",
            mime="application/zip"
        )
        
    except Exception as e:
        st.error(f"Error creando archivo ZIP: {str(e)}")

def _create_consolidated_excel(successful_results):
    """Crea un archivo Excel consolidado con todos los meses."""
    try:
        import io
        
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Hoja de resumen
            summary_data = []
            for month_key, month_data in successful_results.items():
                month_name = month_data['month_name']
                year = month_data['year']
                date_range = month_data['date_range']
                
                summary_data.append({
                    'Mes': month_name,
                    'Año': year,
                    'Fecha_Desde': format_date_for_nubox(date_range[0]),
                    'Fecha_Hasta': format_date_for_nubox(date_range[1]),
                    'Estado': 'Exitoso'
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hojas individuales por mes
            for month_key, month_data in successful_results.items():
                month_name = month_data['month_name']
                year = month_data['year']
                result = month_data['result']
                
                sheet_name = f"{month_name}_{year}"[:31]  # Límite de caracteres en nombres de hojas
                
                if isinstance(result, tuple) and len(result) == 2:
                    df, _ = result
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        excel_buffer.seek(0)
        
        st.download_button(
            label="📊 Descargar Excel Consolidado",
            data=excel_buffer.getvalue(),
            file_name="reportes_mensuales_consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"Error creando archivo Excel consolidado: {str(e)}")