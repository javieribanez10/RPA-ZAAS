#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Página de resultados para reportes individuales del RPA Nubox.
"""

import streamlit as st
import pandas as pd
import datetime
import io
import os
from pathlib import Path

def show_results(df, file_path=None):
    """Muestra los resultados del reporte extraído con análisis mejorado y exportación automática a MongoDB."""
    st.markdown('<h2 class="section-header">📊 Resultados del Reporte</h2>', unsafe_allow_html=True)
    
    if not df.empty:
        # Exportación automática a MongoDB
        _handle_mongodb_export(df, file_path)
        
        # Mostrar información del DataFrame
        _show_dataframe_info(df, file_path)
        
        # Análisis rápido del DataFrame
        _show_quick_analysis(df)
        
        # Filtros para el DataFrame
        filtered_df = _show_filters_section(df)
        
        # Mostrar preview de los datos filtrados
        _show_data_preview(filtered_df, df)
        
        # Análisis estadístico básico
        _show_statistical_analysis(df)
        
        # Opciones de descarga mejoradas
        _show_download_options(df, filtered_df)
        
        # Información adicional si hay archivo descargado
        if file_path:
            _show_file_info(file_path)
    else:
        _show_error_handling(file_path)

def _handle_mongodb_export(df, file_path):
    """Maneja la exportación automática a MongoDB."""
    st.markdown("### 🚀 Exportación Automática a MongoDB")
    
    with st.spinner("Exportando datos a MongoDB..."):
        try:
            from services.mongodb_client import NuboxMongoClient
            
            # Extraer información de la empresa desde los atributos del DataFrame
            company_info = df.attrs.get('company_info', {}) if hasattr(df, 'attrs') else {}
            
            # Preparar metadatos del reporte
            report_metadata = {
                'archivo_origen': os.path.basename(file_path) if file_path else 'streamlit_extraction',
                'cuenta_contable': st.session_state.get('dropdown_options', {}).get('Cuenta Contable', {}).get('selected', ''),
                'fecha_extraccion': datetime.datetime.now().isoformat(),
                'parametros_streamlit': {
                    'formato_salida': 'EXCEL',
                    'include_subcuentas': st.session_state.get('dropdown_options', {}).get('Incluir Subcuentas', {}).get('selected', 'NO')
                }
            }
            
            # Crear cliente MongoDB y exportar
            mongo_client = NuboxMongoClient()
            export_result = mongo_client.export_nubox_dataframe(
                df=df,
                company_info=company_info,
                report_metadata=report_metadata
            )
            
            if export_result['success']:
                st.success(f"✅ **Datos exportados exitosamente a MongoDB**")
                
                # Mostrar detalles de la exportación en un expandidor
                with st.expander("📋 Detalles de la Exportación", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📊 Filas Exportadas", export_result['exported_rows'])
                    with col2:
                        st.metric("🏢 Empresa", company_info.get('Nombre', 'N/A'))
                    with col3:
                        st.metric("📅 Fecha", datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
                    
                    st.write(f"**ID del Documento**: `{export_result['document_id']}`")
                    st.write(f"**Colección**: `{export_result['collection_name']}`")
                    st.write(f"**Base de Datos**: `nubox-data`")
                    
                    if company_info:
                        st.write("**Información de Empresa Exportada**:")
                        for key, value in company_info.items():
                            st.write(f"- **{key}**: {value}")
            else:
                st.error("❌ **Error en la exportación a MongoDB**")
                if export_result['errors']:
                    st.write("**Errores encontrados**:")
                    for error in export_result['errors']:
                        st.write(f"- {error}")
            
            mongo_client.disconnect()
            
        except ImportError:
            st.warning("⚠️ Cliente MongoDB no disponible. Instalar con: `pip install pymongo`")
        except Exception as e:
            st.error(f"❌ Error durante la exportación: {str(e)}")

def _show_dataframe_info(df, file_path):
    """Muestra información básica del DataFrame."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Filas", len(df))
    with col2:
        st.metric("📋 Columnas", len(df.columns))
    with col3:
        if file_path:
            st.metric("📁 Archivo", "Descargado")
        else:
            st.metric("📁 Archivo", "En memoria")
    with col4:
        # Calcular tamaño estimado en MB
        size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        st.metric("💾 Tamaño", f"{size_mb:.2f} MB")

def _show_quick_analysis(df):
    """Muestra análisis rápido del DataFrame."""
    st.markdown("### 📈 Análisis Rápido")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Información de tipos de datos
        with st.expander("🔍 Tipos de Datos"):
            types_info = df.dtypes.value_counts()
            for dtype, count in types_info.items():
                st.write(f"**{dtype}**: {count} columnas")
    
    with col2:
        # Información de valores nulos
        with st.expander("❌ Valores Nulos"):
            null_counts = df.isnull().sum()
            null_cols = null_counts[null_counts > 0]
            if len(null_cols) > 0:
                for col, count in null_cols.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"**{col}**: {count} ({percentage:.1f}%)")
            else:
                st.write("✅ No hay valores nulos")

def _show_filters_section(df):
    """Muestra la sección de filtros y retorna el DataFrame filtrado."""
    st.markdown("### 🔍 Filtros y Exploración")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro por número de filas a mostrar
        rows_to_show = st.selectbox(
            "Filas a mostrar",
            options=[10, 20, 50, 100, "Todas"],
            index=1
        )
    
    with col2:
        # Filtro por columnas
        all_columns = df.columns.tolist()
        selected_columns = st.multiselect(
            "Seleccionar columnas",
            options=all_columns,
            default=all_columns[:10] if len(all_columns) > 10 else all_columns
        )
    
    with col3:
        # Opción de búsqueda
        search_term = st.text_input(
            "Buscar en los datos",
            placeholder="Ingresa término de búsqueda..."
        )

    # Aplicar filtros
    filtered_df = df.copy()
    
    if selected_columns:
        filtered_df = filtered_df[selected_columns]
    
    if search_term:
        # Buscar en todas las columnas de texto
        mask = False
        for col in filtered_df.select_dtypes(include=['object', 'string']).columns:
            mask |= filtered_df[col].astype(str).str.contains(search_term, case=False, na=False)
        
        if mask.any():
            filtered_df = filtered_df[mask]
            st.info(f"🔍 Se encontraron {len(filtered_df)} filas que contienen '{search_term}'")
        else:
            st.warning(f"⚠️ No se encontraron resultados para '{search_term}'")
    
    return filtered_df

def _show_data_preview(filtered_df, original_df):
    """Muestra la vista previa de los datos."""
    st.markdown("### 👀 Vista previa de los datos")
    
    rows_to_show = st.session_state.get('rows_to_show', 20)
    
    if rows_to_show == "Todas":
        display_df = filtered_df
    else:
        display_df = filtered_df.head(rows_to_show)
    
    # Mostrar el DataFrame con mejor formato
    st.dataframe(
        display_df, 
        use_container_width=True,
        height=min(400, len(display_df) * 35 + 50)  # Altura dinámica
    )
    
    # Información adicional del filtrado
    if len(filtered_df) != len(original_df):
        st.info(f"📊 Mostrando {len(display_df)} de {len(filtered_df)} filas filtradas (total: {len(original_df)} filas)")
    else:
        st.info(f"📊 Mostrando {len(display_df)} de {len(original_df)} filas totales")

def _show_statistical_analysis(df):
    """Muestra análisis estadístico básico para columnas numéricas."""
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) > 0:
        st.markdown("### 📊 Estadísticas Descriptivas")
        
        with st.expander("Ver estadísticas numéricas", expanded=False):
            st.dataframe(df[numeric_columns].describe(), use_container_width=True)

def _show_download_options(df, filtered_df):
    """Muestra las opciones de descarga."""
    st.markdown("### 💾 Opciones de Descarga")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Botón para descargar CSV completo
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="💾 Descargar CSV Completo",
            data=csv_data,
            file_name=f"reporte_nubox_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Botón para descargar Excel completo
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📊 Descargar Excel Completo",
            data=excel_data,
            file_name=f"reporte_nubox_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col3:
        # Botón para descargar datos filtrados
        if len(filtered_df) != len(df) and not filtered_df.empty:
            filtered_csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="🔍 Descargar Filtrados CSV",
                data=filtered_csv,
                file_name=f"reporte_filtrado_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

def _show_file_info(file_path):
    """Muestra información adicional del archivo descargado."""
    st.markdown("### 📁 Información del Archivo")
    st.info(f"📁 El archivo original también fue descargado en: {file_path}")
    
    # Mostrar información adicional del archivo
    try:
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        st.write(f"**Tamaño del archivo**: {file_size:.2f} MB")
        st.write(f"**Formato**: {os.path.splitext(file_path)[1].upper()}")
    except:
        pass

def _show_error_handling(file_path):
    """Maneja los casos de error en la extracción."""
    st.markdown("### ⚠️ Problema con la Extracción")
    
    if file_path and file_path.startswith("Archivo inválido:"):
        st.error("❌ **Archivo descargado inválido**")
        st.markdown("""
        **Problema**: El archivo descargado no contiene datos válidos de Excel.
        
        **Posibles causas**:
        - El reporte no generó datos para los parámetros seleccionados
        - Error en el servidor de Nubox
        - Sesión expirada durante la generación
        - Límites de datos excedidos en el reporte
        """)
        
        _show_file_analysis(file_path)
        
    elif file_path == "Descarga no encontrada":
        _show_download_not_found()
        
    elif file_path and file_path.startswith("Error de lectura:"):
        _show_read_error()
    
    _show_error_solutions()

def _show_file_analysis(file_path):
    """Muestra análisis del archivo problemático."""
    actual_path = file_path.replace("Archivo inválido: ", "")
    st.info(f"📁 Archivo problemático: `{os.path.basename(actual_path)}`")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Analizar Contenido del Archivo", key="analyze_file"):
            try:
                file_size = os.path.getsize(actual_path) / 1024  # KB
                
                with open(actual_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)  # Primeros 2000 caracteres
                
                st.markdown("### 📋 Análisis del Archivo")
                st.write(f"**Tamaño**: {file_size:.2f} KB")
                st.write(f"**Nombre**: {os.path.basename(actual_path)}")
                
                # Detectar tipo de contenido
                if '<html' in content.lower():
                    st.error("🌐 **Tipo detectado**: Página HTML")
                    st.write("El archivo contiene código HTML en lugar de datos Excel.")
                elif 'error' in content.lower():
                    st.error("🚫 **Tipo detectado**: Mensaje de error")
                else:
                    st.info("❓ **Tipo detectado**: Contenido desconocido")
                
                # Mostrar contenido en un expandidor
                with st.expander("Ver contenido del archivo", expanded=False):
                    st.code(content[:1000], language="html")
                    if len(content) > 1000:
                        st.write(f"... y {len(content) - 1000} caracteres más")
                
            except Exception as e:
                st.error(f"No se pudo analizar el archivo: {str(e)}")
    
    with col2:
        if st.button("🔧 Soluciones Recomendadas", key="solutions"):
            _show_error_solutions()

def _show_download_not_found():
    """Maneja el caso cuando no se encuentra la descarga."""
    st.error("❌ **No se encontró archivo descargado**")
    st.markdown("""
    **Problema**: No se detectó ningún archivo Excel reciente en la carpeta de descargas.
    
    **Posibles causas**:
    - La descarga no se completó
    - El archivo se guardó en otra ubicación
    - El proceso de generación falló en Nubox
    - Bloqueador de pop-ups impidió la descarga
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📁 Verificar Descargas"):
            # Mostrar archivos recientes en Downloads
            downloads_folder = Path.home() / "Downloads"
            excel_files = list(downloads_folder.glob("*.xls*"))
            
            if excel_files:
                # Ordenar por fecha de modificación
                excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                st.markdown("**Archivos Excel encontrados:**")
                for file in excel_files[:5]:  # Mostrar solo los 5 más recientes
                    mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                    st.write(f"- `{file.name}` (modificado: {mtime.strftime('%d/%m/%Y %H:%M')})")
            else:
                st.warning("No se encontraron archivos Excel en la carpeta de descargas.")
    
    with col2:
        if st.button("⏱️ Esperar y Reintentar"):
            with st.spinner("Esperando 30 segundos más para la descarga..."):
                import time
                time.sleep(30)
            st.rerun()
    
    with col3:
        if st.button("📁 Abrir Carpeta", key="open_folder"):
            import subprocess
            subprocess.run(["open", str(Path.home() / "Downloads")])
            st.info("📂 Carpeta de descargas abierta")
    
    with col4:
        if st.button("🔄 Reintentar", key="retry"):
            st.rerun()

def _show_read_error():
    """Maneja errores de lectura de archivos."""
    st.error("❌ **Error al leer el archivo Excel**")
    st.markdown("""
    **Problema**: El archivo fue descargado pero no se pudo leer como Excel válido.
    
    **Posibles soluciones**:
    - El archivo podría estar corrupto
    - Podría ser un formato diferente (HTML, PDF, etc.)
    - El archivo podría estar vacío o incompleto
    """)

def _show_error_solutions():
    """Muestra soluciones recomendadas para errores."""
    st.markdown("### 🛠️ Pasos para Resolver")
    
    solutions = [
        "1. **Verificar sesión**: Asegúrate de que tu sesión en Nubox sigue activa",
        "2. **Validar parámetros**: Confirma que las fechas y filtros sean correctos",
        "3. **Reducir alcance**: Prueba con un rango de fechas más pequeño",
        "4. **Cambiar formato**: En Nubox, selecciona 'PDF' en lugar de 'Excel'",
        "5. **Reintentar**: Espera unos minutos y vuelve a intentar",
        "6. **Verificar conexión**: Asegúrate de tener buena conexión a internet"
    ]
    
    for solution in solutions:
        st.write(solution)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reintentar Extracción"):
            st.rerun()
    
    with col2:
        if st.button("🧭 Verificar Navegación"):
            if st.session_state.get('nubox_service'):
                try:
                    # Tomar captura de pantalla para diagnóstico
                    st.session_state.nubox_service.browser_manager.take_screenshot("diagnostico_estado_actual.png")
                    st.success("✅ Captura de diagnóstico guardada en la carpeta logs/")
                except:
                    st.error("❌ No se pudo tomar captura de diagnóstico")
            else:
                st.warning("⚠️ Servicio Nubox no disponible")
    
    with col3:
        if st.button("🆕 Reiniciar Todo"):
            # Limpiar completamente el estado
            if st.session_state.get('nubox_service'):
                st.session_state.nubox_service.close()
            
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.success("🔄 Estado reiniciado. Recarga la página para empezar de nuevo.")
            st.rerun()