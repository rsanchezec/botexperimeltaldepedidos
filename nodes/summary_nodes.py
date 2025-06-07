"""
Nodos para mostrar resumen y confirmación del pedido
"""
from datetime import datetime
from models.state import GraphState, StepType
from services.order_service import order_service
from .base_node import BaseNode, QuestionNode, ProcessingNode

class ShowSummaryNode(BaseNode):
    """Nodo para mostrar el resumen del pedido"""
    
    def __init__(self):
        super().__init__("mostrar_resumen")
    
    def execute(self, state: GraphState) -> GraphState:
        """Muestra el resumen del pedido y pregunta si desea modificar"""
        resumen = self._generar_resumen_completo(state)
        self.add_message(state, resumen)
        self.set_step(state, StepType.ESPERANDO_CONFIRMACION_MODIFICAR, waiting_for_input=True)
        return state
    
    def _generar_resumen_completo(self, state: GraphState) -> str:
        """Genera un resumen completo del pedido"""
        resumen = "📋 **RESUMEN DE TU PEDIDO**\n"
        resumen += f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        resumen += f"📦 **Productos ({len(state['pedidos'])} producto(s)):**\n"
        resumen += "=" * 40 + "\n\n"
        
        total_sacos = 0
        total_toneladas = 0
        
        for i, pedido in enumerate(state["pedidos"], 1):
            resumen += f"**📌 Producto {i}:**\n"
            resumen += f"   • Categoría: {pedido['categoria']}\n"
            if pedido['categoria'] == "Ensacado":
                resumen += f"   • Presentación: {pedido['presentacion']}\n"
                total_sacos += pedido['cantidad']
            else:
                total_toneladas += pedido['cantidad']
            resumen += f"   • Tipo: Cemento {pedido['tipo_producto']}\n"
            resumen += f"   • Cantidad: {pedido['cantidad']} {pedido['unidad']}\n\n"
        
        resumen += "=" * 40 + "\n"
        resumen += f"🚚 **Tipo de descargue:** {state['tipo_descargue']}\n"
        resumen += f"📍 **Tipo de entrega:** {state['tipo_entrega']}\n\n"
        
        if total_sacos > 0:
            resumen += f"📊 **Total sacos:** {total_sacos}\n"
        if total_toneladas > 0:
            resumen += f"📊 **Total toneladas:** {total_toneladas}\n"
        
        resumen += "\n✏️ **¿Deseas modificar algo del pedido?**\n\nResponde: Sí o No"
        
        return resumen

class ModificationConfirmationProcessingNode(ProcessingNode):
    """Nodo para procesar la confirmación de modificación"""
    
    def __init__(self):
        valid_responses = ["sí", "si", "no"]
        super().__init__("procesar_confirmacion_modificar", valid_responses)
    
    def is_valid_response(self, user_message: str) -> bool:
        """Verifica si la respuesta es válida"""
        user_lower = user_message.lower()
        return ("sí" in user_lower or "si" in user_lower or 
                "no" in user_lower or "n" == user_lower.strip())
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa la confirmación de modificación"""
        last_message = user_message.lower()
        
        if "sí" in last_message or "si" in last_message:
            # Usuario quiere modificar - ir a preguntar qué quiere modificar
            self.add_message(state, "✏️ Perfecto, vamos a modificar tu pedido.")
            self.set_step(state, "preguntar_que_elemento_modificar")
        else:
            # Usuario no quiere modificar - proceder con confirmación final
            self.add_message(state, "✅ Entendido, procederemos con la confirmación de tu pedido.")
            # Establecer el step pero sin waiting_for_input para que continúe el flujo
            self.set_step(state, "mostrar_confirmacion_final", waiting_for_input=False)
        
        return state

class FinalConfirmationNode(BaseNode):
    """Nodo para mostrar la confirmación final del pedido"""
    
    def __init__(self):
        super().__init__("mostrar_confirmacion_final")
    
    def execute(self, state: GraphState) -> GraphState:
        """Muestra la confirmación final y guarda el pedido"""
        # Intentar guardar en la base de datos
        usuario_id = state.get('usuario_id', 'web_user')
        resultado_db = order_service.guardar_pedido_confirmado(state, usuario_id)
        
        # Generar mensaje de confirmación
        mensaje_confirmacion = self._generar_mensaje_confirmacion(state, resultado_db)
        self.add_message(state, mensaje_confirmacion)
        
        # Finalizar conversación
        self.set_step(state, StepType.FIN, waiting_for_input=False)
        
        # Guardar el ID del pedido si fue exitoso
        if resultado_db.get('success'):
            state["pedido_guardado_id"] = resultado_db['pedido_id']
        
        return state
    
    def _generar_mensaje_confirmacion(self, state: GraphState, resultado_db: dict) -> str:
        """Genera el mensaje de confirmación final"""
        resumen = "🎉 **¡Pedido confirmado con éxito!**\n\n"
        
        # Si se guardó en la base de datos, mostrar el número de pedido
        if resultado_db.get('success'):
            resumen += f"📋 **Número de Pedido: #{resultado_db['pedido_id']}**\n"
        
        resumen += f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        resumen += f"📦 **PEDIDO FINAL ({len(state['pedidos'])} producto(s)):**\n"
        resumen += "=" * 40 + "\n\n"
        
        total_sacos = 0
        total_toneladas = 0
        
        for i, pedido in enumerate(state["pedidos"], 1):
            resumen += f"**📌 Producto {i}:**\n"
            resumen += f"   • Categoría: {pedido['categoria']}\n"
            if pedido['categoria'] == "Ensacado":
                resumen += f"   • Presentación: {pedido['presentacion']}\n"
                total_sacos += pedido['cantidad']
            else:
                total_toneladas += pedido['cantidad']
            resumen += f"   • Tipo: Cemento {pedido['tipo_producto']}\n"
            resumen += f"   • Cantidad: {pedido['cantidad']} {pedido['unidad']}\n\n"
        
        resumen += "=" * 40 + "\n"
        resumen += f"🚚 **Tipo de descargue:** {state['tipo_descargue']}\n"
        resumen += f"📍 **Tipo de entrega:** {state['tipo_entrega']}\n\n"
        
        if total_sacos > 0:
            resumen += f"📊 **Total sacos:** {total_sacos}\n"
        if total_toneladas > 0:
            resumen += f"📊 **Total toneladas:** {total_toneladas}\n"
        
        # Mensaje según el resultado del guardado
        if resultado_db.get('success'):
            resumen += f"\n✅ {resultado_db['mensaje']}\n"
            resumen += "\n✨ ¡Gracias por tu pedido! Un representante se pondrá en contacto contigo pronto.\n\n"
        else:
            resumen += "\n⚠️ Nota: Hubo un problema guardando el pedido en el sistema. "
            resumen += "Por favor, toma nota del resumen anterior.\n\n"
        
        resumen += "Si deseas hacer otro pedido, presiona el botón 'Nuevo Pedido'."
        
        return resumen

class OrderValidationNode(BaseNode):
    """Nodo para validar el pedido antes de guardarlo"""
    
    def __init__(self):
        super().__init__("validar_pedido")
    
    def execute(self, state: GraphState) -> GraphState:
        """Valida que el pedido esté completo y sea válido"""
        es_valido, errores = order_service.validar_pedido_completo(state)
        
        if es_valido:
            # El pedido es válido, continuar con confirmación
            self.set_step(state, "mostrar_confirmacion_final")
        else:
            # El pedido tiene errores, mostrar y solicitar corrección
            mensaje_error = self._generar_mensaje_errores(errores)
            self.add_message(state, mensaje_error)
            
            # Volver al resumen para permitir modificaciones
            self.set_step(state, "mostrar_resumen")
        
        return state
    
    def _generar_mensaje_errores(self, errores: list) -> str:
        """Genera un mensaje con los errores encontrados"""
        mensaje = "⚠️ **Se encontraron algunos problemas con tu pedido:**\n\n"
        
        for i, error in enumerate(errores, 1):
            mensaje += f"{i}. {error}\n"
        
        mensaje += "\nPor favor, revisa y corrige la información."
        return mensaje

# Factory para crear nodos de resumen
class WhatElementToModifyQuestionNode(QuestionNode):
    """Nodo para preguntar qué elemento del pedido modificar"""
    
    def __init__(self):
        question = "🔧 **¿Qué deseas modificar?**"
        super().__init__("preguntar_que_elemento_modificar", question, StepType.ESPERANDO_QUE_ELEMENTO_MODIFICAR)
    
    def format_question(self, state: GraphState) -> str:
        """Formatea la pregunta con las opciones disponibles"""
        mensaje = "🔧 **¿Qué deseas modificar?**\n\n"
        mensaje += "1. 📦 Productos (agregar, eliminar o cambiar productos)\n"
        mensaje += f"2. 🚚 Tipo de descargue (actualmente: {state.get('tipo_descargue', 'No definido')})\n"
        mensaje += f"3. 📍 Tipo de entrega (actualmente: {state.get('tipo_entrega', 'No definido')})\n\n"
        mensaje += "Por favor, escribe el número de la opción que deseas modificar."
        return mensaje

class WhatElementToModifyProcessingNode(ProcessingNode):
    """Nodo para procesar qué elemento modificar"""
    
    def __init__(self):
        super().__init__("procesar_que_elemento_modificar")
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa la selección del elemento a modificar"""
        try:
            opcion = int(user_message.strip())
            
            if opcion == 1:
                # Modificar productos
                self.set_step(state, "preguntar_producto_modificar")
            elif opcion == 2:
                # Modificar tipo de descargue
                self.set_step(state, "preguntar_nuevo_descargue")
            elif opcion == 3:
                # Modificar tipo de entrega
                self.set_step(state, "preguntar_nueva_entrega")
            else:
                error_msg = "❌ Por favor, selecciona una opción válida (1, 2 o 3)"
                self.add_message(state, error_msg)
                self.set_step(state, StepType.ESPERANDO_QUE_ELEMENTO_MODIFICAR, waiting_for_input=True)
            
            return state
            
        except ValueError:
            error_msg = "❌ Por favor, escribe solo el número de la opción (1, 2 o 3)"
            self.add_message(state, error_msg)
            self.set_step(state, StepType.ESPERANDO_QUE_ELEMENTO_MODIFICAR, waiting_for_input=True)
            return state

class NewDischargeQuestionNode(QuestionNode):
    """Nodo para preguntar nuevo tipo de descargue"""
    
    def __init__(self):
        question = "🚚 **¿Cuál es el nuevo tipo de descargue?**\n\n• Manual\n• Mecanizado\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_nuevo_descargue", question, StepType.ESPERANDO_NUEVO_DESCARGUE)

class NewDischargeProcessingNode(ProcessingNode):
    """Nodo para procesar nuevo tipo de descargue"""
    
    def __init__(self):
        valid_responses = ["manual", "mecanizado"]
        super().__init__("procesar_nuevo_descargue", valid_responses)
    
    def process_valid_response(self, state: GraphState, user_message: str) -> GraphState:
        """Procesa el nuevo tipo de descargue"""
        last_message = user_message.lower()
        
        if "manual" in last_message:
            state["tipo_descargue"] = "Manual"
            self.add_message(state, "✅ Tipo de descargue actualizado a Manual.")
        elif "mecanizado" in last_message:
            state["tipo_descargue"] = "Mecanizado"
            self.add_message(state, "✅ Tipo de descargue actualizado a Mecanizado.")
        else:
            return self.process_invalid_response(state, user_message)
        
        self.set_step(state, "mostrar_resumen")
        return state

class NewDeliveryQuestionNode(QuestionNode):
    """Nodo para preguntar nuevo tipo de entrega"""
    
    def __init__(self):
        question = "📍 **¿Cuál es el nuevo tipo de entrega?**\n\n• Entrega (nosotros te lo llevamos)\n• Retira (vienes a recogerlo)\n\nPor favor, escribe tu respuesta."
        super().__init__("preguntar_nueva_entrega", question, StepType.ESPERANDO_NUEVA_ENTREGA)

class NewDeliveryProcessingNode(ProcessingNode):
    """Nodo para procesar nuevo tipo de entrega"""
    
    def __init__(self):
        super().__init__("procesar_nueva_entrega")
    
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
        """Procesa el nuevo tipo de entrega"""
        last_message = user_message.lower()
        
        # Palabras clave para entrega
        entrega_keywords = ["entrega", "entreg", "llev", "domicilio", "llevar"]
        # Palabras clave para retira  
        retira_keywords = ["retira", "retir", "recog", "buscar", "recoger"]
        
        if any(keyword in last_message for keyword in entrega_keywords):
            state["tipo_entrega"] = "Entrega"
            self.add_message(state, "✅ Tipo de entrega actualizado a Entrega a domicilio.")
        elif any(keyword in last_message for keyword in retira_keywords):
            state["tipo_entrega"] = "Retira"
            self.add_message(state, "✅ Tipo de entrega actualizado a Retiro en planta.")
        else:
            error_msg = "❌ Por favor, selecciona una opción válida: Entrega o Retira"
            self.add_message(state, error_msg)
            self.set_step(state, StepType.ESPERANDO_NUEVA_ENTREGA, waiting_for_input=True)
            return state
        
        self.set_step(state, "mostrar_resumen")
        return state

class SummaryNodesFactory:
    """Factory para crear nodos de resumen"""
    
    @staticmethod
    def create_all_summary_nodes() -> dict:
        """Crea todos los nodos de resumen"""
        return {
            "mostrar_resumen": ShowSummaryNode(),
            "procesar_confirmacion_modificar": ModificationConfirmationProcessingNode(),
            "mostrar_confirmacion_final": FinalConfirmationNode(),
            "validar_pedido": OrderValidationNode(),
            "preguntar_que_elemento_modificar": WhatElementToModifyQuestionNode(),
            "procesar_que_elemento_modificar": WhatElementToModifyProcessingNode(),
            "preguntar_nuevo_descargue": NewDischargeQuestionNode(),
            "procesar_nuevo_descargue": NewDischargeProcessingNode(),
            "preguntar_nueva_entrega": NewDeliveryQuestionNode(),
            "procesar_nueva_entrega": NewDeliveryProcessingNode()
        }

# Crear instancias globales de los nodos
summary_nodes = SummaryNodesFactory.create_all_summary_nodes()