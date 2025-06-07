"""
Validadores para el bot de pedidos
"""
import re
from typing import List, Tuple, Optional, Any, Dict
from models.state import GraphState, PedidoItem
from config.settings import settings

class ProductValidator:
    """Validador para productos de cemento"""
    
    @staticmethod
    def validate_category(category: str) -> Tuple[bool, str]:
        """
        Valida la categoría del producto
        
        Args:
            category: Categoría a validar
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not category:
            return False, "La categoría es requerida"
        
        if category not in settings.VALID_CATEGORIES:
            return False, f"Categoría inválida. Opciones válidas: {', '.join(settings.VALID_CATEGORIES)}"
        
        return True, ""
    
    @staticmethod
    def validate_presentation(presentation: str, category: str) -> Tuple[bool, str]:
        """
        Valida la presentación del producto
        
        Args:
            presentation: Presentación a validar
            category: Categoría del producto
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if category == "Granel":
            # Granel no debe tener presentación
            if presentation:
                return False, "Los productos a granel no tienen presentación"
            return True, ""
        
        if category == "Ensacado":
            if not presentation:
                return False, "La presentación es requerida para productos ensacados"
            
            if presentation not in settings.VALID_PRESENTATIONS:
                return False, f"Presentación inválida. Opciones válidas: {', '.join(settings.VALID_PRESENTATIONS)}"
        
        return True, ""
    
    @staticmethod
    def validate_cement_type(cement_type: str) -> Tuple[bool, str]:
        """
        Valida el tipo de cemento
        
        Args:
            cement_type: Tipo de cemento a validar
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not cement_type:
            return False, "El tipo de cemento es requerido"
        
        if cement_type not in settings.VALID_CEMENT_TYPES:
            return False, f"Tipo de cemento inválido. Opciones válidas: {', '.join(settings.VALID_CEMENT_TYPES)}"
        
        return True, ""
    
    @staticmethod
    def validate_quantity(quantity: Any, category: str) -> Tuple[bool, str]:
        """
        Valida la cantidad del producto
        
        Args:
            quantity: Cantidad a validar
            category: Categoría del producto
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        try:
            qty = float(quantity)
        except (ValueError, TypeError):
            return False, "La cantidad debe ser un número válido"
        
        if qty <= 0:
            return False, "La cantidad debe ser mayor a 0"
        
        # Validaciones específicas por categoría
        if category == "Ensacado":
            if qty != int(qty):
                return False, "La cantidad de sacos debe ser un número entero"
            if qty > 10000:  # Límite razonable para sacos
                return False, "La cantidad de sacos parece excesiva (máximo 10,000)"
        
        elif category == "Granel":
            if qty > 1000:  # Límite razonable para toneladas
                return False, "La cantidad de toneladas parece excesiva (máximo 1,000)"
        
        return True, ""
    
    @staticmethod
    def validate_unit(unit: str, category: str) -> Tuple[bool, str]:
        """
        Valida la unidad del producto
        
        Args:
            unit: Unidad a validar
            category: Categoría del producto
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not unit:
            return False, "La unidad es requerida"
        
        if category == "Ensacado" and unit != "sacos":
            return False, "Los productos ensacados deben medirse en sacos"
        
        if category == "Granel" and unit != "toneladas":
            return False, "Los productos a granel deben medirse en toneladas"
        
        return True, ""
    
    @staticmethod
    def validate_complete_product(product: PedidoItem) -> Tuple[bool, List[str]]:
        """
        Valida un producto completo
        
        Args:
            product: Producto a validar
            
        Returns:
            Tupla (es_válido, lista_errores)
        """
        errors = []
        
        # Validar categoría
        is_valid, error = ProductValidator.validate_category(product.get('categoria', ''))
        if not is_valid:
            errors.append(error)
        
        category = product.get('categoria', '')
        
        # Validar presentación
        is_valid, error = ProductValidator.validate_presentation(
            product.get('presentacion', ''), category
        )
        if not is_valid:
            errors.append(error)
        
        # Validar tipo de cemento
        is_valid, error = ProductValidator.validate_cement_type(product.get('tipo_producto', ''))
        if not is_valid:
            errors.append(error)
        
        # Validar cantidad
        is_valid, error = ProductValidator.validate_quantity(
            product.get('cantidad', 0), category
        )
        if not is_valid:
            errors.append(error)
        
        # Validar unidad
        is_valid, error = ProductValidator.validate_unit(
            product.get('unidad', ''), category
        )
        if not is_valid:
            errors.append(error)
        
        return len(errors) == 0, errors

class DeliveryValidator:
    """Validador para información de entrega"""
    
    @staticmethod
    def validate_discharge_type(discharge_type: str) -> Tuple[bool, str]:
        """
        Valida el tipo de descargue
        
        Args:
            discharge_type: Tipo de descargue a validar
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not discharge_type:
            return False, "El tipo de descargue es requerido"
        
        if discharge_type not in settings.VALID_DISCHARGE_TYPES:
            return False, f"Tipo de descargue inválido. Opciones válidas: {', '.join(settings.VALID_DISCHARGE_TYPES)}"
        
        return True, ""
    
    @staticmethod
    def validate_delivery_type(delivery_type: str) -> Tuple[bool, str]:
        """
        Valida el tipo de entrega
        
        Args:
            delivery_type: Tipo de entrega a validar
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not delivery_type:
            return False, "El tipo de entrega es requerido"
        
        if delivery_type not in settings.VALID_DELIVERY_TYPES:
            return False, f"Tipo de entrega inválido. Opciones válidas: {', '.join(settings.VALID_DELIVERY_TYPES)}"
        
        return True, ""

class OrderValidator:
    """Validador para pedidos completos"""
    
    @staticmethod
    def validate_complete_order(state: GraphState) -> Tuple[bool, List[str]]:
        """
        Valida un pedido completo
        
        Args:
            state: Estado del grafo con el pedido
            
        Returns:
            Tupla (es_válido, lista_errores)
        """
        errors = []
        
        # Validar que hay productos
        products = state.get('pedidos', [])
        if not products:
            errors.append("El pedido debe tener al menos un producto")
            return False, errors
        
        # Validar cada producto
        for i, product in enumerate(products, 1):
            is_valid, product_errors = ProductValidator.validate_complete_product(product)
            if not is_valid:
                for error in product_errors:
                    errors.append(f"Producto {i}: {error}")
        
        # Validar tipo de descargue
        is_valid, error = DeliveryValidator.validate_discharge_type(
            state.get('tipo_descargue', '')
        )
        if not is_valid:
            errors.append(error)
        
        # Validar tipo de entrega
        is_valid, error = DeliveryValidator.validate_delivery_type(
            state.get('tipo_entrega', '')
        )
        if not is_valid:
            errors.append(error)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_order_business_rules(state: GraphState) -> Tuple[bool, List[str]]:
        """
        Valida reglas de negocio específicas del pedido
        
        Args:
            state: Estado del grafo con el pedido
            
        Returns:
            Tupla (es_válido, lista_advertencias)
        """
        warnings = []
        products = state.get('pedidos', [])
        
        # Calcular totales
        total_sacos = sum(p['cantidad'] for p in products if p['categoria'] == 'Ensacado')
        total_toneladas = sum(p['cantidad'] for p in products if p['categoria'] == 'Granel')
        
        # Advertencias por cantidades grandes
        if total_sacos > 1000:
            warnings.append(f"Cantidad elevada de sacos ({total_sacos}). Confirme disponibilidad.")
        
        if total_toneladas > 100:
            warnings.append(f"Cantidad elevada de toneladas ({total_toneladas}). Confirme logística.")
        
        # Advertencia por mezcla de tipos
        cement_types = set(p['tipo_producto'] for p in products)
        if len(cement_types) > 1:
            warnings.append("El pedido incluye diferentes tipos de cemento (Blanco y Gris).")
        
        # Advertencia por descargue manual con grandes cantidades
        if (state.get('tipo_descargue') == 'Manual' and 
            (total_sacos > 100 or total_toneladas > 10)):
            warnings.append("Descargue manual con gran cantidad. Considere descargue mecanizado.")
        
        return True, warnings

class InputValidator:
    """Validador para entradas de usuario"""
    
    @staticmethod
    def validate_numeric_input(input_text: str, allow_decimals: bool = True) -> Tuple[bool, Optional[float], str]:
        """
        Valida entrada numérica
        
        Args:
            input_text: Texto de entrada
            allow_decimals: Si se permiten decimales
            
        Returns:
            Tupla (es_válido, valor_numérico, mensaje_error)
        """
        if not input_text or not input_text.strip():
            return False, None, "Debe ingresar un número"
        
        # Limpiar el texto
        cleaned = input_text.strip().replace(',', '.')
        
        try:
            value = float(cleaned)
            
            if not allow_decimals and value != int(value):
                return False, None, "Debe ser un número entero"
            
            if value <= 0:
                return False, None, "El número debe ser mayor a 0"
            
            return True, value, ""
            
        except ValueError:
            return False, None, "Formato de número inválido"
    
    @staticmethod
    def validate_choice_input(input_text: str, valid_choices: List[str], 
                            case_sensitive: bool = False) -> Tuple[bool, Optional[str], str]:
        """
        Valida entrada de opción múltiple
        
        Args:
            input_text: Texto de entrada
            valid_choices: Opciones válidas
            case_sensitive: Si es sensible a mayúsculas
            
        Returns:
            Tupla (es_válido, opción_seleccionada, mensaje_error)
        """
        if not input_text or not input_text.strip():
            return False, None, "Debe seleccionar una opción"
        
        cleaned_input = input_text.strip()
        if not case_sensitive:
            cleaned_input = cleaned_input.lower()
        
        # Buscar coincidencia exacta o parcial
        for choice in valid_choices:
            choice_to_compare = choice if case_sensitive else choice.lower()
            
            if (cleaned_input == choice_to_compare or 
                cleaned_input in choice_to_compare or
                choice_to_compare in cleaned_input):
                return True, choice, ""
        
        choices_str = ", ".join(valid_choices)
        return False, None, f"Opción inválida. Opciones válidas: {choices_str}"
    
    @staticmethod
    def validate_yes_no_input(input_text: str) -> Tuple[bool, Optional[bool], str]:
        """
        Valida entrada sí/no
        
        Args:
            input_text: Texto de entrada
            
        Returns:
            Tupla (es_válido, valor_booleano, mensaje_error)
        """
        if not input_text or not input_text.strip():
            return False, None, "Debe responder Sí o No"
        
        cleaned = input_text.strip().lower()
        
        # Palabras afirmativas
        yes_words = ['si', 'sí', 'yes', 'y', 'ok', 'vale', 'correcto', 'exacto', '1']
        # Palabras negativas
        no_words = ['no', 'n', 'nada', 'ninguno', 'incorrecto', '0']
        
        if any(word in cleaned for word in yes_words):
            return True, True, ""
        elif any(word in cleaned for word in no_words):
            return True, False, ""
        
        return False, None, "Respuesta no reconocida. Por favor responda 'Sí' o 'No'"

class TextValidator:
    """Validador para texto y formato"""
    
    @staticmethod
    def validate_text_length(text: str, min_length: int = 1, max_length: int = 1000) -> Tuple[bool, str]:
        """
        Valida longitud de texto
        
        Args:
            text: Texto a validar
            min_length: Longitud mínima
            max_length: Longitud máxima
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not text:
            return False, f"El texto debe tener al menos {min_length} caracteres"
        
        length = len(text.strip())
        
        if length < min_length:
            return False, f"El texto debe tener al menos {min_length} caracteres"
        
        if length > max_length:
            return False, f"El texto no puede exceder {max_length} caracteres"
        
        return True, ""
    
    @staticmethod
    def contains_dangerous_content(text: str) -> Tuple[bool, str]:
        """
        Verifica si el texto contiene contenido peligroso
        
        Args:
            text: Texto a verificar
            
        Returns:
            Tupla (contiene_peligro, descripción)
        """
        if not text:
            return False, ""
        
        text_lower = text.lower()
        
        # Patrones peligrosos básicos
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower):
                return True, "Contenido potencialmente peligroso detectado"
        
        return False, ""
    
    @staticmethod
    def extract_and_validate_kg(text: str) -> Tuple[bool, Optional[str], str]:
        """
        Extrae y valida presentación en kg
        
        Args:
            text: Texto de entrada
            
        Returns:
            Tupla (es_válido, presentación_extraída, mensaje_error)
        """
        pattern = r'(\d+)\s*kg'
        match = re.search(pattern, text.lower())
        
        if not match:
            return False, None, "No se encontró una presentación válida en kg"
        
        kg_value = match.group(1)
        presentation = f"{kg_value} Kg"
        
        if presentation not in settings.VALID_PRESENTATIONS:
            valid_pres = ", ".join(settings.VALID_PRESENTATIONS)
            return False, None, f"Presentación inválida. Opciones válidas: {valid_pres}"
        
        return True, presentation, ""

# Funciones de utilidad para validación rápida

def quick_validate_product(product: Dict[str, Any]) -> bool:
    """Validación rápida de producto"""
    is_valid, _ = ProductValidator.validate_complete_product(product)
    return is_valid

def quick_validate_order(state: GraphState) -> bool:
    """Validación rápida de pedido"""
    is_valid, _ = OrderValidator.validate_complete_order(state)
    return is_valid

def sanitize_user_input(text: str) -> str:
    """Sanitiza entrada del usuario"""
    if not text:
        return ""
    
    # Eliminar caracteres peligrosos
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limpiar espacios extra
    sanitized = re.sub(r'\s+', ' ', sanitized.strip())
    
    return sanitized