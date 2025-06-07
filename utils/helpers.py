"""
Funciones auxiliares para el bot de pedidos
"""
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from models.state import GraphState, PedidoItem

class DateTimeHelper:
    """Helper para manejo de fechas y horas"""
    
    @staticmethod
    def get_current_datetime_str(format_str: str = "%d/%m/%Y %H:%M") -> str:
        """
        Obtiene la fecha y hora actual como string
        
        Args:
            format_str: Formato de fecha deseado
            
        Returns:
            Fecha y hora formateada
        """
        return datetime.now().strftime(format_str)
    
    @staticmethod
    def get_current_date_str(format_str: str = "%d/%m/%Y") -> str:
        """
        Obtiene la fecha actual como string
        
        Args:
            format_str: Formato de fecha deseado
            
        Returns:
            Fecha formateada
        """
        return datetime.now().strftime(format_str)
    
    @staticmethod
    def parse_date_string(date_str: str, format_str: str = "%d/%m/%Y") -> Optional[datetime]:
        """
        Convierte string a datetime
        
        Args:
            date_str: String de fecha
            format_str: Formato esperado
            
        Returns:
            Objeto datetime o None si hay error
        """
        try:
            return datetime.strptime(date_str, format_str)
        except ValueError:
            return None

class TextHelper:
    """Helper para procesamiento de texto"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Limpia y normaliza texto
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        # Eliminar espacios extra
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalizar caracteres especiales
        text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i')
        text = text.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        text = text.replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
        text = text.replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')
        
        return text
    
    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """
        Extrae números de un texto
        
        Args:
            text: Texto del cual extraer números
            
        Returns:
            Lista de números encontrados
        """
        # Buscar números (enteros y decimales)
        pattern = r'\b\d+(?:[.,]\d+)?\b'
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            try:
                # Normalizar separador decimal
                normalized = match.replace(',', '.')
                numbers.append(float(normalized))
            except ValueError:
                continue
        
        return numbers
    
    @staticmethod
    def extract_kg_presentation(text: str) -> Optional[str]:
        """
        Extrae presentación en kg de un texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Presentación encontrada o None
        """
        pattern = r'(\d+)\s*kg'
        match = re.search(pattern, text.lower())
        
        if match:
            kg = match.group(1)
            return f"{kg} Kg"
        
        return None
    
    @staticmethod
    def format_currency(amount: float, currency: str = "COP") -> str:
        """
        Formatea cantidad como moneda
        
        Args:
            amount: Cantidad a formatear
            currency: Código de moneda
            
        Returns:
            Cantidad formateada
        """
        if currency == "COP":
            return f"${amount:,.0f} COP"
        else:
            return f"{amount:,.2f} {currency}"
    
    @staticmethod
    def pluralize(word: str, count: int) -> str:
        """
        Pluraliza una palabra según la cantidad
        
        Args:
            word: Palabra base
            count: Cantidad
            
        Returns:
            Palabra pluralizada si es necesario
        """
        if count == 1:
            return word
        
        # Reglas básicas de pluralización en español
        if word.endswith('s') or word.endswith('x') or word.endswith('z'):
            return word + "es"
        elif word.endswith('a') or word.endswith('e') or word.endswith('i') or word.endswith('o'):
            return word + "s"
        else:
            return word + "es"

class FormatHelper:
    """Helper para formateo de datos"""
    
    @staticmethod
    def format_product_summary(product: PedidoItem) -> str:
        """
        Formatea un producto para mostrar en resumen
        
        Args:
            product: Producto a formatear
            
        Returns:
            String formateado del producto
        """
        summary = f"{product['cantidad']} {product['unidad']} de cemento {product['tipo_producto']}"
        
        if product['categoria'] == "Ensacado" and product.get('presentacion'):
            summary += f" ({product['presentacion']})"
        
        return summary
    
    @staticmethod
    def format_order_totals(state: GraphState) -> Dict[str, Union[int, float]]:
        """
        Calcula y formatea totales del pedido
        
        Args:
            state: Estado del grafo con pedidos
            
        Returns:
            Diccionario con totales
        """
        total_sacos = 0
        total_toneladas = 0
        total_productos = len(state.get('pedidos', []))
        
        for producto in state.get('pedidos', []):
            if producto['categoria'] == 'Ensacado':
                total_sacos += producto['cantidad']
            elif producto['categoria'] == 'Granel':
                total_toneladas += producto['cantidad']
        
        return {
            'total_productos': total_productos,
            'total_sacos': total_sacos,
            'total_toneladas': total_toneladas
        }
    
    @staticmethod
    def format_statistics_text(stats: Dict[str, Any]) -> str:
        """
        Formatea estadísticas para mostrar al usuario
        
        Args:
            stats: Diccionario con estadísticas
            
        Returns:
            Texto formateado
        """
        if not stats:
            return "📊 No hay estadísticas disponibles."
        
        text = "📊 **Estadísticas del Sistema**\n\n"
        
        if 'total_pedidos' in stats:
            text += f"**Total de pedidos:** {stats['total_pedidos']}\n\n"
        
        if 'por_tipo_entrega' in stats and stats['por_tipo_entrega']:
            text += "**Por tipo de entrega:**\n"
            for tipo, cantidad in stats['por_tipo_entrega'].items():
                text += f"• {tipo}: {cantidad} pedidos\n"
            text += "\n"
        
        if 'productos_populares' in stats and stats['productos_populares']:
            text += "**Productos más pedidos:**\n"
            for producto, cantidad in stats['productos_populares']:
                text += f"• Cemento {producto}: {cantidad:.0f} unidades\n"
        
        return text

class ValidationHelper:
    """Helper para validaciones"""
    
    @staticmethod
    def is_valid_quantity(text: str) -> tuple[bool, Optional[float]]:
        """
        Valida si un texto representa una cantidad válida
        
        Args:
            text: Texto a validar
            
        Returns:
            Tupla (es_válido, valor_numérico)
        """
        try:
            # Normalizar separadores decimales
            normalized = text.replace(',', '.')
            value = float(normalized)
            
            if value > 0:
                return True, value
            else:
                return False, None
        except ValueError:
            return False, None
    
    @staticmethod
    def is_valid_presentation(text: str) -> tuple[bool, Optional[str]]:
        """
        Valida si un texto representa una presentación válida
        
        Args:
            text: Texto a validar
            
        Returns:
            Tupla (es_válido, presentación_normalizada)
        """
        valid_presentations = ["50 Kg", "45 Kg", "20 Kg"]
        
        # Extraer kg del texto
        presentation = TextHelper.extract_kg_presentation(text)
        
        if presentation and presentation in valid_presentations:
            return True, presentation
        
        return False, None
    
    @staticmethod
    def is_confirmation_response(text: str) -> tuple[bool, bool]:
        """
        Valida si un texto es una respuesta de confirmación
        
        Args:
            text: Texto a validar
            
        Returns:
            Tupla (es_válido, es_afirmativo)
        """
        text_clean = TextHelper.clean_text(text).lower()
        
        # Respuestas afirmativas
        yes_words = ['si', 'sí', 'yes', 'ok', 'vale', 'bueno', 'correcto', 'exacto']
        # Respuestas negativas
        no_words = ['no', 'nada', 'ninguno', 'incorrecto', 'falso']
        
        if any(word in text_clean for word in yes_words):
            return True, True
        elif any(word in text_clean for word in no_words):
            return True, False
        
        return False, False

class StateHelper:
    """Helper para manejo de estados"""
    
    @staticmethod
    def get_missing_fields_summary(state: GraphState) -> str:
        """
        Obtiene resumen de campos faltantes
        
        Args:
            state: Estado del grafo
            
        Returns:
            Resumen de campos faltantes
        """
        missing = state.get('informacion_faltante', [])
        
        if not missing:
            return "✅ Información completa"
        
        field_names = {
            'categoria': 'Categoría del producto',
            'presentacion': 'Presentación',
            'tipo_producto': 'Tipo de cemento',
            'cantidad': 'Cantidad',
            'tipo_descargue': 'Tipo de descargue',
            'tipo_entrega': 'Tipo de entrega'
        }
        
        missing_names = []
        for field in missing:
            for key, name in field_names.items():
                if key in field:
                    missing_names.append(name)
                    break
        
        return f"⚠️ Falta: {', '.join(missing_names)}"
    
    @staticmethod
    def is_order_complete(state: GraphState) -> bool:
        """
        Verifica si el pedido está completo
        
        Args:
            state: Estado del grafo
            
        Returns:
            True si el pedido está completo
        """
        required_fields = ['pedidos', 'tipo_descargue', 'tipo_entrega']
        
        for field in required_fields:
            if not state.get(field):
                return False
        
        # Verificar que todos los productos tengan información completa
        for producto in state.get('pedidos', []):
            if not all([
                producto.get('categoria'),
                producto.get('tipo_producto'),
                producto.get('cantidad', 0) > 0,
                producto.get('unidad')
            ]):
                return False
            
            # Si es ensacado, debe tener presentación
            if (producto.get('categoria') == 'Ensacado' and 
                not producto.get('presentacion')):
                return False
        
        return True
    
    @staticmethod
    def create_state_backup(state: GraphState) -> str:
        """
        Crea un respaldo del estado en formato JSON
        
        Args:
            state: Estado a respaldar
            
        Returns:
            Estado serializado como JSON
        """
        # Crear una copia del estado sin los mensajes (que no son serializables)
        backup_state = {
            'pedidos': state.get('pedidos', []),
            'tipo_descargue': state.get('tipo_descargue', ''),
            'tipo_entrega': state.get('tipo_entrega', ''),
            'current_step': state.get('current_step', ''),
            'modo_conversacion': state.get('modo_conversacion', ''),
            'informacion_faltante': state.get('informacion_faltante', []),
            'pedido_guardado_id': state.get('pedido_guardado_id')
        }
        
        return json.dumps(backup_state, ensure_ascii=False, indent=2)

class ErrorHelper:
    """Helper para manejo de errores"""
    
    @staticmethod
    def format_error_message(error: Exception, context: str = "") -> str:
        """
        Formatea un mensaje de error para el usuario
        
        Args:
            error: Excepción ocurrida
            context: Contexto adicional
            
        Returns:
            Mensaje de error formateado
        """
        base_message = "Lo siento, ocurrió un error inesperado."
        
        if context:
            base_message += f" {context}."
        
        # En producción, no mostrar detalles técnicos al usuario
        # En desarrollo, se pueden incluir más detalles
        return f"❌ {base_message} Por favor, intenta de nuevo."
    
    @staticmethod
    def log_error(error: Exception, context: str = "", extra_data: Dict[str, Any] = None):
        """
        Registra un error para debugging
        
        Args:
            error: Excepción ocurrida
            context: Contexto del error
            extra_data: Datos adicionales
        """
        timestamp = DateTimeHelper.get_current_datetime_str("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] ERROR"
        if context:
            log_entry += f" - {context}"
        
        log_entry += f": {str(error)}"
        
        if extra_data:
            log_entry += f" | Extra: {json.dumps(extra_data, default=str)}"
        
        print(log_entry)  # En producción, usar un logger apropiado