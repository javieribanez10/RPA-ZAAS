#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilidades para el manejo de archivos y guardado de reportes.
"""

import os
import csv
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def save_report(data, filepath, format='csv'):
    """
    Guarda los datos del reporte en el formato especificado.
    
    Args:
        data (pandas.DataFrame): Datos del reporte
        filepath (str): Ruta donde guardar el archivo
        format (str): Formato de salida ('csv', 'excel', 'json')
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Guardar según formato
        if format.lower() == 'csv':
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
        elif format.lower() == 'excel':
            data.to_excel(filepath, index=False)
        elif format.lower() == 'json':
            data.to_json(filepath, orient='records')
        else:
            raise ValueError(f"Formato no soportado: {format}")
            
        return True
    except Exception as e:
        print(f"Error al guardar el reporte: {str(e)}")
        return False
        
def get_latest_report(directory, pattern="reporte_nubox_*.csv"):
    """
    Obtiene el reporte más reciente en el directorio especificado.
    
    Args:
        directory (str): Directorio donde buscar
        pattern (str): Patrón de nombre de archivo
        
    Returns:
        str: Ruta al archivo más reciente
    """
    directory = Path(directory)
    files = list(directory.glob(pattern))
    
    if not files:
        return None
        
    return str(max(files, key=os.path.getctime))
    
def load_report(filepath):
    """
    Carga un reporte desde un archivo.
    
    Args:
        filepath (str): Ruta al archivo
        
    Returns:
        pandas.DataFrame: Datos del reporte
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == '.csv':
            return pd.read_csv(filepath)
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(filepath)
        elif ext == '.json':
            return pd.read_json(filepath)
        else:
            raise ValueError(f"Formato no soportado: {ext}")
    except Exception as e:
        print(f"Error al cargar el reporte: {str(e)}")
        return None