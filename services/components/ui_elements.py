#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de elementos UI para la plataforma Nubox.
Responsable únicamente de la interacción con elementos de la interfaz de usuario.
OPTIMIZADO para máximo rendimiento y velocidad.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from utils.performance_monitor import measure_performance, measure_step

logger = logging.getLogger("nubox_rpa.ui_elements")

class UIElementService:
    """
    Maneja la interacción con elementos de la interfaz de usuario.
    Principio de Responsabilidad Única: Solo maneja elementos UI.
    """
    
    def __init__(self, browser_manager):
        """
        Inicializa el servicio de elementos UI.
        
        Args:
            browser_manager (BrowserManager): Instancia del administrador del navegador
        """
        self.browser = browser_manager
    
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
        timeout = timeout or self.browser.timeout
        wait = WebDriverWait(self.browser.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, selector)))
    
    def wait_and_click(self, by, selector, timeout=None):
        """
        Espera a que un elemento sea clickeable y hace clic en él.
        
        Args:
            by: Método de localización
            selector: Selector para localizar el elemento
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            bool: True si el clic fue exitoso
        """
        try:
            timeout = timeout or self.browser.timeout
            wait = WebDriverWait(self.browser.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
        except Exception as e:
            logger.error(f"Error al hacer clic en elemento {selector}: {str(e)}")
            return False
    
    @measure_performance("UIElements.extract_dropdown_options")
    def extract_dropdown_options(self):
        """
        Extrae las opciones de dropdowns disponibles en la página con optimización paralela.
        
        Returns:
            dict: Diccionario con las opciones de cada dropdown
        """
        try:
            logger.info("📋 Extrayendo opciones de dropdowns con procesamiento optimizado")
            
            # Cambiar al contexto correcto si hay iframes
            with measure_step("Switch to dropdown context"):
                self._switch_to_dropdown_context()
            
            # Esperar a que los dropdowns estén presentes
            with measure_step("Wait for dropdowns to load"):
                WebDriverWait(self.browser.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "select"))
                )
            
            # Encontrar todos los dropdowns
            with measure_step("Find and process dropdown elements"):
                dropdown_options = {}
                dropdown_counter = 0
                seen_combinations = set()
                
                all_selects = self.browser.find_elements(By.TAG_NAME, "select")
                logger.info(f"🔍 Encontrados {len(all_selects)} elementos select")
                
                # Procesar cada dropdown con optimización
                for idx, select_element in enumerate(all_selects):
                    try:
                        # Verificar que el elemento esté visible y habilitado
                        if not select_element.is_displayed() or not select_element.is_enabled():
                            continue
                        
                        # Usar JavaScript para extraer opciones más rápido
                        options_data = self.browser.execute_script("""
                            var select = arguments[0];
                            var options = [];
                            var selectedIndex = select.selectedIndex;
                            
                            for (var i = 0; i < select.options.length; i++) {
                                var option = select.options[i];
                                if (option.text && option.text.trim()) {
                                    options.push(option.text.trim());
                                }
                            }
                            
                            var selectedText = selectedIndex >= 0 && select.options[selectedIndex] 
                                ? select.options[selectedIndex].text.trim() 
                                : (options.length > 0 ? options[0] : '');
                            
                            return {
                                options: options,
                                selected: selectedText,
                                name: select.name || select.id || ''
                            };
                        """, select_element)
                        
                        option_texts = options_data.get('options', [])
                        if len(option_texts) <= 1:  # Skip selects with no real options
                            continue
                        
                        # Evitar duplicados
                        options_hash = hash(tuple(sorted(option_texts[:5])))
                        if options_hash in seen_combinations:
                            continue
                        seen_combinations.add(options_hash)
                        
                        selected_option = options_data.get('selected', '')
                        select_name = options_data.get('name', f"Dropdown_{dropdown_counter + 1}")
                        
                        # Mapear nombres más amigables basados en el contenido
                        friendly_name = self._get_friendly_dropdown_name(select_name, option_texts, dropdown_counter)
                        
                        dropdown_options[friendly_name] = {
                            'name': select_name,
                            'options': option_texts,
                            'selected': selected_option,
                            'index': dropdown_counter
                        }
                        
                        dropdown_counter += 1
                        logger.debug(f"✅ Dropdown '{friendly_name}': {len(option_texts)} opciones, seleccionado: '{selected_option}'")
                        
                    except Exception as e:
                        logger.debug(f"⚠️ Error procesando select {idx}: {str(e)}")
                        continue
            
            logger.info(f"✅ Extraídas opciones de {len(dropdown_options)} dropdowns")
            return dropdown_options
            
        except Exception as e:
            logger.error(f"❌ Error al extraer opciones de dropdowns: {str(e)}")
            return {}
    
    def find_element_with_multiple_selectors(self, selectors, element_name="elemento"):
        """
        Busca un elemento usando múltiples selectores como fallback.
        
        Args:
            selectors (list): Lista de selectores a probar
            element_name (str): Nombre del elemento para logging
            
        Returns:
            WebElement o None: Elemento encontrado o None
        """
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    elements = self.browser.find_elements(By.XPATH, selector)
                else:
                    elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                
                logger.debug(f"Selector '{selector}' encontró {len(elements)} elementos de {element_name}")
                
                for element in elements:
                    if element.is_displayed():
                        logger.info(f"{element_name} encontrado con selector: {selector}")
                        return element
                        
            except Exception as e:
                logger.debug(f"Error con selector {selector}: {str(e)}")
                continue
        
        logger.warning(f"No se encontró {element_name} con ningún selector")
        return None
    
    def click_element_safely(self, element, element_name="elemento"):
        """
        Hace clic en un elemento de forma segura con optimización de velocidad.
        
        Args:
            element: Elemento web a hacer clic
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
                # Scroll al elemento si es necesario
                self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                # Intentar click normal
                element.click()
                logger.debug(f"✅ Clic exitoso en {element_name} usando click normal")
                return True
            except Exception as click_error:
                logger.error(f"❌ Error haciendo clic en {element_name}: {click_error}")
                return False
    
    def fill_input_field(self, selector, value, field_name="campo"):
        """
        Llena un campo de input de forma segura.
        
        Args:
            selector (str): Selector del campo
            value (str): Valor a ingresar
            field_name (str): Nombre del campo para logging
            
        Returns:
            bool: True si se llenó exitosamente
        """
        try:
            field = self.browser.find_element(By.CSS_SELECTOR, selector)
            
            if not field.is_displayed() or not field.is_enabled():
                logger.warning(f"Campo {field_name} no está visible o habilitado")
                return False
            
            # Usar JavaScript para llenar el campo más rápido
            self.browser.execute_script("arguments[0].value = arguments[1];", field, value)
            
            logger.debug(f"✅ Campo {field_name} llenado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al llenar campo {field_name}: {str(e)}")
            return False
    
    def select_dropdown_option(self, dropdown_selector, option_text, dropdown_name="dropdown"):
        """
        Selecciona una opción en un dropdown con optimización de velocidad.
        
        Args:
            dropdown_selector (str): Selector del dropdown
            option_text (str): Texto de la opción a seleccionar
            dropdown_name (str): Nombre del dropdown para logging
            
        Returns:
            bool: True si la selección fue exitosa
        """
        try:
            select_element = self.browser.find_element(By.CSS_SELECTOR, dropdown_selector)
            
            if not select_element.is_displayed() or not select_element.is_enabled():
                logger.warning(f"Dropdown {dropdown_name} no está visible o habilitado")
                return False
            
            # Usar JavaScript para selección más rápida
            success = self.browser.execute_script("""
                var select = arguments[0];
                var optionText = arguments[1];
                
                for (var i = 0; i < select.options.length; i++) {
                    if (select.options[i].text.trim() === optionText.trim() || 
                        select.options[i].text.includes(optionText.trim())) {
                        select.selectedIndex = i;
                        select.dispatchEvent(new Event('change'));
                        return true;
                    }
                }
                return false;
            """, select_element, option_text)
            
            if success:
                logger.debug(f"✅ Opción '{option_text}' seleccionada en {dropdown_name}")
                return True
            else:
                logger.warning(f"⚠️ No se encontró opción '{option_text}' en {dropdown_name}")
                return False
                for option in options:
                    if option_text.lower() in option.text.lower() or option.text.lower() in option_text.lower():
                        option.click()
                        logger.info(f"Opción '{option.text}' seleccionada en {dropdown_name} (método alternativo)")
                        return True
                
                logger.warning(f"No se encontró opción '{option_text}' en {dropdown_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error al seleccionar opción en {dropdown_name}: {str(e)}")
            return False
    
    def get_element_text(self, selector, element_name="elemento"):
        """
        Obtiene el texto de un elemento.
        
        Args:
            selector (str): Selector del elemento
            element_name (str): Nombre del elemento para logging
            
        Returns:
            str: Texto del elemento o cadena vacía
        """
        try:
            element = self.browser.find_element(By.CSS_SELECTOR, selector)
            text = element.text or element.get_attribute("value") or ""
            logger.debug(f"Texto obtenido de {element_name}: '{text}'")
            return text
        except Exception as e:
            logger.debug(f"Error al obtener texto de {element_name}: {str(e)}")
            return ""
    
    def is_element_present(self, selector, by=By.CSS_SELECTOR):
        """
        Verifica si un elemento está presente en la página.
        
        Args:
            selector (str): Selector del elemento
            by: Método de localización
            
        Returns:
            bool: True si el elemento está presente
        """
        try:
            elements = self.browser.find_elements(by, selector)
            return len(elements) > 0 and any(el.is_displayed() for el in elements)
        except:
            return False
    
    def wait_for_page_load(self, timeout=30):
        """
        Espera a que la página termine de cargar.
        
        Args:
            timeout (int): Tiempo máximo de espera
            
        Returns:
            bool: True si la página cargó completamente
        """
        try:
            WebDriverWait(self.browser.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            logger.debug("Página cargada completamente")
            return True
        except TimeoutException:
            logger.warning("Timeout esperando carga de página")
            return False
    
    def _switch_to_dropdown_context(self):
        """Cambia al contexto correcto donde están los dropdowns."""
        try:
            iframes = self.browser.find_elements(By.TAG_NAME, "iframe")
            
            if iframes:
                for idx, iframe in enumerate(iframes):
                    try:
                        self.browser.switch_to_frame(iframe)
                        
                        # Verificar si hay selects en este iframe
                        selects_in_frame = self.browser.find_elements(By.TAG_NAME, "select")
                        
                        if len(selects_in_frame) > 0:
                            logger.debug(f"Usando iframe {idx} que contiene {len(selects_in_frame)} selects")
                            break
                        else:
                            self.browser.switch_to_default_content()
                    except Exception as e:
                        logger.debug(f"Error al cambiar a iframe {idx}: {str(e)}")
                        continue
        except Exception as e:
            logger.debug(f"Error al cambiar contexto para dropdowns: {str(e)}")
    
    def _get_friendly_dropdown_name(self, select_name, option_texts, index):
        """
        Genera un nombre amigable para un dropdown basado en su contenido.
        
        Args:
            select_name (str): Nombre del atributo name
            option_texts (list): Lista de opciones del dropdown
            index (int): Índice del dropdown
            
        Returns:
            str: Nombre amigable del dropdown
        """
        sample_options = option_texts[:3] if option_texts else []
        
        # Detectar empresas (contienen números y nombres de empresa)
        if any('LTDA' in opt or 'SPA' in opt or 'S.A.' in opt for opt in sample_options):
            return 'Empresa'
        
        # Detectar cuentas contables (contienen códigos como "1101-01")
        if any('-' in opt and any(char.isdigit() for char in opt) for opt in sample_options):
            return 'Cuenta Contable'
        
        # Detectar formato (PDF, EXCEL, etc.)
        if any(opt.upper() in ['PDF', 'EXCEL', 'CSV'] for opt in sample_options):
            return 'Formato de Salida'
        
        # Detectar tipo de reporte
        if any('ANALISIS' in opt or 'BORRADOR' in opt or 'OFICIAL' in opt for opt in sample_options):
            return 'Tipo de Reporte'
        
        # Detectar opciones SI/NO
        if len(option_texts) == 2 and 'SI' in option_texts and 'NO' in option_texts:
            return 'Incluir Subcuentas'
        
        # Por defecto, usar el nombre del atributo o un índice
        return select_name if select_name != f"Dropdown_{index + 1}" else f"Parámetro {index + 1}"