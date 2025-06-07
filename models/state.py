"""
Definiciones de modelos de estado para el bot de pedidos
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import operator

class PedidoItem(TypedDict):
    """Modelo para un item individual del pedido"""
    categoria: str          # "Ensacado" o "Granel"
    presentacion: str       # "50 Kg", "45 Kg", "20 Kg" (solo para Ensacado)
    tipo_producto: str      # "Blanco" o "Gris"
    cantidad: float         # Cantidad numérica
    unidad: str            # "sacos" o "toneladas"

class GraphState(TypedDict):
    """Estado principal del grafo de conversación"""
    # Historial de mensajes
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Control de flujo
    current_step: str                    # Paso actual en el flujo
    waiting_for_input: bool             # Si está esperando entrada del usuario
    modo_conversacion: str              # "natural" o "guiado"
    
    # Datos del pedido
    pedidos: List[PedidoItem]           # Lista de productos en el pedido
    pedido_actual: Dict[str, Any]       # Producto que se está construyendo
    categoria_actual: str               # Categoría del producto actual
    
    # Configuración de entrega
    tipo_descargue: str                 # "Manual" o "Mecanizado"
    tipo_entrega: str                   # "Entrega" o "Retira"
    
    # Control de información
    informacion_faltante: List[str]     # Lista de campos que faltan
    
    # Modificación de pedidos
    producto_modificando: Optional[int]  # Índice del producto siendo modificado
    modificando_campo: Optional[str]     # Campo que se está modificando
    
    # Información de sesión
    usuario_id: Optional[str]           # ID del usuario
    pedido_guardado_id: Optional[int]   # ID del pedido guardado en DB

class ConversationMode:
    """Constantes para los modos de conversación"""
    NATURAL = "natural"
    GUIDED = "guiado"

class StepType:
    """Constantes para los tipos de pasos"""
    # Pasos de inicio
    INICIO = "inicio"
    ANALIZAR_MENSAJE_INICIAL = "analizar_mensaje_inicial"
    
    # Pasos de productos
    ESPERANDO_CATEGORIA = "esperando_categoria"
    ESPERANDO_PRESENTACION = "esperando_presentacion"
    ESPERANDO_TIPO_PRODUCTO = "esperando_tipo_producto"
    ESPERANDO_CANTIDAD = "esperando_cantidad"
    ESPERANDO_MAS_PRODUCTOS = "esperando_mas_productos"
    
    # Pasos de entrega
    ESPERANDO_TIPO_DESCARGUE = "esperando_tipo_descargue"
    ESPERANDO_TIPO_ENTREGA = "esperando_tipo_entrega"
    
    # Pasos de modificación
    ESPERANDO_CONFIRMACION_MODIFICAR = "esperando_confirmacion_modificar"
    ESPERANDO_QUE_ELEMENTO_MODIFICAR = "esperando_que_elemento_modificar"
    ESPERANDO_PRODUCTO_MODIFICAR = "esperando_producto_modificar"
    ESPERANDO_QUE_MODIFICAR = "esperando_que_modificar"
    ESPERANDO_NUEVA_PRESENTACION = "esperando_nueva_presentacion"
    ESPERANDO_NUEVO_TIPO = "esperando_nuevo_tipo"
    ESPERANDO_NUEVA_CANTIDAD = "esperando_nueva_cantidad"
    ESPERANDO_NUEVO_DESCARGUE = "esperando_nuevo_descargue"
    ESPERANDO_NUEVA_ENTREGA = "esperando_nueva_entrega"
    
    # Pasos finales
    FIN = "fin"

class ProductCategories:
    """Constantes para categorías de productos"""
    ENSACADO = "Ensacado"
    GRANEL = "Granel"

class CementTypes:
    """Constantes para tipos de cemento"""
    BLANCO = "Blanco"
    GRIS = "Gris"

class DeliveryTypes:
    """Constantes para tipos de entrega"""
    ENTREGA = "Entrega"
    RETIRA = "Retira"

class DischargeTypes:
    """Constantes para tipos de descargue"""
    MANUAL = "Manual"
    MECANIZADO = "Mecanizado"

class MessageTypes:
    """Constantes para tipos de mensajes"""
    USUARIO = "Usuario"
    BOT = "Bot"

def get_initial_state() -> GraphState:
    """Retorna el estado inicial para una nueva conversación"""
    return {
        "messages": [],
        "current_step": "",
        "waiting_for_input": False,
        "modo_conversacion": "",
        "pedidos": [],
        "pedido_actual": {
            "categoria": "",
            "presentacion": "",
            "tipo_producto": "",
            "cantidad": 0,
            "unidad": ""
        },
        "categoria_actual": "",
        "tipo_descargue": "",
        "tipo_entrega": "",
        "informacion_faltante": [],
        "producto_modificando": None,
        "modificando_campo": None,
        "usuario_id": None,
        "pedido_guardado_id": None
    }

def create_pedido_item(categoria: str = "", presentacion: str = "", 
                      tipo_producto: str = "", cantidad: float = 0, 
                      unidad: str = "") -> PedidoItem:
    """Factory function para crear un PedidoItem"""
    return {
        "categoria": categoria,
        "presentacion": presentacion,
        "tipo_producto": tipo_producto,
        "cantidad": cantidad,
        "unidad": unidad
    }