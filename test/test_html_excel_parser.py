#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba específico para el nuevo parser HTML-Excel.
Prueba la funcionalidad de extracción de datos de archivos HTML-Excel de Nubox.
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

def test_html_excel_parser():
    """
    Prueba específica del parser HTML-Excel mejorado.
    """
    print("=" * 70)
    print("🧪 PRUEBA DEL NUEVO PARSER HTML-EXCEL")
    print("=" * 70)
    
    # Configurar logging
    logger = setup_logger()
    
    # Ruta del archivo a probar
    file_path = "/Users/javie/Downloads/LIBRO MAYOR DESDE 01_01_2025 A 01_02_2025.xls"
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Archivo no encontrado en {file_path}")
        return None
    
    # Crear instancia del extractor
    class MockBrowser:
        def take_screenshot(self, name):
            pass
        def find_elements(self, by, selector):
            return []
    
    extractor = ReportExtractorService(MockBrowser())
    
    try:
        print(f"📁 Probando archivo: {os.path.basename(file_path)}")
        print(f"📏 Tamaño: {os.path.getsize(file_path)} bytes")
        
        # Paso 1: Verificar si es HTML-Excel
        print("\n🔍 PASO 1: Verificando formato HTML-Excel...")
        is_html_excel = extractor._is_html_excel_format(file_path)
        print(f"✅ Es HTML-Excel: {'SÍ' if is_html_excel else 'NO'}")
        
        if not is_html_excel:
            print("❌ El archivo no parece ser HTML-Excel de Microsoft Office")
            return None
        
        # Paso 2: Parsear con el nuevo método
        print("\n📋 PASO 2: Parseando datos HTML-Excel...")
        df, result_path = extractor._parse_html_excel(file_path)
        
        if df is not None and not df.empty:
            print(f"✅ ÉXITO: DataFrame creado exitosamente")
            print(f"📊 Filas: {len(df)}")
            print(f"📋 Columnas: {len(df.columns)}")
            print(f"🏷️ Nombres de columnas: {list(df.columns)}")
            
            # Mostrar información de la empresa si está disponible
            if hasattr(df, 'attrs') and 'company_info' in df.attrs:
                company_info = df.attrs['company_info']
                if company_info:
                    print(f"\n🏢 INFORMACIÓN DE EMPRESA:")
                    for key, value in company_info.items():
                        print(f"  - {key}: {value}")
            
            # Mostrar tipos de datos
            print(f"\n📈 TIPOS DE DATOS:")
            for col, dtype in df.dtypes.items():
                print(f"  - {col}: {dtype}")
            
            # Mostrar muestra de datos
            print(f"\n👀 MUESTRA DE DATOS (primeras 5 filas):")
            try:
                print(df.head().to_string(max_cols=8, max_colwidth=20))
            except Exception as e:
                print(f"Error mostrando datos: {e}")
                
            # Estadísticas básicas para columnas numéricas
            numeric_columns = df.select_dtypes(include=['number']).columns
            if len(numeric_columns) > 0:
                print(f"\n📊 ESTADÍSTICAS NUMÉRICAS:")
                try:
                    stats = df[numeric_columns].describe()
                    print(stats.to_string())
                except Exception as e:
                    print(f"Error calculando estadísticas: {e}")
            
            # Verificar datos específicos contables
            print(f"\n🔍 ANÁLISIS CONTABLE:")
            
            # Verificar si hay fechas válidas
            if 'FECHA' in df.columns:
                valid_dates = df['FECHA'].notna().sum()
                print(f"  - Fechas válidas: {valid_dates}/{len(df)}")
            
            # Verificar columnas monetarias
            monetary_cols = ['DEBE', 'HABER', 'SALDO']
            for col in monetary_cols:
                if col in df.columns:
                    non_zero = (df[col] != 0).sum()
                    total_amount = df[col].sum() if df[col].dtype in ['float64', 'int64'] else 'N/A'
                    print(f"  - {col}: {non_zero} entradas no-cero, Total: {total_amount}")
            
            return df
            
        else:
            print(f"❌ FALLO: No se pudo crear DataFrame")
            print(f"📁 Resultado: {result_path}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_integration_with_extractor():
    """
    Prueba la integración completa con el método _read_excel_file.
    """
    print("\n" + "=" * 70)
    print("🔗 PRUEBA DE INTEGRACIÓN CON EXTRACTOR")
    print("=" * 70)
    
    file_path = "/Users/javie/Downloads/LIBRO MAYOR DESDE 01_01_2025 A 01_02_2025.xls"
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Archivo no encontrado")
        return None
    
    # Crear instancia del extractor
    class MockBrowser:
        def take_screenshot(self, name):
            pass
        def find_elements(self, by, selector):
            return []
    
    extractor = ReportExtractorService(MockBrowser())
    
    try:
        print("🔄 Probando método _read_excel_file completo...")
        
        # Este método ahora debería detectar automáticamente que es HTML-Excel
        df, result_path = extractor._read_excel_file(file_path)
        
        if df is not None and not df.empty:
            print(f"✅ INTEGRACIÓN EXITOSA")
            print(f"📊 Datos extraídos: {len(df)} filas, {len(df.columns)} columnas")
            print(f"📁 Archivo procesado: {os.path.basename(result_path)}")
            
            # Mostrar resumen de columnas
            print(f"\n📋 RESUMEN DE COLUMNAS:")
            for i, col in enumerate(df.columns, 1):
                non_empty = df[col].notna().sum()
                print(f"  {i}. {col}: {non_empty} valores")
            
            return df
        else:
            print(f"❌ INTEGRACIÓN FALLIDA")
            print(f"📁 Resultado: {result_path}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR EN INTEGRACIÓN: {str(e)}")
        return None

def save_test_results(df):
    """
    Guarda los resultados de la prueba en archivos para verificación.
    """
    if df is None or df.empty:
        print("⚠️ No hay datos para guardar")
        return
    
    print("\n" + "=" * 70)
    print("💾 GUARDANDO RESULTADOS DE PRUEBA")
    print("=" * 70)
    
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Guardar como CSV
        csv_path = f"test_results_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"✅ CSV guardado: {csv_path}")
        
        # Guardar como Excel
        excel_path = f"test_results_{timestamp}.xlsx"
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"✅ Excel guardado: {excel_path}")
        
        # Crear reporte de resumen
        summary_path = f"test_summary_{timestamp}.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("REPORTE DE PRUEBA - PARSER HTML-EXCEL\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Fecha de prueba: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Archivo fuente: LIBRO MAYOR DESDE 01_01_2025 A 01_02_2025.xls\n\n")
            
            f.write(f"RESULTADOS:\n")
            f.write(f"- Filas extraídas: {len(df)}\n")
            f.write(f"- Columnas extraídas: {len(df.columns)}\n")
            f.write(f"- Columnas: {', '.join(df.columns)}\n\n")
            
            # Información de la empresa
            if hasattr(df, 'attrs') and 'company_info' in df.attrs:
                f.write(f"INFORMACIÓN DE EMPRESA:\n")
                for key, value in df.attrs['company_info'].items():
                    f.write(f"- {key}: {value}\n")
                f.write("\n")
            
            # Estadísticas básicas
            f.write(f"ESTADÍSTICAS BÁSICAS:\n")
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                f.write(f"- {col}: min={df[col].min()}, max={df[col].max()}, sum={df[col].sum()}\n")
        
        print(f"✅ Resumen guardado: {summary_path}")
        
    except Exception as e:
        print(f"❌ Error guardando resultados: {str(e)}")

def main():
    """
    Función principal que ejecuta todas las pruebas del parser HTML-Excel.
    """
    print("🧪 INICIANDO PRUEBAS DEL PARSER HTML-EXCEL MEJORADO")
    print("🕒 Fecha:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Prueba 1: Parser específico
    df1 = test_html_excel_parser()
    
    # Prueba 2: Integración completa
    df2 = test_integration_with_extractor()
    
    # Usar el DataFrame de la integración para el resumen
    result_df = df2 if df2 is not None else df1
    
    # Guardar resultados
    if result_df is not None:
        save_test_results(result_df)
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📋 RESUMEN FINAL")
    print("=" * 70)
    
    if result_df is not None:
        print("🎉 ¡PRUEBAS EXITOSAS!")
        print(f"✅ Parser HTML-Excel funcionando correctamente")
        print(f"✅ Se extrajeron {len(result_df)} filas de datos contables")
        print(f"✅ Se identificaron {len(result_df.columns)} columnas")
        print(f"✅ El sistema puede ahora procesar archivos HTML-Excel de Nubox")
        
        # Mostrar información clave
        if 'FECHA' in result_df.columns:
            date_range = f"{result_df['FECHA'].min()} a {result_df['FECHA'].max()}"
            print(f"📅 Rango de fechas: {date_range}")
        
        monetary_cols = ['DEBE', 'HABER', 'SALDO']
        for col in monetary_cols:
            if col in result_df.columns and result_df[col].dtype in ['float64', 'int64']:
                total = result_df[col].sum()
                print(f"💰 Total {col}: {total:,.2f}")
    else:
        print("❌ PRUEBAS FALLIDAS")
        print("❌ El parser HTML-Excel necesita ajustes")
        print("❌ Revisar logs para detalles del error")

if __name__ == "__main__":
    main()