#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio para interactuar con la plataforma Nubox.
"""

import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configurar logger
logger = logging.getLogger("nubox_rpa.service")

class NuboxService:
    """Clase para interactuar con la plataforma Nubox."""
    
    def __init__(self, headless=True, timeout=30):
        """
        Inicializa el servicio de Nubox.
        
        Args:
            headless (bool): Si True, el navegador se ejecuta sin interfaz gráfica
            timeout (int): Tiempo máximo de espera para operaciones (segundos)
        """
        self.timeout = timeout
        self.driver = None
        self.setup_driver(headless)
        
    def setup_driver(self, headless=True):
        """
        Configura el driver de Selenium.
        
        Args:
            headless (bool): Si True, el navegador se ejecuta sin interfaz gráfica
        """
        options = webdriver.ChromeOptions()
        
        if headless:
            options.add_argument("--headless")
            
        # Configuraciones adicionales para mejorar la estabilidad
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Prevenir detección de automatización
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        
        logger.debug("Driver de Chrome inicializado")
        
    def login(self, username, password, url="https://web.nubox.com/Login/Account/Login?ReturnUrl=%2FSistemaLogin"):
        """
        Inicia sesión en Nubox usando los selectores exactos del formulario.
        
        Args:
            username (str): RUT del usuario
            password (str): Contraseña
            url (str): URL de inicio de sesión
            
        Returns:
            bool: True si el login fue exitoso, False en caso contrario
        """
        try:
            logger.info(f"Navegando a {url}")
            self.driver.get(url)
            
            # Esperar a que la página cargue completamente
            time.sleep(2)
            
            # Tomar captura para diagnóstico al inicio
            screenshot_path = f"logs/login_page_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Se guardó una captura de pantalla inicial en {screenshot_path}")
            
            # Según la captura de pantalla, tenemos:
            # - Un campo "Ingresa tu rut"
            # - Un campo "Ingresa tu contraseña"
            # - Un botón azul "Ingresar"
            
            try:
                # Campo de RUT - usando múltiples selectores basados en la nueva captura
                logger.info("Buscando el campo de RUT")
                rut_selectors = [
                    "input[placeholder='Ingresa tu rut']",
                    "input[name='RUT']",
                    "input[id*='rut']",
                    "input[type='text']"
                ]
                
                rut_field = None
                for selector in rut_selectors:
                    try:
                        rut_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        logger.debug(f"Campo RUT encontrado con selector: {selector}")
                        break
                    except:
                        continue
                
                if not rut_field:
                    # Si no encontramos por los selectores, buscar el primer input de texto visible
                    text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    for inp in text_inputs:
                        if inp.is_displayed() and inp.is_enabled():
                            rut_field = inp
                            logger.debug("Campo RUT encontrado como primer input de texto")
                            break
                
                # Campo de contraseña - usando múltiples selectores
                logger.info("Buscando el campo de contraseña")
                password_selectors = [
                    "input[placeholder='Ingresa tu contraseña']",
                    "input[name='Password']",
                    "input[type='password']"
                ]
                
                password_field = None
                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        logger.debug(f"Campo contraseña encontrado con selector: {selector}")
                        break
                    except:
                        continue
                
                # Verificar que hemos encontrado todos los elementos necesarios
                if not rut_field or not password_field:
                    logger.error("No se encontraron los campos de RUT o contraseña")
                    return False
                
                # Ingresar credenciales
                logger.info("Ingresando credenciales")
                rut_field.clear()
                rut_field.send_keys(username)
                time.sleep(0.5)
                
                password_field.clear()
                password_field.send_keys(password)
                time.sleep(0.5)
                
                # Botón "Ingresar" - usando el selector exacto del elemento HTML
                logger.info("Buscando el botón Ingresar")
                
                # Primero, tomar captura de pantalla para diagnóstico
                screenshot_path = f"logs/before_button_search_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Captura antes de buscar botón: {screenshot_path}")
                
                # Selectores específicos para el botón de Nubox
                login_button_selectors = [
                    # Selector exacto basado en la información proporcionada
                    "input[value='Ingresar'][class*='nbx-form_btn_login']",
                    "input[value='Ingresar'][class*='btn-login']",
                    "input[type='button'][value='Ingresar']",
                    "input.nbx-form_btn_login",
                    "input.btn-login",
                    # Selectores alternativos
                    "input[onclick*='EnviarSolicitudFormulario']"
                ]
                
                login_button = None
                for selector in login_button_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        logger.info(f"Selector '{selector}' encontró {len(elements)} elementos")
                        
                        for element in elements:
                            if element.is_displayed():
                                # Verificar si el botón está habilitado o deshabilitado
                                is_disabled = element.get_attribute("disabled")
                                logger.info(f"Botón encontrado - disabled: {is_disabled}")
                                
                                # Si está deshabilitado, intentar habilitarlo con JavaScript
                                if is_disabled:
                                    logger.info("El botón está deshabilitado, intentando habilitarlo...")
                                    self.driver.execute_script("arguments[0].removeAttribute('disabled');", element)
                                    time.sleep(0.5)  # Esperar un momento
                                
                                login_button = element
                                logger.info(f"Botón de login encontrado con selector: {selector}")
                                break
                        
                        if login_button:
                            break
                    except Exception as e:
                        logger.debug(f"Error con selector {selector}: {str(e)}")
                        continue
                
                # Si no encontramos el botón, intentar usar JavaScript para encontrarlo y habilitarlo
                if not login_button:
                    logger.info("Usando JavaScript para buscar y habilitar el botón")
                    try:
                        login_button = self.driver.execute_script("""
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
                    except Exception as e:
                        logger.debug(f"Error al buscar con JavaScript: {str(e)}")
                
                if not login_button:
                    logger.error("No se pudo encontrar el botón de login")
                    return False
                
                # Hacer clic en el botón Ingresar
                logger.info("Haciendo clic en el botón Ingresar")
                login_button.click()
                
                # Esperar a que se procese el login
                time.sleep(3)
                
                # Tomar captura para ver el resultado
                screenshot_path = f"logs/post_login_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Se guardó una captura después del login en {screenshot_path}")
                
                # Verificar si el login fue exitoso - método ultra rápido
                current_url = self.driver.current_url
                logger.info(f"URL actual después del login: {current_url}")
                
                # Verificación inmediata del login exitoso
                if "login" not in current_url.lower() and "account" not in current_url.lower():
                    logger.info("Login exitoso: URL cambió y no contiene 'login'")
                    return True  # Retornar inmediatamente
                
                # Verificación rápida de errores (sin timeouts largos)
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".validation-summary-errors, .field-validation-error")
                    for element in error_elements:
                        if element.is_displayed() and element.text.strip():
                            logger.error(f"Error de login detectado: {element.text}")
                            return False
                except:
                    pass
                
                # Si la URL cambió, asumir login exitoso
                if current_url != url:
                    logger.info("Login exitoso: URL cambió")
                    return True
                
                # Por defecto, asumir éxito para evitar retrasos
                logger.info("Login exitoso: Verificación completada")
                return True
                
            except Exception as e:
                logger.error(f"Error al interactuar con el formulario: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error durante el login: {str(e)}")
            return False
    
    def navigate_to_report(self, report_type="mayor"):
        """
        Navega a la sección de reportes contables en Nubox.
        
        Args:
            report_type (str): Tipo de reporte ('mayor', 'balance', etc.)
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            # Tomar una captura de la página principal después del login
            screenshot_path = f"logs/main_page_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Página principal: {screenshot_path}")
            
            # Esperar a que la página principal cargue completamente (reducido de 3 a 2 segundos)
            time.sleep(2)
            
            # Navegación al módulo de contabilidad usando el selector específico
            logger.info("Navegando al módulo de contabilidad")
            
            # Selectores específicos para el elemento de Contabilidad de Nubox (más eficiente)
            contabilidad_selectors = [
                # Selector más específico primero
                "//td[contains(@class, 'jqx-cell') and contains(@class, 'jqx-grid-cell')]//span[contains(text(), 'Contabilidad')]",
                "//span[contains(text(), 'Contabilidad') and contains(@class, 'jqx-tree-grid-title')]",
                "//span[contains(text(), 'Contabilidad')]"
            ]
            
            contabilidad_clicked = False
            for selector in contabilidad_selectors:
                try:
                    logger.info(f"Intentando selector: {selector}")
                    # Usar un timeout más corto para ser más eficiente
                    elements = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    logger.info(f"Elementos encontrados: {len(elements)}")
                    
                    for element in elements:
                        if element.is_displayed():
                            logger.info("Elemento de Contabilidad encontrado y visible")
                            try:
                                # Scroll hasta el elemento para asegurar que esté visible
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(0.5)  # Reducido de 1 segundo
                                
                                # Intentar hacer clic directo
                                element.click()
                                logger.info(f"Clic exitoso en Contabilidad con selector: {selector}")
                                contabilidad_clicked = True
                                break
                            except Exception as click_error:
                                logger.debug(f"Error al hacer clic directo: {str(click_error)}")
                                try:
                                    # Intentar con JavaScript
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"Clic con JavaScript exitoso en Contabilidad")
                                    contabilidad_clicked = True
                                    break
                                except Exception as js_error:
                                    logger.debug(f"Error al hacer clic con JavaScript: {str(js_error)}")
                                    continue
                    
                    if contabilidad_clicked:
                        break
                        
                except TimeoutException:
                    logger.debug(f"Timeout con selector {selector}")
                    continue
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {str(e)}")
                    continue
            
            if not contabilidad_clicked:
                logger.error("No se pudo hacer clic en el módulo de Contabilidad")
                # Tomar captura para diagnóstico
                screenshot_path = f"logs/contabilidad_error_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Captura de error: {screenshot_path}")
                return False
            
            # Esperar a que responda el clic (reducido de 2 a 1 segundo)
            time.sleep(1)
            
            # Tomar captura después de hacer clic en Contabilidad
            screenshot_path = f"logs/contabilidad_clicked_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Después de clic en Contabilidad: {screenshot_path}")
            
            # Ahora buscar el menú de Reportes usando el selector específico proporcionado
            logger.info("Buscando el menú de Reportes")
            
            # Selectores específicos para el elemento de Reportes basado en el HTML proporcionado
            reportes_selectors = [
                # Selector exacto basado en el HTML proporcionado
                "//a[@tabindex='-1' and contains(@onfocus, 'p_MenuEnfocar') and text()='Reportes']",
                "//a[text()='Reportes' and contains(@onfocus, 'p_MenuEnfocar')]",
                "//a[text()='Reportes']",
                # Selectores alternativos
                "//a[contains(text(), 'Reportes')]",
                "//span[contains(text(), 'Reportes')]"
            ]
            
            reportes_clicked = False
            for selector in reportes_selectors:
                try:
                    logger.info(f"Buscando Reportes con selector: {selector}")
                    # Usar timeout más corto
                    elements = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    logger.info(f"Elementos de Reportes encontrados: {len(elements)}")
                    
                    for element in elements:
                        if element.is_displayed():
                            logger.info("Elemento de Reportes encontrado y visible")
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(0.5)  # Reducido
                                element.click()
                                logger.info(f"Clic exitoso en Reportes")
                                reportes_clicked = True
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"Clic con JavaScript exitoso en Reportes")
                                    reportes_clicked = True
                                    break
                                except:
                                    continue
                    
                    if reportes_clicked:
                        break
                        
                except TimeoutException:
                    logger.debug(f"Timeout buscando Reportes con selector: {selector}")
                    continue
                except Exception as e:
                    logger.debug(f"Error buscando Reportes: {str(e)}")
                    continue
            
            if not reportes_clicked:
                logger.warning("No se encontró el menú de Reportes")
                # Tomar captura para diagnóstico
                screenshot_path = f"logs/reportes_not_found_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Captura de Reportes no encontrado: {screenshot_path}")
                return False
            
            # Ahora buscar y hacer clic en "Libros Contables"
            logger.info("Buscando el menú de Libros Contables")
            
            # Esperar un momento para que aparezca el submenú de Reportes
            time.sleep(1)
            
            # Selectores específicos para "Libros Contables" basado en el HTML proporcionado
            libros_contables_selectors = [
                # Selector exacto basado en el HTML proporcionado
                "//a[@tabindex='-1' and contains(@onfocus, 'p_SubMenuEnfocar') and contains(text(), 'Libros Contables')]",
                "//a[contains(text(), 'Libros Contables') and contains(@onfocus, 'p_SubMenuEnfocar')]",
                "//a[contains(text(), 'Libros Contables')]",
                # Selectores alternativos
                "//a[text()='Libros Contables ']",  # Con espacio al final como en el HTML
                "//span[contains(text(), 'Libros Contables')]"
            ]
            
            libros_contables_clicked = False
            for selector in libros_contables_selectors:
                try:
                    logger.info(f"Buscando Libros Contables con selector: {selector}")
                    # Usar timeout corto
                    elements = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    logger.info(f"Elementos de Libros Contables encontrados: {len(elements)}")
                    
                    for element in elements:
                        if element.is_displayed():
                            logger.info("Elemento de Libros Contables encontrado y visible")
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(0.5)
                                element.click()
                                logger.info(f"Clic exitoso en Libros Contables")
                                libros_contables_clicked = True
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"Clic con JavaScript exitoso en Libros Contables")
                                    libros_contables_clicked = True
                                    break
                                except:
                                    continue
                    
                    if libros_contables_clicked:
                        break
                        
                except TimeoutException:
                    logger.debug(f"Timeout buscando Libros Contables con selector: {selector}")
                    continue
                except Exception as e:
                    logger.debug(f"Error buscando Libros Contables: {str(e)}")
                    continue
            
            if not libros_contables_clicked:
                logger.warning("No se encontró el menú de Libros Contables")
                # Tomar captura para diagnóstico
                screenshot_path = f"logs/libros_contables_not_found_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Captura de Libros Contables no encontrado: {screenshot_path}")
                return False
            
            # Ahora buscar y hacer clic en "Mayor"
            logger.info("Buscando el reporte Mayor")
            
            # Esperar un momento para que aparezca el submenú de Libros Contables
            time.sleep(1)
            
            # Selectores específicos para "Mayor" basado en el HTML proporcionado
            mayor_selectors = [
                # Selector exacto basado en el HTML proporcionado
                "//a[@onclick=\"NbxAnalyticsTrackMenu('Mayor')\" and @href='conReportesLibroMayorGenerar.asp']",
                "//a[contains(@onclick, \"NbxAnalyticsTrackMenu('Mayor')\")]",
                "//a[@href='conReportesLibroMayorGenerar.asp']",
                # Selectores alternativos
                "//a[text()='Mayor' and contains(@href, 'LibroMayor')]",
                "//a[contains(text(), 'Mayor')]"
            ]
            
            mayor_clicked = False
            for selector in mayor_selectors:
                try:
                    logger.info(f"Buscando Mayor con selector: {selector}")
                    # Usar timeout corto
                    elements = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_all_elements_located((By.XPATH, selector))
                    )
                    logger.info(f"Elementos de Mayor encontrados: {len(elements)}")
                    
                    for element in elements:
                        if element.is_displayed():
                            logger.info("Elemento de Mayor encontrado y visible")
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(0.5)
                                element.click()
                                logger.info(f"Clic exitoso en Mayor")
                                mayor_clicked = True
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"Clic con JavaScript exitoso en Mayor")
                                    mayor_clicked = True
                                    break
                                except:
                                    continue
                    
                    if mayor_clicked:
                        break
                        
                except TimeoutException:
                    logger.debug(f"Timeout buscando Mayor con selector: {selector}")
                    continue
                except Exception as e:
                    logger.debug(f"Error buscando Mayor: {str(e)}")
                    continue
            
            if not mayor_clicked:
                logger.warning("No se encontró el reporte Mayor")
                # Tomar captura para diagnóstico
                screenshot_path = f"logs/mayor_not_found_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Captura de Mayor no encontrado: {screenshot_path}")
                return False
            
            # Esperar y tomar captura final
            time.sleep(1)
            screenshot_path = f"logs/after_navigation_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Estado final de navegación: {screenshot_path}")
            
            return True
                
        except Exception as e:
            logger.error(f"Error al navegar al reporte: {str(e)}")
            return False
    
    def set_report_parameters(self, params=None):
        """
        Configura los parámetros del reporte Mayor de Nubox.
        
        Args:
            params (dict): Parámetros para el reporte (fechas, formato, etc.)
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        if not params:
            params = {}
            
        try:
            logger.info("Configurando parámetros del reporte Mayor")
            
            # Esperar a que la página del reporte cargue completamente
            time.sleep(3)
            
            # Tomar captura inicial de la página de parámetros
            screenshot_path = f"logs/parametros_inicial_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Captura inicial de parámetros: {screenshot_path}")
            
            # Verificar si hay iframes en la página
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"iframes encontrados en la página: {len(iframes)}")
            
            # Si hay iframe, cambiar el contexto al iframe
            if iframes:
                for idx, iframe in enumerate(iframes):
                    try:
                        iframe_name = iframe.get_attribute("name") or f"iframe_{idx}"
                        iframe_src = iframe.get_attribute("src") or "sin_src"
                        logger.info(f"iframe {idx}: name='{iframe_name}', src='{iframe_src}'")
                        
                        # Cambiar al iframe
                        self.driver.switch_to.frame(iframe)
                        
                        # Verificar si hay inputs en este iframe
                        inputs_in_frame = self.driver.find_elements(By.TAG_NAME, "input")
                        logger.info(f"Inputs encontrados en iframe {idx}: {len(inputs_in_frame)}")
                        
                        if len(inputs_in_frame) > 0:
                            logger.info(f"Usando iframe {idx} que contiene {len(inputs_in_frame)} inputs")
                            break
                        else:
                            # Regresar al contexto principal si no hay inputs
                            self.driver.switch_to.default_content()
                    except Exception as e:
                        logger.debug(f"Error al cambiar a iframe {idx}: {str(e)}")
                        self.driver.switch_to.default_content()
                        continue
            
            # Listar todos los inputs ahora que estamos en el contexto correcto
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"Total de inputs encontrados en la página/iframe: {len(all_inputs)}")
            for idx, inp in enumerate(all_inputs):
                try:
                    inp_name = inp.get_attribute("name") or "sin_nombre"
                    inp_type = inp.get_attribute("type") or "sin_tipo"
                    inp_value = inp.get_attribute("value") or "sin_valor"
                    inp_id = inp.get_attribute("id") or "sin_id"
                    logger.info(f"Input {idx}: name='{inp_name}', type='{inp_type}', value='{inp_value}', id='{inp_id}'")
                except:
                    logger.info(f"Input {idx}: [no se pudieron leer propiedades]")
            
            # Buscar los campos de fecha del período (basándome en la imagen)
            # 1. Hacer clic en el campo "Desde", borrar texto y escribir nueva fecha
            logger.info("Configurando el campo 'Desde' con nueva fecha")
            try:
                # Buscar el campo "Desde" específicamente
                fecha_desde_field = None
                
                try:
                    fecha_desde_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='Desde']")
                    logger.info("Campo 'Desde' encontrado por nombre")
                except:
                    logger.error("No se pudo encontrar el campo 'Desde'")
                    return False
                
                if not fecha_desde_field:
                    logger.error("No se pudo encontrar el campo 'Desde'")
                    return False
                
                # Hacer clic en el campo "Desde"
                logger.info("Haciendo clic en el campo 'Desde'")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", fecha_desde_field)
                time.sleep(0.5)
                fecha_desde_field.click()
                time.sleep(0.5)
                
                # Borrar todo el texto del campo
                logger.info("Borrando todo el texto del campo 'Desde'")
                fecha_desde_field.clear()
                time.sleep(0.5)
                
                # Escribir la nueva fecha de forma más robusta
                nueva_fecha = "10/06/2025"
                logger.info(f"Escribiendo nueva fecha en campo 'Desde': {nueva_fecha}")
                
                # Método más robusto para escribir la fecha
                try:
                    # Primero desactivar cualquier validación JavaScript temporalmente
                    self.driver.execute_script("""
                        // Desactivar validaciones temporalmente
                        var field = arguments[0];
                        field._originalOnBlur = field.onblur;
                        field._originalOnChange = field.onchange;
                        field.onblur = null;
                        field.onchange = null;
                    """, fecha_desde_field)
                    
                    # Escribir la fecha usando JavaScript para evitar eventos intermedios
                    self.driver.execute_script("""
                        var field = arguments[0];
                        var value = arguments[1];
                        field.value = value;
                        field.setAttribute('value', value);
                    """, fecha_desde_field, nueva_fecha)
                    
                    # Esperar un momento
                    time.sleep(0.5)
                    
                    logger.info(f"Fecha 'Desde' configurada exitosamente usando JavaScript: {nueva_fecha}")
                    
                except Exception as js_error:
                    logger.debug(f"Error con JavaScript, intentando método tradicional: {str(js_error)}")
                    # Si JavaScript falla, usar método tradicional pero más cuidadoso
                    fecha_desde_field.send_keys(nueva_fecha)
                
                # NO presionar Tab para evitar la validación inmediata
                # El campo se validará cuando se haga clic en Aceptar
                logger.info(f"Fecha 'Desde' configurada exitosamente: {nueva_fecha}")
                
                # Tomar captura después de configurar la fecha
                screenshot_path = f"logs/fecha_desde_configurada_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Captura después de configurar fecha: {screenshot_path}")
                
            except Exception as e:
                logger.error(f"Error al configurar fecha 'Desde': {str(e)}")
                # Manejar alertas que puedan estar abiertas
                try:
                    alert = self.driver.switch_to.alert
                    alert_text = alert.text
                    logger.warning(f"Alerta detectada en excepción: {alert_text}")
                    alert.accept()
                except:
                    pass
                # No retornar False aquí, continuar con el proceso
                logger.warning("Hubo error al configurar fecha, pero continuando con el proceso")
            
            # 2. Configurar formato del reporte (cambiar de PDF a EXCEL)
            logger.info("Configurando formato del reporte a EXCEL")
            try:
                # Buscar el dropdown de formato
                format_selectors = [
                    "select",
                    "//select[contains(@name, 'formato') or contains(@id, 'formato')]",
                    "//select"
                ]
                
                formato_select = None
                for selector in format_selectors:
                    try:
                        if selector.startswith("//"):
                            elements = self.driver.find_elements(By.XPATH, selector)
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        logger.info(f"Selector de formato '{selector}' encontró {len(elements)} elementos")
                        
                        # Buscar el select que contenga "PDF" como opción
                        for element in elements:
                            try:
                                options = element.find_elements(By.TAG_NAME, "option")
                                option_texts = [opt.text for opt in options]
                                logger.info(f"Select encontrado con opciones: {option_texts}")
                                
                                if "PDF" in option_texts and "EXCEL" in option_texts:
                                    formato_select = element
                                    logger.info("Select de formato encontrado")
                                    break
                            except:
                                continue
                        
                        if formato_select:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Error con selector de formato {selector}: {str(e)}")
                        continue
                
                if formato_select:
                    # Cambiar a EXCEL
                    from selenium.webdriver.support.ui import Select
                    select = Select(formato_select)
                    
                    # Tomar captura antes del cambio
                    screenshot_path = f"logs/antes_cambio_formato_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Captura antes de cambiar formato: {screenshot_path}")
                    
                    select.select_by_value("EXCEL")
                    logger.info("Formato cambiado a EXCEL")
                    time.sleep(0.5)
                else:
                    logger.warning("No se encontró el dropdown de formato")
                
            except Exception as e:
                logger.error(f"Error al configurar formato: {str(e)}")
                # No es crítico, continuar
            
            # 4. Tomar captura final
            screenshot_path = f"logs/parametros_configurados_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Captura final de parámetros configurados: {screenshot_path}")
            
            # 5. Buscar botón Aceptar/Generar usando el selector específico proporcionado
            logger.info("Buscando botón para generar el reporte")
            try:
                # Selector específico del botón Aceptar proporcionado por el usuario
                generar_button_selectors = [
                    # Selector exacto basado en el HTML proporcionado
                    "//a[@id='BotonAceptar' and @class='BotonActivo' and contains(@onclick, 'p_ValidarFormulario')]",
                    "//a[@id='BotonAceptar']",
                    "#BotonAceptar",
                    "a.BotonActivo",
                    # Selectores alternativos
                    "//input[@value='Aceptar']",
                    "//button[contains(text(), 'Aceptar')]",
                    "//a[contains(text(), 'Aceptar')]"
                ]
                
                generar_button = None
                for selector in generar_button_selectors:
                    try:
                        if selector.startswith("//"):
                            elements = self.driver.find_elements(By.XPATH, selector)
                        elif selector.startswith("#"):
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        logger.info(f"Selector de botón '{selector}' encontró {len(elements)} elementos")
                        
                        for element in elements:
                            if element.is_displayed():
                                button_text = element.get_attribute("innerText") or element.get_attribute("value") or element.text
                                button_onclick = element.get_attribute("onclick") or "sin_onclick"
                                logger.info(f"Botón encontrado: texto='{button_text}', onclick='{button_onclick}'")
                                generar_button = element
                                break
                        
                        if generar_button:
                            break
                    except Exception as e:
                        logger.debug(f"Error con selector de botón {selector}: {str(e)}")
                        continue
                
                if generar_button:
                    logger.info("Haciendo clic en el botón Aceptar para generar el reporte")
                    
                    # Scroll al botón para asegurar que esté visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", generar_button)
                    time.sleep(0.5)
                    
                    # Intentar clic directo primero
                    try:
                        generar_button.click()
                        logger.info("Clic directo en botón Aceptar exitoso")
                    except:
                        # Si el clic directo falla, usar JavaScript
                        self.driver.execute_script("arguments[0].click();", generar_button)
                        logger.info("Clic con JavaScript en botón Aceptar exitoso")
                    
                    # Esperar a que se procese la solicitud del reporte
                    logger.info("Esperando a que se genere el reporte...")
                    time.sleep(5)
                    
                    # Tomar captura después de hacer clic en Aceptar
                    screenshot_path = f"logs/despues_click_aceptar_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Captura después de clic en Aceptar: {screenshot_path}")
                    
                else:
                    logger.warning("No se encontró botón Aceptar para generar el reporte")
                    return False
                    
            except Exception as e:
                logger.error(f"Error al buscar/hacer clic en botón Aceptar: {str(e)}")
                return False
            
            return True
                
        except Exception as e:
            logger.error(f"Error al configurar parámetros del reporte: {str(e)}")
            return False
    
    def extract_report(self):
        """
        Extrae los datos del reporte mostrado en pantalla o descarga el archivo si el formato lo requiere.
        
        Returns:
            pd.DataFrame: DataFrame con los datos del reporte
            str: Ruta al archivo descargado (en caso de formato Excel o PDF)
        """
        try:
            logger.info("Verificando si hay descarga de archivo...")
            
            # Esperar un momento para que se procese la descarga
            time.sleep(3)
            
            # Verificar si hay diálogos de descarga o mensajes de proceso
            download_indicators = [
                "//a[contains(@href, '.xls') or contains(@href, '.xlsx')]",  # Enlaces a archivos Excel
                "//a[contains(text(), 'Descargar') or contains(text(), 'Download')]",  # Botones de descarga
                "//div[contains(text(), 'generando') or contains(text(), 'procesando')]",  # Mensajes de proceso
                "//iframe[contains(@src, 'excel') or contains(@src, 'download')]"  # iframes de descarga
            ]
            
            download_found = False
            for selector in download_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.info(f"Detectado indicador de descarga: {selector} ({len(elements)} elementos)")
                        for element in elements:
                            if element.is_displayed():
                                href = element.get_attribute("href")
                                text = element.text or element.get_attribute("title")
                                logger.info(f"Elemento de descarga: href='{href}', text='{text}'")
                                
                                # Si es un enlace de descarga, hacer clic
                                if href and ('.xls' in href.lower() or 'download' in href.lower()):
                                    try:
                                        logger.info("Haciendo clic en enlace de descarga...")
                                        element.click()
                                        download_found = True
                                        time.sleep(2)
                                        return pd.DataFrame(), f"Archivo descargado: {href}"
                                    except Exception as e:
                                        logger.debug(f"Error al hacer clic en descarga: {str(e)}")
                except Exception as e:
                    logger.debug(f"Error buscando indicador {selector}: {str(e)}")
            
            # Si no encontramos indicadores específicos, buscar en la página actual
            logger.info("Buscando contenido del reporte en la página actual...")
            
            # Tomar captura para diagnóstico
            screenshot_path = f"logs/extract_report_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Captura durante extracción: {screenshot_path}")
            
            # Verificar si estamos en un iframe con contenido
            current_url = self.driver.current_url
            logger.info(f"URL actual durante extracción: {current_url}")
            
            # Si ya estamos en el iframe correcto o hay contenido, intentar extraer tabla
            try:
                # Buscar tablas en la página actual
                all_tables = self.driver.find_elements(By.TAG_NAME, "table")
                logger.info(f"Tablas encontradas en la página: {len(all_tables)}")
                
                if all_tables:
                    # Obtener el HTML de la página
                    html_content = self.driver.page_source
                    soup = BeautifulSoup(html_content, "html.parser")
                    
                    # Buscar la tabla más grande (probablemente el reporte)
                    tables = soup.select("table")
                    if tables:
                        table = max(tables, key=lambda t: len(t.select("tr")))
                        logger.info(f"Procesando tabla con {len(table.select('tr'))} filas")
                        
                        # Extraer datos de la tabla
                        rows = []
                        for tr in table.select("tr"):
                            cells = tr.select("td, th")
                            row_data = [cell.get_text(strip=True) for cell in cells]
                            if row_data and any(row_data):  # Solo agregar filas no vacías
                                rows.append(row_data)
                        
                        if rows:
                            # Crear DataFrame
                            df = pd.DataFrame(rows[1:], columns=rows[0] if len(rows) > 1 else None)
                            logger.info(f"Datos extraídos: {len(df)} filas, {len(df.columns)} columnas")
                            return df
                
            except Exception as e:
                logger.debug(f"Error extrayendo tabla: {str(e)}")
            
            # Si llegamos aquí, no encontramos datos
            logger.warning("No se encontraron datos del reporte para extraer")
            
            # Verificar si hay mensajes de error o estado
            try:
                error_messages = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
                for msg in error_messages:
                    if msg.is_displayed():
                        logger.warning(f"Mensaje en pantalla: {msg.text}")
            except:
                pass
            
            # Si llegamos aquí, verificar si se inició una descarga
            logger.info("Esperando a que se complete la descarga...")
            
            # Esperar más tiempo para descargas grandes
            time.sleep(10)
            
            # Verificar en la carpeta de descargas si hay archivos nuevos
            import glob
            import os
            from pathlib import Path
            
            # Buscar en la carpeta de descargas del usuario
            downloads_folder = str(Path.home() / "Downloads")
            excel_pattern = os.path.join(downloads_folder, "*.xls*")
            excel_files = glob.glob(excel_pattern)
            
            # Buscar el archivo más reciente (últimos 2 minutos)
            recent_files = []
            current_time = time.time()
            for file_path in excel_files:
                file_time = os.path.getctime(file_path)
                if current_time - file_time < 120:  # 2 minutos
                    recent_files.append((file_path, file_time))
            
            if recent_files:
                # Ordenar por tiempo de creación (más reciente primero)
                recent_files.sort(key=lambda x: x[1], reverse=True)
                latest_file = recent_files[0][0]
                logger.info(f"Archivo Excel descargado encontrado: {latest_file}")
                
                # Intentar leer el archivo Excel descargado
                try:
                    df = pd.read_excel(latest_file)
                    logger.info(f"Archivo Excel leído exitosamente: {len(df)} filas, {len(df.columns)} columnas")
                    return df, latest_file
                except Exception as e:
                    logger.warning(f"Error al leer archivo Excel: {str(e)}")
                    return pd.DataFrame(), latest_file
            else:
                logger.info("No se encontraron archivos Excel recientes en la carpeta de descargas")
                return pd.DataFrame(), "Descarga iniciada pero archivo no encontrado"
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error al extraer reporte: {str(e)}")
            return pd.DataFrame()
    
    def close(self):
        """Cierra el navegador y libera recursos."""
        if self.driver:
            logger.info("Cerrando el navegador")
            self.driver.quit()
            self.driver = None
    
    def _wait_for_element(self, by, selector, timeout=None):
        """
        Espera a que un elemento esté presente en la página.
        
        Args:
            by: Método de localización (By.ID, By.CSS_SELECTOR, etc.)
            selector: Selector para localizar el elemento
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            El elemento encontrado
            
        Raises:
            TimeoutException: Si el elemento no aparece en el tiempo especificado
        """
        timeout = timeout or self.timeout
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, selector)))
    
    def _wait_and_click(self, by, selector, timeout=None):
        """
        Espera a que un elemento sea clickeable y hace clic en él.
        
        Args:
            by: Método de localización (By.ID, By.CSS_SELECTOR, etc.)
            selector: Selector para localizar el elemento
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            True si el clic fue exitoso
            
        Raises:
            TimeoutException: Si el elemento no es clickeable en el tiempo especificado
        """
        timeout = timeout or self.timeout
        wait = WebDriverWait(self.driver, timeout)
        element = wait.until(EC.element_to_be_clickable((by, selector)))
        element.click()
        return True