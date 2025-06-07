"""
Servicio para el procesamiento y gestión de pedidos
"""
from typing import Dict, Any, List, Optional, Tuple
from models.state import GraphState, PedidoItem, create_pedido_item
from models.pedido import PedidoAnalyzer, PedidoValidator, PedidoResumen
from services.llm_service import llm_service
from services.database_service import DatabaseService

class OrderService:
    """Servicio para la gestión completa de pedidos"""
    
    @staticmethod
    def procesar_mensaje_inicial(mensaje: str, state: GraphState) -> Tuple[GraphState, str]:
        """Procesa el mensaje inicial del usuario y actualiza el estado"""
        
        # Verificar si el usuario quiere modo guiado
        if any(palabra in mensaje.lower() for palabra in ["paso a paso", "guiar", "ayuda", "no sé", "no se"]):
            state["modo_conversacion"] = "guiado"
            return state, "guided_mode_requested"
        
        # Intentar extraer información del pedido usando LLM
        info_extraida = llm_service.extraer_informacion_pedido(mensaje)
        
        if info_extraida.get("pedidos"):
            state["modo_conversacion"] = "natural"
            
            # Procesar los pedidos extraídos
            for pedido_info in info_extraida["pedidos"]:
                pedido = OrderService._crear_pedido_desde_extraccion(pedido_info)
                if OrderService._es_pedido_valido_parcial(pedido):
                    state["pedidos"].append(pedido)
            
            # Asignar tipo de descargue y entrega si se proporcionaron
            if info_extraida.get("tipo_descargue"):
                state["tipo_descargue"] = info_extraida["tipo_descargue"]
            if info_extraida.get("tipo_entrega"):
                state["tipo_entrega"] = info_extraida["tipo_entrega"]
            
            # Identificar qué información falta
            state["informacion_faltante"] = PedidoAnalyzer.identificar_informacion_faltante(state)
            
            if not state["informacion_faltante"]:
                return state, "complete_order"
            else:
                return state, "partial_order_extracted"
        else:
            # No se pudo extraer información, cambiar a modo guiado
            state["modo_conversacion"] = "guiado"
            return state, "no_order_detected"
    
    @staticmethod
    def _crear_pedido_desde_extraccion(pedido_info: Dict[str, Any]) -> PedidoItem:
        """Crea un PedidoItem desde la información extraída por el LLM"""
        pedido = create_pedido_item(
            categoria=pedido_info.get("categoria", ""),
            presentacion=pedido_info.get("presentacion", ""),
            tipo_producto=pedido_info.get("tipo_producto", ""),
            cantidad=pedido_info.get("cantidad", 0),
            unidad=pedido_info.get("unidad", "")
        )
        
        # Normalizar datos según categoría
        if pedido["categoria"] == "Ensacado":
            pedido["unidad"] = "sacos"
        elif pedido["categoria"] == "Granel":
            pedido["unidad"] = "toneladas"
            pedido["presentacion"] = ""  # Granel no tiene presentación
        
        return pedido
    
    @staticmethod
    def _es_pedido_valido_parcial(pedido: PedidoItem) -> bool:
        """Verifica si un pedido tiene información mínima válida"""
        return (pedido.get("categoria") and 
                pedido.get("cantidad", 0) > 0 and 
                pedido.get("unidad"))
    
    @staticmethod
    def agregar_producto_al_pedido(state: GraphState, producto: PedidoItem) -> GraphState:
        """Agrega un producto al pedido actual"""
        if OrderService._es_pedido_valido_parcial(producto):
            state["pedidos"].append(producto)
            state["informacion_faltante"] = PedidoAnalyzer.identificar_informacion_faltante(state)
        return state
    
    @staticmethod
    def actualizar_producto_en_pedido(state: GraphState, indice: int, campo: str, valor: Any) -> GraphState:
        """Actualiza un campo específico de un producto en el pedido"""
        if 0 <= indice < len(state["pedidos"]):
            state["pedidos"][indice][campo] = valor
            
            # Recalcular información faltante
            state["informacion_faltante"] = PedidoAnalyzer.identificar_informacion_faltante(state)
        
        return state
    
    @staticmethod
    def eliminar_producto_del_pedido(state: GraphState, indice: int) -> GraphState:
        """Elimina un producto del pedido"""
        if 0 <= indice < len(state["pedidos"]):
            state["pedidos"].pop(indice)
            state["informacion_faltante"] = PedidoAnalyzer.identificar_informacion_faltante(state)
        
        return state
    
    @staticmethod
    def validar_pedido_completo(state: GraphState) -> Tuple[bool, List[str]]:
        """Valida si el pedido está completo y listo para guardar"""
        errores = PedidoValidator.validar_pedido_completo(state)
        return len(errores) == 0, errores
    
    @staticmethod
    def generar_resumen_pedido(state: GraphState, incluir_header: bool = True) -> str:
        """Genera un resumen formateado del pedido"""
        resumen_obj = PedidoAnalyzer.crear_resumen_desde_state(state)
        return resumen_obj.generar_resumen_texto(incluir_header)
    
    @staticmethod
    def generar_resumen_parcial(state: GraphState) -> str:
        """Genera un resumen de lo que se ha entendido hasta ahora"""
        resumen = "✅ **Entendí lo siguiente de tu pedido:**\n\n"
        
        for i, pedido in enumerate(state["pedidos"], 1):
            resumen += f"**Producto {i}:**\n"
            if pedido.get("categoria"):
                resumen += f"• Categoría: {pedido['categoria']}\n"
            if pedido.get("presentacion") and pedido["categoria"] == "Ensacado":
                resumen += f"• Presentación: {pedido['presentacion']}\n"
            if pedido.get("tipo_producto"):
                resumen += f"• Tipo: {pedido['tipo_producto']}\n"
            if pedido.get("cantidad") and pedido["cantidad"] > 0:
                resumen += f"• Cantidad: {pedido['cantidad']} {pedido['unidad']}\n"
            resumen += "\n"
        
        if state.get("tipo_descargue"):
            resumen += f"🚚 Tipo de descargue: {state['tipo_descargue']}\n"
        if state.get("tipo_entrega"):
            resumen += f"📍 Tipo de entrega: {state['tipo_entrega']}\n"
        
        resumen += "\n**Necesito algunos datos adicionales para completar tu pedido.**"
        return resumen
    
    @staticmethod
    def guardar_pedido_confirmado(state: GraphState, usuario_id: str = None) -> Dict[str, Any]:
        """Guarda el pedido confirmado en la base de datos"""
        # Validar antes de guardar
        es_valido, errores = OrderService.validar_pedido_completo(state)
        
        if not es_valido:
            return {
                "success": False,
                "error": f"Pedido inválido: {'; '.join(errores)}"
            }
        
        # Guardar en base de datos
        resultado = DatabaseService.guardar_pedido(state, usuario_id)
        
        # Actualizar estado con el ID del pedido si fue exitoso
        if resultado.get("success"):
            state["pedido_guardado_id"] = resultado["pedido_id"]
        
        return resultado
    
    @staticmethod
    def obtener_siguiente_campo_faltante(state: GraphState) -> Optional[str]:
        """Determina cuál es el siguiente campo que se debe preguntar"""
        faltante = state.get("informacion_faltante", [])
        
        if not faltante:
            return None
        
        # Priorizar en orden lógico
        prioridades = [
            "categoria",
            "presentacion", 
            "tipo_producto",
            "cantidad",
            "tipo_descargue",
            "tipo_entrega"
        ]
        
        for prioridad in prioridades:
            for campo in faltante:
                if prioridad in campo:
                    return campo
        
        return faltante[0] if faltante else None
    
    @staticmethod
    def procesar_respuesta_modificacion(state: GraphState, respuesta: str, campo: str) -> Tuple[bool, str]:
        """Procesa una respuesta del usuario para modificar un campo específico"""
        
        # Usar el LLM para validar la respuesta
        validacion = llm_service.validar_entrada_usuario(respuesta, campo)
        
        if validacion["valido"]:
            indice = state.get("producto_modificando")
            if indice is not None and 0 <= indice < len(state["pedidos"]):
                state["pedidos"][indice][campo] = validacion["valor"]
                return True, "Campo actualizado exitosamente"
        
        return False, validacion.get("mensaje", "Respuesta inválida")
    
    @staticmethod
    def calcular_totales_pedido(state: GraphState) -> Dict[str, float]:
        """Calcula los totales del pedido"""
        total_sacos = sum(
            p['cantidad'] for p in state['pedidos'] 
            if p['categoria'] == 'Ensacado'
        )
        total_toneladas = sum(
            p['cantidad'] for p in state['pedidos'] 
            if p['categoria'] == 'Granel'
        )
        
        return {
            "total_sacos": total_sacos,
            "total_toneladas": total_toneladas,
            "total_productos": len(state['pedidos'])
        }
    
    @staticmethod
    def obtener_estadisticas_sistema() -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de pedidos"""
        return DatabaseService.obtener_estadisticas()
    
    @staticmethod
    def buscar_pedidos_usuario(usuario_id: str, limite: int = 10) -> List[Dict[str, Any]]:
        """Busca los pedidos recientes de un usuario"""
        filtros = {"usuario_id": usuario_id}
        return DatabaseService.buscar_pedidos(filtros, limite)

# Crear instancia global del servicio
order_service = OrderService()