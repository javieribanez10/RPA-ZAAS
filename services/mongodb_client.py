#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cliente MongoDB para el sistema RPA Nubox.
Maneja la exportación automática de datos contables extraídos.
"""

import pymongo
from pymongo import MongoClient
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime
import json
import pandas as pd
import ssl
import os
from pathlib import Path

# Configurar logging
logger = logging.getLogger("nubox_rpa.mongodb")

class NuboxMongoClient:
    """
    Cliente para exportar datos contables de Nubox a MongoDB Atlas.
    """
    
    def __init__(self, connection_string: str = None, database_name: str = "nubox-data", 
                 collection_name: str = "test-nubox", timeout: int = 30):
        """
        Inicializa el cliente MongoDB para Nubox.
        
        Args:
            connection_string (str): String de conexión a MongoDB
            database_name (str): Nombre de la base de datos
            collection_name (str): Nombre de la colección para reportes
            timeout (int): Timeout de conexión en segundos
        """
        # Usar credenciales por defecto si no se proporcionan
        self.connection_string = connection_string or "mongodb+srv://javieribanez:Zaaslocura2025@test-apis.i3fzya0.mongodb.net/?retryWrites=true&w=majority&appName=test-apis"
        self.database_name = database_name
        self.collection_name = collection_name
        self.timeout = timeout
        self.client = None
        self.db = None
        
    def connect(self) -> bool:
        """
        Establece conexión con MongoDB Atlas.
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            # Configurar opciones de conexión para MongoDB Atlas
            client_options = {
                'serverSelectionTimeoutMS': self.timeout * 1000,
                'connectTimeoutMS': self.timeout * 1000,
                'socketTimeoutMS': self.timeout * 1000,
                'retryWrites': True,
                'w': 'majority'
            }
            
            self.client = MongoClient(self.connection_string, **client_options)
            
            # Probar la conexión
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            
            logger.info(f"✅ Conectado exitosamente a MongoDB Atlas - Base de datos: {self.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB Atlas: {str(e)}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con MongoDB."""
        if self.client:
            self.client.close()
            logger.info("🔌 Desconectado de MongoDB Atlas")
    
    def export_nubox_dataframe(self, df: pd.DataFrame, company_info: Dict[str, Any] = None,
                              report_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Exporta un DataFrame de Nubox a MongoDB con estructura optimizada.
        
        Args:
            df (pd.DataFrame): DataFrame con datos contables
            company_info (Dict): Información de la empresa extraída
            report_metadata (Dict): Metadatos del reporte (fechas, parámetros, etc.)
            
        Returns:
            Dict[str, Any]: Resultado de la exportación
        """
        result = {
            'success': False,
            'total_rows': 0,
            'exported_rows': 0,
            'document_id': None,
            'errors': [],
            'timestamp': datetime.now().isoformat(),
            'collection_name': self.collection_name
        }
        
        if df.empty:
            result['errors'].append('DataFrame está vacío')
            return result
        
        try:
            if not self.client:
                if not self.connect():
                    result['errors'].append('No se pudo conectar a MongoDB')
                    return result
            
            collection = self.db[self.collection_name]
            result['total_rows'] = len(df)
            
            # Preparar documento principal del reporte
            report_document = self._prepare_report_document(df, company_info, report_metadata)
            
            # Insertar documento principal
            insert_result = collection.insert_one(report_document)
            result['document_id'] = str(insert_result.inserted_id)
            result['exported_rows'] = len(df)
            result['success'] = True
            
            # Crear índices si es necesario
            self._create_nubox_indexes(collection)
            
            logger.info(f"✅ Reporte Nubox exportado exitosamente: {len(df)} filas, ID: {result['document_id']}")
            
        except Exception as e:
            result['errors'].append(f"Error general: {str(e)}")
            logger.error(f"Error en export_nubox_dataframe: {str(e)}")
        
        return result
    
    def _prepare_report_document(self, df: pd.DataFrame, company_info: Dict[str, Any] = None,
                               report_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepara el documento del reporte con estructura exacta según el esquema JSON definido.
        
        Args:
            df (pd.DataFrame): DataFrame con datos contables
            company_info (Dict): Información de la empresa
            report_metadata (Dict): Metadatos del reporte
            
        Returns:
            Dict[str, Any]: Documento estructurado según el esquema JSON
        """
        # Convertir DataFrame a lista de diccionarios con tipos exactos del esquema
        accounting_entries = []
        for _, row in df.iterrows():
            entry = {}
            
            # Mapear cada columna según el esquema exacto
            for col in df.columns:
                value = row[col]
                
                if col == 'FECHA':
                    # Campo "fecha" requerido como Date
                    if pd.notna(value):
                        if isinstance(value, str):
                            try:
                                entry['fecha'] = datetime.strptime(value, '%d/%m/%Y')
                            except:
                                entry['fecha'] = datetime.now()
                        else:
                            entry['fecha'] = value
                    else:
                        entry['fecha'] = datetime.now()  # Requerido, no puede ser null
                        
                elif col == 'COMPROBANTE':
                    # Campo "comprobante" requerido como string
                    entry['comprobante'] = str(value) if pd.notna(value) else ""
                    
                elif col == 'GLOSA':
                    # Campo "glosa" requerido como string
                    entry['glosa'] = str(value) if pd.notna(value) else ""
                    
                elif col == 'DEBE':
                    # Campo "debe" requerido como Double
                    try:
                        entry['debe'] = float(value) if pd.notna(value) else 0.0
                    except:
                        entry['debe'] = 0.0
                        
                elif col == 'HABER':
                    # Campo "haber" requerido como Double
                    try:
                        entry['haber'] = float(value) if pd.notna(value) else 0.0
                    except:
                        entry['haber'] = 0.0
                        
                elif col == 'SALDO':
                    # Campo "saldo" requerido como Double
                    try:
                        entry['saldo'] = float(value) if pd.notna(value) else 0.0
                    except:
                        entry['saldo'] = 0.0
                        
                elif col == 'C.C.':
                    # Campo "c.c." requerido como string (mantener el punto)
                    entry['c.c.'] = str(value) if pd.notna(value) else ""
            
            # Validar que todos los campos requeridos estén presentes
            required_fields = ['fecha', 'comprobante', 'glosa', 'debe', 'haber', 'saldo', 'c.c.']
            for field in required_fields:
                if field not in entry:
                    if field == 'fecha':
                        entry[field] = datetime.now()
                    elif field in ['debe', 'haber', 'saldo']:
                        entry[field] = 0.0
                    else:
                        entry[field] = ""
            
            accounting_entries.append(entry)
        
        # Calcular totales según el esquema (todos requeridos)
        totals = {
            'total_debe': float(df['DEBE'].sum()) if 'DEBE' in df.columns else 0.0,
            'total_haber': float(df['HABER'].sum()) if 'HABER' in df.columns else 0.0,
            'saldo_final': float(df['SALDO'].iloc[-1]) if 'SALDO' in df.columns and len(df) > 0 else 0.0,
            'total_movimientos': int(len(df))
        }
        
        # Periodo con fechas requeridas
        if 'FECHA' in df.columns:
            valid_dates = df['FECHA'].dropna()
            if not valid_dates.empty:
                fecha_desde = valid_dates.min()
                fecha_hasta = valid_dates.max()
            else:
                fecha_desde = fecha_hasta = datetime.now()
        else:
            fecha_desde = fecha_hasta = datetime.now()
        
        periodo = {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta
        }
        
        # Preparar parámetros según el esquema (todos requeridos)
        archivo_origen = report_metadata.get('archivo_origen', '') if report_metadata else ''
        cuenta_contable = report_metadata.get('cuenta_contable', '') if report_metadata else ''
        fecha_extraccion_str = report_metadata.get('fecha_extraccion', datetime.now().isoformat()) if report_metadata else datetime.now().isoformat()
        
        parametros_streamlit = {
            'formato_salida': 'EXCEL',
            'include_subcuentas': 'SI'
        }
        
        if report_metadata and 'parametros_streamlit' in report_metadata:
            parametros_streamlit.update(report_metadata['parametros_streamlit'])
        
        parametros = {
            'archivo_origen': archivo_origen,
            'cuenta_contable': cuenta_contable,
            'fecha_extraccion': fecha_extraccion_str,
            'parametros_streamlit': parametros_streamlit
        }
        
        # Documento final según el esquema exacto
        document = {
            # empresa (objeto requerido con todos sus campos requeridos)
            'empresa': {
                'nombre': company_info.get('Nombre', '') if company_info else '',
                'rut': company_info.get('Rut', '') if company_info else '',
                'representante_legal': company_info.get('Representante Legal', '') if company_info else '',
                'giro_comercial': company_info.get('Giro Comercial', '') if company_info else ''
            },
            
            # reporte (objeto requerido con todos sus campos requeridos)
            'reporte': {
                'tipo': 'LIBRO_MAYOR',
                'cuenta_contable': cuenta_contable,
                'periodo': periodo,
                'parametros': parametros,
                'totales': totals
            },
            
            # movimientos (array requerido)
            'movimientos': accounting_entries,
            
            # metadata (objeto requerido con todos sus campos requeridos)
            'metadata': {
                'fuente': 'nubox_rpa',
                'fecha_extraccion': datetime.now(),
                'version_sistema': '1.0',
                'archivo_origen': archivo_origen,
                'total_registros': int(len(accounting_entries)),
                'columnas_extraidas': list(df.columns)
            }
        }
        
        return document
    
    def _create_nubox_indexes(self, collection):
        """
        Crea índices específicos para consultas eficientes de datos Nubox.
        
        Args:
            collection: Colección de MongoDB
        """
        try:
            # Índices principales
            collection.create_index([("metadata.fecha_extraccion", -1)])
            collection.create_index([("empresa.rut", 1)])
            collection.create_index([("empresa.nombre", 1)])
            collection.create_index([("reporte.tipo", 1)])
            collection.create_index([("reporte.cuenta_contable", 1)])
            
            # Índices para consultas de movimientos
            collection.create_index([("movimientos.fecha", 1)])
            collection.create_index([("reporte.periodo.fecha_desde", 1)])
            collection.create_index([("reporte.periodo.fecha_hasta", 1)])
            
            # Índice compuesto para consultas complejas
            collection.create_index([
                ("empresa.rut", 1),
                ("reporte.cuenta_contable", 1),
                ("metadata.fecha_extraccion", -1)
            ])
            
            logger.info("✅ Índices de Nubox creados exitosamente")
            
        except Exception as e:
            logger.warning(f"Error creando índices: {str(e)}")
    
    def query_reportes_by_empresa(self, rut_empresa: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Consulta reportes por RUT de empresa.
        
        Args:
            rut_empresa (str): RUT de la empresa
            limit (int): Límite de documentos
            
        Returns:
            List[Dict]: Lista de reportes
        """
        try:
            if not self.client:
                if not self.connect():
                    return []
            
            collection = self.db[self.collection_name]
            
            query = {"empresa.rut": rut_empresa}
            cursor = collection.find(query).sort("metadata.fecha_extraccion", -1).limit(limit)
            
            results = list(cursor)
            logger.info(f"📊 Encontrados {len(results)} reportes para RUT: {rut_empresa}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error consultando reportes: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la colección de reportes Nubox.
        
        Returns:
            Dict[str, Any]: Estadísticas de la colección
        """
        try:
            if not self.client:
                if not self.connect():
                    return {}
            
            collection = self.db[self.collection_name]
            
            # Estadísticas básicas
            stats = {
                'total_reportes': collection.count_documents({}),
                'collection_name': self.collection_name,
                'database_name': self.database_name
            }
            
            # Agregaciones para estadísticas detalladas
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_movimientos": {"$sum": {"$size": "$movimientos"}},
                        "empresas_unicas": {"$addToSet": "$empresa.rut"},
                        "primera_extraccion": {"$min": "$metadata.fecha_extraccion"},
                        "ultima_extraccion": {"$max": "$metadata.fecha_extraccion"},
                        "total_debe": {"$sum": "$reporte.totales.total_debe"},
                        "total_haber": {"$sum": "$reporte.totales.total_haber"}
                    }
                }
            ]
            
            agg_results = list(collection.aggregate(pipeline))
            if agg_results:
                result = agg_results[0]
                stats.update({
                    'total_movimientos': result.get('total_movimientos', 0),
                    'empresas_unicas': len(result.get('empresas_unicas', [])),
                    'primera_extraccion': result.get('primera_extraccion'),
                    'ultima_extraccion': result.get('ultima_extraccion'),
                    'total_debe': result.get('total_debe', 0),
                    'total_haber': result.get('total_haber', 0)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión y retorna información del servidor.
        
        Returns:
            Dict[str, Any]: Información de la conexión
        """
        result = {
            'connected': False,
            'database_name': self.database_name,
            'collection_name': self.collection_name,
            'collections': [],
            'error': None
        }
        
        try:
            if not self.client:
                if not self.connect():
                    result['error'] = 'No se pudo establecer conexión'
                    return result
            
            # Probar operación simple
            self.client.admin.command('ping')
            result['collections'] = self.db.list_collection_names()
            result['connected'] = True
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error en test_connection: {str(e)}")
        
        return result
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()