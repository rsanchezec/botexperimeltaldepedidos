"""
Nodos para el manejo de productos en el bot de pedidos
"""
import re
from typing import Optional
from models.state import GraphState, StepType, ProductCategories, CementTypes, create_pedido_item
from services.order_service import order_service
from services.llm_service import llm_service
from .base_node import QuestionNode, ProcessingNode, NodeFactory
from config.settings import settings

class CategoryQuestionNode(QuestionNode):
    """Nodo para preguntar la categoría del producto"""
    
    def __init__(self):
        question = "📦 **¿Qué categoría de cemento deseas?**\n\n• Ensacado\n• Granel\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_categoria", question, StepType.ESPERANDO_CATEGORIA)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta según el modo de conversación"""
        if state.get("modo_conversacion") == "natural":
            faltante = [f for f in state.get("informacion_faltante", []) if "categoria" in f]
            if faltante:
                producto_num = int(faltante[0].split("_")[-1])
                return f"📦 **Para el producto {producto_num}, ¿qué categoría de cemento deseas?**\n\n• Ensacado\n• Granel\n\nPor favor, escribe tu respuesta."
        
        return self.question_text

class CategoryProcessingNode(ProcessingNode):
    """Nodo para procesar la respuesta de categoría"""
    
    def __init__(self):
        valid_responses = ["ensacado", "granel"]
        super().__init__("procesar_categoria", valid_responses)
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa una respuesta válida de categoría"""
        last_message = user_message.lower()
        
        if "ensacado" in last_message:
            categoria = ProductCategories.ENSACADO
            unidad = "sacos"
        elif "granel" in last_message:
            categoria = ProductCategories.GRANEL
            unidad = "toneladas"
        else:
            return self.process_invalid_response(state, user_message)
        
        # Actualizar según el modo de conversación
        if state.get("modo_conversacion") == "natural":
            # Actualizar el producto que necesita categoría
            for pedido in state["pedidos"]:
                if not pedido.get("categoria"):
                    pedido["categoria"] = categoria
                    pedido["unidad"] = unidad
                    if categoria == ProductCategories.GRANEL:
                        pedido["presentacion"] = ""  # Granel no tiene presentación
                    break
            
            # Actualizar información faltante
            state["informacion_faltante"] = order_service.obtener_siguiente_campo_faltante(state)
            
            # Determinar siguiente paso
            if categoria == ProductCategories.ENSACADO:
                faltante_presentacion = [f for f in state.get("informacion_faltante", []) if "presentacion" in f]
                if faltante_presentacion:
                    self.set_step(state, "preguntar_presentacion")
                else:
                    self.set_step(state, "preguntar_tipo_producto")
            else:
                self.set_step(state, "preguntar_tipo_producto")
        else:
            # Modo guiado tradicional
            state["categoria_actual"] = categoria
            state["pedido_actual"]["categoria"] = categoria
            state["pedido_actual"]["unidad"] = unidad
            
            if categoria == ProductCategories.ENSACADO:
                self.set_step(state, "preguntar_presentacion")
            else:
                self.set_step(state, "preguntar_tipo_producto")
        
        return state

class PresentationQuestionNode(QuestionNode):
    """Nodo para preguntar la presentación del producto ensacado"""
    
    def __init__(self):
        question = "⚖️ **¿Qué presentación prefieres?**\n\n• 50 Kg\n• 45 Kg\n• 20 Kg\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_presentacion", question, StepType.ESPERANDO_PRESENTACION)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta según el contexto"""
        if state.get("modo_conversacion") == "natural":
            faltante = [f for f in state.get("informacion_faltante", []) if "presentacion" in f]
            if faltante:
                producto_num = int(faltante[0].split("_")[-1])
                return f"⚖️ **Para el producto {producto_num} (Ensacado), ¿qué presentación prefieres?**\n\n• 50 Kg\n• 45 Kg\n• 20 Kg\n\nPor favor, escribe tu respuesta."
        
        return self.question_text

class PresentationProcessingNode(ProcessingNode):
    """Nodo para procesar la respuesta de presentación"""
    
    def __init__(self):
        super().__init__("procesar_presentacion")
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa una respuesta válida de presentación"""
        # Extraer el número de kg usando regex
        kg_match = re.search(r'(\d+)\s*kg', user_message.lower())
        
        if not kg_match:
            error_msg = "❌ Por favor, especifica una presentación válida (ej: 50 Kg, 45 Kg, 20 Kg)"
            self.add_message(state, error_msg)
            self.set_step(state, StepType.ESPERANDO_PRESENTACION, waiting_for_input=True)
            return state
        
        kg = kg_match.group(1)
        presentacion = f"{kg} Kg"
        
        # Validar que sea una presentación válida
        if presentacion not in settings.VALID_PRESENTATIONS:
            return self.process_invalid_response(state, user_message)
        
        # Actualizar según el modo de conversación
        if state.get("modo_conversacion") == "natural":
            # Actualizar el producto que necesita presentación
            for pedido in state["pedidos"]:
                if pedido.get("categoria") == ProductCategories.ENSACADO and not pedido.get("presentacion"):
                    pedido["presentacion"] = presentacion
                    break
            
            state["informacion_faltante"] = order_service.obtener_siguiente_campo_faltante(state)
        else:
            state["pedido_actual"]["presentacion"] = presentacion
        
        self.set_step(state, "preguntar_tipo_producto")
        return state
    
    def get_error_message(self) -> str:
        """Mensaje de error específico para presentación"""
        return "❌ Por favor, especifica una presentación válida: 50 Kg, 45 Kg, 20 Kg"

class ProductTypeQuestionNode(QuestionNode):
    """Nodo para preguntar el tipo de cemento"""
    
    def __init__(self):
        question = "🎨 **¿Qué tipo de cemento necesitas?**\n\n• Blanco\n• Gris\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_tipo_producto", question, StepType.ESPERANDO_TIPO_PRODUCTO)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta según el contexto"""
        if state.get("modo_conversacion") == "natural":
            faltante = [f for f in state.get("informacion_faltante", []) if "tipo_producto" in f]
            if faltante:
                producto_num = int(faltante[0].split("_")[-1])
                return f"🎨 **Para el producto {producto_num}, ¿qué tipo de cemento necesitas?**\n\n• Blanco\n• Gris\n\nPor favor, escribe tu respuesta."
        
        return self.question_text

class ProductTypeProcessingNode(ProcessingNode):
    """Nodo para procesar la respuesta de tipo de producto"""
    
    def __init__(self):
        valid_responses = ["blanco", "gris"]
        super().__init__("procesar_tipo_producto", valid_responses)
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa una respuesta válida de tipo de producto"""
        last_message = user_message.lower()
        
        if "blanco" in last_message:
            tipo = CementTypes.BLANCO
        elif "gris" in last_message:
            tipo = CementTypes.GRIS
        else:
            return self.process_invalid_response(state, user_message)
        
        # Actualizar según el modo de conversación
        if state.get("modo_conversacion") == "natural":
            # Actualizar el producto que necesita tipo
            for pedido in state["pedidos"]:
                if not pedido.get("tipo_producto"):
                    pedido["tipo_producto"] = tipo
                    break
            
            # Actualizar información faltante
            from models.pedido import PedidoAnalyzer
            state["informacion_faltante"] = PedidoAnalyzer.identificar_informacion_faltante(state)
            
            # Determinar siguiente paso basado en lo que realmente falta
            siguiente_campo = order_service.obtener_siguiente_campo_faltante(state)
            next_step = self._determinar_siguiente_paso(siguiente_campo)
            self.set_step(state, next_step)
        else:
            state["pedido_actual"]["tipo_producto"] = tipo
            self.set_step(state, "preguntar_cantidad")
        
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

class QuantityQuestionNode(QuestionNode):
    """Nodo para preguntar la cantidad del producto"""
    
    def __init__(self):
        question = "🔢 **¿Qué cantidad necesitas?**\n\nPor favor, ingresa la cantidad en número."
        super().__init__("preguntar_cantidad", question, StepType.ESPERANDO_CANTIDAD)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta según el contexto"""
        if state.get("modo_conversacion") == "natural":
            faltante = [f for f in state.get("informacion_faltante", []) if "cantidad" in f]
            if faltante:
                producto_num = int(faltante[0].split("_")[-1])
                pedido = state["pedidos"][producto_num - 1]
                if pedido.get("categoria") == ProductCategories.ENSACADO:
                    return f"🔢 **Para el producto {producto_num}, ¿cuántos sacos necesitas?**\n\nPor favor, ingresa la cantidad en número."
                else:
                    return f"🔢 **Para el producto {producto_num}, ¿cuántas toneladas necesitas?**\n\nPor favor, ingresa la cantidad en número."
        else:
            if state.get("categoria_actual") == ProductCategories.ENSACADO:
                return "🔢 **¿Cuántos sacos necesitas?**\n\nPor favor, ingresa la cantidad en número."
            else:
                return "🔢 **¿Cuántas toneladas necesitas?**\n\nPor favor, ingresa la cantidad en número."
        
        return self.question_text

class QuantityProcessingNode(ProcessingNode):
    """Nodo para procesar la respuesta de cantidad"""
    
    def __init__(self):
        super().__init__("procesar_cantidad")
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa una respuesta válida de cantidad"""
        try:
            cantidad = float(user_message.replace(",", "."))
            if cantidad <= 0:
                raise ValueError("Cantidad debe ser mayor a 0")
            
            # Actualizar según el modo de conversación
            if state.get("modo_conversacion") == "natural":
                # Actualizar el producto que necesita cantidad
                for pedido in state["pedidos"]:
                    if not pedido.get("cantidad") or pedido.get("cantidad") == 0:
                        pedido["cantidad"] = cantidad
                        break
                
                state["informacion_faltante"] = order_service.obtener_siguiente_campo_faltante(state)
                
                # Verificar si necesitamos más información de productos
                faltante_productos = [f for f in state["informacion_faltante"] 
                                    if any(x in f for x in ["categoria", "presentacion", "tipo_producto", "cantidad"])]
                
                if not faltante_productos:
                    # Ya tenemos toda la información de productos
                    if "tipo_descargue" in state["informacion_faltante"]:
                        self.set_step(state, "preguntar_tipo_descargue")
                    elif "tipo_entrega" in state["informacion_faltante"]:
                        self.set_step(state, "preguntar_tipo_entrega")
                    else:
                        self.set_step(state, "mostrar_resumen")
                else:
                    # Continuar con el siguiente dato faltante
                    siguiente_campo = order_service.obtener_siguiente_campo_faltante(state)
                    next_step = self._determinar_siguiente_paso(siguiente_campo)
                    self.set_step(state, next_step)
            else:
                # Modo guiado
                state["pedido_actual"]["cantidad"] = cantidad
                
                # Guardar el pedido actual en la lista
                state["pedidos"].append(dict(state["pedido_actual"]))
                
                # Limpiar pedido actual para el siguiente
                state["pedido_actual"] = {
                    "categoria": state["categoria_actual"],
                    "presentacion": "",
                    "tipo_producto": "",
                    "cantidad": 0,
                    "unidad": state["pedido_actual"]["unidad"]
                }
                
                self.set_step(state, "preguntar_mas_productos")
            
            return state
            
        except ValueError:
            error_msg = "❌ Por favor, ingresa una cantidad válida (número mayor a 0)"
            self.add_message(state, error_msg)
            self.set_step(state, StepType.ESPERANDO_CANTIDAD, waiting_for_input=True)
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

class MoreProductsQuestionNode(QuestionNode):
    """Nodo para preguntar si desea agregar más productos"""
    
    def __init__(self):
        question = "🤔 **¿Deseas agregar más productos al pedido?**\n\nResponde: Sí o No"
        super().__init__("preguntar_mas_productos", question, StepType.ESPERANDO_MAS_PRODUCTOS)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta mostrando un resumen de productos"""
        # Mostrar resumen del pedido actual
        resumen = "✅ **Producto agregado exitosamente!**\n\n"
        resumen += f"📋 **Resumen de productos hasta ahora ({len(state['pedidos'])} producto(s)):**\n\n"
        
        for i, pedido in enumerate(state["pedidos"], 1):
            resumen += f"**Producto {i}:**\n"
            resumen += f"• Categoría: {pedido['categoria']}\n"
            if pedido['categoria'] == ProductCategories.ENSACADO:
                resumen += f"• Presentación: {pedido['presentacion']}\n"
            resumen += f"• Tipo: {pedido['tipo_producto']}\n"
            resumen += f"• Cantidad: {pedido['cantidad']} {pedido['unidad']}\n\n"
        
        resumen += "🤔 **¿Deseas agregar más productos al pedido?**\n\nResponde: Sí o No"
        return resumen

class MoreProductsProcessingNode(ProcessingNode):
    """Nodo para procesar si desea más productos"""
    
    def __init__(self):
        valid_responses = ["sí", "si", "no"]
        super().__init__("procesar_mas_productos", valid_responses)
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa la respuesta sobre más productos"""
        last_message = user_message.lower()
        
        if "sí" in last_message or "si" in last_message:
            # Verificar si el mensaje contiene un nuevo pedido
            info_extraida = llm_service.extraer_informacion_pedido(user_message)
            
            if info_extraida.get("pedidos"):
                # Procesar los nuevos productos
                for pedido_info in info_extraida["pedidos"]:
                    pedido = order_service._crear_pedido_desde_extraccion(pedido_info)
                    if order_service._es_pedido_valido_parcial(pedido):
                        state["pedidos"].append(pedido)
                
                # Actualizar información faltante y cambiar a modo natural
                state["informacion_faltante"] = order_service.obtener_siguiente_campo_faltante(state)
                state["modo_conversacion"] = "natural"
                
                if not state["informacion_faltante"]:
                    self.set_step(state, "mostrar_resumen")
                else:
                    # Determinar siguiente paso
                    siguiente_campo = order_service.obtener_siguiente_campo_faltante(state)
                    next_step = self._determinar_siguiente_paso(siguiente_campo)
                    self.set_step(state, next_step)
            else:
                # Continuar en modo guiado con el mismo tipo de producto
                if state["categoria_actual"] == ProductCategories.ENSACADO:
                    self.set_step(state, "preguntar_presentacion")
                else:
                    self.set_step(state, "preguntar_tipo_producto")
        else:
            # No quiere más productos, continuar con entrega
            self.set_step(state, "preguntar_tipo_descargue")
        
        return state
    
    def _determinar_siguiente_paso(self, campo_faltante: str) -> str:
        """Determina el siguiente paso basado en el campo faltante"""
        if not campo_faltante:
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
            if clave in campo_faltante:
                return paso
        
        return "mostrar_resumen"

# Factory para crear nodos de productos
class ProductNodesFactory:
    """Factory para crear nodos de productos"""
    
    @staticmethod
    def create_all_product_nodes() -> dict:
        """Crea todos los nodos de productos"""
        return {
            "preguntar_categoria": CategoryQuestionNode(),
            "procesar_categoria": CategoryProcessingNode(),
            "preguntar_presentacion": PresentationQuestionNode(),
            "procesar_presentacion": PresentationProcessingNode(),
            "preguntar_tipo_producto": ProductTypeQuestionNode(),
            "procesar_tipo_producto": ProductTypeProcessingNode(),
            "preguntar_cantidad": QuantityQuestionNode(),
            "procesar_cantidad": QuantityProcessingNode(),
            "preguntar_mas_productos": MoreProductsQuestionNode(),
            "procesar_mas_productos": MoreProductsProcessingNode()
        }

# Crear instancias globales de los nodos
product_nodes = ProductNodesFactory.create_all_product_nodes()