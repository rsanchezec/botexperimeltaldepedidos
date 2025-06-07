"""
Interfaz de usuario con Gradio para el bot de pedidos
"""
import gradio as gr
from typing import List, Tuple, Dict, Any, Optional
from controllers.conversation_controller import ConversationController
from services.database_service import DatabaseService
from config.database import DatabaseManager
from config.settings import settings
from utils.helpers import FormatHelper

class GradioInterface:
    """Clase para manejar la interfaz de Gradio"""
    
    def __init__(self, graph_controller):
        """
        Inicializa la interfaz con el controlador del grafo
        
        Args:
            graph_controller: Controlador del grafo de conversación
        """
        self.conversation_controller = ConversationController(graph_controller)
        self.current_session_id = "default_session"
    
    def process_message(self, message: str, history: List[Tuple], 
                       session_state: Dict[str, Any]) -> Tuple[str, List[Tuple], Dict[str, Any]]:
        """
        Procesa un mensaje del usuario
        
        Args:
            message: Mensaje del usuario
            history: Historial de la conversación
            session_state: Estado de la sesión
            
        Returns:
            Tupla (mensaje_limpio, historial_actualizado, estado_actualizado)
        """
        if not session_state:
            session_state = {"session_id": self.current_session_id}
        
        session_id = session_state.get("session_id", self.current_session_id)
        
        # Procesar mensaje
        new_history, updated_state = self.conversation_controller.process_user_message(
            message, session_id, history
        )
        
        # Actualizar estado de la sesión
        session_state["last_state"] = updated_state
        session_state["message_count"] = session_state.get("message_count", 0) + 1
        
        return "", new_history, session_state
    
    def reset_conversation(self, session_state: Dict[str, Any]) -> Tuple[str, List[Tuple], Dict[str, Any]]:
        """
        Reinicia la conversación
        
        Args:
            session_state: Estado actual de la sesión
            
        Returns:
            Tupla (mensaje_limpio, nuevo_historial, nuevo_estado)
        """
        # Generar nuevo ID de sesión
        import time
        new_session_id = f"session_{int(time.time())}"
        
        # Iniciar nueva conversación
        new_history, new_state = self.conversation_controller.start_conversation(new_session_id)
        
        # Crear nuevo estado de sesión
        new_session_state = {
            "session_id": new_session_id,
            "last_state": new_state,
            "message_count": 0
        }
        
        return "", new_history, new_session_state
    
    def initialize_conversation(self, session_state: Dict[str, Any]) -> Tuple[List[Tuple], Dict[str, Any]]:
        """
        Inicializa la conversación cuando se carga la página
        
        Args:
            session_state: Estado de la sesión
            
        Returns:
            Tupla (historial_inicial, estado_inicial)
        """
        if not session_state or "session_id" not in session_state:
            session_state = {"session_id": self.current_session_id}
        
        session_id = session_state["session_id"]
        
        # Verificar si ya existe una conversación
        existing_state = self.conversation_controller.get_session_state(session_id)
        if existing_state and existing_state.get("messages"):
            # Convertir mensajes existentes a historial
            from controllers.conversation_controller import ConversationController
            history = self.conversation_controller._convert_messages_to_history(existing_state["messages"])
            session_state["last_state"] = existing_state
            return history, session_state
        
        # Iniciar nueva conversación
        history, state = self.conversation_controller.start_conversation(session_id)
        session_state["last_state"] = state
        session_state["message_count"] = 0
        
        return history, session_state
    
    def get_statistics(self) -> str:
        """
        Obtiene y formatea estadísticas del sistema
        
        Returns:
            Estadísticas formateadas como string
        """
        try:
            stats = DatabaseService.obtener_estadisticas()
            return FormatHelper.format_statistics_text(stats)
        except Exception as e:
            return f"Error obteniendo estadísticas: {str(e)}"
    
    def get_database_status(self) -> str:
        """
        Obtiene el estado de la base de datos
        
        Returns:
            Estado de la base de datos
        """
        return DatabaseManager.get_database_status()

def create_gradio_interface(graph_controller) -> gr.Blocks:
    """
    Crea la interfaz de Gradio
    
    Args:
        graph_controller: Controlador del grafo
        
    Returns:
        Interfaz de Gradio configurada
    """
    # Crear instancia de la interfaz
    interface = GradioInterface(graph_controller)
    
    # Crear tema personalizado
    theme = gr.themes.Soft().set(
        button_primary_background_fill="#FF6B35",
        button_primary_background_fill_hover="#E55A2B"
    )
    
    # Crear la interfaz con Gradio Blocks
    with gr.Blocks(
        theme=theme,
        title=settings.APP_TITLE,
        css=_get_custom_css()
    ) as demo:
        
        # Estado de sesión - Gradio maneja automáticamente una instancia por usuario
        session_state = gr.State({})
        
        # Header
        with gr.Row():
            gr.Markdown(_get_header_markdown())
        
        # Estado de la base de datos
        with gr.Row():
            db_status = gr.Markdown(interface.get_database_status())
        
        # Chat principal
        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    value=[],
                    elem_id="chatbot",
                    height=500,
                    show_label=False,
                    container=True,
                    bubble_full_width=False
                )
        
        # Área de entrada
        with gr.Row():
            with gr.Column(scale=4):
                msg = gr.Textbox(
                    label="Tu mensaje",
                    placeholder="Ejemplo: 'Quiero 100 sacos de cemento blanco de 50 kg' o escribe tu respuesta...",
                    lines=2,
                    max_lines=5,
                    container=True
                )
            with gr.Column(scale=1, min_width=100):
                submit_btn = gr.Button("Enviar", variant="primary", size="lg")
        
        # Botones de acción
        with gr.Row():
            clear_btn = gr.Button("Nuevo Pedido", variant="secondary", size="sm")
            help_btn = gr.Button("Ayuda", variant="secondary", size="sm")
        
        # Panel de estadísticas (colapsable)
        with gr.Accordion("📊 Estadísticas del Sistema", open=False):
            with gr.Row():
                stats_btn = gr.Button("Actualizar Estadísticas", size="sm")
            with gr.Row():
                stats_display = gr.Markdown("")
        
        # Panel de información (colapsable)
        with gr.Accordion("📝 Información y Ejemplos", open=False):
            gr.Markdown(_get_help_markdown())
        
        # Panel de desarrollador (solo si debug está activado)
        if settings.APP_DEBUG:
            with gr.Accordion("🔧 Información de Desarrollo", open=False):
                with gr.Row():
                    debug_btn = gr.Button("Estado de Sesión", size="sm")
                with gr.Row():
                    debug_info = gr.JSON(label="Estado Actual", visible=True)
        
        # Configurar eventos
        
        # Envío de mensajes
        msg.submit(
            interface.process_message,
            inputs=[msg, chatbot, session_state],
            outputs=[msg, chatbot, session_state]
        )
        submit_btn.click(
            interface.process_message,
            inputs=[msg, chatbot, session_state],
            outputs=[msg, chatbot, session_state]
        )
        
        # Nuevo pedido
        clear_btn.click(
            interface.reset_conversation,
            inputs=[session_state],
            outputs=[msg, chatbot, session_state]
        )
        
        # Botón de ayuda
        def show_help(session_state):
            return interface.process_message("ayuda", [], session_state)
        
        help_btn.click(
            show_help,
            inputs=[session_state],
            outputs=[msg, chatbot, session_state]
        )
        
        # Estadísticas
        stats_btn.click(
            interface.get_statistics,
            outputs=[stats_display]
        )
        
        # Información de debug (solo en modo debug)
        if settings.APP_DEBUG:
            def get_debug_info(session_state):
                if session_state and "last_state" in session_state:
                    # Crear información simplificada para debug
                    debug_data = {
                        "session_id": session_state.get("session_id", ""),
                        "message_count": session_state.get("message_count", 0),
                        "current_step": session_state["last_state"].get("current_step", ""),
                        "mode": session_state["last_state"].get("modo_conversacion", ""),
                        "products_count": len(session_state["last_state"].get("pedidos", [])),
                        "waiting_for_input": session_state["last_state"].get("waiting_for_input", False),
                        "missing_info": session_state["last_state"].get("informacion_faltante", [])
                    }
                    return debug_data
                return {"status": "No session data"}
            
            debug_btn.click(
                get_debug_info,
                inputs=[session_state],
                outputs=[debug_info]
            )
        
        # Inicialización al cargar la página
        demo.load(
            interface.initialize_conversation,
            inputs=[session_state],
            outputs=[chatbot, session_state]
        )
    
    return demo

def _get_custom_css() -> str:
    """Obtiene CSS personalizado para la interfaz"""
    return """
    #chatbot {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .message.user {
        background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
        color: white;
    }
    
    .message.bot {
        background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
        color: white;
        border-left: 4px solid #3498DB;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .header-gradient {
        background: linear-gradient(135deg, #2C3E50 0%, #3498DB 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
        border: 1px solid #34495E;
    }
    
    .stats-card {
        background: #2C3E50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #3498DB;
        color: #ECF0F1;
    }
    
    .help-section {
        background: #34495E;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #ECF0F1;
        border-left: 4px solid #27AE60;
    }
    """

def _get_header_markdown() -> str:
    """Obtiene el markdown del header"""
    return """
    <div class="header-gradient">
    <h1 style="text-align: center; margin: 0;">
        🏗️ Bot de Pedidos - Cementos Argos 🏗️
    </h1>
    <h3 style="text-align: center; margin: 10px 0 0 0; opacity: 0.9;">
        Asistente Virtual Arturo_V3 con Inteligencia Artificial
    </h3>
    </div>
    
    <div style="text-align: center; margin: 20px 0;">
        <p style="font-size: 18px; color: #BDC3C7;">
            Realiza tu pedido de cemento de forma inteligente y natural
        </p>
    </div>
    """

def _get_help_markdown() -> str:
    """Obtiene el markdown de ayuda"""
    return """
    ### 🚀 Nuevas Características
    
    **Procesamiento de Lenguaje Natural:** Ahora puedes hacer tu pedido completo en una sola frase:
    
    ### 📝 Ejemplos de pedidos naturales:
    
    <div class="help-section">
    
    **Pedidos simples:**
    - *"Necesito 50 sacos de cemento gris de 50 kg para entrega con descarga manual"*
    - *"Quiero 30 toneladas de cemento blanco a granel para retirar"*
    - *"Mi pedido es: 100 sacos de 45 kg de cemento gris"*
    
    **Pedidos múltiples:**
    - *"Necesito 20 toneladas de cemento blanco a granel y 50 sacos de cemento gris de 50 kg"*
    - *"Quiero 100 sacos de 50 kg y 30 sacos de 20 kg de cemento blanco"*
    
    </div>
    
    ### 🎯 Modos de Operación
    
    1. **Modo Natural (Recomendado):** 
       - Describe tu pedido completo en lenguaje cotidiano
       - El bot extraerá automáticamente toda la información
       - Solo te preguntará por datos faltantes
    
    2. **Modo Guiado:** 
       - Di "ayuda" o "paso a paso" para activarlo
       - El bot te guiará pregunta por pregunta
    
    ### 📋 Información requerida:
    
    - **Categoría:** Ensacado o Granel
    - **Tipo:** Blanco o Gris  
    - **Cantidad:** Número de sacos o toneladas
    - **Presentación:** 50 Kg, 45 Kg, 20 Kg (solo para ensacado)
    - **Descargue:** Manual o Mecanizado
    - **Entrega:** Entrega a domicilio o Retiro en planta
    
    ### 🤖 Comandos especiales:
    
    - `nuevo pedido` - Inicia un pedido nuevo
    - `ayuda` - Muestra información de ayuda
    - `estadisticas` - Muestra estadísticas del sistema
    
    ### ✨ Funcionalidades avanzadas:
    
    - ✅ Modificación de productos antes de confirmar
    - ✅ Guardado automático en base de datos
    - ✅ Números de pedido únicos
    - ✅ Validación inteligente de datos
    - ✅ Cálculo automático de totales
    
    ---
    
    💡 **Tip:** ¡Prueba describir tu pedido completo en la primera frase!
    """

# Función principal para crear la interfaz
def create_interface(graph_controller) -> gr.Blocks:
    """
    Función principal para crear la interfaz de Gradio
    
    Args:
        graph_controller: Controlador del grafo
        
    Returns:
        Interfaz configurada
    """
    return create_gradio_interface(graph_controller)