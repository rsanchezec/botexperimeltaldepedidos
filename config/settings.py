"""
Configuraciones generales del proyecto
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings:
    """Clase para manejar todas las configuraciones de la aplicación"""
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3
    
    # Configuración de Base de Datos
    DB_CONFIG: Dict[str, str] = {
        'server': os.getenv("DB_SERVER", "localhost"),
        'database': os.getenv("DB_DATABASE", "cementosargos"),
        'username': os.getenv("DB_USERNAME", ""),
        'password': os.getenv("DB_PASSWORD", ""),
        'driver': os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}"),
        'encrypt': 'yes',
        'trust_cert': 'yes'
    }
    
    # Configuración de la aplicación
    APP_TITLE: str = os.getenv("APP_TITLE", "Bot de Pedidos Cementos Argos")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "True").lower() == "true"
    APP_SHARE: bool = os.getenv("APP_SHARE", "True").lower() == "true"
    
    # Configuración del bot
    MAX_ITERATIONS: int = 10
    DEFAULT_THREAD_ID: str = "1"
    
    # Validaciones de productos
    VALID_CATEGORIES = ["Ensacado", "Granel"]
    VALID_PRESENTATIONS = ["50 Kg", "45 Kg", "20 Kg"]
    VALID_CEMENT_TYPES = ["Blanco", "Gris"]
    VALID_DISCHARGE_TYPES = ["Manual", "Mecanizado"]
    VALID_DELIVERY_TYPES = ["Entrega", "Retira"]
    
    @classmethod
    def validate_settings(cls) -> bool:
        """Valida que las configuraciones críticas estén presentes"""
        if not cls.OPENAI_API_KEY:
            print("⚠️ ADVERTENCIA: OPENAI_API_KEY no está configurada")
            return False
        
        if not cls.DB_CONFIG['server'] or not cls.DB_CONFIG['database']:
            print("⚠️ ADVERTENCIA: Configuración de base de datos incompleta")
            return False
            
        return True
    
    @classmethod
    def get_db_connection_string(cls) -> str:
        """Retorna la cadena de conexión a la base de datos"""
        return (
            f"DRIVER={cls.DB_CONFIG['driver']};"
            f"SERVER={cls.DB_CONFIG['server']};"
            f"DATABASE={cls.DB_CONFIG['database']};"
            f"UID={cls.DB_CONFIG['username']};"
            f"PWD={cls.DB_CONFIG['password']}"
        )

# Instancia global de configuraciones
settings = Settings()

# Validar configuraciones al importar
if __name__ == "__main__":
    is_valid = settings.validate_settings()
    print(f"Configuraciones válidas: {is_valid}")
    print(f"API Key presente: {'Sí' if settings.OPENAI_API_KEY else 'No'}")
    print(f"DB Server: {settings.DB_CONFIG['server']}")
    print(f"DB Database: {settings.DB_CONFIG['database']}")