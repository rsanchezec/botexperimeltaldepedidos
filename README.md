# Cementos Argos

# 🏗️ Bot de Pedidos Cementos Argos - Arturo V3

## Descripción

Bot inteligente para la gestión de pedidos de cemento con procesamiento de lenguaje natural (NLP), desarrollado con LangGraph y OpenAI. Permite a los usuarios realizar pedidos de forma natural o guiada, con validación automática y almacenamiento en base de datos SQL Server.

## ✨ Características Principales

### 🧠 Inteligencia Artificial
- **Procesamiento de Lenguaje Natural**: Los usuarios pueden describir su pedido completo en una sola frase
- **Extracción Automática de Información**: El bot identifica productos, cantidades, tipos y condiciones de entrega
- **Modo Dual**: Natural (recomendado) y Guiado paso a paso
- **Validación Inteligente**: Verificación automática de datos y reglas de negocio

### 📦 Gestión de Productos
- **Categorías**: Ensacado y Granel
- **Tipos**: Cemento Blanco y Gris  
- **Presentaciones**: 50 Kg, 45 Kg, 20 Kg (para ensacado)
- **Unidades**: Sacos y Toneladas
- **Múltiples Productos**: Soporte para pedidos con varios productos

### 🚚 Opciones de Entrega
- **Tipos de Entrega**: Entrega a domicilio o Retiro en planta
- **Tipos de Descargue**: Manual o Mecanizado
- **Validación de Compatibilidad**: Verificación automática de opciones

### 💾 Persistencia de Datos
- **Base de Datos SQL Server**: Almacenamiento completo de pedidos
- **Historial de Conversaciones**: Registro de todas las interacciones
- **Números de Pedido Únicos**: Identificación automática
- **Estadísticas del Sistema**: Métricas y reportes

### 🎨 Interfaz de Usuario
- **Gradio Web Interface**: Interfaz moderna y responsiva
- **Chat Intuitivo**: Conversación natural con el bot
- **Panel de Estadísticas**: Visualización de datos del sistema
- **Modo Debug**: Información técnica para desarrollo

## 🏗️ Arquitectura del Proyecto

```
cemento_bot/
├── main.py                           # Punto de entrada principal
├── requirements.txt                  # Dependencias
├── README.md                        # Documentación
├── .env                            # Variables de entorno
├── config/
│   ├── __init__.py
│   ├── database.py                 # Configuración de BD
│   └── settings.py                 # Configuraciones generales
├── models/
│   ├── __init__.py
│   ├── state.py                   # Estados del grafo
│   └── pedido.py                  # Modelos de negocio
├── services/
│   ├── __init__.py
│   ├── database_service.py        # Operaciones de BD
│   ├── llm_service.py            # Servicios de IA
│   └── order_service.py          # Lógica de pedidos
├── controllers/
│   ├── __init__.py
│   ├── conversation_controller.py # Control de conversación
│   └── graph_controller.py       # Control del grafo
├── nodes/
│   ├── __init__.py
│   ├── base_node.py              # Clases base
│   ├── start_nodes.py            # Nodos de inicio
│   ├── product_nodes.py          # Nodos de productos
│   ├── delivery_nodes.py         # Nodos de entrega
│   ├── summary_nodes.py          # Nodos de resumen
│   └── modification_nodes.py     # Nodos de modificación
├── utils/
│   ├── __init__.py
│   ├── helpers.py                # Funciones auxiliares
│   └── validators.py             # Validadores
└── ui/
    ├── __init__.py
    └── gradio_interface.py       # Interfaz web
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.8+
- SQL Server (local o remoto)
- API Key de OpenAI
- Git

### Instalación

1. **Clonar el repositorio**
```bash
git clone 
cd cemento_bot
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
```

Editar `.env` con tus configuraciones:
```env
# OpenAI
OPENAI_API_KEY=tu-api-key-aqui

# Base de Datos
DB_SERVER=tu_servidor
DB_DATABASE=PedidosCemento
DB_USERNAME=tu_usuario
DB_PASSWORD=tu_password

# Aplicación
APP_DEBUG=True
APP_SHARE=False
```

5. **Inicializar base de datos**
```bash
python -c "from config.database import initialize_database; initialize_database()"
```

### Ejecución

```bash
python main.py
```

La aplicación estará disponible en: `http://localhost:7860`

## 📋 Uso del Sistema

### Modo Natural (Recomendado)

Describe tu pedido completo en lenguaje natural:

```
"Quiero 50 sacos de cemento gris de 50 kg con entrega a domicilio y descarga manual"

"Mi pedido es: 30 toneladas de cemento blanco a granel para retirar"

"Necesito 100 sacos de cemento blanco de 45 kg y 20 toneladas de granel gris"
```

### Modo Guiado

Responde "ayuda" o "paso a paso" para que el bot te guíe:

1. Categoría del producto
2. Presentación (si es ensacado)
3. Tipo de cemento
4. Cantidad
5. Tipo de descargue
6. Tipo de entrega

### Comandos Especiales

- `nuevo pedido` - Inicia un pedido nuevo
- `ayuda` - Muestra información de ayuda
- `estadisticas` - Muestra estadísticas del sistema

## 🔧 Desarrollo

### Estructura de Clases

#### Servicios Principales
- **OrderService**: Lógica de negocio para pedidos
- **LLMService**: Interacción con OpenAI
- **DatabaseService**: Operaciones de base de datos

#### Controladores
- **ConversationController**: Gestión de conversaciones
- **GraphController**: Control del grafo de estados

#### Nodos del Grafo
- **BaseNode**: Clase base para todos los nodos
- **QuestionNode**: Nodos que hacen preguntas
- **ProcessingNode**: Nodos que procesan respuestas

### Agregar Nuevas Funcionalidades

1. **Nuevo Tipo de Producto**:
   - Actualizar `VALID_CEMENT_TYPES` en `settings.py`
   - Modificar validadores en `validators.py`

2. **Nueva Presentación**:
   - Actualizar `VALID_PRESENTATIONS` en `settings.py`
   - Ajustar lógica en nodos de productos

3. **Nuevo Nodo**:
   - Heredar de `BaseNode`, `QuestionNode` o `ProcessingNode`
   - Implementar método `execute()`
   - Registrar en el grafo

### Testing

```bash
# Ejecutar tests (cuando estén implementados)
pytest tests/

# Validar configuración
python -c "from config.settings import settings; print(settings.validate_settings())"

# Probar conexión a BD
python -c "from config.database import DatabaseManager; print(DatabaseManager.test_connection())"
```

## 📊 Base de Datos

### Estructura de Tablas

#### Pedidos
```sql
CREATE TABLE Pedidos (
    PedidoID INT IDENTITY(1,1) PRIMARY KEY,
    FechaPedido DATETIME DEFAULT GETDATE(),
    TipoDescargue VARCHAR(20) NOT NULL,
    TipoEntrega VARCHAR(20) NOT NULL,
    Estado VARCHAR(20) DEFAULT 'Confirmado',
    TotalSacos INT DEFAULT 0,
    TotalToneladas DECIMAL(10,2) DEFAULT 0,
    UsuarioID VARCHAR(100),
    Observaciones TEXT
)
```

#### DetallePedidos
```sql
CREATE TABLE DetallePedidos (
    DetalleID INT IDENTITY(1,1) PRIMARY KEY,
    PedidoID INT NOT NULL,
    Categoria VARCHAR(20) NOT NULL,
    Presentacion VARCHAR(20),
    TipoProducto VARCHAR(20) NOT NULL,
    Cantidad DECIMAL(10,2) NOT NULL,
    Unidad VARCHAR(20) NOT NULL,
    FOREIGN KEY (PedidoID) REFERENCES Pedidos(PedidoID)
)
```

#### LogConversaciones
```sql
CREATE TABLE LogConversaciones (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    PedidoID INT,
    FechaHora DATETIME DEFAULT GETDATE(),
    Mensaje TEXT,
    TipoMensaje VARCHAR(10),
    FOREIGN KEY (PedidoID) REFERENCES Pedidos(PedidoID)
)
```

## 🔒 Seguridad

- **Validación de Entrada**: Sanitización de todos los inputs del usuario
- **SQL Injection Prevention**: Uso de parámetros preparados
- **Rate Limiting**: Control de solicitudes (implementar según necesidad)
- **Variables de Entorno**: Configuraciones sensibles en archivos .env

## 📈 Monitoreo y Logs

- **Logs de Aplicación**: Registro de errores y eventos importantes
- **Métricas de Uso**: Estadísticas de pedidos y conversaciones
- **Estado del Sistema**: Monitoreo de base de datos y servicios externos

## 🚀 Despliegue

### Desarrollo Local
```bash
python main.py
```

### Producción
1. Configurar servidor web (nginx/Apache)
2. Usar gunicorn o similar para WSGI
3. Configurar base de datos de producción
4. Establecer variables de entorno seguras
5. Configurar logs y monitoreo

### Docker (Opcional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Changelog

### v3.0.0 (Actual)
- ✅ Arquitectura modular con clases
- ✅ Procesamiento de lenguaje natural
- ✅ Modo dual (natural/guiado)
- ✅ Base de datos SQL Server
- ✅ Interfaz Gradio mejorada
- ✅ Validación inteligente
- ✅ Sistema de estadísticas

### v2.0.0 (Anterior)
- Versión monolítica funcional
- Bot guiado paso a paso
- Funcionalidades básicas

## 🆘 Soporte

Para reportar bugs o solicitar nuevas características:

1. Revisar issues existentes
2. Crear nuevo issue con plantilla
3. Incluir logs y contexto relevante

## 📄 Licencia

Este proyecto es propiedad de Cementos Argos. Todos los derechos reservados.

## 👥 Equipo

- **Desarrollo**: Equipo de Innovación Digital
- **Producto**: Departamento de Ventas
- **Soporte**: IT Cementos Argos

---

**¡Gracias por usar el Bot de Pedidos Cementos Argos! 🏗️**
