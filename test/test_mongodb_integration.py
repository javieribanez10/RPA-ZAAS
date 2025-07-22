#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para verificar la conexión y funcionalidad de MongoDB con Nubox RPA.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from services.mongodb_client import NuboxMongoClient

def test_mongodb_connection():
    """Prueba la conexión básica a MongoDB."""
    print("=" * 60)
    print("🔌 PRUEBA DE CONEXIÓN A MONGODB")
    print("=" * 60)
    
    try:
        # Crear cliente
        mongo_client = NuboxMongoClient()
        
        # Probar conexión
        connection_result = mongo_client.test_connection()
        
        if connection_result['connected']:
            print("✅ Conexión exitosa a MongoDB Atlas")
            print(f"📊 Base de datos: {connection_result['database_name']}")
            print(f"📋 Colección: {connection_result['collection_name']}")
            print(f"📁 Colecciones disponibles: {len(connection_result['collections'])}")
            
            if connection_result['collections']:
                print("   Colecciones encontradas:")
                for collection in connection_result['collections']:
                    print(f"   - {collection}")
            
            return True
        else:
            print("❌ Error de conexión a MongoDB")
            print(f"Error: {connection_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de conexión: {str(e)}")
        return False
    finally:
        try:
            mongo_client.disconnect()
        except:
            pass

def test_export_sample_data():
    """Prueba la exportación de datos de muestra."""
    print("\n" + "=" * 60)
    print("📤 PRUEBA DE EXPORTACIÓN DE DATOS")
    print("=" * 60)
    
    try:
        # Crear DataFrame de muestra similar al que genera Nubox
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
        
        # Convertir fechas
        df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y')
        
        # Agregar información de empresa como atributos
        df.attrs = {
            'company_info': {
                'Nombre': 'SELYT SPA',
                'Rut': '77.081.534-7',
                'Representante Legal': 'PAULO ALEJANDRO SUBIABRE CEPEDA',
                'Giro Comercial': 'SERVICIOS TECNOLOGICOS'
            }
        }
        
        print(f"📊 DataFrame de prueba creado: {len(df)} filas, {len(df.columns)} columnas")
        print("Datos de muestra:")
        print(df.to_string())
        
        # Metadatos de prueba
        report_metadata = {
            'archivo_origen': 'test_mongodb_integration.py',
            'cuenta_contable': '5101-01 VENTAS POR SERVICIO',
            'fecha_extraccion': datetime.now().isoformat(),
            'parametros_streamlit': {
                'formato_salida': 'EXCEL',
                'include_subcuentas': 'SI'
            }
        }
        
        # Exportar a MongoDB
        print("\n🚀 Exportando a MongoDB...")
        mongo_client = NuboxMongoClient()
        
        export_result = mongo_client.export_nubox_dataframe(
            df=df,
            company_info=df.attrs['company_info'],
            report_metadata=report_metadata
        )
        
        if export_result['success']:
            print("✅ Exportación exitosa")
            print(f"📋 Filas exportadas: {export_result['exported_rows']}")
            print(f"🆔 ID del documento: {export_result['document_id']}")
            print(f"📁 Colección: {export_result['collection_name']}")
            return export_result['document_id']
        else:
            print("❌ Error en la exportación")
            for error in export_result['errors']:
                print(f"   - {error}")
            return None
            
    except Exception as e:
        print(f"❌ Error en prueba de exportación: {str(e)}")
        return None
    finally:
        try:
            mongo_client.disconnect()
        except:
            pass

def test_query_data(document_id=None):
    """Prueba las consultas de datos."""
    print("\n" + "=" * 60)
    print("🔍 PRUEBA DE CONSULTAS")
    print("=" * 60)
    
    try:
        mongo_client = NuboxMongoClient()
        
        # Consulta por empresa
        print("📊 Consultando reportes de SELYT SPA...")
        reportes = mongo_client.query_reportes_by_empresa("77.081.534-7", limit=5)
        
        print(f"✅ Encontrados {len(reportes)} reportes")
        
        if reportes:
            for i, reporte in enumerate(reportes, 1):
                print(f"\n📋 Reporte {i}:")
                print(f"   - ID: {reporte['_id']}")
                print(f"   - Empresa: {reporte['empresa']['nombre']}")
                print(f"   - Cuenta: {reporte['reporte']['cuenta_contable']}")
                print(f"   - Movimientos: {len(reporte['movimientos'])}")
                print(f"   - Total DEBE: ${reporte['reporte']['totales']['total_debe']:,.2f}")
                print(f"   - Total HABER: ${reporte['reporte']['totales']['total_haber']:,.2f}")
                print(f"   - Fecha extracción: {reporte['metadata']['fecha_extraccion']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en consultas: {str(e)}")
        return False
    finally:
        try:
            mongo_client.disconnect()
        except:
            pass

def test_collection_stats():
    """Prueba las estadísticas de la colección."""
    print("\n" + "=" * 60)
    print("📈 ESTADÍSTICAS DE LA COLECCIÓN")
    print("=" * 60)
    
    try:
        mongo_client = NuboxMongoClient()
        
        stats = mongo_client.get_collection_stats()
        
        if stats:
            print("📊 Estadísticas generales:")
            print(f"   - Total reportes: {stats.get('total_reportes', 0)}")
            print(f"   - Total movimientos: {stats.get('total_movimientos', 0)}")
            print(f"   - Empresas únicas: {stats.get('empresas_unicas', 0)}")
            print(f"   - Total DEBE: ${stats.get('total_debe', 0):,.2f}")
            print(f"   - Total HABER: ${stats.get('total_haber', 0):,.2f}")
            
            if stats.get('primera_extraccion'):
                print(f"   - Primera extracción: {stats['primera_extraccion']}")
            if stats.get('ultima_extraccion'):
                print(f"   - Última extracción: {stats['ultima_extraccion']}")
        else:
            print("⚠️ No se pudieron obtener estadísticas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {str(e)}")
        return False
    finally:
        try:
            mongo_client.disconnect()
        except:
            pass

def main():
    """Función principal que ejecuta todas las pruebas."""
    print("🧪 INICIANDO PRUEBAS DE INTEGRACIÓN MONGODB + NUBOX RPA")
    print(f"🕒 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Conexión
    connection_ok = test_mongodb_connection()
    
    if not connection_ok:
        print("\n❌ Las pruebas no pueden continuar sin conexión a MongoDB")
        return
    
    # Test 2: Exportación
    document_id = test_export_sample_data()
    
    # Test 3: Consultas
    query_ok = test_query_data(document_id)
    
    # Test 4: Estadísticas
    stats_ok = test_collection_stats()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    tests = [
        ("Conexión MongoDB", connection_ok),
        ("Exportación de datos", document_id is not None),
        ("Consultas", query_ok),
        ("Estadísticas", stats_ok)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ El sistema MongoDB está listo para la integración con Nubox RPA")
        print("🚀 Ahora puedes ejecutar el flujo completo en Streamlit")
    else:
        print(f"\n⚠️ {total - passed} pruebas fallaron")
        print("❌ Revisa la configuración de MongoDB antes de continuar")

if __name__ == "__main__":
    main()