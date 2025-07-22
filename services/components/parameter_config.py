#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de configuración de parámetros para reportes de Nubox.
Responsable únicamente de la configuración de parámetros y dropdowns.
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

logger = logging.getLogger("nubox_rpa.parameter_config")

class ParameterConfigService:
    """
    Maneja la configuración de parámetros de reportes en Nubox.
    Principio de Responsabilidad Única: Solo configura parámetros.
    """
    
    def __init__(self, browser_manager):
        """
        Inicializa el servicio de configuración de parámetros.
        
        Args:
            browser_manager (BrowserManager): Instancia del administrador del navegador
        """
        self.browser = browser_manager
    
    def set_parameters_interactive(self, params=None):
        """
        Configura los parámetros del reporte de forma interactiva.
        
        Args:
            params (dict): Parámetros opcionales para el reporte
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            logger.info("Iniciando configuración interactiva de parámetros")
            
            # Tomar captura inicial
            self.browser.take_screenshot(f"parametros_inicial_{int(time.time())}.png")
            
            # Verificar y cambiar contexto a iframe si es necesario
            self._switch_to_parameters_context()
            
            # Configurar fecha "Desde" interactivamente
            nueva_fecha_desde = self._configure_date_interactive()
            
            # Configurar dropdowns interactivamente
            self._configure_dropdowns_interactive()
            
            # Configurar fecha al final si se especificó
            if nueva_fecha_desde:
                self._set_date_field_robust("Desde", nueva_fecha_desde)
            
            # Confirmación final antes de generar
            if not self._confirm_report_generation():
                return False
            
            # Generar reporte
            return self._generate_report()
            
        except Exception as e:
            logger.error(f"Error al configurar parámetros interactivamente: {str(e)}")
            return False
    
    def set_parameters_programmatic(self, params):
        """
        Configura los parámetros del reporte de forma programática.
        
        Args:
            params (dict): Parámetros para configurar
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            logger.info("Iniciando configuración programática de parámetros")
            
            # Verificar y cambiar contexto a iframe si es necesario
            self._switch_to_parameters_context()
            
            # PASO 1: Configurar dropdowns PRIMERO
            dropdown_selections = params.get('dropdown_selections', {})
            if dropdown_selections:
                logger.info("Configurando dropdowns antes que las fechas para evitar reversión")
                self._configure_dropdowns_programmatic(dropdown_selections)
            
            # PASO 2: Configurar fechas AL FINAL para evitar que se reviertan
            if params.get('fecha_desde'):
                logger.info(f"Configurando fecha 'Desde' al final: {params.get('fecha_desde')}")
                self._set_date_field_robust("Desde", params['fecha_desde'])
            
            if params.get('fecha_hasta'):
                logger.info(f"Configurando fecha 'Hasta' al final: {params.get('fecha_hasta')}")
                self._set_date_field_robust("Hasta", params['fecha_hasta'])
            
            # PASO 3: Generar reporte
            return self._generate_report()
            
        except Exception as e:
            logger.error(f"Error en configuración programática: {str(e)}")
            return False
    
    def _switch_to_parameters_context(self):
        """Cambia al contexto correcto (iframe) donde están los parámetros."""
        try:
            iframes = self.browser.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"iframes encontrados en la página: {len(iframes)}")
            
            if iframes:
                for idx, iframe in enumerate(iframes):
                    try:
                        iframe_name = iframe.get_attribute("name") or f"iframe_{idx}"
                        iframe_src = iframe.get_attribute("src") or "sin_src"
                        logger.info(f"iframe {idx}: name='{iframe_name}', src='{iframe_src}'")
                        
                        self.browser.switch_to_frame(iframe)
                        
                        # Verificar si hay inputs en este iframe
                        inputs_in_frame = self.browser.find_elements(By.TAG_NAME, "input")
                        logger.info(f"Inputs encontrados en iframe {idx}: {len(inputs_in_frame)}")
                        
                        if len(inputs_in_frame) > 0:
                            logger.info(f"Usando iframe {idx} que contiene {len(inputs_in_frame)} inputs")
                            break
                        else:
                            self.browser.switch_to_default_content()
                    except Exception as e:
                        logger.debug(f"Error al cambiar a iframe {idx}: {str(e)}")
                        self.browser.switch_to_default_content()
                        continue
        except Exception as e:
            logger.debug(f"Error al cambiar contexto: {str(e)}")
    
    def _configure_date_interactive(self):
        """
        Configura la fecha 'Desde' de forma interactiva.
        
        Returns:
            str: Nueva fecha si el usuario la cambió, None en caso contrario
        """
        try:
            fecha_desde_field = self.browser.find_element(By.CSS_SELECTOR, "input[name='Desde']")
            fecha_actual = fecha_desde_field.get_attribute("value")
            
            print(f"\n📅 CONFIGURACIÓN DE FECHA DESDE")
            print(f"Fecha actual en el campo: {fecha_actual}")
            
            cambiar_fecha = input("¿Deseas cambiar la fecha 'Desde'? (s/n): ").lower().strip()
            
            if cambiar_fecha in ['s', 'si', 'sí', 'y', 'yes']:
                nueva_fecha_input = input("Ingresa la nueva fecha (formato DD/MM/YYYY): ").strip()
                
                if len(nueva_fecha_input) == 10 and nueva_fecha_input.count('/') == 2:
                    print(f"✅ Nueva fecha programada: {nueva_fecha_input}")
                    print("🔄 Se configurará al final del proceso para evitar que se revierta")
                    logger.info(f"Fecha 'Desde' programada: {nueva_fecha_input}")
                    return nueva_fecha_input
                else:
                    print("❌ Formato de fecha inválido. Manteniendo fecha actual.")
                    logger.warning("Formato de fecha inválido")
            else:
                print(f"✅ Manteniendo fecha actual: {fecha_actual}")
                logger.info("Usuario decidió mantener la fecha actual")
            
        except Exception as e:
            logger.error(f"Error al consultar fecha 'Desde': {str(e)}")
            print("❌ No se pudo encontrar el campo de fecha 'Desde'")
        
        return None
    
    def _configure_dropdowns_interactive(self):
        """Configura dropdowns de forma interactiva."""
        try:
            logger.info("Configurando dropdowns del reporte")
            unique_selects = self._get_unique_dropdowns()
            logger.info(f"Total de dropdowns únicos encontrados: {len(unique_selects)}")
            
            for select_info in unique_selects:
                options = select_info['options']
                selected = select_info['selected']
                select_name = select_info['name']
                dropdown_num = select_info['index']
                
                print(f"\n📋 DROPDOWN {dropdown_num}")
                print(f"Opción actual seleccionada: {selected}")
                print("Opciones disponibles:")
                for i, option in enumerate(options):
                    marker = "👉" if option == selected else "  "
                    print(f"{marker} {i + 1}. {option}")
                
                cambiar = input(f"¿Deseas cambiar la selección del dropdown {dropdown_num}? (s/n): ").lower().strip()
                
                if cambiar in ['s', 'si', 'sí', 'y', 'yes']:
                    try:
                        eleccion = input(f"Ingresa el número de la opción deseada (1-{len(options)}): ").strip()
                        opcion_idx = int(eleccion) - 1
                        
                        if 0 <= opcion_idx < len(options):
                            nueva_opcion = options[opcion_idx]
                            
                            self.browser.take_screenshot(f"antes_cambio_dropdown_{dropdown_num}_{int(time.time())}.png")
                            
                            if self._select_dropdown_option_robust(select_name, nueva_opcion):
                                print(f"✅ Cambiado a: {nueva_opcion}")
                            else:
                                print(f"❌ Error al cambiar a: {nueva_opcion}")
                        else:
                            print("❌ Número de opción inválido. Manteniendo selección actual.")
                    except ValueError:
                        print("❌ Entrada inválida. Manteniendo selección actual.")
                    except Exception as e:
                        print(f"❌ Error al cambiar selección: {str(e)}")
                        logger.error(f"Error al cambiar dropdown {dropdown_num}: {str(e)}")
                else:
                    print(f"✅ Manteniendo selección actual: {selected}")
                    logger.info(f"Usuario decidió mantener selección en dropdown {dropdown_num}")
            
        except Exception as e:
            logger.error(f"Error al configurar dropdowns: {str(e)}")
            print(f"❌ Error al configurar dropdowns: {str(e)}")
    
    def _configure_dropdowns_programmatic(self, dropdown_selections):
        """
        Configura dropdowns de forma programática.
        
        Args:
            dropdown_selections (dict): Diccionario con las selecciones
        """
        logger.info("Configurando selecciones de dropdowns")
        
        for dropdown_name, selected_value in dropdown_selections.items():
            success = self._set_dropdown_value_programmatic(dropdown_name, selected_value)
            if success:
                logger.info(f"Dropdown '{dropdown_name}' configurado: {selected_value}")
            else:
                logger.warning(f"No se pudo configurar dropdown '{dropdown_name}'")
    
    def _get_unique_dropdowns(self):
        """
        Obtiene dropdowns únicos evitando duplicados.
        
        Returns:
            list: Lista de información de dropdowns únicos
        """
        unique_selects = []
        seen_combinations = set()
        
        try:
            all_selects = self.browser.find_elements(By.TAG_NAME, "select")
            logger.info(f"Total de elementos <select> encontrados: {len(all_selects)}")
            
            for idx, select_element in enumerate(all_selects):
                try:
                    if not select_element.is_displayed() or not select_element.is_enabled():
                        continue
                    
                    options = select_element.find_elements(By.TAG_NAME, "option")
                    option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
                    
                    if len(option_texts) <= 1:
                        continue
                    
                    # Crear identificador único basado en las opciones
                    options_hash = hash(tuple(sorted(option_texts[:5])))
                    
                    if options_hash in seen_combinations:
                        continue
                    
                    seen_combinations.add(options_hash)
                    
                    # Obtener el valor seleccionado actualmente
                    select_obj = Select(select_element)
                    selected_option = select_obj.first_selected_option.text.strip()
                    
                    select_info = {
                        'index': len(unique_selects) + 1,
                        'options': option_texts,
                        'selected': selected_option,
                        'name': select_element.get_attribute('name') or f'select_{idx}'
                    }
                    unique_selects.append(select_info)
                    
                except Exception as e:
                    logger.debug(f"Error procesando select {idx}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error general buscando selects: {str(e)}")
        
        return unique_selects
    
    def _select_dropdown_option_robust(self, select_name, option_text):
        """
        Selecciona una opción de dropdown de forma robusta.
        
        Args:
            select_name (str): Nombre del select
            option_text (str): Texto de la opción a seleccionar
            
        Returns:
            bool: True si la selección fue exitosa
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                logger.info(f"Intento {attempt + 1} de seleccionar '{option_text}' en '{select_name}'")
                
                # Re-buscar el elemento select cada vez
                if select_name.startswith('select_'):
                    all_selects = self.browser.find_elements(By.TAG_NAME, "select")
                    visible_selects = [s for s in all_selects if s.is_displayed() and s.is_enabled()]
                    
                    select_index = int(select_name.split('_')[1])
                    if select_index < len(visible_selects):
                        select_element = visible_selects[select_index]
                    else:
                        logger.warning(f"No se encontró select en índice {select_index}")
                        return False
                else:
                    select_element = self.browser.find_element(By.CSS_SELECTOR, f"select[name='{select_name}']")
                
                # Crear nuevo objeto Select
                select_obj = Select(select_element)
                
                # Scroll al elemento
                self.browser.execute_script("arguments[0].scrollIntoView(true);", select_element)
                time.sleep(0.5)
                
                # Intentar selección por texto exacto
                try:
                    select_obj.select_by_visible_text(option_text)
                    time.sleep(1)
                    logger.info(f"✅ Opción '{option_text}' seleccionada exitosamente")
                    return True
                except Exception as e1:
                    # Método alternativo: buscar opción similar
                    options = select_element.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        option_text_clean = option.text.strip()
                        if option_text in option_text_clean or option_text_clean in option_text:
                            option.click()
                            time.sleep(1)
                            logger.info(f"✅ Método alternativo exitoso")
                            return True
                    
                    logger.warning(f"No se encontró opción para '{option_text}'")
                    
            except Exception as e:
                logger.warning(f"Error general en intento {attempt + 1}: {str(e)}")
                
            if attempt < max_attempts - 1:
                time.sleep(1)
        
        logger.error(f"❌ No se pudo seleccionar '{option_text}' después de {max_attempts} intentos")
        return False
    
    def _set_dropdown_value_programmatic(self, dropdown_friendly_name, target_value):
        """
        Configura un dropdown específico de forma programática.
        
        Args:
            dropdown_friendly_name (str): Nombre amigable del dropdown
            target_value (str): Valor a seleccionar
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            all_selects = self.browser.find_elements(By.TAG_NAME, "select")
            dropdown_counter = 0
            seen_combinations = set()
            
            for idx, select_element in enumerate(all_selects):
                try:
                    if not select_element.is_displayed() or not select_element.is_enabled():
                        continue
                    
                    options = select_element.find_elements(By.TAG_NAME, "option")
                    option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
                    
                    if len(option_texts) <= 1:
                        continue
                    
                    # Evitar duplicados
                    options_hash = hash(tuple(sorted(option_texts[:5])))
                    if options_hash in seen_combinations:
                        continue
                    seen_combinations.add(options_hash)
                    
                    # Verificar si este es el dropdown correcto
                    select_name = select_element.get_attribute('name') or f"select_{idx}"
                    friendly_name = self._get_friendly_dropdown_name(select_name, option_texts, dropdown_counter)
                    
                    if friendly_name == dropdown_friendly_name:
                        logger.info(f"Encontrado dropdown correcto: '{friendly_name}'")
                        
                        # Seleccionar el valor
                        self.browser.execute_script("arguments[0].scrollIntoView(true);", select_element)
                        time.sleep(0.5)
                        
                        select_obj = Select(select_element)
                        
                        # Intentar selección por texto exacto
                        try:
                            select_obj.select_by_visible_text(target_value)
                            logger.info(f"✅ Dropdown '{friendly_name}' configurado exitosamente")
                            return True
                        except:
                            # Método alternativo: buscar opción similar
                            for option in options:
                                option_text_clean = option.text.strip()
                                if target_value in option_text_clean or option_text_clean in target_value:
                                    self.browser.execute_script("arguments[0].scrollIntoView(true);", option)
                                    time.sleep(0.3)
                                    option.click()
                                    logger.info(f"✅ Dropdown '{friendly_name}' configurado con método alternativo")
                                    return True
                    
                    dropdown_counter += 1
                    
                except Exception as e:
                    logger.debug(f"Error procesando select {idx}: {str(e)}")
                    continue
            
            logger.warning(f"❌ No se encontró dropdown con nombre '{dropdown_friendly_name}'")
            return False
            
        except Exception as e:
            logger.error(f"Error configurando dropdown '{dropdown_friendly_name}': {str(e)}")
            return False
    
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
        
        # Detectar empresas
        if any('LTDA' in opt or 'SPA' in opt or 'S.A.' in opt for opt in sample_options):
            return 'Empresa'
        
        # Detectar cuentas contables
        if any('-' in opt and any(char.isdigit() for char in opt) for opt in sample_options):
            return 'Cuenta Contable'
        
        # Detectar formato
        if any(opt.upper() in ['PDF', 'EXCEL', 'CSV'] for opt in sample_options):
            return 'Formato de Salida'
        
        # Detectar tipo de reporte
        if any('ANALISIS' in opt or 'BORRADOR' in opt or 'OFICIAL' in opt for opt in sample_options):
            return 'Tipo de Reporte'
        
        # Detectar opciones SI/NO
        if len(option_texts) == 2 and 'SI' in option_texts and 'NO' in option_texts:
            return 'Incluir Subcuentas'
        
        return select_name if select_name != f"select_{index}" else f"Parámetro {index + 1}"
    
    def _set_date_field_robust(self, field_name, date_value):
        """
        Configura un campo de fecha de forma robusta.
        
        Args:
            field_name (str): Nombre del campo ('Desde' o 'Hasta')
            date_value (str): Valor de la fecha
        """
        try:
            field = self.browser.find_element(By.CSS_SELECTOR, f"input[name='{field_name}']")
            
            logger.info(f"Configurando fecha '{field_name}': {date_value}")
            
            # Método robusto para configurar la fecha
            self.browser.execute_script("""
                var field = arguments[0];
                var value = arguments[1];
                
                // Múltiples métodos para asegurar que la fecha se configure
                field.value = value;
                field.setAttribute('value', value);
                field.focus();
                
                // Disparar eventos
                var event = new Event('input', { bubbles: true });
                field.dispatchEvent(event);
                
                var changeEvent = new Event('change', { bubbles: true });
                field.dispatchEvent(changeEvent);
                
                // Bloquear cambios externos
                Object.defineProperty(field, 'value', {
                    get: function() { return value; },
                    set: function(val) { /* ignored */ },
                    configurable: false
                });
            """, field, date_value)
            
            time.sleep(1)
            logger.info(f"Fecha '{field_name}' configurada: {date_value}")
            
        except Exception as e:
            logger.warning(f"Error configurando fecha '{field_name}': {str(e)}")
    
    def _confirm_report_generation(self):
        """
        Solicita confirmación al usuario antes de generar el reporte.
        
        Returns:
            bool: True si el usuario confirma
        """
        print(f"\n🎯 CONFIRMACIÓN FINAL")
        print("¿Estás listo para generar el reporte con la configuración actual?")
        confirmacion = input("Presiona ENTER para continuar o 'n' para cancelar: ").lower().strip()
        
        if confirmacion in ['n', 'no', 'cancel', 'cancelar']:
            print("❌ Operación cancelada por el usuario")
            logger.info("Usuario canceló la generación del reporte")
            return False
        
        return True
    
    def _generate_report(self):
        """
        Hace clic en el botón para generar el reporte.
        
        Returns:
            bool: True si se generó exitosamente
        """
        try:
            logger.info("Buscando botón para generar el reporte")
            print("🔄 Generando reporte...")
            
            # Tomar captura final de parámetros
            self.browser.take_screenshot(f"parametros_configurados_{int(time.time())}.png")
            
            generar_button_selectors = [
                "//a[@id='BotonAceptar' and @class='BotonActivo' and contains(@onclick, 'p_ValidarFormulario')]",
                "//a[@id='BotonAceptar']",
                "#BotonAceptar",
                "a.BotonActivo",
                "//input[@value='Aceptar']",
                "//button[contains(text(), 'Aceptar')]",
                "//a[contains(text(), 'Aceptar')]"
            ]
            
            generar_button = None
            for selector in generar_button_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.browser.find_elements(By.XPATH, selector)
                    elif selector.startswith("#"):
                        elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    else:
                        elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            generar_button = element
                            break
                    
                    if generar_button:
                        break
                except Exception as e:
                    logger.debug(f"Error con selector de botón {selector}: {str(e)}")
                    continue
            
            if generar_button:
                logger.info("Haciendo clic en el botón Aceptar para generar el reporte")
                
                # Scroll al botón y hacer clic
                self.browser.execute_script("arguments[0].scrollIntoView(true);", generar_button)
                time.sleep(0.5)
                
                try:
                    generar_button.click()
                    logger.info("Clic directo en botón Aceptar exitoso")
                    print("✅ Reporte en proceso de generación...")
                except:
                    self.browser.execute_script("arguments[0].click();", generar_button)
                    logger.info("Clic con JavaScript en botón Aceptar exitoso")
                    print("✅ Reporte en proceso de generación...")
                
                # Esperar a que se procese la solicitud
                logger.info("Esperando a que se genere el reporte...")
                time.sleep(5)
                
                # Tomar captura después del clic
                self.browser.take_screenshot(f"despues_click_aceptar_{int(time.time())}.png")
                
                return True
            else:
                logger.warning("No se encontró botón Aceptar para generar el reporte")
                print("❌ No se encontró botón para generar el reporte")
                return False
                
        except Exception as e:
            logger.error(f"Error al buscar/hacer clic en botón Aceptar: {str(e)}")
            print(f"❌ Error al generar reporte: {str(e)}")
            return False