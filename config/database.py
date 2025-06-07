"""
Configuración y utilidades de base de datos
"""
import pyodbc
import traceback
from typing import Optional
from .settings import settings

class DatabaseManager:
    """Clase para manejar las operaciones de base de datos"""
    
    @staticmethod
    def get_connection() -> Optional[pyodbc.Connection]:
        """Crea y retorna una conexión a SQL Server"""
        try:
            conn_str = settings.get_db_connection_string()
            return pyodbc.connect(conn_str)
        except Exception as e:
            print(f"Error conectando a la base de datos: {e}")
            return None
    
    @staticmethod
    def test_connection() -> bool:
        """Prueba la conexión a la base de datos"""
        conn = DatabaseManager.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                return True
            except Exception as e:
                print(f"Error probando conexión: {e}")
                return False
        return False
    
    @staticmethod
    def create_tables() -> bool:
        """Crea las tablas necesarias en la base de datos"""
        conn = DatabaseManager.get_connection()
        if not conn:
            print("No se pudo conectar a la base de datos para crear tablas")
            return False
        
        cursor = conn.cursor()
        
        try:
            # Tabla de pedidos principales
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Pedidos' AND xtype='U')
            CREATE TABLE Pedidos (
                PedidoID INT IDENTITY(1,1) PRIMARY KEY,
                FechaPedido DATETIME NOT NULL DEFAULT GETDATE(),
                TipoDescargue VARCHAR(20) NOT NULL,
                TipoEntrega VARCHAR(20) NOT NULL,
                Estado VARCHAR(20) DEFAULT 'Confirmado',
                TotalSacos INT DEFAULT 0,
                TotalToneladas DECIMAL(10,2) DEFAULT 0,
                UsuarioID VARCHAR(100),
                Observaciones TEXT
            )
            """)
            
            # Tabla de detalle de productos
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DetallePedidos' AND xtype='U')
            CREATE TABLE DetallePedidos (
                DetalleID INT IDENTITY(1,1) PRIMARY KEY,
                PedidoID INT NOT NULL,
                Categoria VARCHAR(20) NOT NULL,
                Presentacion VARCHAR(20),
                TipoProducto VARCHAR(20) NOT NULL,
                Cantidad DECIMAL(10,2) NOT NULL,
                Unidad VARCHAR(20) NOT NULL,
                FOREIGN KEY (PedidoID) REFERENCES Pedidos(PedidoID)
            )
            """)
            
            # Tabla de log de conversaciones
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LogConversaciones' AND xtype='U')
            CREATE TABLE LogConversaciones (
                LogID INT IDENTITY(1,1) PRIMARY KEY,
                PedidoID INT,
                FechaHora DATETIME DEFAULT GETDATE(),
                Mensaje TEXT,
                TipoMensaje VARCHAR(10), -- 'Usuario' o 'Bot'
                FOREIGN KEY (PedidoID) REFERENCES Pedidos(PedidoID)
            )
            """)
            
            conn.commit()
            print("✅ Tablas creadas exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
            print(traceback.format_exc())
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_database_status() -> str:
        """Retorna el estado actual de la base de datos"""
        try:
            if DatabaseManager.test_connection():
                return "✅ Base de datos conectada"
            else:
                return "⚠️ Base de datos no disponible"
        except Exception:
            return "⚠️ Base de datos no configurada"

# Función de utilidad para inicializar la base de datos
def initialize_database() -> bool:
    """Inicializa la base de datos creando las tablas necesarias"""
    print("Inicializando base de datos...")
    
    # Verificar configuración
    if not settings.validate_settings():
        print("❌ Configuración de base de datos inválida")
        return False
    
    # Crear tablas
    return DatabaseManager.create_tables()

if __name__ == "__main__":
    # Ejecutar inicialización si se ejecuta directamente
    success = initialize_database()
    print(f"Inicialización {'exitosa' if success else 'fallida'}")
    print(f"Estado: {DatabaseManager.get_database_status()}")