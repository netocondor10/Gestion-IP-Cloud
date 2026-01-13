import ipaddress
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

# Configuración de conexión
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
    """Calcula el porcentaje de ocupación de un segmento principal"""
    try:
        maestro = ipaddress.IPv4Network(segmento_maestro)
        total_ips = maestro.num_addresses
        
        # Filtramos solo las subredes que están dentro de este segmento maestro
        ocupadas_en_maestro = 0
        for s in subredes_totales:
            red_s = ipaddress.IPv4Network(s)
            if red_s.subnet_of(maestro):
                ocupadas_en_maestro += red_s.num_addresses
        
        porc = (ocupadas_en_maestro / total_ips) * 100
        return round(porc, 2), total_ips, ocupadas_en_maestro
    except:
        return 0.0, 0, 0
    
def calcular_estado_segmento(subred_cidr):
    """Calcula detalladamente IPs libres y ocupadas de una subred específica."""
    try:
        red = ipaddress.IPv4Network(subred_cidr)
        total_hosts = red.num_addresses - 2 # Excluyendo red y broadcast
        # El gateway siempre está ocupado
        ocupadas = 1 
        libres = total_hosts - ocupadas
        porcentaje = (ocupadas / total_hosts) * 100 if total_hosts > 0 else 0
        
        # Determinar color del semáforo
        color = "green" if porcentaje < 50 else "orange" if porcentaje < 85 else "red"
        
        return {
            "total": total_hosts,
            "ocupadas": ocupadas,
            "libres": libres,
            "porcentaje": round(porcentaje, 1),
            "color": color
        }
    except:
        return None