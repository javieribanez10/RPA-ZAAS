#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de navegación para la plataforma Nubox.
Responsable únicamente de la navegación a diferentes secciones.
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger("nubox_rpa.navigation")

class NavigationService:
    """
    Maneja la navegación dentro de la plataforma Nubox.
    Principio de Responsabilidad Única: Solo maneja navegación.
    """
    
    def __init__(self, browser_manager):
        """
        Inicializa el servicio de navegación.
        
        Args:
            browser_manager (BrowserManager): Instancia del administrador del navegador
        """
        self.browser = browser_manager
    
    def navigate_to_report(self, report_type="mayor"):
        """
        Navega a la sección de reportes contables.
        
        Args:
            report_type (str): Tipo de reporte ('mayor', 'balance', etc.)
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            logger.info("Iniciando navegación a reportes contables")
            
            # Tomar captura de la página principal
            self.browser.take_screenshot(f"main_page_{int(time.time())}.png")
            time.sleep(2)
            
            # Secuencia de navegación: Contabilidad -> Reportes -> Libros Contables -> Mayor
            if not self._navigate_to_accounting():
                return False
            
            if not self._navigate_to_reports():
                return False
            
            if not self._navigate_to_accounting_books():
                return False
            
            if not self._navigate_to_mayor_report():
                return False
            
            # Tomar captura final
            self.browser.take_screenshot(f"after_navigation_{int(time.time())}.png")
            logger.info("Navegación completada exitosamente")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al navegar al reporte: {str(e)}")
            return False
    
    def _navigate_to_accounting(self):
        """
        Navega al módulo de Contabilidad.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("Navegando al módulo de Contabilidad")
        
        contabilidad_selectors = [
            "//td[contains(@class, 'jqx-cell') and contains(@class, 'jqx-grid-cell')]//span[contains(text(), 'Contabilidad')]",
            "//span[contains(text(), 'Contabilidad') and contains(@class, 'jqx-tree-grid-title')]",
            "//span[contains(text(), 'Contabilidad')]"
        ]
        
        for selector in contabilidad_selectors:
            try:
                logger.info(f"Intentando selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.info(f"Elementos encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("Elemento de Contabilidad encontrado y visible")
                        if self._click_element_safely(element, "Contabilidad"):
                            time.sleep(1)
                            self.browser.take_screenshot(f"contabilidad_clicked_{int(time.time())}.png")
                            return True
                
            except TimeoutException:
                logger.debug(f"Timeout con selector {selector}")
                continue
            except Exception as e:
                logger.debug(f"Error con selector {selector}: {str(e)}")
                continue
        
        logger.error("No se pudo hacer clic en el módulo de Contabilidad")
        self.browser.take_screenshot(f"contabilidad_error_{int(time.time())}.png")
        return False
    
    def _navigate_to_reports(self):
        """
        Navega al menú de Reportes.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("Buscando el menú de Reportes")
        
        reportes_selectors = [
            "//a[@tabindex='-1' and contains(@onfocus, 'p_MenuEnfocar') and text()='Reportes']",
            "//a[text()='Reportes' and contains(@onfocus, 'p_MenuEnfocar')]",
            "//a[text()='Reportes']",
            "//a[contains(text(), 'Reportes')]",
            "//span[contains(text(), 'Reportes')]"
        ]
        
        for selector in reportes_selectors:
            try:
                logger.info(f"Buscando Reportes con selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.info(f"Elementos de Reportes encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("Elemento de Reportes encontrado y visible")
                        if self._click_element_safely(element, "Reportes"):
                            return True
                
            except TimeoutException:
                logger.debug(f"Timeout buscando Reportes con selector: {selector}")
                continue
            except Exception as e:
                logger.debug(f"Error buscando Reportes: {str(e)}")
                continue
        
        logger.warning("No se encontró el menú de Reportes")
        self.browser.take_screenshot(f"reportes_not_found_{int(time.time())}.png")
        return False
    
    def _navigate_to_accounting_books(self):
        """
        Navega al menú de Libros Contables.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("Buscando el menú de Libros Contables")
        time.sleep(1)  # Esperar a que aparezca el submenú
        
        libros_contables_selectors = [
            "//a[@tabindex='-1' and contains(@onfocus, 'p_SubMenuEnfocar') and contains(text(), 'Libros Contables')]",
            "//a[contains(text(), 'Libros Contables') and contains(@onfocus, 'p_SubMenuEnfocar')]",
            "//a[contains(text(), 'Libros Contables')]",
            "//a[text()='Libros Contables ']",
            "//span[contains(text(), 'Libros Contables')]"
        ]
        
        for selector in libros_contables_selectors:
            try:
                logger.info(f"Buscando Libros Contables con selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.info(f"Elementos de Libros Contables encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("Elemento de Libros Contables encontrado y visible")
                        if self._click_element_safely(element, "Libros Contables"):
                            return True
                
            except TimeoutException:
                logger.debug(f"Timeout buscando Libros Contables con selector: {selector}")
                continue
            except Exception as e:
                logger.debug(f"Error buscando Libros Contables: {str(e)}")
                continue
        
        logger.warning("No se encontró el menú de Libros Contables")
        self.browser.take_screenshot(f"libros_contables_not_found_{int(time.time())}.png")
        return False
    
    def _navigate_to_mayor_report(self):
        """
        Navega al reporte Mayor.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("Buscando el reporte Mayor")
        time.sleep(1)  # Esperar a que aparezca el submenú
        
        mayor_selectors = [
            "//a[@onclick=\"NbxAnalyticsTrackMenu('Mayor')\" and @href='conReportesLibroMayorGenerar.asp']",
            "//a[contains(@onclick, \"NbxAnalyticsTrackMenu('Mayor')\")]",
            "//a[@href='conReportesLibroMayorGenerar.asp']",
            "//a[text()='Mayor' and contains(@href, 'LibroMayor')]",
            "//a[contains(text(), 'Mayor')]"
        ]
        
        for selector in mayor_selectors:
            try:
                logger.info(f"Buscando Mayor con selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.info(f"Elementos de Mayor encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("Elemento de Mayor encontrado y visible")
                        if self._click_element_safely(element, "Mayor"):
                            return True
                
            except TimeoutException:
                logger.debug(f"Timeout buscando Mayor con selector: {selector}")
                continue
            except Exception as e:
                logger.debug(f"Error buscando Mayor: {str(e)}")
                continue
        
        logger.warning("No se encontró el reporte Mayor")
        self.browser.take_screenshot(f"mayor_not_found_{int(time.time())}.png")
        return False
    
    def click_mayor_link(self):
        """
        Navega intencionalmente a SistemaLogin y desde ahí hace todo el proceso
        completo de navegación para la siguiente cuenta. Esto garantiza un estado limpio.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("Navegando intencionalmente a SistemaLogin para empezar proceso limpio")
        
        try:
            # PASO 1: Navegar intencionalmente a SistemaLogin
            sistema_login_url = "https://web.nubox.com/SistemaLogin"
            logger.info(f"🔄 Navegando a {sistema_login_url}")
            self.browser.driver.get(sistema_login_url)
            
            # Esperar a que cargue la página
            time.sleep(3)
            
            # Verificar que llegamos correctamente
            current_url = self.browser.driver.current_url
            logger.info(f"URL actual después de navegación: {current_url}")
            
            if "SistemaLogin" not in current_url:
                logger.warning(f"⚠️ No llegamos a SistemaLogin, URL actual: {current_url}")
                # Intentar de nuevo
                self.browser.driver.get(sistema_login_url)
                time.sleep(2)
            
            # Tomar captura del estado en SistemaLogin
            self.browser.take_screenshot(f"navegado_a_sistema_login_{int(time.time())}.png")
            
            # PASO 2: Ejecutar navegación completa desde SistemaLogin
            logger.info("🚀 Iniciando navegación completa desde SistemaLogin para siguiente cuenta")
            return self._navigate_complete_process_from_sistema_login()
            
        except Exception as e:
            logger.error(f"❌ Error navegando a SistemaLogin: {str(e)}")
            return False
    
    def _navigate_complete_process_from_sistema_login(self):
        """
        Ejecuta todo el proceso de navegación desde SistemaLogin:
        SistemaLogin → Contabilidad → Reportes → Libros Contables → Mayor
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            logger.info("Ejecutando proceso completo de navegación desde SistemaLogin")
            
            # Esperar a que la página SistemaLogin cargue completamente
            time.sleep(2)
            
            # Tomar captura inicial
            self.browser.take_screenshot(f"inicio_navegacion_completa_{int(time.time())}.png")
            
            # Ejecutar la secuencia completa: Contabilidad → Reportes → Libros Contables → Mayor
            if not self._navigate_to_accounting():
                logger.error("❌ Falló navegación a Contabilidad")
                return False
            
            if not self._navigate_to_reports():
                logger.error("❌ Falló navegación a Reportes")
                return False
            
            if not self._navigate_to_accounting_books():
                logger.error("❌ Falló navegación a Libros Contables")
                return False
            
            if not self._navigate_to_mayor_report():
                logger.error("❌ Falló navegación a Mayor")
                return False
            
            # Tomar captura final del éxito
            self.browser.take_screenshot(f"navegacion_completa_exitosa_{int(time.time())}.png")
            logger.info("✅ Navegación completa desde SistemaLogin exitosa")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en navegación completa desde SistemaLogin: {str(e)}")
            return False
    
    def _click_element_safely(self, element, element_name):
        """
        Hace clic en un elemento de forma segura con múltiples métodos.
        
        Args:
            element: Elemento web a hacer clic
            element_name (str): Nombre del elemento para logging
            
        Returns:
            bool: True si el clic fue exitoso
        """
        try:
            # Scroll al elemento para asegurar que esté visible
            self.browser.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Intentar clic directo
            element.click()
            logger.info(f"Clic exitoso en {element_name}")
            return True
            
        except Exception as click_error:
            logger.debug(f"Error al hacer clic directo en {element_name}: {str(click_error)}")
            try:
                # Intentar con JavaScript
                self.browser.execute_script("arguments[0].click();", element)
                logger.info(f"Clic con JavaScript exitoso en {element_name}")
                return True
            except Exception as js_error:
                logger.debug(f"Error al hacer clic con JavaScript en {element_name}: {str(js_error)}")
                return False