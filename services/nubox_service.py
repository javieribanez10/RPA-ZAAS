#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio principal para interactuar con la plataforma Nubox.
Arquitectura refactorizada para mejor separación de responsabilidades.
OPTIMIZADO para máximo rendimiento y velocidad.
"""

import logging
import pandas as pd
from .components.browser_manager import BrowserManager
from .components.authentication import AuthenticationService
from .components.navigation import NavigationService
from .components.parameter_config import ParameterConfigService
from .components.report_extractor import ReportExtractorService
from .components.ui_elements import UIElementService
from utils.performance_monitor import perf_monitor, measure_performance, measure_step

# Configurar logger
logger = logging.getLogger("nubox_rpa.service")

class NuboxService:
    """
    Servicio principal para interactuar con la plataforma Nubox.
    Orquesta las diferentes componentes especializadas.
    OPTIMIZADO para máximo rendimiento y velocidad.
    """
    
    def __init__(self, headless=True, timeout=15):  # Reducido de 30 a 15 segundos
        """
        Inicializa el servicio de Nubox con configuración optimizada.
        
        Args:
            headless (bool): Si True, el navegador se ejecuta sin interfaz gráfica
            timeout (int): Tiempo máximo de espera para operaciones (segundos) - optimizado
        """
        with measure_step("NuboxService initialization"):
            self.timeout = timeout
            
            # Inicializar componentes especializadas con medición de tiempo
            with measure_step("Browser manager setup"):
                self.browser_manager = BrowserManager(headless=headless, timeout=timeout)
            
            with measure_step("Service components setup"):
                self.auth_service = AuthenticationService(self.browser_manager)
                self.navigation_service = NavigationService(self.browser_manager)
                self.parameter_service = ParameterConfigService(self.browser_manager)
                self.extractor_service = ReportExtractorService(self.browser_manager)
                self.ui_service = UIElementService(self.browser_manager)
            
            logger.info("🚀 NuboxService inicializado con arquitectura modular optimizada")
    
    @property
    def driver(self):
        """Acceso al driver para compatibilidad con código existente."""
        return self.browser_manager.driver
    
    @measure_performance("NuboxService.login")
    def login(self, username, password, url="https://web.nubox.com/Login/Account/Login?ReturnUrl=%2FSistemaLogin"):
        """
        Inicia sesión en Nubox con medición de rendimiento.
        
        Args:
            username (str): RUT del usuario
            password (str): Contraseña
            url (str): URL de inicio de sesión
            
        Returns:
            bool: True si el login fue exitoso
        """
        return self.auth_service.login(username, password, url)
    
    @measure_performance("NuboxService.navigate_to_report")
    def navigate_to_report(self, report_type="mayor"):
        """
        Navega a la sección de reportes contables con medición de rendimiento.
        
        Args:
            report_type (str): Tipo de reporte
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        return self.navigation_service.navigate_to_report(report_type)
    
    @measure_performance("NuboxService.extract_dropdown_options")
    def extract_dropdown_options(self):
        """
        Extrae las opciones de dropdowns disponibles con medición de rendimiento.
        
        Returns:
            dict: Diccionario con las opciones de cada dropdown
        """
        return self.ui_service.extract_dropdown_options()
    
    def extract_multiple_reports_by_account(self, params, selected_accounts):
        """
        Extrae múltiples reportes, uno por cada cuenta contable.
        
        Args:
            params (dict): Parámetros base para el reporte
            selected_accounts (list): Lista de cuentas contables
            
        Returns:
            dict: Diccionario con los resultados de cada cuenta
        """
        return self.extractor_service.extract_multiple_reports(params, selected_accounts, self.parameter_service, self.navigation_service)
    
    def extract_multiple_reports_by_company_and_account(self, params, selected_companies, selected_accounts):
        """
        Extrae múltiples reportes para cada combinación de empresa y cuenta contable.
        
        Args:
            params (dict): Parámetros base para el reporte
            selected_companies (list): Lista de empresas
            selected_accounts (list): Lista de cuentas contables
            
        Returns:
            dict: Diccionario con los resultados de cada combinación empresa-cuenta
        """
        return self.extractor_service.extract_multiple_reports_by_company_and_account(
            params, selected_companies, selected_accounts, self.parameter_service, self.navigation_service
        )
    
    def close(self):
        """Cierra el navegador y libera recursos."""
        self.browser_manager.close()
    
    # Métodos de compatibilidad para código existente
    def _wait_for_element(self, by, selector, timeout=None):
        """Método de compatibilidad."""
        return self.ui_service.wait_for_element(by, selector, timeout)
    
    def _wait_and_click(self, by, selector, timeout=None):
        """Método de compatibilidad."""
        return self.ui_service.wait_and_click(by, selector, timeout)
