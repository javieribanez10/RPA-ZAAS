#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Página de resultados para reportes múltiples del RPA Nubox.
Maneja la visualización de resultados de múltiples empresas y cuentas.
"""

import streamlit as st
import pandas as pd
import datetime
import io
import os

def show_multiple_results(results, selected_accounts):
    """Muestra los resultados de múltiples reportes extraídos con exportación automática a MongoDB."""
    st.markdown('<h2 class="section-header">📊 Resultados de Múltiples Reportes</h2>', unsafe_allow_html=True)
    
    if not results or '_summary' not in results:
        st.error("❌ No se obtuvieron resultados válidos de los reportes múltiples.")
        return
    
    summary = results['_summary']
    
    # Mostrar resumen general
    _show_general_summary(summary, selected_accounts)
    
    # Separar resultados exitosos y fallidos
    successful_results, failed_results = _separate_results(results, selected_accounts)
    
    # Exportación automática a MongoDB para reportes múltiples
    if successful_results:
        _handle_multiple_mongodb_export(successful_results)
    
    # Mostrar resultados exitosos en tabs
    if successful_results:
        _show_successful_results_tabs(successful_results)
    
    # Mostrar resultados fallidos
    if failed_results:
        _show_failed_results(failed_results, successful_results)
    
    # Opción para descargar resumen completo
    _show_summary_download(successful_results, failed_results)

def show_multiple_company_account_results(results, selected_companies, selected_accounts):
    """Muestra los resultados de múltiples reportes extraídos para empresas y cuentas."""
    st.markdown('<h2 class="section-header">📊 Resultados de Múltiples Empresas y Cuentas</h2>', unsafe_allow_html=True)
    
    if not results or '_summary' not in results:
        st.error("❌ No se obtuvieron resultados válidos de los reportes múltiples.")
        return
    
    summary = results['_summary']
    
    # Mostrar resumen general para empresas y cuentas
    _show_company_account_summary(summary, selected_companies, selected_accounts)
    
    # Separar resultados exitosos y fallidos para múltiples empresas/cuentas
    successful_results, failed_results = _separate_company_account_results(results)
    
    # Exportación automática a MongoDB para reportes múltiples empresa-cuenta
    if successful_results:
        _handle_company_account_mongodb_export(successful_results, selected_companies, selected_accounts)
    
    # Mostrar resultados organizados por empresa
    if successful_results:
        _show_company_account_results_organized(successful_results, selected_companies, selected_accounts)
    
    # Mostrar resultados fallidos
    if failed_results:
        _show_company_account_failed_results(failed_results, successful_results)
    
    # Descargar resumen completo para múltiples empresas y cuentas
    _show_company_account_summary_download(successful_results, failed_results)

def _show_general_summary(summary, selected_accounts):
    """Muestra el resumen general para múltiples cuentas."""
    st.markdown("### 📈 Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Cuentas", summary['total_accounts'])
    with col2:
        st.metric("✅ Exitosas", summary['successful_extractions'])
    with col3:
        st.metric("❌ Fallidas", summary['failed_extractions'])
    with col4:
        st.metric("📈 Tasa de Éxito", f"{summary['success_rate']:.1f}%")
    
    # Mostrar estado visual
    if summary['success_rate'] >= 80:
        st.success(f"🎉 ¡Excelente! Se procesaron exitosamente {summary['successful_extractions']} de {summary['total_accounts']} cuentas.")
    elif summary['success_rate'] >= 50:
        st.warning(f"⚠️ Se procesaron {summary['successful_extractions']} de {summary['total_accounts']} cuentas. Revisa las que fallaron.")
    else:
        st.error(f"❌ Solo se procesaron {summary['successful_extractions']} de {summary['total_accounts']} cuentas exitosamente.")

def _show_company_account_summary(summary, selected_companies, selected_accounts):
    """Muestra el resumen general para múltiples empresas y cuentas."""
    st.markdown("### 📈 Resumen General")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🏢 Empresas", len(selected_companies))
    with col2:
        st.metric("💰 Cuentas", len(selected_accounts))
    with col3:
        st.metric("📊 Total Combinaciones", summary.get('total_combinaciones', len(selected_companies) * len(selected_accounts)))
    with col4:
        st.metric("✅ Exitosas", summary['successful_extractions'])
    with col5:
        st.metric("📈 Tasa de Éxito", f"{summary['success_rate']:.1f}%")
    
    # Mostrar estado visual mejorado
    total_expected = len(selected_companies) * len(selected_accounts)
    if summary['success_rate'] >= 80:
        st.success(f"🎉 ¡Excelente! Se procesaron exitosamente {summary['successful_extractions']} de {total_expected} combinaciones empresa-cuenta.")
    elif summary['success_rate'] >= 50:
        st.warning(f"⚠️ Se procesaron {summary['successful_extractions']} de {total_expected} combinaciones. Revisa las que fallaron.")
    else:
        st.error(f"❌ Solo se procesaron {summary['successful_extractions']} de {total_expected} combinaciones exitosamente.")

def _separate_results(results, selected_accounts):
    """Separa los resultados en exitosos y fallidos."""
    successful_results = []
    failed_results = []
    
    for account in selected_accounts:
        if account in results and account != '_summary':
            result = results[account]
            if result.get('success', False):
                successful_results.append((account, result))
            else:
                failed_results.append((account, result))
    
    return successful_results, failed_results

def _separate_company_account_results(results):
    """Separa los resultados de empresa-cuenta en exitosos y fallidos."""
    successful_results = []
    failed_results = []
    
    for key, result in results.items():
        if key != '_summary':
            if result.get('success', False):
                successful_results.append((key, result))
            else:
                failed_results.append((key, result))
    
    return successful_results, failed_results

def _handle_multiple_mongodb_export(successful_results):
    """Maneja la exportación múltiple a MongoDB."""
    st.markdown("### 🚀 Exportación Automática a MongoDB")
    
    with st.spinner(f"Exportando {len(successful_results)} reportes a MongoDB..."):
        try:
            from services.mongodb_client import NuboxMongoClient
            
            mongo_client = NuboxMongoClient()
            export_summary = {
                'total_reportes': len(successful_results),
                'exportados_exitosos': 0,
                'exportados_fallidos': 0,
                'document_ids': [],
                'errores': []
            }
            
            # Exportar cada reporte exitoso
            for account, result in successful_results:
                try:
                    df = result.get('data')
                    if df is not None and not df.empty:
                        # Extraer información de la empresa desde los atributos del DataFrame
                        company_info = df.attrs.get('company_info', {}) if hasattr(df, 'attrs') else {}
                        
                        # Preparar metadatos específicos para esta cuenta
                        report_metadata = {
                            'archivo_origen': os.path.basename(result.get('file_path', '')) or 'streamlit_multiple_extraction',
                            'cuenta_contable': account,
                            'fecha_extraccion': datetime.datetime.now().isoformat(),
                            'parametros_streamlit': {
                                'formato_salida': 'EXCEL',
                                'include_subcuentas': st.session_state.get('dropdown_options', {}).get('Incluir Subcuentas', {}).get('selected', 'NO'),
                                'procesamiento_multiple': True,
                                'total_cuentas': len(successful_results)
                            }
                        }
                        
                        export_result = mongo_client.export_nubox_dataframe(
                            df=df,
                            company_info=company_info,
                            report_metadata=report_metadata
                        )
                        
                        if export_result['success']:
                            export_summary['exportados_exitosos'] += 1
                            export_summary['document_ids'].append({
                                'cuenta': account,
                                'document_id': export_result['document_id'],
                                'filas': export_result['exported_rows'],
                                'errores': export_result['errors']
                            })
                        else:
                            export_summary['exportados_fallidos'] += 1
                            export_summary['errores'].append({
                                'cuenta': account,
                                'errores': ['DataFrame vacío o no disponible']
                            })
                            
                except Exception as e:
                    export_summary['exportados_fallidos'] += 1
                    export_summary['errores'].append({
                        'cuenta': account,
                        'errores': [str(e)]
                    })
            
            mongo_client.disconnect()
            
            # Mostrar resultado de la exportación masiva
            if export_summary['exportados_exitosos'] > 0:
                st.success(f"✅ **{export_summary['exportados_exitosos']} reportes exportados exitosamente a MongoDB**")
                
                # Mostrar detalles de la exportación múltiple
                with st.expander("📋 Detalles de la Exportación Masiva", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Reportes Exportados", export_summary['exportados_exitosos'])
                    with col2:
                        st.metric("❌ Fallos de Exportación", export_summary['exportados_fallidos'])
                    with col3:
                        total_filas = sum(doc['filas'] for doc in export_summary['document_ids'])
                        st.metric("📝 Total Filas", total_filas)
                    with col4:
                        st.metric("📅 Fecha", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
                    
                    st.write("**IDs de Documentos Exportados:**")
                    for doc_info in export_summary['document_ids']:
                        st.write(f"- **{doc_info['cuenta']}**: `{doc_info['document_id']}` ({doc_info['filas']} filas)")
            
            if export_summary['exportados_fallidos'] > 0:
                st.warning(f"⚠️ **{export_summary['exportados_fallidos']} reportes fallaron en la exportación**")
                
                with st.expander("❌ Ver errores de exportación", expanded=False):
                    for error_info in export_summary['errores']:
                        st.write(f"**{error_info['cuenta']}**:")
                        for error in error_info['errores']:
                            st.write(f"  - {error}")
        
        except ImportError:
            st.warning("⚠️ Cliente MongoDB no disponible. Instalar con: `pip install pymongo`")
        except Exception as e:
            st.error(f"❌ Error durante la exportación masiva: {str(e)}")

def _handle_company_account_mongodb_export(successful_results, selected_companies, selected_accounts):
    """Maneja la exportación múltiple a MongoDB para empresas y cuentas."""
    st.markdown("### 🚀 Exportación Automática a MongoDB")
    
    with st.spinner(f"Exportando {len(successful_results)} reportes empresa-cuenta a MongoDB..."):
        try:
            from services.mongodb_client import NuboxMongoClient
            
            mongo_client = NuboxMongoClient()
            export_summary = {
                'total_reportes': len(successful_results),
                'exportados_exitosos': 0,
                'exportados_fallidos': 0,
                'document_ids': [],
                'errores': []
            }
            
            # Exportar cada reporte exitoso
            for combination_key, result in successful_results:
                try:
                    df = result.get('data')
                    if df is not None and not df.empty:
                        # Extraer información de la empresa desde los atributos del DataFrame
                        company_info = df.attrs.get('company_info', {}) if hasattr(df, 'attrs') else {}
                        
                        # Preparar metadatos específicos para esta combinación
                        report_metadata = {
                            'archivo_origen': os.path.basename(result.get('file_path', '')) or 'streamlit_multiple_extraction',
                            'empresa': result.get('company', ''),
                            'cuenta_contable': result.get('account', ''),
                            'combinacion': combination_key,
                            'fecha_extraccion': datetime.datetime.now().isoformat(),
                            'parametros_streamlit': {
                                'formato_salida': 'EXCEL',
                                'include_subcuentas': st.session_state.get('dropdown_options', {}).get('Incluir Subcuentas', {}).get('selected', 'NO'),
                                'procesamiento_multiple': True,
                                'total_empresas': len(selected_companies),
                                'total_cuentas': len(selected_accounts),
                                'total_combinaciones': len(selected_companies) * len(selected_accounts)
                            }
                        }
                        
                        export_result = mongo_client.export_nubox_dataframe(
                            df=df,
                            company_info=company_info,
                            report_metadata=report_metadata
                        )
                        
                        if export_result['success']:
                            export_summary['exportados_exitosos'] += 1
                            export_summary['document_ids'].append({
                                'combinacion': combination_key,
                                'document_id': export_result['document_id'],
                                'filas': export_result['exported_rows'],
                                'errores': export_result['errors']
                            })
                        else:
                            export_summary['exportados_fallidos'] += 1
                            export_summary['errores'].append({
                                'combinacion': combination_key,
                                'errores': ['DataFrame vacío o no disponible']
                            })
                            
                except Exception as e:
                    export_summary['exportados_fallidos'] += 1
                    export_summary['errores'].append({
                        'combinacion': combination_key,
                        'errores': [str(e)]
                    })
            
            mongo_client.disconnect()
            
            # Mostrar resultado de la exportación masiva
            if export_summary['exportados_exitosos'] > 0:
                st.success(f"✅ **{export_summary['exportados_exitosos']} reportes exportados exitosamente a MongoDB**")
                
                # Mostrar detalles de la exportación múltiple
                with st.expander("📋 Detalles de la Exportación Masiva", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Reportes Exportados", export_summary['exportados_exitosos'])
                    with col2:
                        st.metric("❌ Fallos de Exportación", export_summary['exportados_fallidos'])
                    with col3:
                        total_filas = sum(doc['filas'] for doc in export_summary['document_ids'])
                        st.metric("📝 Total Filas", total_filas)
                    with col4:
                        st.metric("📅 Fecha", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
                    
                    st.write("**IDs de Documentos Exportados:**")
                    for doc_info in export_summary['document_ids']:
                        st.write(f"- **{doc_info['combinacion']}**: `{doc_info['document_id']}` ({doc_info['filas']} filas)")
            
            if export_summary['exportados_fallidos'] > 0:
                st.warning(f"⚠️ **{export_summary['exportados_fallidos']} reportes fallaron en la exportación**")
        
        except ImportError:
            st.warning("⚠️ Cliente MongoDB no disponible. Instalar con: `pip install pymongo`")
        except Exception as e:
            st.error(f"❌ Error durante la exportación masiva: {str(e)}")

def _show_successful_results_tabs(successful_results):
    """Muestra los resultados exitosos en tabs."""
    st.markdown("### ✅ Reportes Exitosos")
    
    # Crear tabs para cada reporte exitoso (limitado a 10 para evitar problemas de UI)
    tab_data = successful_results[:10]
    
    if len(successful_results) > 10:
        st.warning(f"⚠️ Mostrando solo los primeros 10 resultados de {len(successful_results)} exitosos.")
    
    if tab_data:
        tab_names = [f"📊 {account[:20]}..." if len(account) > 20 else f"📊 {account}" for account, _ in tab_data]
        tabs = st.tabs(tab_names)
        
        for i, (tab, (account, result)) in enumerate(zip(tabs, tab_data)):
            with tab:
                _show_individual_report_result(account, result)

def _show_company_account_results_organized(successful_results, selected_companies, selected_accounts):
    """Muestra resultados organizados por empresa para múltiples empresas y cuentas."""
    st.markdown("### ✅ Reportes Exitosos por Empresa")
    
    # Organizar resultados por empresa
    company_results = {}
    for combination_key, result in successful_results:
        company = result.get('company', 'Empresa desconocida')
        if company not in company_results:
            company_results[company] = []
        company_results[company].append((combination_key, result))
    
    # Crear tabs por empresa
    if company_results:
        company_names = list(company_results.keys())[:5]  # Limitar a 5 empresas para la UI
        
        if len(company_results) > 5:
            st.warning(f"⚠️ Mostrando solo las primeras 5 empresas de {len(company_results)} con resultados.")
        
        company_tabs = st.tabs([f"🏢 {name[:15]}..." if len(name) > 15 else f"🏢 {name}" for name in company_names])
        
        for company_tab, company in zip(company_tabs, company_names):
            with company_tab:
                st.markdown(f"#### Resultados para: {company}")
                
                company_data = company_results[company]
                
                # Sub-tabs por cuenta dentro de cada empresa
                if len(company_data) > 1:
                    account_names = [f"💰 {result.get('account', 'Cuenta')[:15]}..." 
                                   if len(result.get('account', 'Cuenta')) > 15 
                                   else f"💰 {result.get('account', 'Cuenta')}" 
                                   for _, result in company_data]
                    account_tabs = st.tabs(account_names)
                    
                    for account_tab, (combination_key, result) in zip(account_tabs, company_data):
                        with account_tab:
                            _show_individual_report_result(combination_key, result)
                else:
                    # Solo una cuenta, mostrar directamente
                    combination_key, result = company_data[0]
                    _show_individual_report_result(combination_key, result)

def _show_individual_report_result(combination_key, result):
    """Función auxiliar para mostrar un resultado individual de reporte."""
    account = result.get('account', 'Cuenta desconocida')
    
    # Métricas del reporte individual
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Filas", result.get('rows_count', 0))
    with col2:
        st.metric("📋 Columnas", result.get('columns_count', 0))
    with col3:
        file_status = "Descargado" if result.get('file_path') else "En memoria"
        st.metric("📁 Archivo", file_status)
    
    # Mostrar preview de los datos si están disponibles
    df = result.get('data')
    if df is not None and not df.empty:
        st.markdown("**Vista previa de los datos:**")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Botones de descarga para este reporte
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar CSV
            csv_data = df.to_csv(index=False)
            account_code = result.get('account_code', combination_key.replace(' ', '_'))
            st.download_button(
                label="💾 Descargar CSV",
                data=csv_data,
                file_name=f"reporte_{account_code}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"csv_{combination_key}"
            )
        
        with col2:
            # Descargar Excel
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Excel",
                data=excel_data,
                file_name=f"reporte_{account_code}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{combination_key}"
            )
    else:
        st.info("ℹ️ No hay datos para mostrar, pero el archivo fue descargado exitosamente.")
    
    # Mostrar información del archivo descargado
    file_path = result.get('file_path')
    if file_path and file_path != "Descarga no encontrada":
        st.info(f"📁 Archivo descargado en: {file_path}")

def _show_failed_results(failed_results, successful_results):
    """Muestra los resultados fallidos."""
    st.markdown("### ❌ Reportes Fallidos")
    
    with st.expander(f"Ver detalles de {len(failed_results)} reportes fallidos", expanded=len(successful_results) == 0):
        for account, result in failed_results:
            error_msg = result.get('error', 'Error desconocido')
            st.error(f"**{account}**: {error_msg}")

def _show_company_account_failed_results(failed_results, successful_results):
    """Muestra los resultados fallidos para empresa-cuenta."""
    st.markdown("### ❌ Reportes Fallidos")
    
    with st.expander(f"Ver detalles de {len(failed_results)} reportes fallidos", expanded=len(successful_results) == 0):
        for combination_key, result in failed_results:
            error_msg = result.get('error', 'Error desconocido')
            st.error(f"**{combination_key}**: {error_msg}")

def _show_summary_download(successful_results, failed_results):
    """Muestra las opciones de descarga del resumen."""
    st.markdown("### 📋 Descarga del Resumen Completo")
    
    if successful_results:
        # Crear DataFrame combinado con información de resumen
        summary_data = []
        
        for account, result in successful_results + failed_results:
            summary_data.append({
                'Cuenta': account,
                'Código': result.get('account_code', ''),
                'Estado': 'Exitoso' if result.get('success', False) else 'Fallido',
                'Filas': result.get('rows_count', 0),
                'Columnas': result.get('columns_count', 0),
                'Archivo': result.get('file_path', '') if result.get('file_path') and result.get('file_path') != "Descarga no encontrada" else '',
                'Error': result.get('error', '') if not result.get('success', False) else ''
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar resumen en CSV
            summary_csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📄 Descargar Resumen CSV",
                data=summary_csv,
                file_name=f"resumen_reportes_multiples_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Descargar resumen en Excel
            summary_excel_buffer = io.BytesIO()
            summary_df.to_excel(summary_excel_buffer, index=False, engine='openpyxl')
            summary_excel_data = summary_excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Resumen Excel",
                data=summary_excel_data,
                file_name=f"resumen_reportes_multiples_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Mostrar tabla de resumen
        st.markdown("**Vista previa del resumen:**")
        st.dataframe(summary_df, use_container_width=True)

def _show_company_account_summary_download(successful_results, failed_results):
    """Muestra las opciones de descarga del resumen para empresa-cuenta."""
    st.markdown("### 📋 Descarga del Resumen Completo")
    
    if successful_results:
        # Crear DataFrame combinado con información de resumen
        summary_data = []
        
        for combination_key, result in successful_results + failed_results:
            summary_data.append({
                'Combinación': combination_key,
                'Empresa': result.get('company', ''),
                'Cuenta': result.get('account', ''),
                'Código': result.get('account_code', ''),
                'Estado': 'Exitoso' if result.get('success', False) else 'Fallido',
                'Filas': result.get('rows_count', 0),
                'Columnas': result.get('columns_count', 0),
                'Archivo': result.get('file_path', '') if result.get('file_path') and result.get('file_path') != "Descarga no encontrada" else '',
                'Error': result.get('error', '') if not result.get('success', False) else ''
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Descargar resumen en CSV
            summary_csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📄 Descargar Resumen CSV",
                data=summary_csv,
                file_name=f"resumen_reportes_multiples_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Descargar resumen en Excel
            summary_excel_buffer = io.BytesIO()
            summary_df.to_excel(summary_excel_buffer, index=False, engine='openpyxl')
            summary_excel_data = summary_excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Resumen Excel",
                data=summary_excel_data,
                file_name=f"resumen_reportes_multiples_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Mostrar tabla de resumen
        st.markdown("**Vista previa del resumen:**")
        st.dataframe(summary_df, use_container_width=True)