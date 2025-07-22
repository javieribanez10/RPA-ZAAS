#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de extracción de reportes para el RPA Nubox.
Maneja la configuración de parámetros y extracción de reportes.
"""

import streamlit as st
import datetime
import logging
from utils.date_utils import generate_monthly_date_ranges, format_date_for_nubox, get_month_name_es, should_use_monthly_extraction

# Configurar logger
logger = logging.getLogger("nubox_rpa.extraction")

class ReportExtractor:
    """Manejador de extracción de reportes."""
    
    def extract_report_process(self, fecha_desde, fecha_hasta, dropdown_selections, 
                             selected_accounts, selected_companies, progress_container, log_container):
        """Extrae el reporte con los parámetros configurados."""
        try:
            # Verificar si se debe usar extracción mensual
            use_monthly = should_use_monthly_extraction(fecha_desde, fecha_hasta)
            
            if use_monthly:
                with log_container:
                    st.text(f"📅 Rango de fechas detectado: {fecha_desde} a {fecha_hasta}")
                    st.text("🗓️ Activando modo de extracción mensual automática")
                
                return self._process_monthly_extractions(
                    fecha_desde, fecha_hasta, dropdown_selections,
                    selected_accounts, selected_companies, progress_container, log_container
                )
            else:
                # Modo normal para rangos cortos
                return self._process_standard_extraction(
                    fecha_desde, fecha_hasta, dropdown_selections,
                    selected_accounts, selected_companies, progress_container, log_container
                )
                    
        except Exception as e:
            with log_container:
                st.text(f"❌ Error en extracción: {str(e)}")
            st.error(f"❌ Error durante la extracción: {str(e)}")
            return False

    def _process_monthly_extractions(self, fecha_desde, fecha_hasta, dropdown_selections,
                                   selected_accounts, selected_companies, progress_container, log_container):
        """Procesa extracciones mensuales automáticas."""
        try:
            # Generar rangos mensuales
            monthly_ranges = generate_monthly_date_ranges(fecha_desde, fecha_hasta)
            
            with log_container:
                st.text(f"📊 Se generarán {len(monthly_ranges)} reportes mensuales:")
                for i, (start, end) in enumerate(monthly_ranges, 1):
                    month_name = get_month_name_es(start)
                    st.text(f"  {i}. {month_name}: {format_date_for_nubox(start)} a {format_date_for_nubox(end)}")
            
            all_monthly_results = {}
            total_monthly_reports = len(monthly_ranges)
            
            with progress_container:
                monthly_progress = st.progress(0)
                monthly_status = st.empty()
                
                for month_idx, (month_start, month_end) in enumerate(monthly_ranges, 1):
                    month_name = get_month_name_es(month_start)
                    monthly_status.text(f"📅 Procesando {month_name} ({month_idx}/{total_monthly_reports})")
                    
                    with log_container:
                        st.text(f"\n🗓️ === PROCESANDO MES {month_idx}: {month_name.upper()} ===")
                        st.text(f"Período: {format_date_for_nubox(month_start)} a {format_date_for_nubox(month_end)}")
                    
                    # Procesar este mes específico
                    monthly_result = self._process_standard_extraction(
                        month_start, month_end, dropdown_selections,
                        selected_accounts, selected_companies, None, log_container  # Sin progress_container para evitar conflicto
                    )
                    
                    # Almacenar resultado mensual
                    month_key = f"{month_name}_{month_start.year}"
                    all_monthly_results[month_key] = {
                        'month_name': month_name,
                        'year': month_start.year,
                        'date_range': (month_start, month_end),
                        'result': monthly_result,
                        'success': monthly_result is not False
                    }
                    
                    # Actualizar progreso mensual
                    progress_percent = (month_idx / total_monthly_reports) * 100
                    monthly_progress.progress(int(progress_percent))
                    
                    with log_container:
                        if monthly_result is not False:
                            st.text(f"✅ {month_name} completado exitosamente")
                        else:
                            st.text(f"❌ Error en {month_name}")
                
                monthly_status.text("✅ ¡Todas las extracciones mensuales completadas!")
                monthly_progress.progress(100)
            
            # Mostrar resumen final
            self._show_monthly_summary(all_monthly_results, log_container)
            
            return all_monthly_results
            
        except Exception as e:
            with log_container:
                st.text(f"❌ Error en extracción mensual: {str(e)}")
            logger.error(f"Error en extracción mensual: {str(e)}")
            return False

    def _process_standard_extraction(self, fecha_desde, fecha_hasta, dropdown_selections,
                                   selected_accounts, selected_companies, progress_container, log_container):
        """Procesa una extracción estándar (no mensual)."""
        # Determinar el tipo de procesamiento
        is_multiple_accounts = len(selected_accounts) > 1
        is_multiple_companies = len(selected_companies) > 1
        is_multiple_processing = is_multiple_accounts or is_multiple_companies
        
        # Crear progress container si no se proporciona (para extracciones mensuales)
        if progress_container is None:
            progress_container = st.container()
        
        with progress_container:
            # Barra de progreso para extracción
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Preparar parámetros base
            base_params = {
                'fecha_desde': format_date_for_nubox(fecha_desde),
                'fecha_hasta': format_date_for_nubox(fecha_hasta),
                'dropdown_selections': dropdown_selections
            }
            
            # Procesar según el modo
            if is_multiple_processing:
                return self._process_multiple_reports(
                    base_params, selected_companies, selected_accounts,
                    progress_bar, status_text, log_container
                )
            else:
                return self._process_single_report(
                    base_params, progress_bar, status_text, log_container
                )

    def _show_monthly_summary(self, monthly_results, log_container):
        """Muestra un resumen de las extracciones mensuales."""
        successful_months = sum(1 for result in monthly_results.values() if result['success'])
        failed_months = len(monthly_results) - successful_months
        
        with log_container:
            st.text(f"\n📊 === RESUMEN DE EXTRACCIONES MENSUALES ===")
            st.text(f"Total de meses procesados: {len(monthly_results)}")
            st.text(f"Meses exitosos: {successful_months}")
            st.text(f"Meses fallidos: {failed_months}")
            st.text(f"Tasa de éxito: {(successful_months/len(monthly_results)*100):.1f}%")
            
            if failed_months > 0:
                st.text(f"\n❌ Meses con errores:")
                for month_key, result in monthly_results.items():
                    if not result['success']:
                        st.text(f"  - {result['month_name']} {result['year']}")

    def _process_multiple_reports(self, base_params, selected_companies, selected_accounts,
                                progress_bar, status_text, log_container):
        """Procesa múltiples reportes (empresas y/o cuentas)."""
        total_combinations = len(selected_companies) * len(selected_accounts)
        status_text.text(f"📊 Procesando {total_combinations} combinaciones ({len(selected_companies)} empresas × {len(selected_accounts)} cuentas)...")
        progress_bar.progress(20)
        
        with log_container:
            st.text(f"🔢 Iniciando procesamiento múltiple:")
            st.text(f"  - Empresas: {len(selected_companies)}")
            st.text(f"  - Cuentas: {len(selected_accounts)}")
            st.text(f"  - Total combinaciones: {total_combinations}")
        
        # Llamar al método de extracción múltiple por empresas y cuentas
        results = st.session_state.nubox_service.extract_multiple_reports_by_company_and_account(
            base_params, selected_companies, selected_accounts
        )
        
        progress_bar.progress(95)
        
        # Procesar y mostrar resultados múltiples
        if results and '_summary' in results:
            summary = results['_summary']
            
            with log_container:
                st.text(f"✅ Extracción completada:")
                st.text(f"  - Total combinaciones: {summary.get('total_combinaciones', total_combinations)}")
                st.text(f"  - Exitosas: {summary['successful_extractions']}")
                st.text(f"  - Fallidas: {summary['failed_extractions']}")
                st.text(f"  - Tasa de éxito: {summary['success_rate']:.1f}%")
            
            progress_bar.progress(100)
            status_text.text("✅ ¡Proceso múltiple completado!")
            
            return results
        else:
            with log_container:
                st.text("❌ Error en la extracción múltiple")
            st.error("❌ No se pudieron extraer los reportes.")
            return False

    def _process_single_report(self, base_params, progress_bar, status_text, log_container):
        """Procesa un solo reporte."""
        # MODO UNA SOLA COMBINACIÓN
        status_text.text("⚙️ Configurando parámetros del reporte...")
        progress_bar.progress(25)
        
        # Configurar parámetros usando el método automatizado
        config_success = self.configure_parameters_programmatically(base_params, log_container)
        
        if config_success:
            with log_container:
                st.text("✅ Parámetros configurados correctamente")
            progress_bar.progress(50)
        else:
            with log_container:
                st.text("❌ Error al configurar parámetros")
            st.error("❌ Error al configurar parámetros del reporte.")
            return False
        
        # Generar y extraer reporte único
        status_text.text("📊 Generando y extrayendo reporte...")
        progress_bar.progress(75)
        
        report_data = st.session_state.nubox_service.extract_report()
        
        if isinstance(report_data, tuple):
            df, file_path = report_data
        else:
            df = report_data
            file_path = None
        
        progress_bar.progress(100)
        status_text.text("✅ ¡Extracción completada!")
        
        with log_container:
            st.text("✅ Reporte extraído exitosamente")
        
        st.session_state.report_generated = True
        
        return df, file_path

    def configure_parameters_programmatically(self, params, log_container):
        """Configura los parámetros del reporte de forma programática."""
        try:
            # Crear un objeto de parámetros que el servicio pueda usar
            service_params = {
                'fecha_desde': params['fecha_desde'],
                'fecha_hasta': params.get('fecha_hasta'),
                'dropdown_selections': params['dropdown_selections']
            }
            
            with log_container:
                st.text(f"📅 Configurando fecha desde: {params['fecha_desde']}")
                if params.get('fecha_hasta'):
                    st.text(f"📅 Configurando fecha hasta: {params['fecha_hasta']}")
                for dropdown, selection in params['dropdown_selections'].items():
                    st.text(f"🔽 {dropdown}: {selection}")
            
            # Llamar al método programático del servicio
            success = st.session_state.nubox_service.set_report_parameters_programmatic(service_params)
            
            if success:
                with log_container:
                    st.text("✅ Configuración programática completada exitosamente")
            else:
                with log_container:
                    st.text("❌ Error en la configuración programática")
            
            return success
            
        except Exception as e:
            with log_container:
                st.text(f"❌ Error configurando parámetros: {str(e)}")
            return False