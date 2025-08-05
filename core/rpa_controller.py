#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador principal para el proceso RPA de Nubox.
Maneja la inicialización, navegación y extracción de reportes.
OPTIMIZADO para máximo rendimiento y velocidad.
"""

import streamlit as st
import logging
from services.nubox_service import NuboxService
from config.settings import setup_config
from utils.logger import setup_logger
from utils.performance_monitor import perf_monitor, measure_step

# Configurar logger
logger = logging.getLogger("nubox_rpa.controller")

class RPAController:
    """Controlador principal para el proceso RPA."""
    
    def __init__(self):
        self.logger = setup_logger()
        self.config = setup_config()
    
    def initialize_rpa_process(self, username, password, custom_url, headless, timeout, progress_container, log_container):
        """Inicializa el proceso RPA: login y navegación hasta cargar los dropdowns con optimización de velocidad."""
        try:
            # Iniciar sesión de monitoreo de rendimiento
            perf_monitor.start_session()
            
            with progress_container:
                # Barra de progreso para inicialización
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Paso 1: Inicializar servicio
                with measure_step("Service initialization"):
                    status_text.text("🚀 Inicializando servicio Nubox optimizado...")
                    progress_bar.progress(10)
                    
                    if not st.session_state.nubox_service:
                        st.session_state.nubox_service = NuboxService(
                            headless=headless, 
                            timeout=max(15, timeout-15)  # Timeout optimizado
                        )
                
                with log_container:
                    st.text("✅ Servicio Nubox inicializado")
                
                # Paso 2: Login optimizado
                if not st.session_state.logged_in:
                    with measure_step("Login process"):
                        status_text.text("🔐 Iniciando sesión en Nubox...")
                        progress_bar.progress(30)
                        
                        login_success = st.session_state.nubox_service.login(username, password, custom_url)
                        
                        if login_success:
                            st.session_state.logged_in = True
                            with log_container:
                                login_time = perf_monitor.get_step_time("Login process")
                                st.text(f"✅ Login exitoso ({login_time:.2f}s)")
                        else:
                            with log_container:
                                st.text("❌ Error en login")
                            st.error("❌ Error al conectar con Nubox. Verifica tus credenciales.")
                            return False
                
                # Paso 3: Navegación optimizada
                if not st.session_state.navigation_complete:
                    with measure_step("Navigation process"):
                        status_text.text("🧭 Navegando al reporte Mayor...")
                        progress_bar.progress(60)
                        
                        navigation_success = st.session_state.nubox_service.navigate_to_report()
                        
                        if navigation_success:
                            st.session_state.navigation_complete = True
                            with log_container:
                                nav_time = perf_monitor.get_step_time("Navigation process")
                                st.text(f"✅ Navegación completada ({nav_time:.2f}s)")
                        else:
                            with log_container:
                                st.text("❌ Error en navegación")
                            st.error("❌ Error al navegar al reporte. Intenta nuevamente.")
                            return False
                
                # Paso 4: Carga de parámetros optimizada
                with measure_step("Dropdown loading"):
                    status_text.text("📋 Cargando opciones de parámetros...")
                    progress_bar.progress(80)
                    
                    if self.load_dropdown_options():
                        with log_container:
                            dropdown_time = perf_monitor.get_step_time("Dropdown loading")
                            st.text(f"✅ Opciones de parámetros cargadas ({dropdown_time:.2f}s)")
                    else:
                        with log_container:
                            st.text("⚠️ Usando opciones de respaldo")
                
                # Completar y mostrar métricas de rendimiento
                progress_bar.progress(100)
                total_time = perf_monitor.end_session()
                status_text.text(f"✅ ¡Inicialización completada en {total_time:.2f}s!")
                
                # Mostrar métricas de rendimiento
                with log_container:
                    st.text("📊 Métricas de rendimiento:")
                    bottlenecks = perf_monitor.get_bottlenecks(1.0)
                    if bottlenecks:
                        for step, duration in bottlenecks.items():
                            st.text(f"  ⚠️ {step}: {duration:.2f}s")
                    else:
                        st.text("  🎯 Todos los pasos fueron rápidos (<1s)")
                
                return True
                
        except Exception as e:
            with log_container:
                st.text(f"❌ Error en inicialización: {str(e)}")
            st.error(f"❌ Error durante la inicialización: {str(e)}")
            return False

    def load_dropdown_options(self):
        """Extrae las opciones de dropdowns dinámicamente desde Nubox."""
        try:
            if st.session_state.nubox_service:
                self.logger.info("Extrayendo opciones de dropdowns de la página de Nubox")
                dropdown_options = st.session_state.nubox_service.extract_dropdown_options()
                
                if dropdown_options:
                    st.session_state.dropdown_options = dropdown_options
                    st.session_state.dropdown_options_loaded = True  # Marcar como cargado
                    self.logger.info(f"Opciones de dropdowns extraídas exitosamente: {len(dropdown_options)} dropdowns")
                    return True
                else:
                    self.logger.warning("No se pudieron extraer opciones reales, usando opciones de respaldo")
                    st.session_state.dropdown_options = self._get_fallback_options()
                    st.session_state.dropdown_options_loaded = True  # Marcar como cargado con respaldo
                    self.logger.info("Usando opciones de respaldo predefinidas")
                    return True
            else:
                self.logger.error("Servicio Nubox no disponible para extraer opciones")
                st.session_state.dropdown_options_loaded = False
                return False
        except Exception as e:
            self.logger.error(f"Error cargando opciones de dropdowns: {str(e)}")
            st.session_state.dropdown_options_loaded = False
            st.error(f"Error cargando opciones de dropdowns: {str(e)}")
            return False

    def _get_fallback_options(self):
        """Retorna opciones de respaldo si no se pueden extraer desde Nubox."""
        return {
            "Empresa": {
                "options": [
                    "051, VERSE CONSULTORES LTDA",
                    "205, INSTITUTO DE CAP. Y GESTION SPA", 
                    "282, SUGA SPA",
                    "527, PUNTO HUMANO SPA",
                    "586, SERV. EMPRESARIALES INSERT PRO SPA",
                    "689, DELSO SPA",
                    "796, INVERSIONES LAS TRALCAS SPA",
                    "838, SERV. ASESORIAS EMP. NRED SPA",
                    "903, COMERCIALIZADORA INSERT S.A.",
                    "904, UAU TELECOM SPA",
                    "905, Paulo Subiabre Cepeda E. Individual",
                    "906, SELYT SPA"
                ],
                "selected": "051, VERSE CONSULTORES LTDA",
                "name": "ComboEmpresa",
                "index": 0
            },
            "Tipo de Reporte": {
                "options": [
                    "ANALISIS POR CUENTA",
                    "BORRADOR", 
                    "OFICIAL SIN NOMBRE",
                    "OFICIAL CON NOMBRE"
                ],
                "selected": "ANALISIS POR CUENTA",
                "name": "ComboTipoReporte",
                "index": 1
            },
            "Formato de Salida": {
                "options": ["PDF", "EXCEL"],
                "selected": "PDF",
                "name": "ComboFormato",
                "index": 2
            },
            "Cuenta Contable": {
                "options": [
                    "1101-01 CUENTA CAJA",
                    "1101-02 BANCO SANTANDER",
                    "1101-03 BANCO BCI",
                    "1104-01 CLIENTES NACIONALES",
                    "5101-01 VENTAS POR SERVICIO",
                    "4201-01 ARRIENDOS OFICINAS"
                ],
                "selected": "1101-01 CUENTA CAJA",
                "name": "ComboCodigoSubcuenta",
                "index": 3
            },
            "Incluir Subcuentas": {
                "options": ["NO", "SI"],
                "selected": "NO",
                "name": "ComboIncluirSubcuentas",
                "index": 4
            }
        }