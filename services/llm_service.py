"""
Servicio para interacciones con el modelo de lenguaje (OpenAI)
"""
import json
import re
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import settings

class LLMService:
    """Servicio para todas las operaciones con el modelo de lenguaje"""
    
    def __init__(self):
        """Inicializa el servicio LLM"""
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
    
    def extraer_informacion_pedido(self, mensaje: str) -> Dict[str, Any]:
        """Usa el LLM para extraer información del pedido del mensaje del usuario"""
        
        system_prompt = """Eres un asistente que extrae información de pedidos de cemento.
        Debes extraer la siguiente información del mensaje del usuario:
        
        1. Productos (puede haber múltiples):
           - categoria: "Ensacado" o "Granel"
           - presentacion: "50 Kg", "45 Kg", "20 Kg", etc. (solo para ensacado)
           - tipo_producto: "Blanco" o "Gris"
           - cantidad: número
           - unidad: "sacos" (para ensacado) o "toneladas" (para granel)
        
        2. tipo_descargue: "Manual" o "Mecanizado"
        3. tipo_entrega: "Entrega" o "Retira"
        
        IMPORTANTE: 
        - Si mencionan "descarga manual", "manual", o "a mano" -> tipo_descargue: "Manual"
        - Si mencionan "entrega", "entregar", "domicilio", "llevar" -> tipo_entrega: "Entrega"
        - Si mencionan "retira", "retirar", "recoger", "buscar" -> tipo_entrega: "Retira"
        - Si mencionan "mecanizado", "grúa", "montacargas" -> tipo_descargue: "Mecanizado"
        
        Responde SOLO con un JSON válido con la estructura:
        {
            "pedidos": [
                {
                    "categoria": "Ensacado/Granel",
                    "presentacion": "XX Kg" (solo si es ensacado),
                    "tipo_producto": "Blanco/Gris",
                    "cantidad": número,
                    "unidad": "sacos/toneladas"
                }
            ],
            "tipo_descargue": "Manual/Mecanizado" o null,
            "tipo_entrega": "Entrega/Retira" o null
        }
        
        Si no encuentras alguna información, usa null.
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Extrae la información del siguiente pedido: {mensaje}")
            ])
            
            # Limpiar la respuesta para obtener solo el JSON
            json_str = response.content.strip()
            # Encontrar el JSON en la respuesta
            json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            
            result = json.loads(json_str)
            
            # Validar y limpiar el resultado
            return self._validar_y_limpiar_extraccion(result)
            
        except Exception as e:
            print(f"Error extrayendo información: {e}")
            return {"pedidos": [], "tipo_descargue": None, "tipo_entrega": None}
    
    def _validar_y_limpiar_extraccion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y limpia los datos extraídos por el LLM"""
        resultado = {
            "pedidos": [],
            "tipo_descargue": None,
            "tipo_entrega": None
        }
        
        # Validar y limpiar pedidos
        if "pedidos" in data and isinstance(data["pedidos"], list):
            for pedido in data["pedidos"]:
                if isinstance(pedido, dict):
                    pedido_limpio = self._limpiar_producto(pedido)
                    if pedido_limpio:
                        resultado["pedidos"].append(pedido_limpio)
        
        # Validar tipo de descargue
        if data.get("tipo_descargue") in settings.VALID_DISCHARGE_TYPES:
            resultado["tipo_descargue"] = data["tipo_descargue"]
        
        # Validar tipo de entrega
        if data.get("tipo_entrega") in settings.VALID_DELIVERY_TYPES:
            resultado["tipo_entrega"] = data["tipo_entrega"]
        
        return resultado
    
    def _limpiar_producto(self, producto: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia y valida un producto individual"""
        producto_limpio = {
            "categoria": "",
            "presentacion": "",
            "tipo_producto": "",
            "cantidad": 0,
            "unidad": ""
        }
        
        # Limpiar categoría
        categoria = producto.get("categoria", "")
        if categoria in settings.VALID_CATEGORIES:
            producto_limpio["categoria"] = categoria
        
        # Limpiar presentación (solo para ensacado)
        presentacion = producto.get("presentacion", "")
        if producto_limpio["categoria"] == "Ensacado" and presentacion in settings.VALID_PRESENTATIONS:
            producto_limpio["presentacion"] = presentacion
        
        # Limpiar tipo de producto
        tipo_producto = producto.get("tipo_producto", "")
        if tipo_producto in settings.VALID_CEMENT_TYPES:
            producto_limpio["tipo_producto"] = tipo_producto
        
        # Limpiar cantidad
        try:
            cantidad = float(producto.get("cantidad", 0))
            if cantidad > 0:
                producto_limpio["cantidad"] = cantidad
        except (ValueError, TypeError):
            pass
        
        # Limpiar unidad
        unidad = producto.get("unidad", "")
        if unidad in ["sacos", "toneladas"]:
            producto_limpio["unidad"] = unidad
        
        # Validar coherencia
        if producto_limpio["categoria"] == "Ensacado" and producto_limpio["unidad"] != "sacos":
            producto_limpio["unidad"] = "sacos"
        elif producto_limpio["categoria"] == "Granel" and producto_limpio["unidad"] != "toneladas":
            producto_limpio["unidad"] = "toneladas"
            producto_limpio["presentacion"] = ""  # Granel no tiene presentación
        
        # Solo retornar si tiene información mínima válida
        if (producto_limpio["categoria"] and 
            producto_limpio["cantidad"] > 0 and 
            producto_limpio["unidad"]):
            return producto_limpio
        
        return None
    
    def analizar_respuesta_usuario(self, mensaje: str, contexto: str = "") -> Dict[str, Any]:
        """Analiza una respuesta del usuario en contexto específico"""
        
        system_prompt = f"""Eres un asistente que analiza respuestas de usuarios en un contexto específico.
        
        Contexto actual: {contexto}
        
        Analiza la respuesta del usuario y determina:
        1. intent: qué quiere hacer el usuario
        2. entities: entidades específicas mencionadas
        3. confidence: qué tan seguro estás de la interpretación (0-1)
        4. action: acción recomendada
        
        Responde en JSON:
        {{
            "intent": "string",
            "entities": {{}},
            "confidence": float,
            "action": "string"
        }}
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=mensaje)
            ])
            
            json_str = response.content.strip()
            json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            
            return json.loads(json_str)
            
        except Exception as e:
            print(f"Error analizando respuesta: {e}")
            return {
                "intent": "unknown",
                "entities": {},
                "confidence": 0.0,
                "action": "clarify"
            }
    
    def generar_respuesta_personalizada(self, contexto: str, datos_usuario: Dict[str, Any]) -> str:
        """Genera una respuesta personalizada basada en el contexto y datos del usuario"""
        
        system_prompt = """Eres Arturo_V3, un asistente virtual especializado en pedidos de cemento de Cementos Argos.
        Eres amigable, profesional y eficiente. 
        
        Genera una respuesta apropiada para el contexto dado, usando los datos del usuario proporcionados.
        La respuesta debe ser clara, concisa y útil.
        """
        
        user_prompt = f"""
        Contexto: {contexto}
        Datos del usuario: {json.dumps(datos_usuario, indent=2)}
        
        Genera una respuesta apropiada.
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generando respuesta personalizada: {e}")
            return "Lo siento, hubo un error procesando tu solicitud. ¿Podrías intentar de nuevo?"
    
    def validar_entrada_usuario(self, entrada: str, tipo_esperado: str) -> Dict[str, Any]:
        """Valida si la entrada del usuario corresponde al tipo esperado"""
        
        validaciones = {
            "categoria": settings.VALID_CATEGORIES,
            "presentacion": settings.VALID_PRESENTATIONS,
            "tipo_producto": settings.VALID_CEMENT_TYPES,
            "tipo_descargue": settings.VALID_DISCHARGE_TYPES,
            "tipo_entrega": settings.VALID_DELIVERY_TYPES,
            "cantidad": "numeric",
            "confirmacion": ["si", "sí", "no"]
        }
        
        entrada_lower = entrada.lower().strip()
        
        if tipo_esperado == "cantidad":
            try:
                cantidad = float(entrada.replace(",", "."))
                return {
                    "valido": cantidad > 0,
                    "valor": cantidad if cantidad > 0 else None,
                    "mensaje": None if cantidad > 0 else "La cantidad debe ser mayor a 0"
                }
            except ValueError:
                return {
                    "valido": False,
                    "valor": None,
                    "mensaje": "Por favor, ingresa un número válido"
                }
        
        elif tipo_esperado == "confirmacion":
            if any(palabra in entrada_lower for palabra in ["sí", "si", "yes", "y"]):
                return {"valido": True, "valor": True, "mensaje": None}
            elif any(palabra in entrada_lower for palabra in ["no", "n"]):
                return {"valido": True, "valor": False, "mensaje": None}
            else:
                return {
                    "valido": False,
                    "valor": None,
                    "mensaje": "Por favor, responde con 'Sí' o 'No'"
                }
        
        else:
            # Validación por lista de valores válidos
            valores_validos = validaciones.get(tipo_esperado, [])
            
            for valor in valores_validos:
                if valor.lower() in entrada_lower:
                    return {"valido": True, "valor": valor, "mensaje": None}
            
            return {
                "valido": False,
                "valor": None,
                "mensaje": f"Por favor, selecciona una opción válida: {', '.join(valores_validos)}"
            }

# Instancia global del servicio LLM
llm_service = LLMService()