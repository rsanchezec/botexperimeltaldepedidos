"""
Clase base para todos los nodos del grafo de conversación
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, HumanMessage
from models.state import GraphState, StepType

class BaseNode(ABC):
    """Clase base abstracta para todos los nodos del grafo"""
    
    def __init__(self, node_name: str):
        """
        Inicializa el nodo base
        
        Args:
            node_name: Nombre identificador del nodo
        """
        self.node_name = node_name
    
    @abstractmethod
    def execute(self, state: GraphState) -> GraphState:
        """
        Ejecuta la lógica principal del nodo
        
        Args:
            state: Estado actual del grafo
            
        Returns:
            Estado actualizado del grafo
        """
        pass
    
    def add_message(self, state: GraphState, content: str) -> None:
        """
        Agrega un mensaje del bot al estado
        
        Args:
            state: Estado del grafo
            content: Contenido del mensaje
        """
        state["messages"].append(AIMessage(content=content))
    
    def get_last_user_message(self, state: GraphState) -> Optional[str]:
        """
        Obtiene el último mensaje del usuario
        
        Args:
            state: Estado del grafo
            
        Returns:
            Contenido del último mensaje del usuario o None
        """
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                return message.content
        return None
    
    def set_step(self, state: GraphState, step: str, waiting_for_input: bool = False) -> None:
        """
        Establece el paso actual y si está esperando entrada
        
        Args:
            state: Estado del grafo
            step: Nuevo paso
            waiting_for_input: Si está esperando entrada del usuario
        """
        state["current_step"] = step
        state["waiting_for_input"] = waiting_for_input
    
    def validate_step_transition(self, state: GraphState, expected_step: str) -> bool:
        """
        Valida si la transición de paso es válida
        
        Args:
            state: Estado del grafo
            expected_step: Paso esperado
            
        Returns:
            True si la transición es válida
        """
        return state.get("current_step") == expected_step

class QuestionNode(BaseNode):
    """Clase base para nodos que hacen preguntas al usuario"""
    
    def __init__(self, node_name: str, question_text: str, next_step: str):
        """
        Inicializa un nodo de pregunta
        
        Args:
            node_name: Nombre del nodo
            question_text: Texto de la pregunta
            next_step: Siguiente paso después de la pregunta
        """
        super().__init__(node_name)
        self.question_text = question_text
        self.next_step = next_step
    
    def execute(self, state: GraphState) -> GraphState:
        """Ejecuta la pregunta y configura el estado para esperar respuesta"""
        question = self.format_question(state)
        self.add_message(state, question)
        self.set_step(state, self.next_step, waiting_for_input=True)
        return state
    
    def format_question(self, state: GraphState) -> str:
        """
        Formatea la pregunta basada en el estado actual
        Puede ser sobrescrito por clases hijas
        
        Args:
            state: Estado del grafo
            
        Returns:
            Pregunta formateada
        """
        return self.question_text

class ProcessingNode(BaseNode):
    """Clase base para nodos que procesan respuestas del usuario"""
    
    def __init__(self, node_name: str, valid_responses: List[str] = None):
        """
        Inicializa un nodo de procesamiento
        
        Args:
            node_name: Nombre del nodo
            valid_responses: Lista de respuestas válidas esperadas
        """
        super().__init__(node_name)
        self.valid_responses = valid_responses or []
    
    def execute(self, state: GraphState) -> GraphState:
        """Ejecuta el procesamiento de la respuesta del usuario"""
        user_message = self.get_last_user_message(state)
        
        if user_message is None:
            self.handle_no_user_message(state)
            return state
        
        if self.is_valid_response(user_message):
            return self.process_valid_response(state, user_message)
        else:
            return self.process_invalid_response(state, user_message)
    
    def is_valid_response(self, user_message: str) -> bool:
        """
        Verifica si la respuesta del usuario es válida
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            True si la respuesta es válida
        """
        if not self.valid_responses:
            return True  # Si no hay respuestas específicas, aceptar cualquiera
        
        user_lower = user_message.lower()
        return any(valid.lower() in user_lower for valid in self.valid_responses)
    
    @abstractmethod
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """
        Procesa una respuesta válida del usuario
        
        Args:
            state: Estado del grafo
            user_message: Mensaje del usuario
            
        Returns:
            Estado actualizado
        """
        pass
    
    def process_invalid_response(self, state: GraphState, user_message: str) -> GraphState:
        """
        Procesa una respuesta inválida del usuario
        
        Args:
            state: Estado del grafo
            user_message: Mensaje del usuario
            
        Returns:
            Estado actualizado
        """
        error_message = self.get_error_message()
        self.add_message(state, error_message)
        self.set_step(state, state["current_step"], waiting_for_input=True)
        return state
    
    def get_error_message(self) -> str:
        """
        Obtiene el mensaje de error para respuestas inválidas
        Puede ser sobrescrito por clases hijas
        
        Returns:
            Mensaje de error
        """
        if self.valid_responses:
            return f"❌ Por favor, selecciona una opción válida: {', '.join(self.valid_responses)}"
        return "❌ Por favor, proporciona una respuesta válida."
    
    def handle_no_user_message(self, state: GraphState) -> None:
        """
        Maneja el caso cuando no hay mensaje del usuario
        
        Args:
            state: Estado del grafo
        """
        self.set_step(state, state["current_step"], waiting_for_input=True)

class ConditionalNode(BaseNode):
    """Clase base para nodos que toman decisiones basadas en el estado"""
    
    def __init__(self, node_name: str):
        super().__init__(node_name)
    
    def execute(self, state: GraphState) -> GraphState:
        """Ejecuta la lógica condicional"""
        next_step = self.determine_next_step(state)
        state["current_step"] = next_step
        return state
    
    @abstractmethod
    def determine_next_step(self, state: GraphState) -> str:
        """
        Determina el siguiente paso basado en el estado
        
        Args:
            state: Estado del grafo
            
        Returns:
            Nombre del siguiente paso
        """
        pass

class NodeFactory:
    """Factory para crear nodos específicos"""
    
    @staticmethod
    def create_choice_question(node_name: str, question: str, choices: List[str], 
                              next_step: str) -> QuestionNode:
        """
        Crea un nodo de pregunta con opciones múltiples
        
        Args:
            node_name: Nombre del nodo
            question: Pregunta a hacer
            choices: Lista de opciones
            next_step: Siguiente paso
            
        Returns:
            Nodo de pregunta configurado
        """
        formatted_question = f"{question}\n\n"
        for choice in choices:
            formatted_question += f"• {choice}\n"
        formatted_question += "\nPor favor, escribe tu respuesta."
        
        return QuestionNode(node_name, formatted_question, next_step)
    
    @staticmethod
    def create_numeric_question(node_name: str, question: str, 
                               next_step: str) -> QuestionNode:
        """
        Crea un nodo de pregunta numérica
        
        Args:
            node_name: Nombre del nodo
            question: Pregunta a hacer
            next_step: Siguiente paso
            
        Returns:
            Nodo de pregunta configurado
        """
        formatted_question = f"{question}\n\nPor favor, ingresa la cantidad en número."
        
        return QuestionNode(node_name, formatted_question, next_step)

# Clases de utilidad para manejo de errores y logging

class NodeError(Exception):
    """Excepción específica para errores en nodos"""
    
    def __init__(self, node_name: str, message: str):
        self.node_name = node_name
        self.message = message
        super().__init__(f"Error en nodo '{node_name}': {message}")

class NodeLogger:
    """Logger simple para nodos"""
    
    @staticmethod
    def log_node_execution(node_name: str, state_info: str = ""):
        """Registra la ejecución de un nodo"""
        print(f"[NODE] Ejecutando {node_name} - {state_info}")
    
    @staticmethod
    def log_node_error(node_name: str, error: str):
        """Registra un error en un nodo"""
        print(f"[ERROR] Nodo {node_name}: {error}")
    
    @staticmethod
    def log_step_transition(from_step: str, to_step: str):
        """Registra una transición de paso"""
        print(f"[TRANSITION] {from_step} → {to_step}")