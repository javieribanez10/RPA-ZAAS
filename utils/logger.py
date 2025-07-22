#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuración del logger para el RPA de Nubox.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

def setup_logger(name="nubox_rpa", level=logging.INFO):
    """
    Configura un logger con formato personalizado que escribe tanto en consola como en archivo.
    
    Args:
        name (str): Nombre del logger
        level (int): Nivel de logging (default: logging.INFO)
        
    Returns:
        logging.Logger: Logger configurado
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Si ya hay handlers, no agregamos más
    if logger.hasHandlers():
        return logger
        
    # Crear directorio logs si no existe
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"nubox_rpa_{timestamp}.log"
    
    # Formato para los logs
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger