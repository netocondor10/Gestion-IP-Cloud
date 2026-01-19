import psycopg2
import hashlib

def fix_admin_user():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1", 
            port="5432", 
            database="gestion_ips", 
            user="admin_red", 
            password="password123"
        )
        cur = conn.cursor()
        
        # 1. Creamos la unidad con un segmento base para cumplir con el NOT NULL
        cur.execute("""
            INSERT INTO unidades_negocio (nombre, segmento_base) 
            VALUES ('Administración Central', '192.168.254.0/24') 
            ON CONFLICT DO NOTHING;
        """)
        conn.commit()
        
        # 2. Obtenemos el ID de la unidad (sea la nueva o una existente)
        cur.execute("SELECT id FROM unidades_negocio WHERE nombre = 'Administración Central' LIMIT 1;")
        unidad_id = cur.fetchone()[0]
        
        # 3. Vinculamos el usuario admin a esa unidad
        pw_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cur.execute("""
            INSERT INTO usuarios_unidades (unidad_id, username, password_hash, es_temporal)
            VALUES (%s, 'admin', %s, FALSE)
            ON CONFLICT (username) 
            DO UPDATE SET unidad_id = %s;
        """, (unidad_id, pw_hash, unidad_id))
        
        conn.commit()
        print(f"✅ ÉXITO: Usuario 'admin' vinculado a la unidad '{unidad_id}' con segmento base.")
        cur.close(); conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_admin_user()
