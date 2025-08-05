#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de autenticación para la plataforma Nubox.
Responsable únicamente del proceso de login.
OPTIMIZADO para máximo rendimiento y velocidad.
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.performance_monitor import measure_performance, measure_step

logger = logging.getLogger("nubox_rpa.authentication")

class AuthenticationService:
    """
    Maneja el proceso de autenticación en Nubox.
    Principio de Responsabilidad Única: Solo maneja el login.
    """
    
    def __init__(self, browser_manager):
        """
        Inicializa el servicio de autenticación.
        
        Args:
            browser_manager (BrowserManager): Instancia del administrador del navegador
        """
        self.browser = browser_manager
    
    @measure_performance("Authentication.login")
    def login(self, username, password, url="https://web.nubox.com/Login/Account/Login?ReturnUrl=%2FSistemaLogin"):
        """
        Inicia sesión en Nubox con optimización de velocidad.
        
        Args:
            username (str): RUT del usuario
            password (str): Contraseña
            url (str): URL de inicio de sesión
            
        Returns:
            bool: True si el login fue exitoso
        """
        try:
            logger.info("🔐 Iniciando proceso de autenticación optimizado")
            
            # Navegar a la página de login
            with measure_step("Navigate to login page"):
                self.browser.navigate_to(url)
                # Esperar a que la página esté completamente cargada
                WebDriverWait(self.browser.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            
            # Buscar y llenar campos de credenciales
            with measure_step("Fill credentials"):
                if not self._fill_credentials_optimized(username, password):
                    return False
            
            # Buscar y hacer clic en el botón de login
            with measure_step("Click login button"):
                if not self._click_login_button_optimized():
                    return False
            
            # Verificar si el login fue exitoso
            with measure_step("Verify login success"):
                return self._verify_login_success_optimized(url)
            
        except Exception as e:
            logger.error(f"❌ Error durante el login: {str(e)}")
            return False
    
    def _fill_credentials_optimized(self, username, password):
        """
        Llena los campos de usuario y contraseña con optimización de velocidad.
        
        Args:
            username (str): RUT del usuario
            password (str): Contraseña
            
        Returns:
            bool: True si se llenaron exitosamente
        """
        try:
            # Buscar campo de RUT con wait explícito
            rut_field = self._find_rut_field_optimized()
            if not rut_field:
                logger.error("❌ No se encontró el campo de RUT")
                return False
            
            # Buscar campo de contraseña con wait explícito
            password_field = self._find_password_field_optimized()
            if not password_field:
                logger.error("❌ No se encontró el campo de contraseña")
                return False
            
            # Llenar credenciales usando JavaScript para mayor velocidad
            logger.info("📝 Ingresando credenciales")
            self.browser.execute_script(
                "arguments[0].value = arguments[1];", 
                rut_field, username
            )
            self.browser.execute_script(
                "arguments[0].value = arguments[1];", 
                password_field, password
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al llenar credenciales: {str(e)}")
            return False
    
    def _find_rut_field_optimized(self):
        """
        Busca el campo de RUT usando múltiples selectores con wait explícito.
        
        Returns:
            WebElement: Campo de RUT encontrado o None
        """
        rut_selectors = [
            "input[placeholder*='rut' i]",
            "input[name='RUT']",
            "input[id*='rut' i]",
            "input[type='text']:first-of-type"
        ]
        
        for selector in rut_selectors:
            try:
                element = WebDriverWait(self.browser.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.debug(f"✅ Campo RUT encontrado con selector: {selector}")
                return element
            except TimeoutException:
                continue
        
        logger.warning("⚠️ Campo RUT no encontrado con selectores CSS, intentando XPath")
        xpath_selectors = [
            "//input[contains(@placeholder, 'rut') or contains(@placeholder, 'RUT')]",
            "//input[@name='RUT']",
            "//input[contains(@id, 'rut') or contains(@id, 'RUT')]"
        ]
        
        for xpath in xpath_selectors:
            try:
                element = WebDriverWait(self.browser.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                logger.debug(f"✅ Campo RUT encontrado con XPath: {xpath}")
                return element
            except TimeoutException:
                continue
        
        return None
    
    def _find_password_field_optimized(self):
        """
        Busca el campo de contraseña usando múltiples selectores con wait explícito.
        
        Returns:
            WebElement: Campo de contraseña encontrado o None
        """
        password_selectors = [
            "input[type='password']",
            "input[placeholder*='contraseña' i]",
            "input[placeholder*='password' i]",
            "input[name*='password' i]"
        ]
        
        for selector in password_selectors:
            try:
                element = WebDriverWait(self.browser.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.debug(f"✅ Campo contraseña encontrado con selector: {selector}")
                return element
            except TimeoutException:
                continue
        
    
    def _click_login_button_optimized(self):
        """
        Busca y hace clic en el botón de login con optimización de velocidad.
        
        Returns:
            bool: True si se hizo clic exitosamente
        """
        try:
            login_button = self._find_login_button_optimized()
            if not login_button:
                logger.error("❌ No se pudo encontrar el botón de login")
                return False
            
            # Hacer clic en el botón usando JavaScript para mayor velocidad
            logger.info("🚀 Haciendo clic en el botón Ingresar")
            self.browser.execute_script("arguments[0].click();", login_button)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al hacer clic en el botón de login: {str(e)}")
            return False
    
    def _find_login_button_optimized(self):
        """
        Busca el botón de login usando múltiples selectores con wait explícito.
        
        Returns:
            WebElement: Botón de login encontrado o None
        """
        login_selectors = [
            "input[value*='Ingresar' i]",
            "button[type='submit']",
            "input[type='submit']",
            "button:contains('Ingresar')",
            "*[onclick*='login' i]"
        ]
        
        for selector in login_selectors:
            try:
                element = WebDriverWait(self.browser.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.debug(f"✅ Botón login encontrado con selector: {selector}")
                return element
            except TimeoutException:
                continue
        
        # Intentar con XPath si CSS no funciona
        xpath_selectors = [
            "//input[@value='Ingresar' or @value='INGRESAR']",
            "//button[contains(text(), 'Ingresar')]",
            "//input[@type='submit']",
            "//button[@type='submit']"
        ]
        
        for xpath in xpath_selectors:
            try:
                element = WebDriverWait(self.browser.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                logger.debug(f"✅ Botón login encontrado con XPath: {xpath}")
                return element
            except TimeoutException:
                continue
        
        return None
    
    def _verify_login_success_optimized(self, original_url):
        """
        Verifica si el login fue exitoso usando condiciones explícitas.
        
        Args:
            original_url (str): URL original de login
            
        Returns:
            bool: True si el login fue exitoso
        """
        try:
            # Esperar a que el navegador redirija o cambie la página
            WebDriverWait(self.browser.driver, 10).until(
                lambda driver: driver.current_url != original_url
            )
            
            current_url = self.browser.current_url
            logger.info(f"📍 URL después del login: {current_url}")
            
            # Verificar si no estamos en la página de login
            login_indicators = [
                "login", "signin", "account/login"
            ]
            
            is_still_login = any(indicator in current_url.lower() for indicator in login_indicators)
            
            if is_still_login:
                logger.warning("⚠️ Todavía en página de login, verificando elementos...")
                
                # Buscar elementos que indiquen login fallido
                error_selectors = [
                    ".error", ".alert-danger", "[class*='error']",
                    "*[contains(text(), 'incorrecto')]", "*[contains(text(), 'error')]"
                ]
                
                for selector in error_selectors:
                    try:
                        error_element = WebDriverWait(self.browser.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if error_element.is_displayed():
                            logger.error("❌ Error de login detectado")
                            return False
                    except TimeoutException:
                        continue
                
                # Si no hay errores visibles, asumir que el login está en progreso
                logger.info("⏳ No se detectaron errores, esperando redirección...")
                try:
                    WebDriverWait(self.browser.driver, 5).until(
                        lambda driver: not any(indicator in driver.current_url.lower() 
                                             for indicator in login_indicators)
                    )
                except TimeoutException:
                    logger.error("❌ Timeout esperando redirección después del login")
                    return False
            
            # Verificar elementos que indican login exitoso
            success_indicators = [
                "dashboard", "main", "home", "sistema"
            ]
            
            final_url = self.browser.current_url
            login_success = any(indicator in final_url.lower() for indicator in success_indicators)
            
            if login_success:
                logger.info("✅ Login exitoso - redirección detectada")
                return True
            
            # Como alternativa, buscar elementos típicos de dashboard
            dashboard_selectors = [
                ".main-content", "#main", ".dashboard", 
                "*[class*='menu']", "*[class*='nav']"
            ]
            
            for selector in dashboard_selectors:
                try:
                    WebDriverWait(self.browser.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info("✅ Login exitoso - elementos de dashboard detectados")
                    return True
                except TimeoutException:
                    continue
            
            logger.warning(f"⚠️ Login status incierto. URL final: {final_url}")
            return True  # Asumir éxito si no hay indicadores claros de fallo
            
        except Exception as e:
            logger.error(f"❌ Error verificando el éxito del login: {str(e)}")
            return False
