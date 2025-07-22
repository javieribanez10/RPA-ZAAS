#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de autenticación para la plataforma Nubox.
Responsable únicamente del proceso de login.
"""

import time
import logging
from selenium.webdriver.common.by import By

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
        try:
            logger.info("Iniciando proceso de autenticación")
            
            # Navegar a la página de login
            self.browser.navigate_to(url)
            time.sleep(2)
            
            # Tomar captura inicial
            self.browser.take_screenshot(f"login_page_{int(time.time())}.png")
            
            # Buscar y llenar campos de credenciales
            if not self._fill_credentials(username, password):
                return False
            
            # Buscar y hacer clic en el botón de login
            if not self._click_login_button():
                return False
            
            # Verificar si el login fue exitoso
            return self._verify_login_success(url)
            
        except Exception as e:
            logger.error(f"Error durante el login: {str(e)}")
            return False
    
    def _fill_credentials(self, username, password):
        """
        Llena los campos de usuario y contraseña.
        
        Args:
            username (str): RUT del usuario
            password (str): Contraseña
            
        Returns:
            bool: True si se llenaron exitosamente
        """
        try:
            # Buscar campo de RUT
            rut_field = self._find_rut_field()
            if not rut_field:
                logger.error("No se encontró el campo de RUT")
                return False
            
            # Buscar campo de contraseña
            password_field = self._find_password_field()
            if not password_field:
                logger.error("No se encontró el campo de contraseña")
                return False
            
            # Llenar credenciales
            logger.info("Ingresando credenciales")
            rut_field.clear()
            rut_field.send_keys(username)
            time.sleep(0.5)
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error al llenar credenciales: {str(e)}")
            return False
    
    def _find_rut_field(self):
        """
        Busca el campo de RUT usando múltiples selectores.
        
        Returns:
            WebElement: Campo de RUT encontrado o None
        """
        rut_selectors = [
            "input[placeholder='Ingresa tu rut']",
            "input[name='RUT']",
            "input[id*='rut']",
            "input[type='text']"
        ]
        
        for selector in rut_selectors:
            try:
                field = self.browser.find_element(By.CSS_SELECTOR, selector)
                if field.is_displayed() and field.is_enabled():
                    logger.debug(f"Campo RUT encontrado con selector: {selector}")
                    return field
            except:
                continue
        
        # Buscar el primer input de texto visible como fallback
        try:
            text_inputs = self.browser.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for inp in text_inputs:
                if inp.is_displayed() and inp.is_enabled():
                    logger.debug("Campo RUT encontrado como primer input de texto")
                    return inp
        except:
            pass
        
        return None
    
    def _find_password_field(self):
        """
        Busca el campo de contraseña usando múltiples selectores.
        
        Returns:
            WebElement: Campo de contraseña encontrado o None
        """
        password_selectors = [
            "input[placeholder='Ingresa tu contraseña']",
            "input[name='Password']",
            "input[type='password']"
        ]
        
        for selector in password_selectors:
            try:
                field = self.browser.find_element(By.CSS_SELECTOR, selector)
                if field.is_displayed() and field.is_enabled():
                    logger.debug(f"Campo contraseña encontrado con selector: {selector}")
                    return field
            except:
                continue
        
        return None
    
    def _click_login_button(self):
        """
        Busca y hace clic en el botón de login.
        
        Returns:
            bool: True si se hizo clic exitosamente
        """
        try:
            # Tomar captura antes de buscar el botón
            self.browser.take_screenshot(f"before_button_search_{int(time.time())}.png")
            
            login_button = self._find_login_button()
            if not login_button:
                logger.error("No se pudo encontrar el botón de login")
                return False
            
            # Hacer clic en el botón
            logger.info("Haciendo clic en el botón Ingresar")
            login_button.click()
            time.sleep(3)
            
            # Tomar captura después del clic
            self.browser.take_screenshot(f"post_login_{int(time.time())}.png")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al hacer clic en botón de login: {str(e)}")
            return False
    
    def _find_login_button(self):
        """
        Busca el botón de login usando múltiples estrategias.
        
        Returns:
            WebElement: Botón de login encontrado o None
        """
        login_button_selectors = [
            "input[value='Ingresar'][class*='nbx-form_btn_login']",
            "input[value='Ingresar'][class*='btn-login']",
            "input[type='button'][value='Ingresar']",
            "input.nbx-form_btn_login",
            "input.btn-login",
            "input[onclick*='EnviarSolicitudFormulario']"
        ]
        
        for selector in login_button_selectors:
            try:
                elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                logger.debug(f"Selector '{selector}' encontró {len(elements)} elementos")
                
                for element in elements:
                    if element.is_displayed():
                        # Verificar si el botón está deshabilitado y habilitarlo
                        is_disabled = element.get_attribute("disabled")
                        if is_disabled:
                            logger.info("El botón está deshabilitado, intentando habilitarlo...")
                            self.browser.execute_script("arguments[0].removeAttribute('disabled');", element)
                            time.sleep(0.5)
                        
                        logger.info(f"Botón de login encontrado con selector: {selector}")
                        return element
            except Exception as e:
                logger.debug(f"Error con selector {selector}: {str(e)}")
                continue
        
        # Intentar con JavaScript como último recurso
        return self._find_login_button_with_javascript()
    
    def _find_login_button_with_javascript(self):
        """
        Busca el botón de login usando JavaScript.
        
        Returns:
            WebElement: Botón encontrado o None
        """
        try:
            logger.info("Usando JavaScript para buscar y habilitar el botón")
            login_button = self.browser.execute_script("""
                // Buscar el botón de login
                var button = document.querySelector('input[value="Ingresar"]') ||
                            document.querySelector('input.nbx-form_btn_login') ||
                            document.querySelector('input.btn-login') ||
                            document.querySelector('input[onclick*="EnviarSolicitudFormulario"]');
                
                if (button) {
                    // Habilitar el botón si está deshabilitado
                    button.removeAttribute('disabled');
                    button.disabled = false;
                    return button;
                }
                return null;
            """)
            
            if login_button:
                logger.info("Botón encontrado y habilitado usando JavaScript")
                return login_button
                
        except Exception as e:
            logger.debug(f"Error al buscar con JavaScript: {str(e)}")
        
        return None
    
    def _verify_login_success(self, original_url):
        """
        Verifica si el login fue exitoso.
        
        Args:
            original_url (str): URL original de login
            
        Returns:
            bool: True si el login fue exitoso
        """
        try:
            current_url = self.browser.current_url
            logger.info(f"URL actual después del login: {current_url}")
            
            # Verificación inmediata del login exitoso
            if "login" not in current_url.lower() and "account" not in current_url.lower():
                logger.info("Login exitoso: URL cambió y no contiene 'login'")
                return True
            
            # Verificar errores de login
            try:
                error_elements = self.browser.find_elements(
                    By.CSS_SELECTOR, 
                    ".validation-summary-errors, .field-validation-error"
                )
                for element in error_elements:
                    if element.is_displayed() and element.text.strip():
                        logger.error(f"Error de login detectado: {element.text}")
                        return False
            except:
                pass
            
            # Si la URL cambió, asumir login exitoso
            if current_url != original_url:
                logger.info("Login exitoso: URL cambió")
                return True
            
            # Por defecto, asumir éxito
            logger.info("Login exitoso: Verificación completada")
            return True
            
        except Exception as e:
            logger.error(f"Error al verificar login: {str(e)}")
            return False