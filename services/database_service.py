"""
Servicio para operaciones de base de datos
"""
from typing import Dict, Any, List, Optional, Tuple
import traceback
from langchain_core.messages import HumanMessage, AIMessage
from config.database import DatabaseManager
from models.state import GraphState, MessageTypes

class DatabaseService:
    """Servicio para todas las operaciones de base de datos"""
    
    @staticmethod
    def guardar_pedido(state: GraphState, usuario_id: str = None) -> Dict[str, Any]:
        """Guarda el pedido confirmado en la base de datos"""
        conn = DatabaseManager.get_connection()
        if not conn:
            return {"success": False, "error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        try:
            # Calcular totales
            total_sacos = sum(p['cantidad'] for p in state['pedidos'] if p['categoria'] == 'Ensacado')
            total_toneladas = sum(p['cantidad'] for p in state['pedidos'] if p['categoria'] == 'Granel')
            
            # Insertar pedido principal
            cursor.execute("""
            INSERT INTO Pedidos (TipoDescargue, TipoEntrega, TotalSacos, TotalToneladas, UsuarioID)
            VALUES (?, ?, ?, ?, ?)
            """, (state['tipo_descargue'], state['tipo_entrega'], total_sacos, total_toneladas, usuario_id))
            
            # Obtener el ID del pedido recién insertado usando @@IDENTITY
            cursor.execute("SELECT @@IDENTITY")
            result = cursor.fetchone()
            if result is None or result[0] is None:
                raise Exception("No se pudo obtener el ID del pedido recién insertado")
            pedido_id = int(result[0])
            
            # Insertar detalles del pedido
            for producto in state['pedidos']:
                cursor.execute("""
                INSERT INTO DetallePedidos (PedidoID, Categoria, Presentacion, TipoProducto, Cantidad, Unidad)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pedido_id,
                    producto['categoria'],
                    producto.get('presentacion', ''),
                    producto['tipo_producto'],
                    producto['cantidad'],
                    producto['unidad']
                ))
            
            # Guardar el historial de la conversación
            DatabaseService._guardar_historial_conversacion(cursor, pedido_id, state['messages'])
            
            conn.commit()
            
            return {
                "success": True, 
                "pedido_id": pedido_id,
                "mensaje": f"Pedido #{pedido_id} guardado exitosamente"
            }
            
        except Exception as e:
            conn.rollback()
            error_msg = f"Error guardando pedido: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return {"success": False, "error": error_msg}
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def _guardar_historial_conversacion(cursor, pedido_id: int, messages: List) -> None:
        """Guarda el historial de la conversación en la base de datos"""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                tipo_mensaje = MessageTypes.USUARIO
            elif isinstance(msg, AIMessage):
                tipo_mensaje = MessageTypes.BOT
            else:
                continue
                
            cursor.execute("""
            INSERT INTO LogConversaciones (PedidoID, Mensaje, TipoMensaje)
            VALUES (?, ?, ?)
            """, (pedido_id, msg.content, tipo_mensaje))
    
    @staticmethod
    def obtener_pedido_por_id(pedido_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un pedido específico por su ID"""
        conn = DatabaseManager.get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        try:
            # Obtener información del pedido principal
            cursor.execute("""
            SELECT PedidoID, FechaPedido, TipoDescargue, TipoEntrega, Estado, 
                   TotalSacos, TotalToneladas, UsuarioID, Observaciones
            FROM Pedidos 
            WHERE PedidoID = ?
            """, (pedido_id,))
            
            pedido_row = cursor.fetchone()
            if not pedido_row:
                return None
            
            # Convertir a diccionario
            pedido = {
                'pedido_id': pedido_row[0],
                'fecha_pedido': pedido_row[1],
                'tipo_descargue': pedido_row[2],
                'tipo_entrega': pedido_row[3],
                'estado': pedido_row[4],
                'total_sacos': pedido_row[5],
                'total_toneladas': pedido_row[6],
                'usuario_id': pedido_row[7],
                'observaciones': pedido_row[8]
            }
            
            # Obtener detalles del pedido
            cursor.execute("""
            SELECT Categoria, Presentacion, TipoProducto, Cantidad, Unidad
            FROM DetallePedidos 
            WHERE PedidoID = ?
            ORDER BY DetalleID
            """, (pedido_id,))
            
            productos = []
            for row in cursor.fetchall():
                productos.append({
                    'categoria': row[0],
                    'presentacion': row[1],
                    'tipo_producto': row[2],
                    'cantidad': row[3],
                    'unidad': row[4]
                })
            
            pedido['productos'] = productos
            return pedido
            
        except Exception as e:
            print(f"Error obteniendo pedido: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def obtener_estadisticas() -> Dict[str, Any]:
        """Obtiene estadísticas generales de los pedidos"""
        conn = DatabaseManager.get_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor()
        stats = {}
        
        try:
            # Total de pedidos
            cursor.execute("SELECT COUNT(*) FROM Pedidos")
            stats['total_pedidos'] = cursor.fetchone()[0]
            
            # Pedidos por tipo de entrega
            cursor.execute("""
            SELECT TipoEntrega, COUNT(*) 
            FROM Pedidos 
            GROUP BY TipoEntrega
            """)
            stats['por_tipo_entrega'] = dict(cursor.fetchall())
            
            # Productos más pedidos
            cursor.execute("""
            SELECT TOP 5 TipoProducto, SUM(Cantidad) as Total
            FROM DetallePedidos
            GROUP BY TipoProducto
            ORDER BY Total DESC
            """)
            stats['productos_populares'] = cursor.fetchall()
            
            # Pedidos por mes (últimos 6 meses)
            cursor.execute("""
            SELECT 
                FORMAT(FechaPedido, 'yyyy-MM') as Mes,
                COUNT(*) as Total
            FROM Pedidos 
            WHERE FechaPedido >= DATEADD(month, -6, GETDATE())
            GROUP BY FORMAT(FechaPedido, 'yyyy-MM')
            ORDER BY Mes DESC
            """)
            stats['pedidos_por_mes'] = cursor.fetchall()
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
        finally:
            cursor.close()
            conn.close()
        
        return stats
    
    @staticmethod
    def buscar_pedidos(filtros: Dict[str, Any] = None, limite: int = 50) -> List[Dict[str, Any]]:
        """Busca pedidos con filtros opcionales"""
        conn = DatabaseManager.get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        try:
            query = """
            SELECT PedidoID, FechaPedido, TipoDescargue, TipoEntrega, 
                   TotalSacos, TotalToneladas, UsuarioID
            FROM Pedidos 
            WHERE 1=1
            """
            params = []
            
            # Aplicar filtros si existen
            if filtros:
                if filtros.get('fecha_desde'):
                    query += " AND FechaPedido >= ?"
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    query += " AND FechaPedido <= ?"
                    params.append(filtros['fecha_hasta'])
                
                if filtros.get('tipo_entrega'):
                    query += " AND TipoEntrega = ?"
                    params.append(filtros['tipo_entrega'])
                
                if filtros.get('usuario_id'):
                    query += " AND UsuarioID = ?"
                    params.append(filtros['usuario_id'])
            
            query += f" ORDER BY FechaPedido DESC"
            
            # En SQL Server usamos TOP en lugar de LIMIT
            query = query.replace("SELECT ", f"SELECT TOP {limite} ")
            
            cursor.execute(query, params)
            
            pedidos = []
            for row in cursor.fetchall():
                pedidos.append({
                    'pedido_id': row[0],
                    'fecha_pedido': row[1],
                    'tipo_descargue': row[2],
                    'tipo_entrega': row[3],
                    'total_sacos': row[4],
                    'total_toneladas': row[5],
                    'usuario_id': row[6]
                })
            
            return pedidos
            
        except Exception as e:
            print(f"Error buscando pedidos: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def actualizar_estado_pedido(pedido_id: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de un pedido"""
        conn = DatabaseManager.get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            UPDATE Pedidos 
            SET Estado = ? 
            WHERE PedidoID = ?
            """, (nuevo_estado, pedido_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error actualizando estado del pedido: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()