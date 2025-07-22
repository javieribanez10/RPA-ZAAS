# RPA Nubox Report Extractor

Automatización avanzada para la extracción de reportes contables desde Nubox utilizando Python, Selenium y una interfaz web moderna con Streamlit.

## Descripción

Este proyecto implementa un RPA (Robotic Process Automation) de última generación que automatiza completamente la extracción de reportes contables desde la plataforma Nubox. El sistema incluye una interfaz web moderna, procesamiento múltiple de reportes, y exportación automática a MongoDB.

## 🚀 Características Principales

### Automatización Core
- ✅ Login automático en Nubox con manejo robusto de errores
- ✅ Navegación inteligente a través de la interfaz web
- ✅ Configuración automática de filtros (fechas, empresa, cuenta, etc.)
- ✅ Extracción de datos en formato de tabla con validación
- ✅ Soporte para diferentes tipos de reportes (mayor, balance, etc.)
- ✅ Manejo robusto de errores y recuperación automática

### Nuevas Funcionalidades Avanzadas
- 🎯 **Selección Múltiple de Empresas**: Procesa reportes para múltiples empresas automáticamente
- 🎯 **Selección Múltiple de Cuentas**: Genera reportes para múltiples cuentas contables
- 🎯 **Procesamiento Combinado**: Genera reportes para cada combinación empresa-cuenta
- 🎯 **Interfaz Web Moderna**: Interfaz Streamlit amigable y fácil de usar
- 🎯 **Exportación a MongoDB**: Almacenamiento automático de reportes en base de datos
- 🎯 **Análisis HTML-Excel**: Parser avanzado para archivos Excel-HTML de Nubox
- 🎯 **Progreso en Tiempo Real**: Monitoreo visual del proceso de extracción

### Formatos de Salida
- 📊 CSV (Comma Separated Values)
- 📊 Excel (.xlsx)
- 📊 JSON (JavaScript Object Notation)
- 📊 MongoDB (Base de datos NoSQL)
- 📊 HTML-Excel (Formato nativo de Nubox)

## 🛠️ Arquitectura del Sistema

### Componentes Principales

```
RPA/
├── streamlit_app.py           # 🌐 Interfaz web principal con Streamlit
├── main.py                    # 🚀 Punto de entrada para ejecución por consola
├── config/                    # ⚙️ Configuración del proyecto
│   ├── config.json           # 📋 Configuración en formato JSON
│   └── settings.py           # 🔧 Manejo de configuración
├── services/                  # 🔥 Servicios especializados (Arquitectura Modular)
│   ├── nubox_service.py      # 🎯 Servicio principal de Nubox
│   ├── mongodb_client.py     # 🗄️ Cliente para MongoDB
│   └── components/           # 🧩 Componentes especializados
│       ├── browser_manager.py     # 🌐 Gestión del navegador
│       ├── authentication.py     # 🔐 Autenticación
│       ├── navigation.py         # 🧭 Navegación
│       ├── parameter_config.py   # ⚙️ Configuración de parámetros
│       ├── report_extractor.py   # 📊 Extracción de reportes
│       └── ui_elements.py        # 🎨 Elementos de interfaz
├── utils/                     # 🛠️ Utilidades
│   ├── logger.py             # 📝 Sistema de logging avanzado
│   └── file_handler.py       # 📁 Manejo de archivos
├── logs/                      # 📋 Archivos de registro y capturas
├── output/                    # 📊 Reportes generados
└── backup/                    # 💾 Respaldos del sistema
```

## 📦 Instalación y Configuración

### Requisitos del Sistema
- **Python**: 3.8 o superior
- **Chrome/Chromium**: Última versión
- **ChromeDriver**: Compatible con la versión del navegador
- **MongoDB**: (Opcional) Para almacenamiento de reportes

### Librerías Python Requeridas

```bash
# Librerías principales
selenium>=4.0.0
streamlit>=1.28.0
pandas>=2.0.0
beautifulsoup4>=4.12.0

# Manejo de datos
openpyxl>=3.1.0
xlrd>=2.0.0
pymongo>=4.0.0

# Interfaz y utilidades
requests>=2.25.0
python-dotenv>=1.0.0
```

### Instalación Paso a Paso

1. **Clonar o descargar el proyecto**
```bash
git clone <repository-url>
cd RPA
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate     # En Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
# Crear archivo .env
touch .env

# Agregar credenciales (opcional para consola)
echo "NUBOX_USERNAME=tu_usuario" >> .env
echo "NUBOX_PASSWORD=tu_contraseña" >> .env
```

## 🚀 Modos de Uso

### 1. Interfaz Web con Streamlit (Recomendado)

**Iniciar la aplicación web:**
```bash
streamlit run streamlit_app.py
```

**Funcionalidades disponibles:**
- 🎯 **Selección Múltiple de Empresas**: Checkbox para activar y multiselect para elegir empresas
- 🎯 **Selección Múltiple de Cuentas**: Checkbox para activar y multiselect para elegir cuentas
- 📊 **Cálculo Automático**: Muestra total de reportes a generar (empresas × cuentas)
- 📈 **Progreso en Tiempo Real**: Barras de progreso y logs detallados
- 📊 **Resultados Organizados**: Tabs por empresa con sub-tabs por cuenta
- 💾 **Exportación Automática**: A MongoDB y descarga en CSV/Excel
- 🎨 **Interfaz Amigable**: Configuración visual de todos los parámetros

**Flujo de trabajo:**
1. 🔐 Ingresa credenciales de Nubox
2. 🚀 Inicia proceso (login y navegación)
3. 🏢 Selecciona empresas (una o múltiples)
4. 💰 Selecciona cuentas contables (una o múltiples)
5. 📅 Configura fechas y otros parámetros
6. 📊 Extrae reportes automáticamente
7. 📋 Revisa resultados organizados por empresa

### 2. Línea de Comandos (Avanzado)

```bash
# Ejecución básica
python main.py

# Con parámetros específicos
python main.py --headless --timeout 60
```

## ⚙️ Configuración Avanzada

### Archivo de Configuración (config/config.json)

```json
{
  "NUBOX_URL": "https://web.nubox.com/Login/Account/Login?ReturnUrl=%2FSistemaLogin",
  "HEADLESS": true,
  "TIMEOUT": 30,
  "REPORT_TYPE": "mayor",
  "OUTPUT_FORMAT": "excel",
  "MONGODB_CONFIG": {
    "enabled": true,
    "connection_string": "mongodb://localhost:27017/",
    "database": "nubox-data",
    "collection": "reportes"
  },
  "REPORT_PARAMS": {
    "fecha_inicio": "01-01-2025",
    "fecha_fin": "01-02-2025",
    "formato": "excel",
    "tipo_reporte": "ANALISIS POR CUENTA",
    "incluir_subcuentas": false
  }
}
```

### Parámetros Disponibles

#### Configuración General
- **NUBOX_URL**: URL de inicio de sesión de Nubox
- **HEADLESS**: Ejecutar navegador sin interfaz gráfica
- **TIMEOUT**: Tiempo máximo de espera (segundos)
- **REPORT_TYPE**: Tipo de reporte a extraer

#### Configuración de Reportes
- **fecha_inicio/fin**: Rango de fechas del reporte
- **empresa**: Empresa específica o "multiple" para varias
- **cuenta**: Cuenta específica o "multiple" para varias
- **formato**: Formato de salida del reporte
- **tipo_reporte**: Tipo específico de análisis
- **incluir_subcuentas**: Incluir subcuentas en el reporte

#### Configuración MongoDB
- **enabled**: Activar/desactivar exportación a MongoDB
- **connection_string**: Cadena de conexión a MongoDB
- **database**: Nombre de la base de datos
- **collection**: Nombre de la colección

## 🎯 Funcionalidades Avanzadas

### Procesamiento Múltiple

**Ejemplo: 3 empresas × 2 cuentas = 6 reportes**
```
Empresas seleccionadas:
1. VERSE CONSULTORES LTDA
2. COMERCIALIZADORA INSERT S.A.
3. SELYT SPA

Cuentas seleccionadas:
1. 1101-01 CUENTA CAJA
2. 5101-01 VENTAS POR SERVICIO

Reportes generados: 6 combinaciones automáticamente
```

### Navegación Inteligente

El sistema optimiza la navegación según el tipo de cambio:
- **Entre cuentas de la misma empresa**: Solo clic en "Mayor" (rápido)
- **Entre empresas diferentes**: Navegación completa (robusta)

### Manejo de Errores

- ✅ **Recuperación automática** de errores de navegación
- ✅ **Validación de archivos** descargados (HTML-Excel vs errores)
- ✅ **Continuación del proceso** aunque fallen algunos reportes
- ✅ **Logging detallado** para diagnóstico
- ✅ **Capturas de pantalla** automáticas para debugging

### Exportación a MongoDB

Cada reporte se almacena con metadatos completos:
```json
{
  "_id": "ObjectId(...)",
  "empresa": "COMERCIALIZADORA INSERT S.A.",
  "cuenta_contable": "5101-01 VENTAS POR SERVICIO",
  "fecha_extraccion": "2025-07-22T15:49:46.123Z",
  "parametros": {
    "fecha_desde": "01/01/2025",
    "fecha_hasta": "01/02/2025",
    "formato_salida": "EXCEL"
  },
  "datos_contables": [...],
  "informacion_empresa": {
    "nombre": "COMERCIALIZADORA INSERT S.A.",
    "rut": "76.129.903-4",
    "representante_legal": "PAULO ALEJANDRO SUBIABRE CEPEDA"
  }
}
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### Error de Navegación
```
❌ No se pudo hacer clic en el módulo de Contabilidad
```
**Solución**: 
- Verificar que la sesión de Nubox esté activa
- Revisar capturas en `/logs/` para ver el estado actual
- Intentar con `HEADLESS: false` para ver la navegación

#### Archivo Excel Inválido
```
🚨 El archivo contiene HTML genérico en lugar de datos Excel
```
**Solución**:
- Verificar parámetros del reporte
- Comprobar que la cuenta contable tenga movimientos
- Reducir el rango de fechas

#### Error de MongoDB
```
❌ Cliente MongoDB no disponible
```
**Solución**:
```bash
pip install pymongo
# o
pip install -r requirements.txt
```

### Logs y Debugging

**Ubicación de logs**: `/logs/`
- `*.png`: Capturas de pantalla del proceso
- Logs en consola con timestamp y nivel de detalle

**Activar debugging**:
```python
# En config/config.json
{
  "HEADLESS": false,
  "DEBUG": true,
  "SCREENSHOT_ON_ERROR": true
}
```

## 📊 Rendimiento y Escalabilidad

### Tiempos de Procesamiento
- **Una combinación**: ~2-3 minutos
- **Múltiples combinaciones**: ~2-3 minutos por combinación
- **Optimización**: Navegación inteligente reduce tiempo entre cuentas

### Limitaciones
- **Recomendado**: Máximo 10 combinaciones por sesión
- **Tiempo de sesión**: Nubox expira sesiones después de inactividad
- **Rate limiting**: Pausas automáticas entre extracciones

## 🔮 Próximas Mejoras

- [ ] **Programación de extracciones**: Ejecución automática en horarios específicos
- [ ] **API REST**: Endpoints para integración con otros sistemas
- [ ] **Dashboard de reportes**: Visualización web de datos extraídos
- [ ] **Notificaciones**: Email/Slack al completar extracciones
- [ ] **Plantillas personalizadas**: Formatos de salida configurables

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## 🤝 Soporte y Contacto

- **Desarrollado por**: ZAAS
- **Soporte técnico**: Disponible para consultas e implementación
- **Documentación**: README.md y comentarios en código
- **Issues**: Reportar problemas en el repositorio del proyecto

---

## 🎉 Changelog

### v2.0.0 (Julio 2025)
- ✨ **Nueva funcionalidad**: Selección múltiple de empresas y cuentas
- ✨ **Interfaz Streamlit**: Interfaz web moderna y amigable
- ✨ **Exportación MongoDB**: Almacenamiento automático en base de datos
- ✨ **Parser HTML-Excel**: Soporte nativo para archivos de Nubox
- ✨ **Navegación inteligente**: Optimización según tipo de cambio
- ✨ **Arquitectura modular**: Componentes especializados y reutilizables

### v1.0.0 (Anterior)
- 🎯 Funcionalidad básica de extracción
- 🎯 Login y navegación manual
- 🎯 Exportación CSV/Excel básica