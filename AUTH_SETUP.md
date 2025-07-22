# 🔐 DB Viewer con Autenticación Supabase

Sistema de login integrado para el visualizador de base de datos MongoDB del proyecto RPA Nubox.

## 📋 Características

- ✅ Autenticación completa con Supabase
- ✅ Registro de nuevos usuarios
- ✅ Login/Logout seguro
- ✅ Recuperación de contraseña
- ✅ Sesiones persistentes
- ✅ Interfaz moderna y responsive
- ✅ Protección de rutas
- ✅ Integración con MongoDB viewer existente

## 🚀 Configuración Inicial

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Supabase

1. Ve a tu proyecto en Supabase: `https://mlgxjlygckkhqzggtdqp.supabase.co`
2. Obtén las claves API:
   - Ve a **Settings > API**
   - Copia el `Project URL` y `anon public key`

### 3. Configurar variables de entorno

Edita el archivo `.env` con tus credenciales reales:

```env
# Supabase configuration
SUPABASE_URL=https://mlgxjlygckkhqzggtdqp.supabase.co
SUPABASE_ANON_KEY=tu_clave_anon_real_aqui
SUPABASE_SERVICE_KEY=tu_clave_service_real_aqui

# MongoDB configuration (existing)
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE=nubox-data
```

### 4. Configurar autenticación en Supabase

En el dashboard de Supabase:

1. Ve a **Authentication > Settings**
2. Configura los providers que desees
3. Ajusta las configuraciones de email (opcional)
4. Habilita confirmación de email si es necesario

## 🎯 Uso del Sistema

### Ejecutar la aplicación autenticada

```bash
streamlit run mongodb_viewer_auth.py
```

### Funcionalidades disponibles

1. **🔑 Login**: Acceso con email/contraseña
2. **👤 Registro**: Crear nueva cuenta
3. **🔄 Recuperación**: Reset de contraseña por email
4. **📊 Dashboard**: Vista completa del DB viewer
5. **🚪 Logout**: Cierre de sesión seguro

## 📁 Estructura del Proyecto

```
RPA/
├── mongodb_viewer_auth.py          # Viewer con autenticación
├── services/
│   └── supabase_auth.py           # Cliente Supabase
├── ui/
│   └── auth_components.py         # Componentes de UI
├── .env                           # Variables de entorno
└── requirements.txt               # Dependencias actualizadas
```

## 🔧 Personalización

### Modificar diseño del login

Edita `ui/auth_components.py`:
- Cambia colores en los gradientes CSS
- Modifica textos y mensajes
- Ajusta validaciones

### Agregar más campos al registro

En `services/supabase_auth.py`:
- Modifica `register_user()` para incluir más campos
- Actualiza la metadata del usuario

### Configurar roles y permisos

En Supabase dashboard:
1. Ve a **Authentication > Users**
2. Configura roles personalizados
3. Implementa RLS (Row Level Security)

## 🛡️ Seguridad

- ✅ Autenticación JWT con Supabase
- ✅ Sesiones seguras
- ✅ Validación de inputs
- ✅ Protección CSRF
- ✅ Variables de entorno para claves

## 🐛 Troubleshooting

### Error: "Configuración de Supabase no encontrada"
- Verifica que el archivo `.env` existe
- Confirma que las variables `SUPABASE_URL` y `SUPABASE_ANON_KEY` están configuradas

### Error: "Error conectando a Supabase"
- Verifica que la URL de Supabase es correcta
- Confirma que la clave anon es válida
- Revisa la conexión a internet

### Login no funciona
- Verifica que el usuario existe en Supabase
- Confirma que el email está verificado (si está habilitado)
- Revisa los logs de Supabase para errores

## 📞 Soporte

Para problemas o consultas:
1. Revisa los logs de Streamlit
2. Verifica los logs de Supabase
3. Confirma la configuración de variables de entorno