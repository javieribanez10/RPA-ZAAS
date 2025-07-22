#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio principal para interactuar con la plataforma Nubox.
Arquitectura refactorizada para mejor separación de responsabilidades.
"""

import time
import logging
import pandas as pd
from .components.browser_manager import BrowserManager
from .components.authentication import AuthenticationService
from .components.navigation import NavigationService
from .components.parameter_config import ParameterConfigService
from .components.report_extractor import ReportExtractorService
from .components.ui_elements import UIElementService

# Configurar logger
logger = logging.getLogger("nubox_rpa.service")

class NuboxService:
    """
    Servicio principal para interactuar con la plataforma Nubox.
    Orquesta las diferentes componentes especializadas.
    """
    
    def __init__(self, headless=True, timeout=30):
        """
        Inicializa el servicio de Nubox.
        
        Args:
            headless (bool): Si True, el navegador se ejecuta sin interfaz gráfica
            timeout (int): Tiempo máximo de espera para operaciones (segundos)
        """
        self.timeout = timeout
        
        # Inicializar componentes especializadas
        self.browser_manager = BrowserManager(headless=headless, timeout=timeout)
        self.auth_service = AuthenticationService(self.browser_manager)
        self.navigation_service = NavigationService(self.browser_manager)
        self.parameter_service = ParameterConfigService(self.browser_manager)
        self.extractor_service = ReportExtractorService(self.browser_manager)
        self.ui_service = UIElementService(self.browser_manager)
        
        logger.info("NuboxService inicializado con arquitectura modular")
    
    @property
    def driver(self):
        """Acceso al driver para compatibilidad con código existente."""
        return self.browser_manager.driver
    
    def login(self, username, password, url="https://web.nubox.com/Login/Account/Login?ReturnUrl=%2FSistemaLogin"):
        """
        Inicia sesión en Nubox.
        
        Args:
            username (str): RUT del usuario
            password (str): Contraseña
            url (str): URL de inicio de sesión
            
        Returns:
            bool: True si el login fue exitoso
        """
        return self.auth_service.login(username, password, url)
    
    def navigate_to_report(self, report_type="mayor"):
        """
        Navega a la sección de reportes contables.
        
        Args:
            report_type (str): Tipo de reporte
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        return self.navigation_service.navigate_to_report(report_type)
    
    def set_report_parameters(self, params=None):
        """
        Configura los parámetros del reporte de forma interactiva.
        
        Args:
            params (dict): Parámetros para el reporte
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        return self.parameter_service.set_parameters_interactive(params)
    
    def set_report_parameters_programmatic(self, params):
        """
        Configura los parámetros del reporte de forma programática.
        
        Args:
            params (dict): Parámetros para configurar
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        return self.parameter_service.set_parameters_programmatic(params)
    
    def extract_report(self, is_multiple_accounts=False):
        """
        Extrae el archivo Excel descargado desde Nubox.
        
        Args:
            is_multiple_accounts (bool): True si es parte de un proceso de múltiples cuentas
        
        Returns:
            tuple: (DataFrame, file_path)
        """
        return self.extractor_service.extract_report(is_multiple_accounts)
    
    def extract_dropdown_options(self):
        """
        Extrae las opciones de dropdowns disponibles.
        
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
