#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servicio de extracción de reportes de Nubox.
Responsable únicamente de extraer y procesar los reportes descargados.
"""

import time
import logging
import pandas as pd
import glob
import os
from pathlib import Path
from selenium.webdriver.common.by import By

logger = logging.getLogger("nubox_rpa.report_extractor")

class ReportExtractorService:
    """
    Maneja la extracción y procesamiento de reportes de Nubox.
    Principio de Responsabilidad Única: Solo extrae reportes.
    """
    
    def __init__(self, browser_manager):
        """
        Inicializa el servicio de extracción de reportes.
        
        Args:
            browser_manager (BrowserManager): Instancia del administrador del navegador
        """
        self.browser = browser_manager
    
    def extract_report(self, is_multiple_accounts=False):
        """
        Extrae el archivo Excel descargado desde Nubox.
        
        Args:
            is_multiple_accounts (bool): True si es parte de un proceso de múltiples cuentas
        
        Returns:
            tuple: (DataFrame, file_path)
        """
        try:
            logger.info("Iniciando extracción de reporte")
            
            # Buscar indicadores de descarga
            if self._check_download_indicators():
                logger.info("Detectados indicadores de descarga")
            
            # Tomar captura durante extracción
            self.browser.take_screenshot(f"extract_report_{int(time.time())}.png")
            
            # Verificar mensajes de error
            self._check_error_messages()
            
            # Esperar a que se complete la descarga
            logger.info("Esperando a que se complete la descarga...")
            time.sleep(10)
            
            # Buscar archivo Excel descargado
            return self._find_and_process_downloaded_file(is_multiple_accounts)
            
        except Exception as e:
            logger.error(f"Error al extraer reporte: {str(e)}")
            return pd.DataFrame(), None
    
    def extract_multiple_reports(self, params, selected_accounts, parameter_service, navigation_service):
        """
        Extrae múltiples reportes, uno por cada cuenta contable.
        
        Args:
            params (dict): Parámetros base para el reporte
            selected_accounts (list): Lista de cuentas contables
            parameter_service: Servicio de configuración de parámetros
            navigation_service: Servicio de navegación
            
        Returns:
            dict: Diccionario con los resultados de cada cuenta
        """
        try:
            logger.info(f"Iniciando extracción múltiple para {len(selected_accounts)} cuentas")
            
            results = {}
            successful_extractions = 0
            failed_extractions = 0
            
            for i, account in enumerate(selected_accounts):
                logger.info(f"Procesando cuenta {i+1}/{len(selected_accounts)}: {account}")
                
                try:
                    # Preparar parámetros específicos para esta cuenta
                    account_params = params.copy()
                    account_params.setdefault('dropdown_selections', {})
                    account_params['dropdown_selections']['Cuenta Contable'] = account
                    
                    # Limpiar código de cuenta para nombre de archivo
                    account_code = account.split(' ')[0] if ' ' in account else account
                    account_code = account_code.replace('-', '_').replace('/', '_')
                    
                    logger.info(f"Configurando parámetros para cuenta: {account}")
                    
                    # Configurar parámetros para esta cuenta específica
                    config_success = parameter_service.set_parameters_programmatic(account_params)
                    
                    if not config_success:
                        logger.warning(f"Error configurando parámetros para cuenta {account}")
                        results[account] = self._create_failed_result(
                            'Error en configuración de parámetros', account_code
                        )
                        failed_extractions += 1
                        continue
                    
                    # Esperar entre configuración y extracción
                    time.sleep(2)
                    
                    logger.info(f"Extrayendo datos para cuenta: {account}")
                    
                    # Extraer reporte con flag de múltiples cuentas
                    report_data = self.extract_report(is_multiple_accounts=True)
                    
                    if isinstance(report_data, tuple):
                        df, file_path = report_data
                    else:
                        df = report_data
                        file_path = None
                    
                    # Verificar si se extrajeron datos o hubo descarga exitosa
                    if not df.empty or (file_path and file_path != "Descarga no encontrada"):
                        logger.info(f"✅ Descarga exitosa para cuenta {account}")
                        
                        results[account] = {
                            'success': True,
                            'error': None,
                            'data': df,
                            'file_path': file_path,
                            'account_code': account_code,
                            'rows_count': len(df) if not df.empty else 0,
                            'columns_count': len(df.columns) if not df.empty else 0
                        }
                        successful_extractions += 1
                        
                        # Si no es la última cuenta, navegar al formulario Mayor
                        if i < len(selected_accounts) - 1:
                            logger.info(f"Navegando al formulario Mayor para siguiente cuenta ({i+2}/{len(selected_accounts)})")
                            
                            mayor_click_success = navigation_service.click_mayor_link()
                            
                            if not mayor_click_success:
                                logger.warning("Error al hacer clic en enlace Mayor, intentando navegación alternativa")
                                nav_success = navigation_service.navigate_to_report()
                                
                                if not nav_success:
                                    logger.error("Error crítico: No se pudo navegar al formulario para la siguiente cuenta")
                                    # Marcar cuentas restantes como fallidas
                                    for remaining_account in selected_accounts[i+1:]:
                                        results[remaining_account] = self._create_failed_result(
                                            'Error de navegación - proceso interrumpido', 
                                            remaining_account.split(' ')[0] if ' ' in remaining_account else remaining_account
                                        )
                                        failed_extractions += 1
                                    break
                        
                    else:
                        logger.warning(f"❌ No se extrajeron datos para cuenta {account}")
                        results[account] = {
                            'success': False,
                            'error': 'No se extrajeron datos ni se detectó descarga',
                            'data': pd.DataFrame(),
                            'file_path': file_path,
                            'account_code': account_code
                        }
                        failed_extractions += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando cuenta {account}: {str(e)}")
                    results[account] = self._create_failed_result(str(e), account_code)
                    failed_extractions += 1
                    
                    # Intentar recuperar navegación después del error
                    if i < len(selected_accounts) - 1:
                        logger.info("Intentando recuperar navegación después del error...")
                        try:
                            navigation_service.navigate_to_report()
                            time.sleep(2)
                        except:
                            logger.error("No se pudo recuperar la navegación, terminando proceso")
                            # Marcar cuentas restantes como fallidas
                            for remaining_account in selected_accounts[i+1:]:
                                results[remaining_account] = self._create_failed_result(
                                    'Proceso interrumpido por error de navegación',
                                    remaining_account.split(' ')[0] if ' ' in remaining_account else remaining_account
                                )
                                failed_extractions += 1
                            break
            
            # Resumen final
            logger.info(f"🎯 Extracción completada: {successful_extractions} exitosas, {failed_extractions} fallidas")
            
            # Agregar resumen a los resultados
            results['_summary'] = {
                'total_accounts': len(selected_accounts),
                'successful_extractions': successful_extractions,
                'failed_extractions': failed_extractions,
                'success_rate': (successful_extractions / len(selected_accounts)) * 100 if selected_accounts else 0
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error general en extracción múltiple: {str(e)}")
            return {
                '_summary': {
                    'total_accounts': len(selected_accounts),
                    'successful_extractions': 0,
                    'failed_extractions': len(selected_accounts),
                    'success_rate': 0,
                    'error': str(e)
                }
            }
    
    def extract_multiple_reports_by_company_and_account(self, params, selected_companies, selected_accounts, parameter_service, navigation_service):
        """
        Extrae múltiples reportes para cada combinación de empresa y cuenta contable.
        
        Args:
            params (dict): Parámetros base para el reporte
            selected_companies (list): Lista de empresas
            selected_accounts (list): Lista de cuentas contables
            parameter_service: Servicio de configuración de parámetros
            navigation_service: Servicio de navegación
            
        Returns:
            dict: Diccionario con los resultados de cada combinación empresa-cuenta
        """
        try:
            total_combinations = len(selected_companies) * len(selected_accounts)
            logger.info(f"Iniciando extracción múltiple para {total_combinations} combinaciones ({len(selected_companies)} empresas × {len(selected_accounts)} cuentas)")
            
            results = {}
            successful_extractions = 0
            failed_extractions = 0
            
            # Procesar cada combinación empresa-cuenta
            combination_count = 0
            for company_idx, company in enumerate(selected_companies):
                logger.info(f"🏢 Procesando empresa {company_idx + 1}/{len(selected_companies)}: {company}")
                
                for account_idx, account in enumerate(selected_accounts):
                    combination_count += 1
                    combination_key = f"{company} - {account}"
                    
                    logger.info(f"💰 Procesando combinación {combination_count}/{total_combinations}: {combination_key}")
                    
                    try:
                        # Preparar parámetros específicos para esta combinación
                        combination_params = params.copy()
                        combination_params.setdefault('dropdown_selections', {})
                        combination_params['dropdown_selections']['Empresa'] = company
                        combination_params['dropdown_selections']['Cuenta Contable'] = account
                        
                        # Limpiar códigos para nombres de archivo
                        company_code = company.split(',')[0].strip() if ',' in company else company.split(' ')[0]
                        account_code = account.split(' ')[0] if ' ' in account else account
                        safe_combination_code = f"{company_code}_{account_code}".replace('-', '_').replace('/', '_')
                        
                        logger.info(f"Configurando parámetros para: {combination_key}")
                        
                        # Configurar parámetros para esta combinación específica
                        config_success = parameter_service.set_parameters_programmatic(combination_params)
                        
                        if not config_success:
                            logger.warning(f"Error configurando parámetros para {combination_key}")
                            results[combination_key] = self._create_failed_combination_result(
                                'Error en configuración de parámetros', 
                                company, account, safe_combination_code
                            )
                            failed_extractions += 1
                            continue
                        
                        # Esperar entre configuración y extracción
                        time.sleep(3)  # Un poco más de tiempo para cambios de empresa
                        
                        logger.info(f"Extrayendo datos para: {combination_key}")
                        
                        # Extraer reporte con flag de múltiples combinaciones
                        report_data = self.extract_report(is_multiple_accounts=True)
                        
                        if isinstance(report_data, tuple):
                            df, file_path = report_data
                        else:
                            df = report_data
                            file_path = None
                        
                        # Verificar si se extrajeron datos o hubo descarga exitosa
                        if not df.empty or (file_path and file_path != "Descarga no encontrada"):
                            logger.info(f"✅ Descarga exitosa para: {combination_key}")
                            
                            results[combination_key] = {
                                'success': True,
                                'error': None,
                                'data': df,
                                'file_path': file_path,
                                'company': company,
                                'account': account,
                                'account_code': safe_combination_code,
                                'rows_count': len(df) if not df.empty else 0,
                                'columns_count': len(df.columns) if not df.empty else 0
                            }
                            successful_extractions += 1
                            
                        else:
                            logger.warning(f"❌ No se extrajeron datos para: {combination_key}")
                            results[combination_key] = self._create_failed_combination_result(
                                'No se extrajeron datos ni se detectó descarga',
                                company, account, safe_combination_code
                            )
                            failed_extractions += 1
                        
                        # Navegación para siguiente combinación (si no es la última)
                        if combination_count < total_combinations:
                            logger.info(f"Navegando al formulario Mayor para siguiente combinación ({combination_count + 1}/{total_combinations})")
                            
                            # CORRIGIDO: Usar la misma navegación simple para todos los casos
                            # No importa si es cambio de empresa o cuenta, ambos usan click_mayor_link
                            mayor_click_success = navigation_service.click_mayor_link()
                            
                            if not mayor_click_success:
                                logger.warning("Error al hacer clic en enlace Mayor, intentando navegación alternativa")
                                nav_success = navigation_service.navigate_to_report()
                                
                                if not nav_success:
                                    logger.error("Error crítico: No se pudo navegar al formulario para la siguiente combinación")
                                    # Marcar combinaciones restantes como fallidas
                                    remaining_combinations = total_combinations - combination_count
                                    failed_extractions += remaining_combinations
                                    
                                    # Calcular qué combinaciones quedan
                                    current_company_idx = company_idx
                                    current_account_idx = account_idx + 1
                                    
                                    # Si terminamos las cuentas de esta empresa, pasar a la siguiente
                                    if current_account_idx >= len(selected_accounts):
                                        current_company_idx += 1
                                        current_account_idx = 0
                                    
                                    self._mark_remaining_combinations_as_failed(
                                        results, selected_companies, selected_accounts, 
                                        current_company_idx, current_account_idx, 
                                        'Error de navegación - proceso interrumpido'
                                    )
                                    break
            
                    except Exception as e:
                        logger.error(f"Error procesando combinación {combination_key}: {str(e)}")
                        results[combination_key] = self._create_failed_combination_result(
                            str(e), company, account, safe_combination_code
                        )
                        failed_extractions += 1
                        
                        # Intentar recuperar navegación después del error
                        if combination_count < total_combinations:
                            logger.info("Intentando recuperar navegación después del error...")
                            try:
                                navigation_service.navigate_to_report()
                                time.sleep(3)
                            except:
                                logger.error("No se pudo recuperar la navegación, terminando proceso")
                                self._mark_remaining_combinations_as_failed(
                                    results, selected_companies, selected_accounts,
                                    company_idx, account_idx + 1, 'Proceso interrumpido por error de navegación'
                                )
                                failed_extractions += (total_combinations - combination_count)
                                break
                
                # Si hubo error crítico en la empresa actual, salir del bucle principal
                if combination_count + failed_extractions >= total_combinations:
                    break
            
            # Resumen final
            logger.info(f"🎯 Extracción múltiple completada: {successful_extractions} exitosas, {failed_extractions} fallidas de {total_combinations} combinaciones")
            
            # Agregar resumen a los resultados
            results['_summary'] = {
                'total_combinations': total_combinations,
                'total_companies': len(selected_companies),
                'total_accounts': len(selected_accounts),
                'successful_extractions': successful_extractions,
                'failed_extractions': failed_extractions,
                'success_rate': (successful_extractions / total_combinations) * 100 if total_combinations > 0 else 0
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error general en extracción múltiple por empresa y cuenta: {str(e)}")
            total_combinations = len(selected_companies) * len(selected_accounts)
            return {
                '_summary': {
                    'total_combinations': total_combinations,
                    'total_companies': len(selected_companies),
                    'total_accounts': len(selected_accounts),
                    'successful_extractions': 0,
                    'failed_extractions': total_combinations,
                    'success_rate': 0,
                    'error': str(e)
                }
            }
    
    def _check_download_indicators(self):
        """
        Verifica indicadores de que se está procesando una descarga.
        
        Returns:
            bool: True si se detectaron indicadores
        """
        try:
            download_indicators = [
                "//a[contains(@href, '.xls') or contains(@href, 'download')]",
                "//div[contains(text(), 'generando') or contains(text(), 'procesando')]",
                "//iframe[contains(@src, 'excel') or contains(@src, 'download')]"
            ]
            
            download_found = False
            for selector in download_indicators:
                try:
                    elements = self.browser.find_elements(By.XPATH, selector)
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
                                        return True
                                    except Exception as e:
                                        logger.debug(f"Error al hacer clic en descarga: {str(e)}")
                except Exception as e:
                    logger.debug(f"Error buscando indicador {selector}: {str(e)}")
            
            return download_found
            
        except Exception as e:
            logger.debug(f"Error verificando indicadores de descarga: {str(e)}")
            return False
    
    def _check_error_messages(self):
        """Verifica si hay mensajes de error en la página."""
        try:
            error_messages = self.browser.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
            for msg in error_messages:
                if msg.is_displayed():
                    logger.warning(f"Mensaje en pantalla: {msg.text}")
        except:
            pass
    
    def _find_and_process_downloaded_file(self, is_multiple_accounts):
        """
        Busca y procesa el archivo Excel descargado con validación mejorada.
        
        Args:
            is_multiple_accounts (bool): True si es parte de proceso múltiple
            
        Returns:
            tuple: (DataFrame, file_path)
        """
        try:
            # Buscar en la carpeta de descargas
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
                logger.info(f"Archivo descargado encontrado: {latest_file}")
                
                # Validar que el archivo descargado sea realmente un Excel
                if not self._validate_excel_file(latest_file):
                    logger.error(f"El archivo descargado no es un Excel válido: {latest_file}")
                    return pd.DataFrame(), f"Archivo inválido: {latest_file}"
                
                # Procesar según el tipo de proceso
                if not is_multiple_accounts:
                    logger.info("🎯 Descarga exitosa completada. Sistema detenido como se solicitó.")
                    return self._read_excel_file(latest_file)
                else:
                    logger.info("✅ Descarga exitosa. Preparando para siguiente cuenta...")
                    return self._read_excel_file(latest_file)
            else:
                logger.warning("No se encontraron archivos Excel recientes en la carpeta de descargas")
                return pd.DataFrame(), "Descarga no encontrada"
            
        except Exception as e:
            logger.error(f"Error al procesar archivo descargado: {str(e)}")
            return pd.DataFrame(), None
    
    def _validate_excel_file(self, file_path):
        """
        Valida que el archivo descargado sea realmente un Excel válido.
        
        Args:
            file_path (str): Ruta del archivo a validar
            
        Returns:
            bool: True si es un archivo Excel válido O HTML-Excel de Nubox
        """
        try:
            # Verificar el tamaño del archivo (muy pequeño = probable HTML)
            file_size = os.path.getsize(file_path)
            logger.info(f"Validando archivo: {file_path} (tamaño: {file_size} bytes)")
            
            if file_size < 1024:  # Menos de 1KB es sospechoso para un Excel
                logger.warning(f"Archivo muy pequeño ({file_size} bytes), probablemente no es Excel")
            
            # Leer los primeros bytes para verificar el formato
            with open(file_path, 'rb') as f:
                # Leer más bytes para mejor detección
                header_bytes = f.read(512)
                header_text = header_bytes.decode('utf-8', errors='ignore')
                
                # Log del contenido para diagnóstico
                logger.info(f"Primeros 100 caracteres del archivo: {header_text[:100]}")
                
                # NUEVO: Verificar si es HTML-Excel de Nubox (formato válido)
                nubox_html_excel_indicators = [
                    'xmlns:x="urn:schemas-microsoft-com:office:excel"',
                    '<x:ExcelWorkbook>',
                    '<x:ExcelWorksheets>',
                    'LIBRO MAYOR DESDE'
                ]
                
                is_nubox_html_excel = any(indicator in header_text for indicator in nubox_html_excel_indicators)
                
                if is_nubox_html_excel:
                    logger.info("✅ DETECTADO: Archivo HTML-Excel válido de Nubox")
                    return True  # Es válido para nuestro parser
                
                # Verificar signatures de archivos Excel válidos
                # Excel 97-2003 (.xls) comienza con firma específica
                excel_signatures = [
                    b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # OLE2 signature (Excel 97-2003)
                    b'PK\x03\x04',  # ZIP signature (Excel 2007+)
                    b'\x09\x08\x06\x00\x00\x00\x10\x00'  # Otra variante de Excel
                ]
                
                # Verificar si tiene una firma válida de Excel
                has_valid_signature = any(header_bytes.startswith(sig) for sig in excel_signatures)
                
                if has_valid_signature:
                    logger.info("✅ Archivo tiene firma válida de Excel")
                    return True
                
                # Si contiene HTML genérico (no de Nubox), es inválido
                html_indicators = ['<html', '<!doctype', '<head>', '<body>', '<title>']
                if any(indicator in header_text.lower() for indicator in html_indicators) and not is_nubox_html_excel:
                    logger.error("🚨 DETECTADO: El archivo contiene HTML genérico en lugar de datos Excel")
                    logger.error(f"Contenido HTML detectado en el archivo: {header_text[:300]}...")
                    
                    # Guardar el contenido completo para análisis
                    try:
                        f.seek(0)
                        full_content = f.read().decode('utf-8', errors='ignore')
                        
                        # Buscar indicadores específicos de errores de Nubox
                        nubox_error_indicators = [
                            'error', 'session', 'timeout', 'expired', 'invalid',
                            'no se pudo', 'problema', 'access denied', 'forbidden'
                        ]
                        
                        found_errors = [indicator for indicator in nubox_error_indicators 
                                      if indicator in full_content.lower()]
                        
                        if found_errors:
                            logger.error(f"Indicadores de error de Nubox encontrados: {found_errors}")
                        
                        # Guardar contenido en archivo para análisis posterior
                        error_file_path = file_path + "_error_content.html"
                        with open(error_file_path, 'w', encoding='utf-8') as error_file:
                            error_file.write(full_content)
                        logger.info(f"Contenido del archivo error guardado en: {error_file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error al analizar contenido completo: {str(e)}")
                    
                    return False
                
                # Verificar otros indicadores de error
                error_indicators = [
                    'error', 'no se pudo', 'problema', 'timeout', 'session',
                    'expired', 'invalid', 'access denied', 'forbidden', 'unauthorized'
                ]
                
                found_errors = [indicator for indicator in error_indicators 
                              if indicator in header_text.lower()]
                
                if found_errors:
                    logger.error(f"Indicadores de error encontrados en el archivo: {found_errors}")
                    logger.error(f"Contenido que contiene errores: {header_text}")
                    return False
                
                # Si no tiene firma válida y no es HTML, podría ser otro tipo de archivo
                if not has_valid_signature:
                    logger.warning(f"Archivo sin firma Excel válida. Primeros bytes: {header_bytes[:20]}")
                    
                    # Intentar detectar si es un archivo de texto plano que se puede leer como CSV
                    try:
                        # Si contiene separadores típicos de CSV, podría ser válido
                        if any(sep in header_text for sep in [',', ';', '\t']):
                            logger.info("El archivo podría ser un CSV con extensión .xls")
                            return True
                    except:
                        pass
                    
                    return False
            
            logger.info("✅ Archivo pasa la validación básica")
            return True
            
        except Exception as e:
            logger.error(f"Error validando archivo Excel: {str(e)}")
            return False
    
    def _read_excel_file(self, file_path):
        """
        Lee un archivo Excel con manejo mejorado de errores y soporte para HTML-Excel de Nubox.
        
        Args:
            file_path (str): Ruta del archivo Excel
            
        Returns:
            tuple: (DataFrame, file_path)
        """
        try:
            # Verificar primero si es HTML con formato Excel de Microsoft Office
            if self._is_html_excel_format(file_path):
                logger.info("📋 Detectado formato HTML-Excel de Microsoft Office (Nubox)")
                return self._parse_html_excel(file_path)
            
            # Intentar leer con diferentes engines y configuraciones
            engines = ['openpyxl', 'xlrd']
            
            for engine in engines:
                try:
                    logger.info(f"Intentando leer Excel con engine '{engine}'...")
                    
                    # Configuraciones especiales según el engine
                    if engine == 'xlrd':
                        # Para archivos .xls antiguos
                        df = pd.read_excel(file_path, engine=engine)
                    else:
                        # Para archivos .xlsx más modernos
                        df = pd.read_excel(file_path, engine=engine)
                    
                    if not df.empty:
                        logger.info(f"✅ Archivo Excel leído exitosamente con {engine}: {len(df)} filas, {len(df.columns)} columnas")
                        logger.info(f"Columnas encontradas: {list(df.columns)}")
                        return df, file_path
                    else:
                        logger.warning(f"DataFrame vacío con engine {engine}")
                        
                except Exception as e:
                    logger.warning(f"Error con engine {engine}: {str(e)}")
                    continue
            
            # Si todos los engines fallan, intentar otras estrategias
            logger.info("Intentando estrategias alternativas de lectura...")
            
            # Estrategia 1: Intentar leer solo las primeras hojas
            try:
                with pd.ExcelFile(file_path) as xls:
                    sheet_names = xls.sheet_names
                    logger.info(f"Hojas encontradas en el Excel: {sheet_names}")
                    
                    for sheet in sheet_names:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet)
                            if not df.empty:
                                logger.info(f"✅ Datos encontrados en hoja '{sheet}': {len(df)} filas, {len(df.columns)} columnas")
                                return df, file_path
                        except Exception as e:
                            logger.warning(f"Error leyendo hoja '{sheet}': {str(e)}")
                            continue
            except Exception as e:
                logger.warning(f"Error accediendo a hojas del Excel: {str(e)}")
            
            # Estrategia 2: Intentar como CSV si tiene extensión .xls pero es realmente CSV
            try:
                logger.info("Intentando leer como CSV...")
                df = pd.read_csv(file_path, encoding='utf-8')
                if not df.empty:
                    logger.info(f"✅ Archivo leído como CSV: {len(df)} filas, {len(df.columns)} columnas")
                    return df, file_path
            except:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                    if not df.empty:
                        logger.info(f"✅ Archivo leído como CSV (latin-1): {len(df)} filas, {len(df.columns)} columnas")
                        return df, file_path
                except Exception as e:
                    logger.warning(f"Error leyendo como CSV: {str(e)}")
            
            # Si nada funciona, retornar información del error
            logger.error("❌ No se pudo leer el archivo con ningún método")
            return pd.DataFrame(), f"Error de lectura: {file_path}"
            
        except Exception as e:
            logger.error(f"Error general leyendo archivo Excel: {str(e)}")
            return pd.DataFrame(), None
    
    def _is_html_excel_format(self, file_path):
        """
        Verifica si el archivo es HTML con formato Excel de Microsoft Office.
        
        Args:
            file_path (str): Ruta del archivo
            
        Returns:
            bool: True si es HTML-Excel
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)  # Leer primeros 500 caracteres
                
            # Buscar indicadores específicos de HTML-Excel de Microsoft Office
            html_excel_indicators = [
                'xmlns:x="urn:schemas-microsoft-com:office:excel"',
                '<x:ExcelWorkbook>',
                '<x:ExcelWorksheets>',
                '<table border="1">'
            ]
            
            return any(indicator in content for indicator in html_excel_indicators)
            
        except Exception as e:
            logger.error(f"Error verificando formato HTML-Excel: {str(e)}")
            return False
    
    def _parse_html_excel(self, file_path):
        """
        Extrae datos de un archivo HTML con formato Excel de Microsoft Office.
        
        Args:
            file_path (str): Ruta del archivo HTML-Excel
            
        Returns:
            tuple: (DataFrame, file_path)
        """
        try:
            import re
            from bs4 import BeautifulSoup
            
            logger.info("📋 Iniciando extracción de datos HTML-Excel...")
            
            # Leer el contenido HTML
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Parsear con BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Buscar la tabla principal
            table = soup.find('table', {'border': '1'})
            if not table:
                logger.error("No se encontró tabla con datos en el HTML")
                return pd.DataFrame(), file_path
            
            # Extraer información de cabecera
            company_info = {}
            rows = table.find_all('tr')
            
            # Extraer información de la empresa (primeras filas)
            for i, row in enumerate(rows[:10]):  # Revisar las primeras 10 filas
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if key in ['Nombre:', 'Rut:', 'Dirección:', 'Representante Legal:', 'Giro Comercial:']:
                        company_info[key.replace(':', '')] = value
            
            logger.info(f"📋 Información de empresa extraída: {company_info}")
            
            # Buscar el inicio de la tabla de datos contables
            data_rows = []
            header_found = False
            headers = []
            
            for row in rows:
                cells = row.find_all('td')
                
                # Buscar la fila de encabezados de la tabla contable
                if not header_found and len(cells) > 5:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # Verificar si esta fila contiene encabezados contables
                    if any(header in cell_texts for header in ['FECHA', 'COMPROBANTE', 'GLOSA', 'DEBE', 'HABER', 'SALDO']):
                        headers = cell_texts
                        header_found = True
                        logger.info(f"📋 Encabezados encontrados: {headers}")
                        continue
                
                # Si ya encontramos encabezados, extraer datos
                if header_found and len(cells) >= len(headers):
                    cell_texts = []
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        # Limpiar texto y convertir números
                        text = re.sub(r'\s+', ' ', text)  # Normalizar espacios
                        cell_texts.append(text)
                    
                    # Verificar si es una fila de datos válida
                    if cell_texts[0] and not cell_texts[0].startswith('TOTAL'):
                        # Solo agregar si tiene fecha o es fila de auxiliar
                        if self._is_valid_data_row(cell_texts):
                            data_rows.append(cell_texts[:len(headers)])  # Ajustar al número de headers
            
            logger.info(f"📊 Se extrajeron {len(data_rows)} filas de datos")
            
            if not data_rows:
                logger.warning("No se encontraron filas de datos válidas")
                return pd.DataFrame(), file_path
            
            # Crear DataFrame
            # Ajustar headers si es necesario
            if len(headers) > 10:
                headers = headers[:10]  # Limitar a 10 columnas máximo
            
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Limpiar y procesar los datos
            df = self._clean_accounting_data(df)
            
            # Agregar información de la empresa como metadatos
            df.attrs['company_info'] = company_info
            
            logger.info(f"✅ DataFrame HTML-Excel creado exitosamente: {len(df)} filas, {len(df.columns)} columnas")
            logger.info(f"Columnas: {list(df.columns)}")
            
            return df, file_path
            
        except ImportError:
            logger.error("❌ BeautifulSoup no está instalado. Instalar con: pip install beautifulsoup4")
            return pd.DataFrame(), f"Error: BeautifulSoup requerido"
        except Exception as e:
            logger.error(f"Error parseando HTML-Excel: {str(e)}")
            return pd.DataFrame(), f"Error de parsing: {file_path}"
    
    def _is_valid_data_row(self, row_data):
        """
        Verifica si una fila contiene datos contables válidos.
        
        Args:
            row_data (list): Lista con los datos de la fila
            
        Returns:
            bool: True si es una fila válida
        """
        if not row_data or len(row_data) < 3:
            return False
        
        # Verificar si tiene fecha (formato dd/mm/yyyy)
        import re
        date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'
        if re.match(date_pattern, row_data[0]):
            return True
        
        # Verificar si es fila auxiliar (RUT o código)
        if len(row_data) > 2 and row_data[2]:
            # Buscar patrones de RUT chileno
            rut_pattern = r'\d{1,8}-[\dk]'
            if re.match(rut_pattern, row_data[2], re.IGNORECASE):
                return True
        
        # Verificar si contiene "ACUMULACION ANTERIOR" o "TOTAL"
        row_text = ' '.join(row_data).upper()
        if any(keyword in row_text for keyword in ['ACUMULACION ANTERIOR', 'TOTAL']):
            return True
        
        return False
    
    def _clean_accounting_data(self, df):
        """
        Limpia y formatea los datos contables extraídos.
        
        Args:
            df (DataFrame): DataFrame con datos sin procesar
            
        Returns:
            DataFrame: DataFrame limpio y formateado
        """
        try:
            # Hacer una copia para no modificar el original
            cleaned_df = df.copy()
            
            # Limpiar columnas numéricas (DEBE, HABER, SALDO)
            numeric_columns = ['DEBE', 'HABER', 'SALDO']
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    # Remover caracteres no numéricos excepto puntos y comas
                    cleaned_df[col] = cleaned_df[col].astype(str).str.replace(r'[^\d.,\-]', '', regex=True)
                    # Convertir a numérico
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
            
            # Limpiar fechas
            if 'FECHA' in cleaned_df.columns:
                # Intentar convertir fechas
                try:
                    cleaned_df['FECHA'] = pd.to_datetime(cleaned_df['FECHA'], format='%d/%m/%Y', errors='coerce')
                except:
                    pass  # Mantener como string si no se puede convertir
            
            # Remover filas completamente vacías
            cleaned_df = cleaned_df.dropna(how='all')
            
            # Remover columnas completamente vacías
            cleaned_df = cleaned_df.dropna(axis=1, how='all')
            
            logger.info(f"✅ Datos contables limpiados: {len(cleaned_df)} filas resultantes")
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"Error limpiando datos contables: {str(e)}")
            return df  # Retornar original si hay error
    
    def _create_failed_result(self, error_message, account_code=None):
        """
        Crea un resultado fallido estándar.
        
        Args:
            error_message (str): Mensaje de error
            account_code (str): Código de cuenta (opcional)
            
        Returns:
            dict: Resultado fallido
        """
        result = {
            'success': False,
            'error': error_message,
            'data': pd.DataFrame(),
            'file_path': None
        }
        
        if account_code:
            result['account_code'] = account_code
            
        return result
    
    def _create_failed_combination_result(self, error_message, company, account, combination_code):
        """
        Crea un resultado fallido estándar para combinaciones empresa-cuenta.
        
        Args:
            error_message (str): Mensaje de error
            company (str): Nombre de la empresa
            account (str): Nombre de la cuenta
            combination_code (str): Código de la combinación
            
        Returns:
            dict: Resultado fallido
        """
        return {
            'success': False,
            'error': error_message,
            'data': pd.DataFrame(),
            'file_path': None,
            'company': company,
            'account': account,
            'account_code': combination_code,
            'rows_count': 0,
            'columns_count': 0
        }
    
    def _mark_remaining_combinations_as_failed(self, results, selected_companies, selected_accounts, 
                                             start_company_idx, start_account_idx, error_message):
        """
        Marca las combinaciones restantes como fallidas.
        
        Args:
            results (dict): Diccionario de resultados
            selected_companies (list): Lista de empresas
            selected_accounts (list): Lista de cuentas
            start_company_idx (int): Índice de empresa desde donde empezar
            start_account_idx (int): Índice de cuenta desde donde empezar
            error_message (str): Mensaje de error
            
        Returns:
            int: Número de combinaciones marcadas como fallidas
        """
        failed_count = 0
        
        for company_idx in range(start_company_idx, len(selected_companies)):
            account_start = start_account_idx if company_idx == start_company_idx else 0
            for account_idx in range(account_start, len(selected_accounts)):
                company = selected_companies[company_idx]
                account = selected_accounts[account_idx]
                combination_key = f"{company} - {account}"
                
                company_code = company.split(',')[0].strip() if ',' in company else company.split(' ')[0]
                account_code = account.split(' ')[0] if ' ' in account else account
                safe_combination_code = f"{company_code}_{account_code}".replace('-', '_').replace('/', '_')
                
                results[combination_key] = self._create_failed_combination_result(
                    error_message, company, account, safe_combination_code
                )
                failed_count += 1
                
        return failed_count