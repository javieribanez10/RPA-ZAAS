#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Administrador del navegador web para la automatización de Nubox.
Responsable únicamente de la configuración y gestión del driver de Selenium.
OPTIMIZADO para máximo rendimiento y velocidad.
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.performance_monitor import measure_performance, measure_step

logger = logging.getLogger("nubox_rpa.browser_manager")

class BrowserManager:
    """
    Administra la configuración y ciclo de vida del navegador web.
    Principio de Responsabilidad Única: Solo maneja el navegador.
    OPTIMIZADO para rendimiento máximo.
    """
    
    def __init__(self, headless=True, timeout=15):
        """
        Inicializa el administrador del navegador con configuración optimizada.
        
        Args:
            headless (bool): Si True, el navegador se ejecuta sin interfaz gráfica
            timeout (int): Tiempo máximo de espera para operaciones (segundos) - reducido de 30 a 15
        """
        self.timeout = timeout
        self.driver = None
        with measure_step("Browser initialization"):
            self._setup_driver(headless)
    
    def _setup_driver(self, headless=True):
        """
        Configura el driver de Selenium con las opciones optimizadas para máximo rendimiento.
        
        Args:
            headless (bool): Si True, el navegador se ejecuta sin interfaz gráfica
        """
        options = webdriver.ChromeOptions()
        
        if headless:
            options.add_argument("--headless=new")  # Usar nuevo modo headless más rápido
            
        # Configuraciones de rendimiento máximo
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--window-size=1920,1080")
        
        # Optimizaciones de velocidad
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Deshabilitar carga de imágenes
        options.add_argument("--disable-javascript")  # Deshabilitar JS innecesario donde sea posible
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-networking")
        
        # Configuraciones de red para velocidad
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        
        # Prevenir detección de automatización
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Configurar preferencias para rendimiento
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,  # Bloquear imágenes
                "plugins": 2,  # Bloquear plugins
                "popups": 2,  # Bloquear popups
                "media_stream": 2,  # Bloquear media stream
            },
            "profile.managed_default_content_settings": {
                "images": 2
            }
        }
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        
        # Configurar timeouts optimizados
        self.driver.implicitly_wait(2)  # Reducido de 10 a 2 segundos
        self.driver.set_page_load_timeout(15)  # Timeout de carga de página
        self.driver.set_script_timeout(10)  # Timeout de scripts
        
        logger.info("🚀 Driver de Chrome inicializado con configuración de alto rendimiento")
    
    def navigate_to(self, url):
        """
        Navega a una URL específica.
        
        Args:
            url (str): URL de destino
        """
        logger.info(f"Navegando a {url}")
        self.driver.get(url)
    
    def take_screenshot(self, filename):
        """
        Toma una captura de pantalla.
        
        Args:
            filename (str): Nombre del archivo de la captura
            
        Returns:
            str: Ruta completa del archivo de captura
        """
        screenshot_path = f"logs/{filename}"
        self.driver.save_screenshot(screenshot_path)
        logger.debug(f"Captura guardada: {screenshot_path}")
        return screenshot_path
    
    def wait_for_element(self, by, selector, timeout=None):
        """
        Espera a que un elemento esté presente en la página.
        
        Args:
            by: Método de localización (By.ID, By.CSS_SELECTOR, etc.)
            selector: Selector para localizar el elemento
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            WebElement: El elemento encontrado
            
        Raises:
            TimeoutException: Si el elemento no aparece en el tiempo especificado
        """
        timeout = timeout or self.timeout
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, selector)))
    
    def wait_for_element_clickable(self, by, selector, timeout=None):
        """
        Espera a que un elemento sea clickeable.
        
        Args:
            by: Método de localización
            selector: Selector del elemento
            timeout: Tiempo máximo de espera
            
        Returns:
            WebElement: El elemento clickeable
        """
        timeout = timeout or self.timeout
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.element_to_be_clickable((by, selector)))
    
    def execute_script(self, script, *args):
        """
        Ejecuta JavaScript en el navegador.
        
        Args:
            script (str): Código JavaScript a ejecutar
            *args: Argumentos para el script
            
        Returns:
            Any: Resultado de la ejecución del script
        """
        return self.driver.execute_script(script, *args)
    
    def switch_to_frame(self, frame):
        """
        Cambia el contexto a un iframe.
        
        Args:
            frame: Elemento iframe o selector
        """
        self.driver.switch_to.frame(frame)
    
    def switch_to_default_content(self):
        """Regresa al contexto principal de la página."""
        self.driver.switch_to.default_content()
    
    def find_element(self, by, selector):
        """
        Busca un elemento en la página.
        
        Args:
            by: Método de localización
            selector: Selector del elemento
            
        Returns:
            WebElement: El elemento encontrado
        """
        return self.driver.find_element(by, selector)
    
    def find_elements(self, by, selector):
        """
        Busca múltiples elementos en la página.
        
        Args:
            by: Método de localización
            selector: Selector de los elementos
            
        Returns:
            List[WebElement]: Lista de elementos encontrados
        """
        return self.driver.find_elements(by, selector)
    
    @property
    def current_url(self):
        """Obtiene la URL actual."""
        return self.driver.current_url
    
    @property
    def page_source(self):
        """Obtiene el código fuente de la página."""
        return self.driver.page_source
    
    def close(self):
        """Cierra el navegador y libera recursos."""
        if self.driver:
            logger.info("Cerrando el navegador")
            self.driver.quit()
            self.driver = None