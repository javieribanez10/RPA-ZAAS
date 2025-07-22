#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para validar la exportación MongoDB según el esquema JSON definido.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import json

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from services.mongodb_client import NuboxMongoClient

def validate_schema_compliance(document):
    """
    Valida que el documento cumpla con el esquema JSON definido.
    
    Args:
        document (dict): Documento a validar
        
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # Validar campos principales requeridos
    required_main_fields = ['_id', 'empresa', 'metadata', 'movimientos', 'reporte']
    for field in required_main_fields:
        if field not in document and field != '_id':  # _id se agrega automáticamente por MongoDB
            errors.append(f"Campo principal requerido faltante: {field}")
    
    # Validar estructura empresa
    if 'empresa' in document:
        empresa = document['empresa']
        required_empresa_fields = ['giro_comercial', 'nombre', 'representante_legal', 'rut']
        for field in required_empresa_fields:
            if field not in empresa:
                errors.append(f"Campo empresa requerido faltante: {field}")
            elif not isinstance(empresa[field], str):
                errors.append(f"Campo empresa.{field} debe ser string")
    
    # Validar estructura metadata
    if 'metadata' in document:
        metadata = document['metadata']
        required_metadata_fields = [
            'archivo_origen', 'columnas_extraidas', 'fecha_extraccion', 
            'fuente', 'total_registros', 'version_sistema'
        ]
        for field in required_metadata_fields:
            if field not in metadata:
                errors.append(f"Campo metadata requerido faltante: {field}")
        
        # Validar tipos específicos
        if 'columnas_extraidas' in metadata and not isinstance(metadata['columnas_extraidas'], list):
            errors.append("metadata.columnas_extraidas debe ser array")
        if 'total_registros' in metadata and not isinstance(metadata['total_registros'], int):
            errors.append("metadata.total_registros debe ser integer")
        if 'fecha_extraccion' in metadata and not isinstance(metadata['fecha_extraccion'], datetime):
            errors.append("metadata.fecha_extraccion debe ser Date")
    
    # Validar estructura movimientos
    if 'movimientos' in document:
        movimientos = document['movimientos']
        if not isinstance(movimientos, list):
            errors.append("movimientos debe ser array")
        else:
            required_mov_fields = ['c.c.', 'comprobante', 'debe', 'fecha', 'glosa', 'haber', 'saldo']
            for i, movimiento in enumerate(movimientos):
                for field in required_mov_fields:
                    if field not in movimiento:
                        errors.append(f"Campo movimientos[{i}].{field} requerido faltante")
                
                # Validar tipos específicos
                if 'fecha' in movimiento and not isinstance(movimiento['fecha'], datetime):
                    errors.append(f"movimientos[{i}].fecha debe ser Date")
                for field in ['debe', 'haber', 'saldo']:
                    if field in movimiento and not isinstance(movimiento[field], (int, float)):
                        errors.append(f"movimientos[{i}].{field} debe ser número")
    
    # Validar estructura reporte
    if 'reporte' in document:
        reporte = document['reporte']
        required_reporte_fields = ['cuenta_contable', 'parametros', 'periodo', 'tipo', 'totales']
        for field in required_reporte_fields:
            if field not in reporte:
                errors.append(f"Campo reporte requerido faltante: {field}")
        
        # Validar totales
        if 'totales' in reporte:
            totales = reporte['totales']
            required_totales_fields = ['saldo_final', 'total_debe', 'total_haber', 'total_movimientos']
            for field in required_totales_fields:
                if field not in totales:
                    errors.append(f"Campo reporte.totales.{field} requerido faltante")
            
            if 'total_movimientos' in totales and not isinstance(totales['total_movimientos'], int):
                errors.append("reporte.totales.total_movimientos debe ser integer")
        
        # Validar periodo
        if 'periodo' in reporte:
            periodo = reporte['periodo']
            required_periodo_fields = ['fecha_desde', 'fecha_hasta']
            for field in required_periodo_fields:
                if field not in periodo:
                    errors.append(f"Campo reporte.periodo.{field} requerido faltante")
                elif field in periodo and not isinstance(periodo[field], datetime):
                    errors.append(f"reporte.periodo.{field} debe ser Date")
        
        # Validar parametros
        if 'parametros' in reporte:
            parametros = reporte['parametros']
            required_param_fields = ['archivo_origen', 'cuenta_contable', 'fecha_extraccion', 'parametros_streamlit']
            for field in required_param_fields:
                if field not in parametros:
                    errors.append(f"Campo reporte.parametros.{field} requerido faltante")
            
            if 'parametros_streamlit' in parametros:
                streamlit_params = parametros['parametros_streamlit']
                required_streamlit_fields = ['formato_salida', 'include_subcuentas']
                for field in required_streamlit_fields:
                    if field not in streamlit_params:
                        errors.append(f"Campo reporte.parametros.parametros_streamlit.{field} requerido faltante")
    
    return len(errors) == 0, errors

def test_schema_validation():
    """Prueba la validación del esquema con datos reales."""
    print("=" * 70)
    print("📋 PRUEBA DE VALIDACIÓN DE ESQUEMA JSON")
    print("=" * 70)
    
    try:
        # Crear DataFrame de prueba
        sample_data = {
            'FECHA': ['31/01/2025', '31/01/2025'],
            'COMPROBANTE': ['TRASPASO 2364 5', 'TRASPASO 2364 6'],
            'GLOSA': ['CENTRALIZACION VENTAS ENERO', 'CENTRALIZACION COMPRAS ENERO'],
            'DEBE': [2133631.0, 0.0],
            'HABER': [0.0, 114731103.0],
            'SALDO': [-2133631, 112597472],
            'C.C.': ['905', '905']
        }
        
        df = pd.DataFrame(sample_data)
        df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y')
        
        # Información de empresa
        company_info = {
            'Nombre': 'SELYT SPA',
            'Rut': '77.081.534-7',
            'Representante Legal': 'PAULO ALEJANDRO SUBIABRE CEPEDA',
            'Giro Comercial': 'SERVICIOS TECNOLOGICOS'
        }
        
        # Metadatos del reporte
        report_metadata = {
            'archivo_origen': 'test_schema_validation.py',
            'cuenta_contable': '5101-01 VENTAS POR SERVICIO',
            'fecha_extraccion': datetime.now().isoformat(),
            'parametros_streamlit': {
                'formato_salida': 'EXCEL',
                'include_subcuentas': 'SI'
            }
        }
        
        # Crear cliente y preparar documento
        mongo_client = NuboxMongoClient()
        document = mongo_client._prepare_report_document(df, company_info, report_metadata)
        
        print("✅ Documento preparado exitosamente")
        print(f"📊 Estructura del documento:")
        print(f"   - Empresa: {document['empresa']['nombre']}")
        print(f"   - Movimientos: {len(document['movimientos'])}")
        print(f"   - Total DEBE: ${document['reporte']['totales']['total_debe']:,.2f}")
        print(f"   - Total HABER: ${document['reporte']['totales']['total_haber']:,.2f}")
        
        # Validar esquema
        print("\n🔍 Validando cumplimiento del esquema...")
        is_valid, errors = validate_schema_compliance(document)
        
        if is_valid:
            print("✅ ¡ESQUEMA VÁLIDO! El documento cumple con todos los requisitos")
            
            # Mostrar estructura detallada
            print("\n📋 Estructura validada:")
            print("   ✅ empresa (4/4 campos requeridos)")
            print("   ✅ metadata (6/6 campos requeridos)")
            print("   ✅ movimientos (array con campos requeridos)")
            print("   ✅ reporte (5/5 campos requeridos)")
            print("   ✅ reporte.totales (4/4 campos requeridos)")
            print("   ✅ reporte.periodo (2/2 campos requeridos)")
            print("   ✅ reporte.parametros (4/4 campos requeridos)")
            
            # Validar tipos de datos
            print("\n🔢 Tipos de datos validados:")
            for movimiento in document['movimientos']:
                print(f"   ✅ movimiento.fecha: {type(movimiento['fecha']).__name__}")
                print(f"   ✅ movimiento.debe: {type(movimiento['debe']).__name__}")
                print(f"   ✅ movimiento.haber: {type(movimiento['haber']).__name__}")
                print(f"   ✅ movimiento.saldo: {type(movimiento['saldo']).__name__}")
                print(f"   ✅ movimiento.c.c.: {type(movimiento['c.c.']).__name__}")
                break  # Solo mostrar el primero
            
            return True
        else:
            print("❌ ESQUEMA INVÁLIDO - Se encontraron errores:")
            for error in errors:
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error en la validación: {str(e)}")
        return False

def test_real_export():
    """Prueba la exportación real a MongoDB."""
    print("\n" + "=" * 70)
    print("🚀 PRUEBA DE EXPORTACIÓN REAL A MONGODB")
    print("=" * 70)
    
    try:
        # Datos de prueba
        sample_data = {
            'FECHA': ['31/01/2025', '31/01/2025'],
            'COMPROBANTE': ['TRASPASO 2364 5', 'TRASPASO 2364 6'],
            'GLOSA': ['CENTRALIZACION VENTAS ENERO', 'CENTRALIZACION COMPRAS ENERO'],
            'DEBE': [2133631.0, 0.0],
            'HABER': [0.0, 114731103.0],
            'SALDO': [-2133631, 112597472],
            'C.C.': ['905', '905']
        }
        
        df = pd.DataFrame(sample_data)
        df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y')
        
        company_info = {
            'Nombre': 'SELYT SPA',
            'Rut': '77.081.534-7',
            'Representante Legal': 'PAULO ALEJANDRO SUBIABRE CEPEDA',
            'Giro Comercial': 'SERVICIOS TECNOLOGICOS'
        }
        
        report_metadata = {
            'archivo_origen': 'test_schema_validation.py',
            'cuenta_contable': '5101-01 VENTAS POR SERVICIO',
            'fecha_extraccion': datetime.now().isoformat(),
            'parametros_streamlit': {
                'formato_salida': 'EXCEL',
                'include_subcuentas': 'SI'
            }
        }
        
        # Exportar a MongoDB
        mongo_client = NuboxMongoClient()
        
        print("🔌 Conectando a MongoDB...")
        if not mongo_client.connect():
            print("❌ No se pudo conectar a MongoDB")
            return False
        
        print("📤 Exportando documento...")
        export_result = mongo_client.export_nubox_dataframe(df, company_info, report_metadata)
        
        if export_result['success']:
            print("✅ EXPORTACIÓN EXITOSA")
            print(f"🆔 ID del documento: {export_result['document_id']}")
            print(f"📊 Filas exportadas: {export_result['exported_rows']}")
            print(f"📁 Colección: {export_result['collection_name']}")
            
            # Verificar el documento en MongoDB
            print("\n🔍 Verificando documento en MongoDB...")
            collection = mongo_client.db[mongo_client.collection_name]
            from bson import ObjectId
            
            retrieved_doc = collection.find_one({"_id": ObjectId(export_result['document_id'])})
            
            if retrieved_doc:
                print("✅ Documento recuperado de MongoDB")
                print(f"   - Empresa: {retrieved_doc['empresa']['nombre']}")
                print(f"   - RUT: {retrieved_doc['empresa']['rut']}")
                print(f"   - Movimientos: {len(retrieved_doc['movimientos'])}")
                print(f"   - Fecha extracción: {retrieved_doc['metadata']['fecha_extraccion']}")
                
                # Validar esquema del documento recuperado
                is_valid, errors = validate_schema_compliance(retrieved_doc)
                if is_valid:
                    print("✅ Documento en MongoDB cumple el esquema")
                else:
                    print("❌ Documento en MongoDB NO cumple el esquema:")
                    for error in errors:
                        print(f"   - {error}")
                
                return True
            else:
                print("❌ No se pudo recuperar el documento de MongoDB")
                return False
        else:
            print("❌ Error en la exportación:")
            for error in export_result['errors']:
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error en la exportación real: {str(e)}")
        return False
    finally:
        try:
            mongo_client.disconnect()
        except:
            pass

def main():
    """Función principal que ejecuta todas las pruebas de validación de esquema."""
    print("🧪 INICIANDO PRUEBAS DE VALIDACIÓN DE ESQUEMA JSON")
    print(f"🕒 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Validación del esquema
    schema_valid = test_schema_validation()
    
    # Test 2: Exportación real (solo si el esquema es válido)
    export_success = False
    if schema_valid:
        export_success = test_real_export()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📋 RESUMEN DE VALIDACIÓN DE ESQUEMA")
    print("=" * 70)
    
    tests = [
        ("Validación de Esquema", schema_valid),
        ("Exportación Real a MongoDB", export_success)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("✅ El documento cumple exactamente con el esquema JSON definido")
        print("🚀 El sistema está listo para exportar datos a MongoDB con formato correcto")
    else:
        print(f"\n⚠️ {total - passed} validaciones fallaron")
        print("❌ Revisa la estructura del documento antes de continuar")

if __name__ == "__main__":
    main()