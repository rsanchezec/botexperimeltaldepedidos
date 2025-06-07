"""
Nodos para el manejo de entrega y descargue en el bot de pedidos
"""
from models.state import GraphState, StepType, DeliveryTypes, DischargeTypes
from services.order_service import order_service
from .base_node import QuestionNode, ProcessingNode

class DischargeTypeQuestionNode(QuestionNode):
    """Nodo para preguntar el tipo de descargue"""
    
    def __init__(self):
        question = "🚚 **¿Qué tipo de descargue prefieres?**\n\n• Manual\n• Mecanizado\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_tipo_descargue", question, StepType.ESPERANDO_TIPO_DESCARGUE)

class DischargeTypeProcessingNode(ProcessingNode):
    """Nodo para procesar la respuesta de tipo de descargue"""
    
    def __init__(self):
        valid_responses = ["manual", "mecanizado"]
        super().__init__("procesar_tipo_descargue", valid_responses)
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa una respuesta válida de tipo de descargue"""
        last_message = user_message.lower()
        
        if "manual" in last_message:
            state["tipo_descargue"] = DischargeTypes.MANUAL
        elif "mecanizado" in last_message:
            state["tipo_descargue"] = DischargeTypes.MECANIZADO
        else:
            return self.process_invalid_response(state, user_message)
        
        # Actualizar información faltante
        if state.get("modo_conversacion") == "natural":
            from models.pedido import PedidoAnalyzer
            state["informacion_faltante"] = PedidoAnalyzer.identificar_informacion_faltante(state)
        
        # Determinar siguiente paso - verificar si aún falta tipo_entrega
        if not state.get("tipo_entrega"):
            self.set_step(state, "preguntar_tipo_entrega")
        else:
            self.set_step(state, "mostrar_resumen")
        
        return state

class DeliveryTypeQuestionNode(QuestionNode):
    """Nodo para preguntar el tipo de entrega"""
    
    def __init__(self):
        question = "📍 **¿Cómo prefieres recibir tu pedido?**\n\n• Entrega (nosotros te lo llevamos)\n• Retira (vienes a recogerlo)\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_tipo_entrega", question, StepType.ESPERANDO_TIPO_ENTREGA)

class DeliveryTypeProcessingNode(ProcessingNode):
    """Nodo para procesar la respuesta de tipo de entrega"""
    
    def __init__(self):
        valid_responses = ["entrega", "retira"]
        super().__init__("procesar_tipo_entrega", valid_responses)
    
    def is_valid_response(self, user_message: str) -> bool:
        """Verifica si la respuesta es válida para tipo de entrega"""
        user_lower = user_message.lower()
        
        # Palabras clave para entrega
        entrega_keywords = ["entrega", "entreg", "llev", "domicilio", "llevar"]
        # Palabras clave para retira
        retira_keywords = ["retira", "retir", "recog", "buscar", "recoger"]
        
        return (any(keyword in user_lower for keyword in entrega_keywords) or 
                any(keyword in user_lower for keyword in retira_keywords))
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa una respuesta válida de tipo de entrega"""
        last_message = user_message.lower()
        
        # Palabras clave para entrega
        entrega_keywords = ["entrega", "entreg", "llev", "domicilio", "llevar"]
        # Palabras clave para retira  
        retira_keywords = ["retira", "retir", "recog", "buscar", "recoger"]
        
        if any(keyword in last_message for keyword in entrega_keywords):
            state["tipo_entrega"] = DeliveryTypes.ENTREGA
        elif any(keyword in last_message for keyword in retira_keywords):
            state["tipo_entrega"] = DeliveryTypes.RETIRA
        else:
            return self.process_invalid_response(state, user_message)
        
        # Actualizar información faltante
        if state.get("modo_conversacion") == "natural":
            from models.pedido import PedidoAnalyzer
            state["informacion_faltante"] = PedidoAnalyzer.identificar_informacion_faltante(state)
        
        # Ir al resumen
        self.set_step(state, "mostrar_resumen")
        return state
    
    def get_error_message(self) -> str:
        """Mensaje de error específico para tipo de entrega"""
        return "❌ Por favor, selecciona una opción válida: Entrega o Retira"

# Factory para crear nodos de entrega
class DeliveryNodesFactory:
    """Factory para crear nodos de entrega"""
    
    @staticmethod
    def create_all_delivery_nodes() -> dict:
        """Crea todos los nodos de entrega"""
        return {
            "preguntar_tipo_descargue": DischargeTypeQuestionNode(),
            "procesar_tipo_descargue": DischargeTypeProcessingNode(),
            "preguntar_tipo_entrega": DeliveryTypeQuestionNode(),
            "procesar_tipo_entrega": DeliveryTypeProcessingNode()
        }

# Crear instancias globales de los nodos
delivery_nodes = DeliveryNodesFactory.create_all_delivery_nodes()