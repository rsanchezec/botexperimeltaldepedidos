"""
Modelo de negocio para pedidos de cemento
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from .state import PedidoItem, GraphState

@dataclass
class PedidoResumen:
    """Clase para generar resúmenes de pedidos"""
    productos: List[PedidoItem]
    tipo_descargue: str
    tipo_entrega: str
    total_sacos: int = 0
    total_toneladas: float = 0.0
    fecha_creacion: datetime = None
    
    def __post_init__(self):
        if self.fecha_creacion is None:
            self.fecha_creacion = datetime.now()
        self._calcular_totales()
    
    def _calcular_totales(self):
        """Calcula los totales de sacos y toneladas"""
        self.total_sacos = sum(
            p['cantidad'] for p in self.productos 
            if p['categoria'] == 'Ensacado'
        )
        self.total_toneladas = sum(
            p['cantidad'] for p in self.productos 
            if p['categoria'] == 'Granel'
        )
    
    def generar_resumen_texto(self, incluir_header: bool = True) -> str:
        """Genera un resumen en texto del pedido"""
        if incluir_header:
            resumen = "📋 **RESUMEN DE TU PEDIDO**\n"
            resumen += f"📅 Fecha: {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\n\n"
        else:
            resumen = ""
        
        resumen += f"📦 **Productos ({len(self.productos)} producto(s)):**\n"
        resumen += "=" * 40 + "\n\n"
        
        for i, producto in enumerate(self.productos, 1):
            resumen += f"**📌 Producto {i}:**\n"
            resumen += f"   • Categoría: {producto['categoria']}\n"
            if producto['categoria'] == "Ensacado":
                resumen += f"   • Presentación: {producto['presentacion']}\n"
            resumen += f"   • Tipo: Cemento {producto['tipo_producto']}\n"
            resumen += f"   • Cantidad: {producto['cantidad']} {producto['unidad']}\n\n"
        
        resumen += "=" * 40 + "\n"
        resumen += f"🚚 **Tipo de descargue:** {self.tipo_descargue}\n"
        resumen += f"📍 **Tipo de entrega:** {self.tipo_entrega}\n\n"
        
        if self.total_sacos > 0:
            resumen += f"📊 **Total sacos:** {self.total_sacos}\n"
        if self.total_toneladas > 0:
            resumen += f"📊 **Total toneladas:** {self.total_toneladas}\n"
        
        return resumen
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resumen a diccionario"""
        return {
            "productos": self.productos,
            "tipo_descargue": self.tipo_descargue,
            "tipo_entrega": self.tipo_entrega,
            "total_sacos": self.total_sacos,
            "total_toneladas": self.total_toneladas,
            "fecha_creacion": self.fecha_creacion.isoformat()
        }

class PedidoValidator:
    """Clase para validar pedidos"""
    
    @staticmethod
    def validar_producto(producto: PedidoItem) -> List[str]:
        """Valida un producto individual y retorna lista de errores"""
        errores = []
        
        if not producto.get('categoria'):
            errores.append("Falta la categoría del producto")
        elif producto['categoria'] not in ['Ensacado', 'Granel']:
            errores.append("Categoría inválida")
        
        if producto.get('categoria') == 'Ensacado' and not producto.get('presentacion'):
            errores.append("Falta la presentación para producto ensacado")
        
        if not producto.get('tipo_producto'):
            errores.append("Falta el tipo de producto")
        elif producto['tipo_producto'] not in ['Blanco', 'Gris']:
            errores.append("Tipo de producto inválido")
        
        if not producto.get('cantidad') or producto['cantidad'] <= 0:
            errores.append("Cantidad debe ser mayor a 0")
        
        if not producto.get('unidad'):
            errores.append("Falta la unidad")
        
        return errores
    
    @staticmethod
    def validar_pedido_completo(state: GraphState) -> List[str]:
        """Valida un pedido completo y retorna lista de errores"""
        errores = []
        
        if not state.get('pedidos'):
            errores.append("El pedido debe tener al menos un producto")
        else:
            for i, producto in enumerate(state['pedidos'], 1):
                errores_producto = PedidoValidator.validar_producto(producto)
                for error in errores_producto:
                    errores.append(f"Producto {i}: {error}")
        
        if not state.get('tipo_descargue'):
            errores.append("Falta el tipo de descargue")
        elif state['tipo_descargue'] not in ['Manual', 'Mecanizado']:
            errores.append("Tipo de descargue inválido")
        
        if not state.get('tipo_entrega'):
            errores.append("Falta el tipo de entrega")
        elif state['tipo_entrega'] not in ['Entrega', 'Retira']:
            errores.append("Tipo de entrega inválido")
        
        return errores

class PedidoAnalyzer:
    """Clase para analizar y procesar información de pedidos"""
    
    @staticmethod
    def identificar_informacion_faltante(state: GraphState) -> List[str]:
        """Identifica qué información falta en el pedido"""
        faltante = []
        
        if not state["pedidos"]:
            faltante.append("productos")
        else:
            for i, pedido in enumerate(state["pedidos"]):
                if not pedido.get("categoria"):
                    faltante.append(f"categoria_producto_{i+1}")
                elif pedido["categoria"] == "Ensacado" and not pedido.get("presentacion"):
                    faltante.append(f"presentacion_producto_{i+1}")
                if not pedido.get("tipo_producto"):
                    faltante.append(f"tipo_producto_{i+1}")
                if not pedido.get("cantidad") or pedido.get("cantidad") == 0:
                    faltante.append(f"cantidad_producto_{i+1}")
        
        if not state["tipo_descargue"]:
            faltante.append("tipo_descargue")
        if not state["tipo_entrega"]:
            faltante.append("tipo_entrega")
        
        return faltante
    
    @staticmethod
    def crear_resumen_desde_state(state: GraphState) -> PedidoResumen:
        """Crea un objeto PedidoResumen desde el estado del grafo"""
        return PedidoResumen(
            productos=state["pedidos"],
            tipo_descargue=state["tipo_descargue"],
            tipo_entrega=state["tipo_entrega"]
        )
    
    @staticmethod
    def generar_lista_productos_para_modificar(productos: List[PedidoItem]) -> str:
        """Genera una lista formateada de productos para mostrar al usuario"""
        mensaje = ""
        for i, pedido in enumerate(productos, 1):
            mensaje += f"**{i}.** {pedido['cantidad']} {pedido['unidad']} de cemento {pedido['tipo_producto']}"
            if pedido['categoria'] == "Ensacado":
                mensaje += f" ({pedido['presentacion']})"
            mensaje += "\n"
        return mensaje
    
    @staticmethod
    def es_pedido_valido(state: GraphState) -> bool:
        """Verifica si el pedido es válido para ser guardado"""
        errores = PedidoValidator.validar_pedido_completo(state)
        return len(errores) == 0

def crear_pedido_desde_state(state: GraphState) -> PedidoResumen:
    """Función de utilidad para crear un pedido desde el estado"""
    return PedidoAnalyzer.crear_resumen_desde_state(state)

def validar_estado_pedido(state: GraphState) -> tuple[bool, List[str]]:
    """Función de utilidad para validar el estado del pedido"""
    errores = PedidoValidator.validar_pedido_completo(state)
    return len(errores) == 0, errores