#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuración para el RPA de Nubox.
"""

import os
import json
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "config.json"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

def setup_config():
    """
    Carga la configuración desde el archivo config.json y variables de entorno.
    Las variables de entorno tienen prioridad sobre el archivo de configuración.
    """
    # Valores por defecto
    config = {
        "NUBOX_URL": "https://www.nubox.com/login",
        "HEADLESS": True,
        "TIMEOUT": 30,
        "OUTPUT_DIR": str(OUTPUT_DIR),
        "LOGS_DIR": str(LOGS_DIR)
    }
    
    # Cargar desde archivo si existe
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
        except json.JSONDecodeError:
            print("Error: El archivo config.json no es válido.")
        except Exception as e:
            print(f"Error al leer config.json: {str(e)}")
    
    # Variables de entorno (mayor prioridad)
    env_vars = {
        "NUBOX_USERNAME": os.environ.get("NUBOX_USERNAME"),
        "NUBOX_PASSWORD": os.environ.get("NUBOX_PASSWORD"),
        "NUBOX_URL": os.environ.get("NUBOX_URL"),
        "HEADLESS": os.environ.get("HEADLESS"),
        "TIMEOUT": os.environ.get("TIMEOUT")
    }
    
    # Actualizar config con variables de entorno (si existen)
    for key, value in env_vars.items():
        if value is not None:
            # Convertir tipos cuando sea necesario
            if key == "HEADLESS":
                value = value.lower() in ["true", "1", "yes", "y"]
            elif key == "TIMEOUT":
                value = int(value)
            config[key] = value
    
    return config

# Asegurar que los directorios existan
def ensure_directories():
    """Crea los directorios necesarios si no existen."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

# Crear directorios al importar
ensure_directories()