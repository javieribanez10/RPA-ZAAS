#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RPA Nubox Report Extractor
--------------------------
Automatización para extraer reportes contables desde Nubox.
"""

import os
import logging
import shutil
from datetime import datetime
from config.settings import setup_config
from utils.logger import setup_logger
from services.nubox_service import NuboxService
from utils.file_handler import save_report, get_latest_report

# Configurar el logger
logger = setup_logger()

def main():
    """Función principal que ejecuta el proceso RPA completo."""
    try:
        # Inicializar configuración
        logger.info("Iniciando extracción de reporte Nubox")
        config = setup_config()
        
        # Validar credenciales
        if not config.get("NUBOX_USERNAME") or not config.get("NUBOX_PASSWORD"):
            logger.error("Credenciales no configuradas. Verifica las variables de entorno.")
            return False
        
        # Iniciar el servicio Nubox
        logger.info("Inicializando servicio Nubox")
        nubox = NuboxService(
            headless=config.get("HEADLESS", True), 
            timeout=config.get("TIMEOUT", 30)
        )
        
        try:
            # Login
            logger.info("Iniciando sesión en Nubox")
            login_success = nubox.login(
                config["NUBOX_USERNAME"],
                config["NUBOX_PASSWORD"],
                url=config.get("NUBOX_URL", "https://www.nubox.com/login")
            )
            
            if not login_success:
                logger.error("No se pudo iniciar sesión en Nubox. Verifique las credenciales.")
                return False
            
            # Navegar al reporte
            logger.info("Navegando al módulo de reportes")
            report_type = config.get("REPORT_TYPE", "mayor")
            navigation_success = nubox.navigate_to_report(report_type)
            
            if not navigation_success:
                logger.error(f"No se pudo navegar al reporte de tipo: {report_type}")
                return False
            
            # Configurar parámetros del reporte
            logger.info("Configurando parámetros del reporte")
            report_params = config.get("REPORT_PARAMS", {})
            params_success = nubox.set_report_parameters(report_params)
            
            if not params_success:
                logger.error("No se pudieron configurar los parámetros del reporte")
                return False
            
            # Extraer datos
            logger.info("Extrayendo datos del reporte")
            report_data = nubox.extract_report()
            
            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Si el resultado es una tupla (DataFrame, download_path), es porque se descargó un archivo
            download_path = None
            if isinstance(report_data, tuple) and len(report_data) == 2:
                report_data, download_path = report_data
            
            # Si tenemos un DataFrame con datos, guardarlo
            if not report_data.empty:
                # Determinar el formato de salida
                output_format = config.get("OUTPUT_FORMAT", "csv").lower()
                
                # Generar nombre de archivo según formato
                if output_format == "excel":
                    filename = f"reporte_nubox_{timestamp}.xlsx"
                elif output_format == "json":
                    filename = f"reporte_nubox_{timestamp}.json"
                else:
                    filename = f"reporte_nubox_{timestamp}.csv"
                
                save_path = os.path.join(config["OUTPUT_DIR"], filename)
                
                # Guardar reporte
                save_success = save_report(report_data, save_path, format=output_format)
                
                if save_success:
                    logger.info(f"Reporte guardado exitosamente en: {save_path}")
                else:
                    logger.error("Error al guardar el reporte")
                    return False
            
            # Si se descargó un archivo directamente desde Nubox, moverlo a la carpeta de output
            elif download_path and download_path != "Descarga completada":
                try:
                    # Determinar el formato basado en la extensión del archivo descargado
                    _, ext = os.path.splitext(download_path)
                    filename = f"reporte_nubox_{timestamp}{ext}"
                    save_path = os.path.join(config["OUTPUT_DIR"], filename)
                    
                    # Mover el archivo a la carpeta de output
                    shutil.move(download_path, save_path)
                    logger.info(f"Archivo descargado movido a: {save_path}")
                except Exception as e:
                    logger.error(f"Error al mover el archivo descargado: {str(e)}")
            else:
                logger.error("No se obtuvieron datos del reporte")
                return False
            
            return True
            
        finally:
            # Cerrar el navegador
            logger.info("Finalizando sesión y cerrando navegador")
            nubox.close()
            
    except Exception as e:
        logger.error(f"Error en el proceso RPA: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    exit(exit_code)