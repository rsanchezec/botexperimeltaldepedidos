# Sistema de Pedidos Inteligente

# 🏗️ Bot de Pedidos 

## Descripción

Bot inteligente para la gestión de pedidos de productos de construcción con procesamiento de lenguaje natural (NLP), desarrollado con LangGraph y OpenAI. Permite a los usuarios realizar pedidos de forma natural o guiada, con validación automática y almacenamiento en base de datos SQL Server.

## ✨ Características Principales

### 🧠 Inteligencia Artificial
- **Procesamiento de Lenguaje Natural**: Los usuarios pueden describir su pedido completo en una sola frase
- **Extracción Automática de Información**: El bot identifica productos, cantidades, tipos y condiciones de entrega
- **Modo Dual**: Natural (recomendado) y Guiado paso a paso
- **Validación Inteligente**: Verificación automática de datos y reglas de negocio

### 📦 Gestión de Productos
- **Categorías**: Ensacado y Granel
- **Tipos de Producto**: Blanco y Gris  
- **Presentaciones**: 50 Kg, 45 Kg, 20 Kg (para productos ensacados)
- **Unidades**: Sacos y Toneladas
- **Múltiples Productos**: Soporte para pedidos con varios artículos

### 🚚 Opciones de Entrega
- **Métodos de Entrega**: A domicilio o Retiro en punto de distribución
- **Métodos de Descargue**: Manual o Mecanizado
- **Validación de Compatibilidad**: Verificación automática de combinaciones permitidas

### 💾 Persistencia de Datos
- **Base de Datos SQL Server**: Almacenamiento estructurado de pedidos
- **Historial de Conversaciones**: Registro completo de interacciones
- **Identificadores Únicos de Pedido**: Generación automática
- **Estadísticas del Sistema**: Informes de uso y métricas operativas

### 🎨 Interfaz de Usuario
- **Gradio Web Interface**: Interfaz moderna y responsiva
- **Chat Intuitivo**: Interacción natural con el bot
- **Panel de Estadísticas**: Visualización de datos clave
- **Modo Debug**: Información técnica para desarrollo

