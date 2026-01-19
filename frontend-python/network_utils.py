import ipaddress
import psycopg2
import pandas as pd
import hashlib
from sqlalchemy import create_engine

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_URL = "postgresql+psycopg2://admin_red:password123@127.0.0.1:5432/gestion_ips"

def obtener_motor():
    return create_engine(DB_URL)

def conectar_db():
    return psycopg2.connect(
        host="127.0.0.1", 
        port="5432", 
        database="gestion_ips", 
        user="admin_red", 
        password="password123"
    )

# --- GESTIÓN DE SEGMENTOS Y COLISIONES ---

def verificar_colision(nueva_red_str, tabla, columna_red, excluir_id=None):
    """Verifica si una red se traslapa con otras existentes en la base de datos"""
    try:
        nueva_red = ipaddress.IPv4Network(nueva_red_str, strict=False)
        engine = obtener_motor()
        query = f"SELECT id, {columna_red} FROM {tabla}"
        if excluir_id: 
            query += f" WHERE id != {excluir_id}"
        
        df = pd.read_sql(query, engine)
        for _, row in df.iterrows():
            red_existente = ipaddress.IPv4Network(row[columna_red])
            if nueva_red.overlaps(red_existente):
                return True, row[columna_red]
        return False, None
    except Exception as e:
        return True, f"Error de formato: {str(e)}"

def calcular_subred_por_hosts(segmento_maestro_str, num_hosts, subredes_ocupadas_list):
    """Encuentra la primera subred disponible para un número X de hosts"""
    try:
        maestro = ipaddress.IPv4Network(segmento_maestro_str)
        # 32 - bits necesarios (hosts + red + broadcast)
        nuevo_prefijo = 32 - (num_hosts + 2 - 1).bit_length()
        
        posibles_subredes = list(maestro.subnets(new_prefix=nuevo_prefijo))
        ocupadas = [ipaddress.IPv4Network(s) for s in subredes_ocupadas_list]
        
        for sub in posibles_subredes:
            if not any(sub.overlaps(o) for o in ocupadas):
                return str(sub)
        return None
    except:
        return None

# --- CÁLCULOS TÉCNICOS DE RED ---

def obtener_detalles_red(subred_cidr):
    """Calcula Gateway, Máscara Decimal y Rangos usables"""
    try:
        red = ipaddress.IPv4Network(subred_cidr)
        return {
            "mask_decimal": str(red.netmask),
            "gateway": str(red.network_address + 1),
            "primera_usable": str(red.network_address + 1),
            "ultima_usable": str(red.broadcast_address - 1),
            "broadcast": str(red.broadcast_address),
            "total_hosts": max(0, red.num_addresses - 2)
        }
    except:
        return {"mask_decimal": "N/A", "gateway": "N/A", "primera_usable": "N/A", "ultima_usable": "N/A", "broadcast": "N/A", "total_hosts": 0}

def calcular_uso_red(segmento_maestro, subredes_totales):
    """Calcula el porcentaje de ocupación de un segmento principal (Global)"""
    try:
        maestro = ipaddress.IPv4Network(segmento_maestro)
        total_ips = maestro.num_addresses
        ocupadas_en_maestro = 0
        for s in subredes_totales:
            red_s = ipaddress.IPv4Network(s)
            if red_s.subnet_of(maestro):
                ocupadas_en_maestro += red_s.num_addresses
        
        porc = (ocupadas_en_maestro / total_ips) * 100
        return round(porc, 2), total_ips, ocupadas_en_maestro
    except:
        return 0.0, 0, 0

# --- ALGORITMO DE ESTADO Y CUPO (DINÁMICO) ---

def calcular_estado_segmento(segmento_cidr):
    """Calcula detalladamente IPs libres y ocupadas sumando solicitudes aprobadas."""
    try:
        red = ipaddress.IPv4Network(segmento_cidr)
        # Capacidad: Total - (Red + Broadcast + Gateway)
        capacidad_maxima = max(0, red.num_addresses - 3)
        
        engine = obtener_motor()
        # Query que une la asignación base con solicitudes de grupos aprobadas
        q = f"""
            SELECT 
                (SELECT COALESCE(SUM(num_ips_solicitadas), 0) FROM rangos_unidades WHERE segmento_asignado = '{segmento_cidr}') +
                (SELECT COALESCE(SUM(cantidad_ips), 0) FROM solicitudes_ip WHERE estado = 'Aprobado' AND unidad_id IN 
                    (SELECT unidad_id FROM rangos_unidades WHERE segmento_asignado = '{segmento_cidr}')
                ) as total_ocupado
        """
        res = pd.read_sql(q, engine)
        ocupadas = int(res['total_ocupado'][0]) if res['total_ocupado'][0] is not None else 1
        
        libres = max(0, capacidad_maxima - ocupadas)
        porcentaje = round((ocupadas / capacidad_maxima) * 100, 1) if capacidad_maxima > 0 else 0
        
        # Lógica de semáforo CELEC
        color = "green" if porcentaje < 50 else "orange" if porcentaje < 85 else "red"
        
        return {
            "total": capacidad_maxima,
            "ocupadas": ocupadas,
            "libres": libres,
            "porcentaje": porcentaje,
            "color": color,
            "ocupadas": ocupadas
        }
    except:
        return {"porcentaje": 0, "color": "gray", "libres": 0, "ocupadas": 0, "total": 0}

def verificar_capacidad_disponible(segmento_cidr, ips_solicitadas):
    """Verifica si un segmento tiene suficientes IPs libres antes de permitir una solicitud."""
    try:
        estado = calcular_estado_segmento(segmento_cidr)
        disponible = estado['libres']
        return disponible >= int(ips_solicitadas), disponible
    except:
        return False, 0

# --- GESTIÓN DE USUARIOS Y SOLICITUDES ---

def generar_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def crear_usuario_unidad(unidad_id, username, password_plano):
    try:
        conn = conectar_db(); cur = conn.cursor()
        hash_pw = generar_hash(password_plano)
        cur.execute("""
            INSERT INTO usuarios_unidades (unidad_id, username, password_hash, es_temporal)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash, es_temporal = TRUE
        """, (unidad_id, username, hash_pw))
        conn.commit(); cur.close(); conn.close()
        return True
    except:
        return False

def enviar_solicitud_ip(unidad_id, nombre_grupo, cantidad):
    try:
        conn = conectar_db(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO solicitudes_ip (unidad_id, nombre_grupo, cantidad_ips, estado)
            VALUES (%s, %s, %s, 'Pendiente')
        """, (unidad_id, nombre_grupo, cantidad))
        conn.commit(); cur.close(); conn.close()
        return True
    except:
        return False

def obtener_usuarios_registrados():
    engine = obtener_motor()
    query = """
        SELECT u.id, n.nombre as unidad, u.username, u.es_temporal 
        FROM usuarios_unidades u
        JOIN unidades_negocio n ON u.unidad_id = n.id
    """
    return pd.read_sql(query, engine)

def inicializar_tablas_faltantes():
    """Crea las tablas de seguridad y solicitudes si no existen en la DB."""
    conn = conectar_db(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_unidades (
            id SERIAL PRIMARY KEY,
            unidad_id INTEGER REFERENCES unidades_negocio(id) ON DELETE CASCADE,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            es_temporal BOOLEAN DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS solicitudes_ip (
            id SERIAL PRIMARY KEY,
            unidad_id INTEGER REFERENCES unidades_negocio(id) ON DELETE CASCADE,
            nombre_grupo VARCHAR(100),
            cantidad_ips INTEGER,
            estado VARCHAR(20) DEFAULT 'Pendiente',
            fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit(); cur.close(); conn.close()

def calcular_estado_segmento(segmento_cidr):
    import ipaddress
    try:
        red = ipaddress.IPv4Network(segmento_cidr)
        # Capacidad física real
        capacidad_maxima = max(1, red.num_addresses - 3) 
        
        engine = obtener_motor()
        q = f"""
            SELECT 
                (SELECT COALESCE(SUM(num_ips_solicitadas), 0) FROM rangos_unidades WHERE segmento_asignado = '{segmento_cidr}') +
                (SELECT COALESCE(SUM(cantidad_ips), 0) FROM solicitudes_ip WHERE estado = 'Aprobado' AND unidad_id IN 
                    (SELECT unidad_id FROM rangos_unidades WHERE segmento_asignado = '{segmento_cidr}')
                ) as total_ocupado
        """
        res = pd.read_sql(q, engine)
        ocupadas = int(res['total_ocupado'][0]) if res['total_ocupado'][0] is not None else 0
        
        # Ajuste para evitar errores de Streamlit y lógica
        libres = max(0, capacidad_maxima - ocupadas)
        porcentaje_real = (ocupadas / capacidad_maxima) * 100
        
        return {
            "porcentaje": round(porcentaje_real, 1), 
            "color": "red" if porcentaje_real >= 90 else "orange" if porcentaje_real >= 75 else "green", 
            "libres": libres, 
            "ocupadas": ocupadas
        }
    except Exception as e:
        return {"porcentaje": 0, "color": "gray", "libres": 0, "ocupadas": 0}