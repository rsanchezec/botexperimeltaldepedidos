"""
Controlador principal para el manejo de conversaciones
"""
from typing import Dict, Any, List, Tuple, Optional
from langchain_core.messages import HumanMessage, AIMessage
from models.state import GraphState, get_initial_state
from services.order_service import order_service
from config.settings import settings

class ConversationController:
    """Controlador principal para manejar conversaciones del bot"""
    
    def __init__(self, graph_controller):
        """
        Inicializa el controlador de conversación
        
        Args:
            graph_controller: Controlador del grafo de estados
        """
        self.graph_controller = graph_controller
        self.session_states: Dict[str, GraphState] = {}
    
    def start_conversation(self, session_id: str) -> Tuple[List[Tuple], GraphState]:
        """
        Inicia una nueva conversación
        
        Args:
            session_id: ID único de la sesión
            
        Returns:
            Tupla con historial inicial y estado de la sesión
        """
        # Crear nuevo estado inicial
        new_state = get_initial_state()
        
        # Ejecutar el nodo inicial del grafo
        result = self.graph_controller.execute_start_node(new_state)
        
        # Guardar estado de la sesión
        self.session_states[session_id] = result
        
        # Convertir mensajes a formato de historial para Gradio
        history = self._convert_messages_to_history(result["messages"])
        
        return history, result
    
    def process_user_message(self, message: str, session_id: str, 
                           current_history: List[Tuple] = None) -> Tuple[List[Tuple], GraphState]:
        """
        Procesa un mensaje del usuario
        
        Args:
            message: Mensaje del usuario
            session_id: ID de la sesión
            current_history: Historial actual de la conversación
            
        Returns:
            Tupla con historial actualizado y estado de la sesión
        """
        if not message or not message.strip():
            # Si el mensaje está vacío, devolver el estado actual
            current_state = self.session_states.get(session_id)
            if current_state:
                return current_history or [], current_state
            else:
                return self.start_conversation(session_id)
        
        # Obtener o inicializar estado de la sesión
        if session_id not in self.session_states:
            self.start_conversation(session_id)
        
        current_state = self.session_states[session_id]
        
        # Manejar comandos especiales
        if self._is_special_command(message):
            return self._handle_special_command(message, session_id, current_history)
        
        # Agregar mensaje del usuario al historial visual
        if current_history is None:
            current_history = []
        
        current_history.append((message, None))
        
        # Guardar conteo de mensajes antes del procesamiento
        old_message_count = len(current_state["messages"])
        
        # Agregar mensaje al estado interno
        current_state["messages"].append(HumanMessage(content=message))
        
        # Procesar mensaje a través del grafo
        try:
            updated_state = self._process_through_graph(current_state)
            
            # Actualizar estado de la sesión
            self.session_states[session_id] = updated_state
            
            # Obtener respuestas del bot usando el conteo correcto
            bot_responses = self._extract_bot_responses_from_count(updated_state, old_message_count + 1)
            
            # Actualizar historial con respuestas del bot
            if bot_responses:
                combined_response = "\n\n".join(bot_responses)
                current_history[-1] = (message, combined_response)
            
            return current_history, updated_state
            
        except Exception as e:
            # Manejar errores graciosamente
            error_response = f"Lo siento, hubo un error procesando tu mensaje: {str(e)}"
            current_history[-1] = (message, error_response)
            return current_history, current_state
    
    def reset_conversation(self, session_id: str) -> Tuple[List[Tuple], GraphState]:
        """
        Reinicia una conversación
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Tupla con nuevo historial y estado
        """
        # Incrementar session_id para crear una nueva conversación
        new_session_id = f"{session_id}_{len(self.session_states)}"
        return self.start_conversation(new_session_id)
    
    def get_session_state(self, session_id: str) -> Optional[GraphState]:
        """
        Obtiene el estado de una sesión específica
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Estado de la sesión o None si no existe
        """
        return self.session_states.get(session_id)
    
    def _is_special_command(self, message: str) -> bool:
        """Verifica si el mensaje es un comando especial"""
        special_commands = ["nuevo pedido", "reset", "ayuda", "estadisticas"]
        return message.lower().strip() in special_commands
    
    def _handle_special_command(self, command: str, session_id: str, 
                               current_history: List[Tuple]) -> Tuple[List[Tuple], GraphState]:
        """Maneja comandos especiales"""
        command_lower = command.lower().strip()
        
        if command_lower in ["nuevo pedido", "reset"]:
            return self.reset_conversation(session_id)
        elif command_lower == "ayuda":
            return self._show_help(session_id, current_history)
        elif command_lower == "estadisticas":
            return self._show_statistics(session_id, current_history)
        
        # Si no se reconoce el comando, procesarlo normalmente
        return self.process_user_message(command, session_id, current_history)
    
    def _show_help(self, session_id: str, current_history: List[Tuple]) -> Tuple[List[Tuple], GraphState]:
        """Muestra información de ayuda"""
        help_text = """
🤖 **Ayuda - Bot de Pedidos Cementos Argos**

**Comandos disponibles:**
• `nuevo pedido` - Inicia un nuevo pedido
• `ayuda` - Muestra esta información
• `estadisticas` - Muestra estadísticas del sistema

**Cómo hacer un pedido:**
1. **Modo Natural:** Describe tu pedido completo
   - *"Quiero 50 sacos de cemento gris de 50 kg con entrega"*
   
2. **Modo Guiado:** Responde paso a paso
   - El bot te guiará através de cada campo necesario

**Información requerida:**
• Categoría: Ensacado o Granel
• Tipo: Blanco o Gris  
• Cantidad: Número de sacos o toneladas
• Presentación: 50 Kg, 45 Kg, 20 Kg (solo ensacado)
• Descargue: Manual o Mecanizado
• Entrega: Entrega a domicilio o Retiro en planta

¿En qué más puedo ayudarte?
        """
        
        current_state = self.session_states.get(session_id)
        if current_history:
            current_history.append(("ayuda", help_text.strip()))
        
        return current_history or [("ayuda", help_text.strip())], current_state
    
    def _show_statistics(self, session_id: str, current_history: List[Tuple]) -> Tuple[List[Tuple], GraphState]:
        """Muestra estadísticas del sistema"""
        try:
            stats = order_service.obtener_estadisticas_sistema()
            stats_text = self._format_statistics(stats)
        except Exception as e:
            stats_text = f"Error obteniendo estadísticas: {str(e)}"
        
        current_state = self.session_states.get(session_id)
        if current_history:
            current_history.append(("estadisticas", stats_text))
        
        return current_history or [("estadisticas", stats_text)], current_state
    
    def _format_statistics(self, stats: Dict[str, Any]) -> str:
        """Formatea las estadísticas para mostrar"""
        if not stats:
            return "📊 No se pudieron obtener las estadísticas del sistema."
        
        texto = "📊 **Estadísticas del Sistema**\n\n"
        texto += f"**Total de pedidos:** {stats.get('total_pedidos', 0)}\n\n"
        
        if stats.get('por_tipo_entrega'):
            texto += "**Por tipo de entrega:**\n"
            for tipo, cantidad in stats['por_tipo_entrega'].items():
                texto += f"• {tipo}: {cantidad} pedidos\n"
            texto += "\n"
        
        if stats.get('productos_populares'):
            texto += "**Productos más pedidos:**\n"
            for producto, cantidad in stats['productos_populares']:
                texto += f"• Cemento {producto}: {cantidad:.0f} unidades\n"
        
        return texto
    
    def _process_through_graph(self, state: GraphState) -> GraphState:
        """Procesa el estado a través del grafo de conversación"""
        return self.graph_controller.process_state(state)
    
    def _extract_bot_responses(self, new_state: GraphState, old_state: GraphState) -> List[str]:
        """Extrae las nuevas respuestas del bot"""
        old_message_count = len(old_state["messages"])
        new_messages = new_state["messages"][old_message_count:]
        
        bot_responses = []
        for message in new_messages:
            if isinstance(message, AIMessage):
                bot_responses.append(message.content)
        
        return bot_responses
    
    def _extract_bot_responses_from_count(self, state: GraphState, start_index: int) -> List[str]:
        """Extrae las respuestas del bot desde un índice específico"""
        if start_index >= len(state["messages"]):
            return []
        
        new_messages = state["messages"][start_index:]
        
        bot_responses = []
        for message in new_messages:
            if isinstance(message, AIMessage):
                bot_responses.append(message.content)
        
        return bot_responses
    
    def _convert_messages_to_history(self, messages: List) -> List[Tuple]:
        """Convierte mensajes internos a formato de historial para Gradio"""
        history = []
        current_user_msg = None
        
        for message in messages:
            if isinstance(message, HumanMessage):
                current_user_msg = message.content
            elif isinstance(message, AIMessage) and current_user_msg is not None:
                history.append((current_user_msg, message.content))
                current_user_msg = None
            elif isinstance(message, AIMessage):
                # Mensaje del bot sin mensaje previo del usuario
                history.append((None, message.content))
        
        return history
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene un resumen de la conversación actual
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Diccionario con resumen de la conversación
        """
        state = self.session_states.get(session_id)
        if not state:
            return {"error": "Sesión no encontrada"}
        
        summary = {
            "session_id": session_id,
            "current_step": state.get("current_step", ""),
            "mode": state.get("modo_conversacion", ""),
            "products_count": len(state.get("pedidos", [])),
            "is_complete": not bool(state.get("informacion_faltante", [])),
            "waiting_for_input": state.get("waiting_for_input", False)
        }
        
        # Agregar información del pedido si existe
        if state.get("pedidos"):
            totals = order_service.calcular_totales_pedido(state)
            summary.update(totals)
        
        return summary
    
    def cleanup_old_sessions(self, max_sessions: int = 100):
        """
        Limpia sesiones antiguas para liberar memoria
        
        Args:
            max_sessions: Número máximo de sesiones a mantener
        """
        if len(self.session_states) > max_sessions:
            # Mantener solo las sesiones más recientes
            # Para una implementación más sofisticada, se podría usar timestamps
            session_items = list(self.session_states.items())
            self.session_states = dict(session_items[-max_sessions:])