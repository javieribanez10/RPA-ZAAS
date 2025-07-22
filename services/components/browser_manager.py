#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Administrador del navegador web para la automatización de Nubox.
Responsable únicamente de la configuración y gestión del driver de Selenium.
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger("nubox_rpa.browser_manager")

class BrowserManager:
    """
    Administra la configuración y ciclo de vida del navegador web.
    Principio de Responsabilidad Única: Solo maneja el navegador.
    """
    
    def __init__(self, headless=True, timeout=30):
        """
        Inicializa el administrador del navegador.
        
        Args:
            headless (bool): Si True, el navegador se ejecuta sin interfaz gráfica
            timeout (int): Tiempo máximo de espera para operaciones (segundos)
        """
        self.timeout = timeout
        self.driver = None
        self._setup_driver(headless)
    
    def _setup_driver(self, headless=True):
        """
        Configura el driver de Selenium con las opciones optimizadas.
        
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