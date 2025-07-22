#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilidades para manejo de fechas en el RPA Nubox.
"""

import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger("nubox_rpa.date_utils")

def generate_monthly_date_ranges(fecha_desde, fecha_hasta):
    """
    Genera rangos de fechas mensuales entre dos fechas.
    
    Args:
        fecha_desde (datetime.date): Fecha de inicio
        fecha_hasta (datetime.date): Fecha de fin
        
    Returns:
        list: Lista de tuplas (fecha_inicio, fecha_fin) para cada mes
        
    Example:
        Si fecha_desde = 01/01/2025 y fecha_hasta = 01/07/2025
        Retorna: [(01/01/2025, 01/02/2025), (01/02/2025, 01/03/2025), ...]
    """
    try:
        monthly_ranges = []
        current_date = fecha_desde
        
        logger.info(f"Generando rangos mensuales desde {fecha_desde} hasta {fecha_hasta}")
        
        while current_date < fecha_hasta:
            # Calcular el primer día del siguiente mes
            next_month = current_date + relativedelta(months=1)
            
            # Si el siguiente mes excede la fecha hasta, usar la fecha hasta
            if next_month > fecha_hasta:
                next_month = fecha_hasta
            
            monthly_ranges.append((current_date, next_month))
            logger.debug(f"Rango mensual agregado: {current_date} a {next_month}")
            
            current_date = next_month
        
        logger.info(f"Se generaron {len(monthly_ranges)} rangos mensuales")
        return monthly_ranges
        
    except Exception as e:
        logger.error(f"Error generando rangos mensuales: {str(e)}")
        return [(fecha_desde, fecha_hasta)]  # Fallback al rango original

def format_date_for_nubox(date_obj):
    """
    Formatea una fecha para uso en Nubox (DD/MM/YYYY).
    
    Args:
        date_obj (datetime.date): Objeto de fecha
        
    Returns:
        str: Fecha formateada como DD/MM/YYYY
    """
    return date_obj.strftime("%d/%m/%Y")

def get_month_name_es(date_obj):
    """
    Obtiene el nombre del mes en español para una fecha.
    
    Args:
        date_obj (datetime.date): Objeto de fecha
        
    Returns:
        str: Nombre del mes en español
    """
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    return meses[date_obj.month - 1]

def should_use_monthly_extraction(fecha_desde, fecha_hasta, min_days_for_monthly=32):
    """
    Determina si se debe usar extracción mensual basado en el rango de fechas.
    
    Args:
        fecha_desde (datetime.date): Fecha de inicio
        fecha_hasta (datetime.date): Fecha de fin
        min_days_for_monthly (int): Mínimo de días para activar extracción mensual
        
    Returns:
        bool: True si se debe usar extracción mensual
    """
    delta = fecha_hasta - fecha_desde
    return delta.days >= min_days_for_monthly