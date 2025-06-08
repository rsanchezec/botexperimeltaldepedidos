"""
Nodos de inicio y análisis inicial del bot de pedidos
"""
from models.state import GraphState, StepType, ConversationMode
from services.order_service import order_service
from .base_node import BaseNode, ConditionalNode

class StartNode(BaseNode):
    """Nodo inicial del bot"""
    
    def __init__(self):
        super().__init__("inicio")
    
    def execute(self, state: GraphState) -> GraphState:
        """Ejecuta la inicialización sin mostrar mensaje"""
        self.set_step(state, StepType.INICIO, waiting_for_input=True)
        return state

class InitialAnalysisNode(BaseNode):
    """Nodo que analiza el primer mensaje del usuario"""
    
    def __init__(self):
        super().__init__("analizar_mensaje_inicial")
    
    def execute(self, state: GraphState) -> GraphState:
        """Analiza el primer mensaje y determina el modo de conversación"""
        user_message = self.get_last_user_message(state)
        
        if not user_message:
            self.set_step(state, StepType.INICIO, waiting_for_input=True)
            return state
        
        # Procesar el mensaje inicial usando el servicio de pedidos
        updated_state, result_type = order_service.procesar_mensaje_inicial(user_message, state)
        
        # Actualizar el estado con el resultado
        state.update(updated_state)
        
        # Manejar el resultado según el tipo
        if result_type == "guided_mode_requested":
            return self._handle_guided_mode_request(state)
        elif result_type == "complete_order":
            return self._handle_complete_order(state)
        elif result_type == "partial_order_extracted":
            return self._handle_partial_order(state)
        elif result_type == "no_order_detected":
            return self._handle_no_order_detected(state)
        else:
            # Caso por defecto - modo guiado
            return self._handle_guided_mode_request(state)
    
    def _handle_guided_mode_request(self, state: GraphState) -> GraphState:
        """Maneja cuando el usuario solicita modo guiado"""
        state["modo_conversacion"] = ConversationMode.GUIDED
        # No agregamos mensaje aquí, el siguiente nodo lo hará
        self.set_step(state, "preguntar_categoria")
        return state
    
    def _handle_complete_order(self, state: GraphState) -> GraphState:
        """Maneja cuando se detecta un pedido completo"""
        self.set_step(state, "mostrar_resumen")
        return state
    
    def _handle_partial_order(self, state: GraphState) -> GraphState:
        """Maneja cuando se extrae información parcial del pedido"""
        # Mostrar lo que se entendió
        resumen = order_service.generar_resumen_parcial(state)
        self.add_message(state, resumen)
        
        # Determinar qué preguntar a continuación
        siguiente_campo = order_service.obtener_siguiente_campo_faltante(state)
        next_step = self._determinar_siguiente_paso(siguiente_campo)
        
        # Si el siguiente paso es para preguntar algo, configurar waiting_for_input=False
        # para que continúe el flujo y ejecute el nodo de pregunta
        self.set_step(state, next_step, waiting_for_input=False)
        
        return state
    
    def _handle_no_order_detected(self, state: GraphState) -> GraphState:
        """Maneja cuando no se detecta información de pedido"""
        message = "No pude entender completamente tu pedido. Te guiaré paso a paso para completarlo. 😊"
        self.add_message(state, message)
        self.set_step(state, "preguntar_categoria")
        return state
    
    def _determinar_siguiente_paso(self, campo_faltante: str) -> str:
        """Determina el siguiente paso basado en el campo faltante"""
        if not campo_faltante:
            return "mostrar_resumen"
        
        if "categoria" in campo_faltante:
            return "preguntar_categoria"
        elif "presentacion" in campo_faltante:
            return "preguntar_presentacion"
        elif "tipo_producto" in campo_faltante:
            return "preguntar_tipo_producto"
        elif "cantidad" in campo_faltante:
            return "preguntar_cantidad"
        elif "tipo_descargue" in campo_faltante:
            return "preguntar_tipo_descargue"
        elif "tipo_entrega" in campo_faltante:
            return "preguntar_tipo_entrega"
        else:
            return "mostrar_resumen"

class NextStepDeterminer(ConditionalNode):
    """Nodo que determina el siguiente paso en el flujo"""
    
    def __init__(self):
        super().__init__("determinar_siguiente_paso")
    
    def determine_next_step(self, state: GraphState) -> str:
        """Determina el siguiente paso basado en el estado actual"""
        current_step = state["current_step"]
        
        # Mapeo de pasos de espera a pasos de procesamiento
        processing_steps = {
            StepType.ESPERANDO_CATEGORIA: "procesar_categoria",
            StepType.ESPERANDO_PRESENTACION: "procesar_presentacion",
            StepType.ESPERANDO_TIPO_PRODUCTO: "procesar_tipo_producto",
            StepType.ESPERANDO_CANTIDAD: "procesar_cantidad",
            StepType.ESPERANDO_MAS_PRODUCTOS: "procesar_mas_productos",
            StepType.ESPERANDO_TIPO_DESCARGUE: "procesar_tipo_descargue",
            StepType.ESPERANDO_TIPO_ENTREGA: "procesar_tipo_entrega",
            StepType.ESPERANDO_CONFIRMACION_MODIFICAR: "procesar_confirmacion_modificar",
            StepType.ESPERANDO_PRODUCTO_MODIFICAR: "procesar_producto_modificar",
            StepType.ESPERANDO_QUE_MODIFICAR: "procesar_que_modificar",
            StepType.ESPERANDO_NUEVA_PRESENTACION: "procesar_nueva_presentacion",
            StepType.ESPERANDO_NUEVO_TIPO: "procesar_nuevo_tipo",
            StepType.ESPERANDO_NUEVA_CANTIDAD: "procesar_nueva_cantidad"
        }
        
        # Si estamos esperando una respuesta específica
        if current_step in processing_steps:
            return processing_steps[current_step]
        
        # Si estamos en modo natural, verificar información faltante
        if state.get("modo_conversacion") == ConversationMode.NATURAL:
            faltante = state.get("informacion_faltante", [])
            if not faltante:
                return "mostrar_resumen"
            
            # Determinar qué preguntar basado en lo que falta
            siguiente_campo = order_service.obtener_siguiente_campo_faltante(state)
            return self._mapear_campo_a_paso(siguiente_campo)
        
        # Flujo por defecto
        if current_step == StepType.INICIO:
            return "analizar_mensaje_inicial"
        
        return "END"
    
    def _mapear_campo_a_paso(self, campo: str) -> str:
        """Mapea un campo faltante a un paso de pregunta"""
        if not campo:
            return "mostrar_resumen"
        
        mapeo = {
            "categoria": "preguntar_categoria",
            "presentacion": "preguntar_presentacion",
            "tipo_producto": "preguntar_tipo_producto",
            "cantidad": "preguntar_cantidad",
            "tipo_descargue": "preguntar_tipo_descargue",
            "tipo_entrega": "preguntar_tipo_entrega"
        }
        
        for clave, paso in mapeo.items():
            if clave in campo:
                return paso
        
        return "mostrar_resumen"

class ConversationResetNode(BaseNode):
    """Nodo para reiniciar la conversación"""
    
    def __init__(self):
        super().__init__("reset_conversation")
    
    def execute(self, state: GraphState) -> GraphState:
        """Reinicia la conversación manteniendo el historial"""
        # Limpiar datos del pedido pero mantener mensajes
        state["pedidos"] = []
        state["pedido_actual"] = {
            "categoria": "",
            "presentacion": "",
            "tipo_producto": "",
            "cantidad": 0,
            "unidad": ""
        }
        state["categoria_actual"] = ""
        state["tipo_descargue"] = ""
        state["tipo_entrega"] = ""
        state["informacion_faltante"] = []
        state["producto_modificando"] = None
        state["modificando_campo"] = None
        state["modo_conversacion"] = ""
        state["pedido_guardado_id"] = None
        
        # Enviar mensaje de reinicio
        reset_message = "🔄 **Nueva conversación iniciada**\n\n¿En qué puedo ayudarte con tu nuevo pedido?"
        self.add_message(state, reset_message)
        
        # Volver al inicio
        self.set_step(state, StepType.INICIO, waiting_for_input=True)
        
        return state

# Factory para crear nodos de inicio
class StartNodesFactory:
    """Factory para crear nodos de inicio"""
    
    @staticmethod
    def create_start_node() -> StartNode:
        return StartNode()
    
    @staticmethod
    def create_analysis_node() -> InitialAnalysisNode:
        return InitialAnalysisNode()
    
    @staticmethod
    def create_step_determiner() -> NextStepDeterminer:
        return NextStepDeterminer()
    
    @staticmethod
    def create_reset_node() -> ConversationResetNode:
        return ConversationResetNode()

# Crear instancias globales
start_node = StartNodesFactory.create_start_node()
analysis_node = StartNodesFactory.create_analysis_node()
step_determiner = StartNodesFactory.create_step_determiner()
reset_node = StartNodesFactory.create_reset_node()