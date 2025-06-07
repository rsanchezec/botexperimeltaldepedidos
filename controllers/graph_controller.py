"""
Controlador del grafo de estados para el bot de pedidos
"""
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models.state import GraphState, get_initial_state
from nodes.start_nodes import start_node, analysis_node, step_determiner
from nodes.product_nodes import product_nodes
from nodes.delivery_nodes import delivery_nodes
from nodes.summary_nodes import summary_nodes
from nodes.modification_nodes import modification_nodes
from config.settings import settings

class GraphController:
    """Controlador principal del grafo de estados"""
    
    def __init__(self):
        """Inicializa el controlador del grafo"""
        self.workflow = None
        self.app = None
        self.memory = MemorySaver()
        self._initialize_graph()
    
    def _initialize_graph(self):
        """Inicializa y compila el grafo de estados"""
        # Crear el grafo
        self.workflow = StateGraph(GraphState)
        
        # Agregar todos los nodos
        self._add_all_nodes()
        
        # Configurar las conexiones entre nodos
        self._configure_node_connections()
        
        # Compilar el grafo
        self.app = self.workflow.compile(checkpointer=self.memory)
    
    def _add_all_nodes(self):
        """Agrega todos los nodos al grafo"""
        # Nodos de inicio
        self.workflow.add_node("inicio", start_node.execute)
        self.workflow.add_node("analizar_mensaje_inicial", analysis_node.execute)
        
        # Nodos de productos
        for node_name, node_instance in product_nodes.items():
            self.workflow.add_node(node_name, node_instance.execute)
        
        # Nodos de entrega
        for node_name, node_instance in delivery_nodes.items():
            self.workflow.add_node(node_name, node_instance.execute)
        
        # Nodos de resumen
        for node_name, node_instance in summary_nodes.items():
            self.workflow.add_node(node_name, node_instance.execute)
        
        # Nodos de modificación
        for node_name, node_instance in modification_nodes.items():
            self.workflow.add_node(node_name, node_instance.execute)
    
    def _configure_node_connections(self):
        """Configura las conexiones entre nodos"""
        # Establecer punto de entrada
        self.workflow.set_entry_point("inicio")
        
        # Agregar edges que van directamente al END (para permitir pausas)
        all_nodes = [
            "inicio", "analizar_mensaje_inicial"
        ] + list(product_nodes.keys()) + list(delivery_nodes.keys()) + list(summary_nodes.keys()) + list(modification_nodes.keys())
        
        for node_name in all_nodes:
            self.workflow.add_edge(node_name, END)
    
    def execute_start_node(self, state: GraphState) -> GraphState:
        """
        Ejecuta el nodo inicial
        
        Args:
            state: Estado inicial
            
        Returns:
            Estado actualizado después del nodo inicial
        """
        thread_id = "default"
        config = {"configurable": {"thread_id": thread_id}}
        
        result = self.app.invoke(state, config)
        return result
    
    def process_state(self, state: GraphState) -> GraphState:
        """
        Procesa el estado a través del grafo
        
        Args:
            state: Estado actual
            
        Returns:
            Estado actualizado
        """
        max_iterations = settings.MAX_ITERATIONS
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Determinar el siguiente paso
            next_step = self._determine_next_step(state)
            
            if not next_step or next_step == END:
                break
            
            # Guardar paso anterior para detectar loops
            prev_step = state.get("current_step", "")
            
            # Ejecutar el nodo correspondiente
            state = self._execute_node(next_step, state)
            
            # Verificar si estamos en un loop o esperando entrada
            if (state.get("current_step") == prev_step and 
                state.get("waiting_for_input", False)):
                break
            
            # Si el estado requiere entrada del usuario, parar
            if state.get("waiting_for_input", False):
                break
        
        return state
    
    def _determine_next_step(self, state: GraphState) -> str:
        """
        Determina el siguiente paso basado en el estado actual
        
        Args:
            state: Estado actual
            
        Returns:
            Nombre del siguiente paso
        """
        current_step = state.get("current_step", "")
        
        # Si current_step está vacío, ir a analizar mensaje inicial
        if not current_step:
            return "analizar_mensaje_inicial"
        
        # Mapeo de pasos de espera a pasos de procesamiento
        processing_steps = {
            "esperando_categoria": "procesar_categoria",
            "esperando_presentacion": "procesar_presentacion",
            "esperando_tipo_producto": "procesar_tipo_producto",
            "esperando_cantidad": "procesar_cantidad",
            "esperando_mas_productos": "procesar_mas_productos",
            "esperando_tipo_descargue": "procesar_tipo_descargue",
            "esperando_tipo_entrega": "procesar_tipo_entrega",
            "esperando_confirmacion_modificar": "procesar_confirmacion_modificar",
            "esperando_producto_modificar": "procesar_producto_modificar",
            "esperando_que_modificar": "procesar_que_modificar",
            "esperando_nueva_presentacion": "procesar_nueva_presentacion",
            "esperando_nuevo_tipo": "procesar_nuevo_tipo",
            "esperando_nueva_cantidad": "procesar_nueva_cantidad",
            "esperando_que_elemento_modificar": "procesar_que_elemento_modificar",
            "esperando_nuevo_descargue": "procesar_nuevo_descargue",
            "esperando_nueva_entrega": "procesar_nueva_entrega"
        }
        
        # Si estamos esperando una respuesta específica, procesarla
        if current_step in processing_steps:
            return processing_steps[current_step]
        
        # Flujo específico basado en pasos
        step_transitions = {
            "inicio": "analizar_mensaje_inicial",
            "mostrar_resumen": current_step,  # Ejecutar el nodo mostrar_resumen
            "mostrar_confirmacion_final": current_step,  # Ejecutar el nodo mostrar_confirmacion_final
            "preguntar_categoria": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_presentacion": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_tipo_producto": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_cantidad": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_mas_productos": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_tipo_descargue": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_tipo_entrega": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_producto_modificar": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_que_modificar": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_nueva_presentacion": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_nuevo_tipo": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_nueva_cantidad": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_que_elemento_modificar": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_nuevo_descargue": current_step,  # Ejecutar el nodo de pregunta
            "preguntar_nueva_entrega": current_step,  # Ejecutar el nodo de pregunta
            "fin": END
        }
        
        return step_transitions.get(current_step, END)
    
    def _get_next_missing_field(self, faltante: list) -> str:
        """Obtiene el siguiente campo faltante en orden de prioridad"""
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
        
        return faltante[0] if faltante else ""
    
    def _map_field_to_step(self, campo: str) -> str:
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
    
    def _execute_node(self, node_name: str, state: GraphState) -> GraphState:
        """
        Ejecuta un nodo específico
        
        Args:
            node_name: Nombre del nodo a ejecutar
            state: Estado actual
            
        Returns:
            Estado actualizado
        """
        # Mapear nombres de nodos a instancias
        node_map = {
            "inicio": start_node,
            "analizar_mensaje_inicial": analysis_node,
            **product_nodes,
            **delivery_nodes,
            **summary_nodes,
            **modification_nodes
        }
        
        node_instance = node_map.get(node_name)
        if node_instance:
            try:
                return node_instance.execute(state)
            except Exception as e:
                print(f"Error ejecutando nodo {node_name}: {e}")
                # En caso de error, mantener el estado actual
                return state
        else:
            print(f"Nodo no encontrado: {node_name}")
            return state
    
    def get_graph_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el grafo
        
        Returns:
            Diccionario con información del grafo
        """
        node_count = len(self.workflow.nodes) if self.workflow else 0
        
        return {
            "node_count": node_count,
            "has_memory": self.memory is not None,
            "is_compiled": self.app is not None,
            "available_nodes": list(self.workflow.nodes.keys()) if self.workflow else []
        }
    
    def validate_graph(self) -> Dict[str, Any]:
        """
        Valida que el grafo esté correctamente configurado
        
        Returns:
            Diccionario con resultados de validación
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Verificar que el grafo esté compilado
            if not self.app:
                validation_results["errors"].append("Grafo no compilado")
                validation_results["is_valid"] = False
            
            # Verificar nodos críticos
            critical_nodes = [
                "inicio", "analizar_mensaje_inicial", "mostrar_resumen",
                "mostrar_confirmacion_final"
            ]
            
            for node in critical_nodes:
                if node not in self.workflow.nodes:
                    validation_results["errors"].append(f"Nodo crítico faltante: {node}")
                    validation_results["is_valid"] = False
            
            # Verificar memoria
            if not self.memory:
                validation_results["warnings"].append("Sistema de memoria no inicializado")
            
        except Exception as e:
            validation_results["errors"].append(f"Error durante validación: {str(e)}")
            validation_results["is_valid"] = False
        
        return validation_results
    
    def reset_memory(self):
        """Reinicia el sistema de memoria del grafo"""
        self.memory = MemorySaver()
        if self.workflow:
            self.app = self.workflow.compile(checkpointer=self.memory)
    
    def get_node_execution_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas de ejecución de nodos
        (Placeholder para futuras métricas)
        
        Returns:
            Diccionario con estadísticas por nodo
        """
        # En una implementación completa, aquí se podrían rastrear
        # métricas como número de ejecuciones por nodo, tiempo promedio, etc.
        return {
            "total_executions": 0,
            "node_stats": {}
        }