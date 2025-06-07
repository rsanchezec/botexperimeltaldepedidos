"""
Punto de entrada principal del Bot de Pedidos de Cementos Argos
"""
import sys
import os
from typing import Optional

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from config.database import initialize_database, DatabaseManager
from controllers.graph_controller import GraphController
from ui.gradio_interface import create_gradio_interface

class CementoBotApp:
    """Clase principal de la aplicación"""
    
    def __init__(self):
        """Inicializa la aplicación"""
        self.graph_controller: Optional[GraphController] = None
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """
        Inicializa todos los componentes de la aplicación
        
        Returns:
            True si la inicialización fue exitosa
        """
        print("🚀 Iniciando Bot de Pedidos de Cementos Argos...")
        
        # Validar configuraciones
        if not self._validate_configuration():
            return False
        
        # Inicializar base de datos
        if not self._initialize_database():
            print("⚠️ Continuando sin base de datos...")
        
        # Inicializar controlador del grafo
        if not self._initialize_graph_controller():
            return False
        
        self.is_initialized = True
        print("✅ Aplicación inicializada exitosamente")
        return True
    
    def _validate_configuration(self) -> bool:
        """Valida las configuraciones críticas"""
        print("🔍 Validando configuraciones...")
        
        if not settings.validate_settings():
            print("❌ Error en configuraciones críticas")
            return False
        
        print("✅ Configuraciones validadas")
        return True
    
    def _initialize_database(self) -> bool:
        """Inicializa la base de datos"""
        print("🗄️ Inicializando base de datos...")
        
        try:
            success = initialize_database()
            if success:
                print("✅ Base de datos inicializada")
                return True
            else:
                print("⚠️ Error inicializando base de datos")
                return False
        except Exception as e:
            print(f"❌ Error en base de datos: {e}")
            return False
    
    def _initialize_graph_controller(self) -> bool:
        """Inicializa el controlador del grafo"""
        print("🤖 Inicializando controlador de conversación...")
        
        try:
            self.graph_controller = GraphController()
            print("✅ Controlador de conversación inicializado")
            return True
        except Exception as e:
            print(f"❌ Error inicializando controlador: {e}")
            return False
    
    def run(self, share: bool = None, debug: bool = None) -> None:
        """
        Ejecuta la aplicación
        
        Args:
            share: Si compartir la interfaz públicamente (None usa configuración)
            debug: Si activar modo debug (None usa configuración)
        """
        if not self.is_initialized:
            print("❌ Aplicación no inicializada. Ejecuta initialize() primero.")
            return
        
        print("🌐 Iniciando interfaz web...")
        
        # Usar configuraciones por defecto si no se especifican
        share = share if share is not None else settings.APP_SHARE
        debug = debug if debug is not None else settings.APP_DEBUG
        
        # Crear y lanzar la interfaz Gradio
        try:
            interface = create_gradio_interface(self.graph_controller)
            
            print(f"📱 Interfaz creada - Share: {share}, Debug: {debug}")
            print("🎯 La aplicación se está iniciando...")
            
            interface.launch(
                share=share,
                debug=debug,
                server_name="0.0.0.0",  # Permitir acceso desde otras IPs
                server_port=7860,       # Puerto por defecto de Gradio
                #show_tips=False,        # No mostrar tips de Gradio
                quiet=False             # Mostrar logs de Gradio
            )
            
        except Exception as e:
            print(f"❌ Error lanzando interfaz: {e}")
            raise
    
    def get_status(self) -> dict:
        """
        Obtiene el estado actual de la aplicación
        
        Returns:
            Diccionario con el estado de los componentes
        """
        status = {
            "initialized": self.is_initialized,
            "database": DatabaseManager.get_database_status(),
            "llm_configured": bool(settings.OPENAI_API_KEY),
            "graph_controller": self.graph_controller is not None
        }
        
        return status
    
    def shutdown(self) -> None:
        """Cierra la aplicación de forma segura"""
        print("🔄 Cerrando aplicación...")
        
        # Aquí se pueden agregar tareas de limpieza si es necesario
        # Por ejemplo, cerrar conexiones de base de datos, guardar logs, etc.
        
        print("✅ Aplicación cerrada")

def print_startup_banner():
    """Imprime el banner de inicio"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║           🏗️ BOT DE PEDIDOS - CEMENTOS ARGOS 🏗️                ║
    ║                        Versión Arturo_V3                        ║
    ║                                                                  ║
    ║              Asistente Virtual Inteligente con NLP               ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_system_info():
    """Imprime información del sistema"""
    print("📋 Información del sistema:")
    print(f"   • Modelo LLM: {settings.OPENAI_MODEL}")
    print(f"   • Base de datos: {settings.DB_CONFIG['server']}/{settings.DB_CONFIG['database']}")
    print(f"   • Modo debug: {settings.APP_DEBUG}")
    print(f"   • Compartir públicamente: {settings.APP_SHARE}")
    print()

def main():
    """Función principal"""
    try:
        # Mostrar banner de inicio
        print_startup_banner()
        print_system_info()
        
        # Crear y inicializar la aplicación
        app = CementoBotApp()
        
        if not app.initialize():
            print("❌ Error inicializando la aplicación")
            sys.exit(1)
        
        # Mostrar estado de la aplicación
        status = app.get_status()
        print("🔍 Estado de la aplicación:")
        for component, state in status.items():
            icon = "✅" if state else "❌"
            print(f"   {icon} {component}: {state}")
        print()
        
        # Ejecutar la aplicación
        print("🚀 Iniciando servidor web...")
        app.run()
        
    except KeyboardInterrupt:
        print("\n🔄 Cerrando aplicación por solicitud del usuario...")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("👋 ¡Hasta luego!")

if __name__ == "__main__":
    main()