#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para la extracción de datos de reportes Excel.
Prueba específicamente el archivo descargado para validar la funcionalidad.
"""

import os
import sys
import pandas as pd
import time
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from services.components.report_extractor import ReportExtractorService
from utils.logger import setup_logger

def test_file_validation(file_path):
    """
    Prueba la validación de archivos Excel.
    """
    print("=" * 60)
    print("🔍 PRUEBA 1: VALIDACIÓN DE ARCHIVO")
    print("=" * 60)
    
    # Crear instancia simulada del extractor para usar sus métodos de validación
    class MockBrowser:
        def take_screenshot(self, name):
            pass
        def find_elements(self, by, selector):
            return []
    
    extractor = ReportExtractorService(MockBrowser())
    
    # Información básica del archivo
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"📁 Archivo encontrado: {os.path.basename(file_path)}")
        print(f"📏 Tamaño: {file_size} bytes ({file_size/1024:.2f} KB)")
        
        # Probar validación
        is_valid = extractor._validate_excel_file(file_path)
        print(f"✅ Validación: {'VÁLIDO' if is_valid else 'INVÁLIDO'}")
        
        # Leer primeros bytes para análisis
        try:
            with open(file_path, 'rb') as f:
                header_bytes = f.read(100)
                header_text = header_bytes.decode('utf-8', errors='ignore')
                print(f"🔍 Primeros 100 bytes (como texto): {header_text[:50]}...")
                print(f"🔍 Primeros 20 bytes (como hex): {header_bytes[:20].hex()}")
        except Exception as e:
            print(f"❌ Error leyendo header: {e}")
        
        return is_valid
    else:
        print(f"❌ Archivo no encontrado: {file_path}")
        return False

def test_excel_reading(file_path):
    """
    Prueba la lectura del archivo Excel con diferentes métodos.
    """
    print("\n" + "=" * 60)
    print("📖 PRUEBA 2: LECTURA DE EXCEL")
    print("=" * 60)
    
    # Crear instancia del extractor
    class MockBrowser:
        def take_screenshot(self, name):
            pass
        def find_elements(self, by, selector):
            return []
    
    extractor = ReportExtractorService(MockBrowser())
    
    # Probar lectura con el método del extractor
    print("🔄 Intentando leer con método del extractor...")
    df, result_path = extractor._read_excel_file(file_path)
    
    if not df.empty:
        print(f"✅ ÉXITO: DataFrame creado")
        print(f"📊 Filas: {len(df)}")
        print(f"📋 Columnas: {len(df.columns)}")
        print(f"🏷️ Nombres de columnas: {list(df.columns)}")
        
        # Mostrar tipos de datos
        print("\n📈 Tipos de datos:")
        for col, dtype in df.dtypes.items():
            print(f"  - {col}: {dtype}")
        
        # Mostrar primeras filas
        print(f"\n👀 Primeras 5 filas:")
        print(df.head().to_string())
        
        return df
    else:
        print(f"❌ FALLO: No se pudo crear DataFrame")
        print(f"📁 Path retornado: {result_path}")
        return None

def test_manual_reading(file_path):
    """
    Prueba lectura manual con diferentes engines y configuraciones.
    """
    print("\n" + "=" * 60)
    print("🛠️ PRUEBA 3: LECTURA MANUAL CON DIFERENTES ENGINES")
    print("=" * 60)
    
    engines = ['xlrd', 'openpyxl']
    successful_reads = []
    
    for engine in engines:
        print(f"\n🔧 Probando engine: {engine}")
        try:
            df = pd.read_excel(file_path, engine=engine)
            print(f"✅ ÉXITO con {engine}")
            print(f"📊 Filas: {len(df)}, Columnas: {len(df.columns)}")
            successful_reads.append((engine, df))
            
            # Mostrar info básica
            if not df.empty:
                print(f"🏷️ Columnas: {list(df.columns)[:5]}...")  # Solo primeras 5
                
        except Exception as e:
            print(f"❌ FALLO con {engine}: {str(e)}")
    
    return successful_reads

def test_csv_reading(file_path):
    """
    Prueba si el archivo se puede leer como CSV.
    """
    print("\n" + "=" * 60)
    print("📄 PRUEBA 4: LECTURA COMO CSV")
    print("=" * 60)
    
    encodings = ['utf-8', 'latin-1', 'cp1252']
    separators = [',', ';', '\t']
    
    for encoding in encodings:
        for sep in separators:
            try:
                print(f"🔄 Probando encoding: {encoding}, separador: '{sep}'")
                df = pd.read_csv(file_path, encoding=encoding, separator=sep)
                
                if not df.empty and len(df.columns) > 1:
                    print(f"✅ ÉXITO como CSV")
                    print(f"📊 Filas: {len(df)}, Columnas: {len(df.columns)}")
                    print(f"🏷️ Columnas: {list(df.columns)[:3]}...")
                    return df
                    
            except Exception as e:
                print(f"❌ Fallo: {str(e)[:50]}...")
    
    print("❌ No se pudo leer como CSV")
    return None

def test_content_analysis(file_path):
    """
    Analiza el contenido del archivo para diagnóstico.
    """
    print("\n" + "=" * 60)
    print("🔍 PRUEBA 5: ANÁLISIS DE CONTENIDO")
    print("=" * 60)
    
    try:
        # Leer como texto
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text_content = f.read(1000)  # Primeros 1000 caracteres
        
        print("📝 Contenido como texto:")
        print(text_content[:300] + "..." if len(text_content) > 300 else text_content)
        
        # Detectar tipo de contenido
        if '<html' in text_content.lower():
            print("🌐 DETECTADO: Contenido HTML")
        elif 'error' in text_content.lower():
            print("🚫 DETECTADO: Mensaje de error")
        elif any(word in text_content.lower() for word in ['session', 'timeout', 'expired']):
            print("⏰ DETECTADO: Problema de sesión")
        else:
            print("❓ DETECTADO: Contenido desconocido")
        
        # Leer como binario para análisis de firma
        with open(file_path, 'rb') as f:
            binary_content = f.read(50)
        
        print(f"\n🔍 Firma binaria (primeros 50 bytes):")
        print(f"Hex: {binary_content.hex()}")
        print(f"ASCII: {binary_content.decode('ascii', errors='ignore')}")
        
        # Verificar firmas conocidas
        excel_signatures = {
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': 'Excel 97-2003 (OLE2)',
            b'PK\x03\x04': 'Excel 2007+ (ZIP)',
            b'<html': 'HTML',
            b'<!DOCTYPE': 'HTML DOCTYPE'
        }
        
        detected_format = "Desconocido"
        for signature, format_name in excel_signatures.items():
            if binary_content.startswith(signature):
                detected_format = format_name
                break
        
        print(f"📋 Formato detectado: {detected_format}")
        
    except Exception as e:
        print(f"❌ Error analizando contenido: {e}")

def main():
    """
    Función principal que ejecuta todas las pruebas.
    """
    print("🧪 INICIANDO PRUEBAS DE EXTRACCIÓN DE DATOS")
    print("🕒 Fecha:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Configurar logging
    logger = setup_logger()
    
    # Ruta del archivo a probar
    file_path = "/Users/javie/Downloads/LIBRO MAYOR DESDE 01_01_2025 A 01_02_2025.xls"
    
    print(f"📁 Archivo de prueba: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Archivo no encontrado en {file_path}")
        return
    
    # Ejecutar todas las pruebas
    try:
        # Prueba 1: Validación
        is_valid = test_file_validation(file_path)
        
        # Prueba 2: Lectura con extractor
        df_extractor = test_excel_reading(file_path)
        
        # Prueba 3: Lectura manual
        manual_results = test_manual_reading(file_path)
        
        # Prueba 4: Como CSV
        df_csv = test_csv_reading(file_path)
        
        # Prueba 5: Análisis de contenido
        test_content_analysis(file_path)
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📋 RESUMEN DE RESULTADOS")
        print("=" * 60)
        
        print(f"🔍 Validación: {'✅ VÁLIDO' if is_valid else '❌ INVÁLIDO'}")
        print(f"📖 Extractor RPA: {'✅ ÉXITO' if df_extractor is not None else '❌ FALLO'}")
        print(f"🛠️ Lectura manual: {len(manual_results)} engines exitosos")
        print(f"📄 Como CSV: {'✅ ÉXITO' if df_csv is not None else '❌ FALLO'}")
        
        # Mostrar mejor resultado
        if df_extractor is not None:
            print(f"\n🏆 MEJOR RESULTADO (Extractor RPA):")
            print(f"📊 {len(df_extractor)} filas, {len(df_extractor.columns)} columnas")
            print(f"🏷️ Columnas: {list(df_extractor.columns)}")
        elif manual_results:
            engine, df = manual_results[0]
            print(f"\n🏆 MEJOR RESULTADO (Engine {engine}):")
            print(f"📊 {len(df)} filas, {len(df.columns)} columnas")
            print(f"🏷️ Columnas: {list(df.columns)}")
        elif df_csv is not None:
            print(f"\n🏆 MEJOR RESULTADO (CSV):")
            print(f"📊 {len(df_csv)} filas, {len(df_csv.columns)} columnas")
        else:
            print(f"\n❌ NO SE PUDO LEER EL ARCHIVO CON NINGÚN MÉTODO")
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()