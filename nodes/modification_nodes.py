"""
Nodos para la modificación de pedidos
"""
import re
from models.state import GraphState, StepType, ProductCategories
from services.order_service import order_service
from .base_node import QuestionNode, ProcessingNode
from config.settings import settings

class ProductModificationQuestionNode(QuestionNode):
    """Nodo para preguntar qué producto modificar"""
    
    def __init__(self):
        question = "🔧 **¿Qué producto deseas modificar?**"
        super().__init__("preguntar_producto_modificar", question, StepType.ESPERANDO_PRODUCTO_MODIFICAR)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta mostrando la lista de productos"""
        mensaje = "🔧 **¿Qué producto deseas modificar?**\n\n"
        
        for i, pedido in enumerate(state["pedidos"], 1):
            mensaje += f"**{i}.** {pedido['cantidad']} {pedido['unidad']} de cemento {pedido['tipo_producto']}"
            if pedido['categoria'] == ProductCategories.ENSACADO:
                mensaje += f" ({pedido['presentacion']})"
            mensaje += "\n"
        
        # Agregar opción para añadir producto nuevo
        mensaje += f"\n**{len(state['pedidos']) + 1}.** ➕ Agregar un producto nuevo\n"
        
        mensaje += "\nPor favor, escribe el número de la opción que deseas."
        return mensaje

class ProductModificationProcessingNode(ProcessingNode):
    """Nodo para procesar qué producto modificar"""
    
    def __init__(self):
        super().__init__("procesar_producto_modificar")
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa la selección del producto a modificar"""
        try:
            opcion_num = int(user_message.strip())
            
            # Verificar si es un producto existente
            if 1 <= opcion_num <= len(state["pedidos"]):
                state["producto_modificando"] = opcion_num - 1
                self.set_step(state, "preguntar_que_modificar")
                return state
            # Verificar si es la opción de agregar producto nuevo
            elif opcion_num == len(state["pedidos"]) + 1:
                self.add_message(state, "➕ **Agregar producto nuevo**\n\nVamos a agregar un nuevo producto a tu pedido.")
                state["modo_conversacion"] = "guiado"
                self.set_step(state, "preguntar_categoria")
                return state
            else:
                error_msg = f"❌ Por favor, selecciona un número válido entre 1 y {len(state['pedidos']) + 1}"
                self.add_message(state, error_msg)
                self.set_step(state, StepType.ESPERANDO_PRODUCTO_MODIFICAR, waiting_for_input=True)
                return state
        except ValueError:
            error_msg = "❌ Por favor, escribe solo el número de la opción que deseas"
            self.add_message(state, error_msg)
            self.set_step(state, StepType.ESPERANDO_PRODUCTO_MODIFICAR, waiting_for_input=True)
            return state

class WhatToModifyQuestionNode(QuestionNode):
    """Nodo para preguntar qué campo modificar"""
    
    def __init__(self):
        question = "📝 **¿Qué deseas modificar?**"
        super().__init__("preguntar_que_modificar", question, StepType.ESPERANDO_QUE_MODIFICAR)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta según el producto seleccionado"""
        if state.get("producto_modificando") is None:
            return "❌ Error: No hay producto seleccionado para modificar"
        
        producto = state["pedidos"][state["producto_modificando"]]
        
        mensaje = f"📝 **Modificando Producto {state['producto_modificando'] + 1}**\n\n"
        mensaje += f"**Producto actual:** {producto['cantidad']} {producto['unidad']} de cemento {producto['tipo_producto']}"
        if producto['categoria'] == ProductCategories.ENSACADO:
            mensaje += f" ({producto['presentacion']})"
        mensaje += "\n\n"
        
        mensaje += "**¿Qué deseas hacer?**\n\n"
        
        opciones = []
        if producto["categoria"] == ProductCategories.ENSACADO:
            opciones.append(f"1. ⚖️ Cambiar presentación (actual: {producto['presentacion']})")
            opciones.append(f"2. 🎨 Cambiar tipo de cemento (actual: {producto['tipo_producto']})")
            opciones.append(f"3. 🔢 Cambiar cantidad (actual: {producto['cantidad']} {producto['unidad']})")
            opciones.append("4. 🗑️ Eliminar este producto")
        else:  # Granel
            opciones.append(f"1. 🎨 Cambiar tipo de cemento (actual: {producto['tipo_producto']})")
            opciones.append(f"2. 🔢 Cambiar cantidad (actual: {producto['cantidad']} {producto['unidad']})")
            opciones.append("3. 🗑️ Eliminar este producto")
        
        mensaje += "\n".join(opciones)
        mensaje += "\n\n**Escribe el número de la opción que deseas:**"
        
        return mensaje

class WhatToModifyProcessingNode(ProcessingNode):
    """Nodo para procesar qué campo modificar"""
    
    def __init__(self):
        super().__init__("procesar_que_modificar")
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa la selección del campo a modificar"""
        try:
            opcion = int(user_message.strip())
            producto = state["pedidos"][state["producto_modificando"]]
            
            # Determinar qué se va a modificar basado en la opción
            if producto["categoria"] == ProductCategories.ENSACADO:
                if opcion == 1:
                    state["modificando_campo"] = "presentacion"
                    self.set_step(state, "preguntar_nueva_presentacion")
                elif opcion == 2:
                    state["modificando_campo"] = "tipo_producto"
                    self.set_step(state, "preguntar_nuevo_tipo")
                elif opcion == 3:
                    state["modificando_campo"] = "cantidad"
                    self.set_step(state, "preguntar_nueva_cantidad")
                elif opcion == 4:
                    return self._eliminar_producto(state)
                else:
                    return self._opcion_invalida(state)
            else:  # Granel
                if opcion == 1:
                    state["modificando_campo"] = "tipo_producto"
                    self.set_step(state, "preguntar_nuevo_tipo")
                elif opcion == 2:
                    state["modificando_campo"] = "cantidad"
                    self.set_step(state, "preguntar_nueva_cantidad")
                elif opcion == 3:
                    return self._eliminar_producto(state)
                else:
                    return self._opcion_invalida(state)
            
            return state
            
        except ValueError:
            error_msg = "❌ Por favor, escribe solo el número de la opción"
            self.add_message(state, error_msg)
            self.set_step(state, StepType.ESPERANDO_QUE_MODIFICAR, waiting_for_input=True)
            return state
    
    def _eliminar_producto(self, state: GraphState) -> GraphState:
        """Elimina el producto seleccionado"""
        state["pedidos"].pop(state["producto_modificando"])
        self.add_message(state, "✅ Producto eliminado exitosamente.")
        
        # Verificar si quedan productos
        if len(state["pedidos"]) > 0:
            self.set_step(state, "mostrar_resumen")
        else:
            self.add_message(state, "⚠️ No hay productos en el pedido. Agregando uno nuevo...")
            state["modo_conversacion"] = "guiado"
            self.set_step(state, "preguntar_categoria")
        
        return state
    
    def _opcion_invalida(self, state: GraphState) -> GraphState:
        """Maneja opción inválida"""
        producto = state["pedidos"][state["producto_modificando"]]
        if producto["categoria"] == ProductCategories.ENSACADO:
            error_msg = "❌ Por favor, selecciona una opción válida (1, 2, 3 o 4)"
        else:
            error_msg = "❌ Por favor, selecciona una opción válida (1, 2 o 3)"
        self.add_message(state, error_msg)
        self.set_step(state, StepType.ESPERANDO_QUE_MODIFICAR, waiting_for_input=True)
        return state

class NewPresentationQuestionNode(QuestionNode):
    """Nodo para preguntar nueva presentación"""
    
    def __init__(self):
        question = "⚖️ **¿Cuál es la nueva presentación?**\n\n• 50 Kg\n• 45 Kg\n• 20 Kg\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_nueva_presentacion", question, StepType.ESPERANDO_NUEVA_PRESENTACION)

class NewPresentationProcessingNode(ProcessingNode):
    """Nodo para procesar nueva presentación"""
    
    def __init__(self):
        super().__init__("procesar_nueva_presentacion")
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa la nueva presentación"""
        kg_match = re.search(r'(\d+)\s*kg', user_message.lower())
        
        if kg_match:
            kg = kg_match.group(1)
            nueva_presentacion = f"{kg} Kg"
            
            if nueva_presentacion in settings.VALID_PRESENTATIONS:
                state["pedidos"][state["producto_modificando"]]["presentacion"] = nueva_presentacion
                self.add_message(state, "✅ Presentación actualizada exitosamente.")
                self.set_step(state, "mostrar_resumen")
                return state
        
        error_msg = "❌ Por favor, especifica una presentación válida (ej: 50 Kg, 45 Kg, 20 Kg)"
        self.add_message(state, error_msg)
        self.set_step(state, StepType.ESPERANDO_NUEVA_PRESENTACION, waiting_for_input=True)
        return state

class NewTypeQuestionNode(QuestionNode):
    """Nodo para preguntar nuevo tipo de cemento"""
    
    def __init__(self):
        question = "🎨 **¿Cuál es el nuevo tipo de cemento?**\n\n• Blanco\n• Gris\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_nuevo_tipo", question, StepType.ESPERANDO_NUEVO_TIPO)

class NewTypeProcessingNode(ProcessingNode):
    """Nodo para procesar nuevo tipo de cemento"""
    
    def __init__(self):
        valid_responses = ["blanco", "gris"]
        super().__init__("procesar_nuevo_tipo", valid_responses)
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa el nuevo tipo de cemento"""
        last_message = user_message.lower()
        
        if "blanco" in last_message:
            state["pedidos"][state["producto_modificando"]]["tipo_producto"] = "Blanco"
            self.add_message(state, "✅ Tipo de cemento actualizado exitosamente.")
            self.set_step(state, "mostrar_resumen")
            return state
        elif "gris" in last_message:
            state["pedidos"][state["producto_modificando"]]["tipo_producto"] = "Gris"
            self.add_message(state, "✅ Tipo de cemento actualizado exitosamente.")
            self.set_step(state, "mostrar_resumen")
            return state
        else:
            return self.process_invalid_response(state, user_message)

class NewQuantityQuestionNode(QuestionNode):
    """Nodo para preguntar nueva cantidad"""
    
    def __init__(self):
        question = "🔢 **¿Cuál es la nueva cantidad?**"
        super().__init__("preguntar_nueva_cantidad", question, StepType.ESPERANDO_NUEVA_CANTIDAD)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta según la unidad del producto"""
        if state.get("producto_modificando") is not None:
            producto = state["pedidos"][state["producto_modificando"]]
            unidad = producto["unidad"]
            return f"🔢 **¿Cuál es la nueva cantidad de {unidad}?**\n\nPor favor, ingresa la cantidad en número."
        
        return self.question_text

class NewQuantityProcessingNode(ProcessingNode):
    """Nodo para procesar nueva cantidad"""
    
    def __init__(self):
        super().__init__("procesar_nueva_cantidad")
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa la nueva cantidad"""
        try:
            cantidad = float(user_message.replace(",", "."))
            if cantidad <= 0:
                raise ValueError("Cantidad debe ser mayor a 0")
            
            state["pedidos"][state["producto_modificando"]]["cantidad"] = cantidad
            self.add_message(state, "✅ Cantidad actualizada exitosamente.")
            self.set_step(state, "mostrar_resumen")
            return state
            
        except ValueError:
            error_msg = "❌ Por favor, ingresa una cantidad válida (número mayor a 0)"
            self.add_message(state, error_msg)
            self.set_step(state, StepType.ESPERANDO_NUEVA_CANTIDAD, waiting_for_input=True)
            return state

# Factory para crear nodos de modificación
class ModificationNodesFactory:
    """Factory para crear nodos de modificación"""
    
    @staticmethod
    def create_all_modification_nodes() -> dict:
        """Crea todos los nodos de modificación"""
        return {
            "preguntar_producto_modificar": ProductModificationQuestionNode(),
            "procesar_producto_modificar": ProductModificationProcessingNode(),
            "preguntar_que_modificar": WhatToModifyQuestionNode(),
            "procesar_que_modificar": WhatToModifyProcessingNode(),
            "preguntar_nueva_presentacion": NewPresentationQuestionNode(),
            "procesar_nueva_presentacion": NewPresentationProcessingNode(),
            "preguntar_nuevo_tipo": NewTypeQuestionNode(),
            "procesar_nuevo_tipo": NewTypeProcessingNode(),
            "preguntar_nueva_cantidad": NewQuantityQuestionNode(),
            "procesar_nueva_cantidad": NewQuantityProcessingNode()
        }

# Crear instancias globales de los nodos
modification_nodes = ModificationNodesFactory.create_all_modification_nodes()