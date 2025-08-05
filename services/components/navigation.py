#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de navegación para la plataforma Nubox.
Responsable únicamente de la navegación a diferentes secciones.
OPTIMIZADO para máximo rendimiento y velocidad.
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.performance_monitor import measure_performance, measure_step

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
    
    @measure_performance("Navigation.navigate_to_report")
    def navigate_to_report(self, report_type="mayor"):
        """
        Navega a la sección de reportes contables con optimización de velocidad.
        
        Args:
            report_type (str): Tipo de reporte ('mayor', 'balance', etc.)
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            logger.info("🧭 Iniciando navegación optimizada a reportes contables")
            
            # Secuencia de navegación optimizada: Contabilidad -> Reportes -> Libros Contables -> Mayor
            with measure_step("Navigate to Accounting module"):
                if not self._navigate_to_accounting_optimized():
                    return False
            
            with measure_step("Navigate to Reports menu"):
                if not self._navigate_to_reports_optimized():
                    return False
            
            with measure_step("Navigate to Accounting Books"):
                if not self._navigate_to_accounting_books_optimized():
                    return False
            
            with measure_step("Navigate to Mayor report"):
                if not self._navigate_to_mayor_report_optimized():
                    return False
            
            logger.info("✅ Navegación completada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al navegar al reporte: {str(e)}")
            return False
    
    def _navigate_to_accounting_optimized(self):
        """
        Navega al módulo de Contabilidad con optimización de velocidad.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("🏢 Navegando al módulo de Contabilidad")
        
        contabilidad_selectors = [
            "//span[contains(text(), 'Contabilidad') and contains(@class, 'jqx-tree-grid-title')]",
            "//td[contains(@class, 'jqx-cell')]//span[contains(text(), 'Contabilidad')]",
            "//span[text()='Contabilidad']"
        ]
        
        for selector in contabilidad_selectors:
            try:
                logger.debug(f"🔍 Intentando selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.debug(f"📋 Elementos encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("✅ Elemento de Contabilidad encontrado y visible")
                        if self._click_element_safely_optimized(element, "Contabilidad"):
                            # Esperar que el menú se actualice
                            WebDriverWait(self.browser.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Reportes')]"))
                            )
                            return True
                
            except TimeoutException:
                logger.debug(f"⏰ Timeout con selector {selector}")
                continue
            except Exception as e:
                logger.debug(f"❌ Error con selector {selector}: {str(e)}")
                continue
        
        logger.error("❌ No se pudo hacer clic en el módulo de Contabilidad")
        return False
    
    def _navigate_to_reports_optimized(self):
        """
        Navega al menú de Reportes con optimización de velocidad.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("📊 Buscando el menú de Reportes")
        
        reportes_selectors = [
            "//a[@tabindex='-1' and contains(@onfocus, 'p_MenuEnfocar') and text()='Reportes']",
            "//a[text()='Reportes' and contains(@onfocus, 'p_MenuEnfocar')]",
            "//a[text()='Reportes']"
        ]
        
        for selector in reportes_selectors:
            try:
                logger.debug(f"🔍 Buscando Reportes con selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.debug(f"📋 Elementos de Reportes encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("✅ Elemento de Reportes encontrado y visible")
                        if self._click_element_safely_optimized(element, "Reportes"):
                            # Esperar que aparezca el submenú
                            WebDriverWait(self.browser.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Libros Contables')]"))
                            )
                            return True
                
            except TimeoutException:
                logger.debug(f"⏰ Timeout buscando Reportes con selector: {selector}")
                continue
            except Exception as e:
                logger.debug(f"❌ Error buscando Reportes: {str(e)}")
                continue
        
        logger.error("❌ No se pudo hacer clic en Reportes")
        return False
    
    def _navigate_to_accounting_books_optimized(self):
        """
        Navega al submenú de Libros Contables con optimización de velocidad.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("📚 Buscando el submenú de Libros Contables")
        
        libros_selectors = [
            "//a[@tabindex='-1' and contains(@onfocus, 'p_MenuEnfocar') and text()='Libros Contables']",
            "//a[text()='Libros Contables']"
        ]
        
        for selector in libros_selectors:
            try:
                logger.debug(f"🔍 Buscando Libros Contables con selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.debug(f"📋 Elementos de Libros Contables encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("✅ Elemento de Libros Contables encontrado y visible")
                        if self._click_element_safely_optimized(element, "Libros Contables"):
                            # Esperar que aparezca el submenú
                            WebDriverWait(self.browser.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Mayor')]"))
                            )
                            return True
                
            except TimeoutException:
                logger.debug(f"⏰ Timeout buscando Libros Contables: {selector}")
                continue
            except Exception as e:
                logger.debug(f"❌ Error buscando Libros Contables: {str(e)}")
                continue
        
    
    def _navigate_to_mayor_report_optimized(self):
        """
        Navega al reporte Mayor con optimización de velocidad.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        logger.info("📈 Buscando el reporte Mayor")
        
        mayor_selectors = [
            "//a[@tabindex='-1' and contains(@onfocus, 'p_SubMenuEnfocar') and text()='Mayor']",
            "//a[text()='Mayor' and contains(@onfocus, 'p_SubMenuEnfocar')]",
            "//a[text()='Mayor']"
        ]
        
        for selector in mayor_selectors:
            try:
                logger.debug(f"🔍 Buscando Mayor con selector: {selector}")
                elements = WebDriverWait(self.browser.driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                logger.debug(f"📋 Elementos de Mayor encontrados: {len(elements)}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info("✅ Elemento de Mayor encontrado y visible")
                        if self._click_element_safely_optimized(element, "Mayor"):
                            # Esperar que la página del reporte cargue
                            WebDriverWait(self.browser.driver, 10).until(
                                lambda driver: "mayor" in driver.current_url.lower() or 
                                              any(el.is_displayed() for el in driver.find_elements(By.TAG_NAME, "select"))
                            )
                            logger.info("✅ Página del reporte Mayor cargada exitosamente")
                            return True
                
            except TimeoutException:
                logger.debug(f"⏰ Timeout buscando Mayor: {selector}")
                continue
            except Exception as e:
                logger.debug(f"❌ Error buscando Mayor: {str(e)}")
                continue
        
        logger.error("❌ No se pudo hacer clic en Mayor")
        return False
    
    def _click_element_safely_optimized(self, element, element_name):
        """
        Hace clic en un elemento de forma segura con optimización de velocidad.
        
        Args:
            element: WebElement a hacer clic
            element_name (str): Nombre del elemento para logging
            
        Returns:
            bool: True si el clic fue exitoso
        """
        try:
            # Usar JavaScript para hacer clic más rápido
            self.browser.execute_script("arguments[0].click();", element)
            logger.debug(f"✅ Clic exitoso en {element_name} usando JavaScript")
            return True
        except Exception as js_error:
            logger.debug(f"⚠️ JavaScript click falló para {element_name}, intentando click normal: {js_error}")
            try:
                element.click()
                logger.debug(f"✅ Clic exitoso en {element_name} usando click normal")
                return True
            except Exception as click_error:
                logger.error(f"❌ Error haciendo clic en {element_name}: {click_error}")
                return False
