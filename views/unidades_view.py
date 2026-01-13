import streamlit as st
import pandas as pd
from network_utils import (
    conectar_db, obtener_motor, calcular_subred_por_hosts, obtener_detalles_red
)

def render_unidades():
    st.subheader("🏢 Gestión de Unidades de Negocio - CELEC")
    engine = obtener_motor()
    
    # 1. Cargar Datos
    df_seg_maestros = pd.read_sql("SELECT nombre, rango_red FROM segmentos_globales", engine)
    df_u_lista = pd.read_sql("SELECT id, nombre FROM unidades_negocio ORDER BY nombre", engine)

    # Estado de edición
    is_editing = st.session_state.get('ed_tipo') == 'rango_edit'
    
    # 2. Formulario de Asignación / Edición
    with st.expander("➕ Configurar Nuevo Rango o Editar Selección", expanded=is_editing):
        if df_seg_maestros.empty or df_u_lista.empty:
            st.warning("Debe registrar Segmentos Globales y Unidades primero.")
        else:
            with st.form("f_unidades_final"):
                c1, c2, c3 = st.columns([2, 1, 2])
                with c1:
                    u_id = st.selectbox("Unidad de Negocio", options=df_u_lista['id'], 
                                       format_func=lambda x: df_u_lista[df_u_lista['id']==x]['nombre'].values[0])
                with c2:
                    n_ips = st.number_input("IPs Requeridas", min_value=1, value=st.session_state.get('ed_ips', 14))
                with c3:
                    s_nom = st.selectbox("Desde Segmento Global", df_seg_maestros['nombre'])

                # Previsualización técnica
                red_m_str = df_seg_maestros[df_seg_maestros['nombre'] == s_nom]['rango_red'].values[0]
                q_ocup = "SELECT segmento_asignado FROM rangos_unidades"
                if is_editing: q_ocup += f" WHERE id != {st.session_state.ed_id}"
                ocupadas = pd.read_sql(q_ocup, engine)['segmento_asignado'].tolist()
                
                segmento_calculado = calcular_subred_por_hosts(red_m_str, n_ips, ocupadas)

                if segmento_calculado:
                    st.success(f"📍 Red asignada: `{segmento_calculado}`")
                
                if st.form_submit_button("💾 Guardar Configuración", width='stretch'):
                    if segmento_calculado:
                        conn = conectar_db(); cur = conn.cursor()
                        if is_editing:
                            cur.execute("""
                                UPDATE rangos_unidades 
                                SET unidad_id=%s, segmento_asignado=%s, num_ips_solicitadas=%s 
                                WHERE id=%s
                            """, (int(u_id), segmento_calculado, int(n_ips), st.session_state.ed_id))
                        else:
                            cur.execute("""
                                INSERT INTO rangos_unidades (unidad_id, segmento_asignado, num_ips_solicitadas) 
                                VALUES (%s, %s, %s)
                            """, (int(u_id), segmento_calculado, int(n_ips)))
                        
                        conn.commit(); conn.close()
                        
                        # --- LIMPIEZA DE CAMPOS ---
                        # Reseteamos las variables de control para que el formulario vuelva a su estado inicial
                        st.session_state['ed_id'] = None
                        st.session_state['ed_ips'] = 14  # Valor por defecto
                        st.session_state['ed_tipo'] = None
                        
                        # Opcional: Si quieres limpiar selectbox específicos, puedes usar llaves (keys)
                        # st.session_state['mi_key_selectbox'] = None 

                        st.success("✅ Asignación guardada. Campos listos para el siguiente registro.")
                        
                        # Forzamos el reinicio de la página para aplicar la limpieza
                        st.rerun()

    # 3. Resumen Técnico con Nombres de Segmentos
    st.divider()
    st.markdown("### 📋 Resumen de Segmentos Asignados")

    query_resumen = """
        SELECT u.nombre as unidad, r.id as rango_id, r.segmento_asignado as red_cidr,
               r.num_ips_solicitadas as ips, sg.nombre as nombre_global
        FROM unidades_negocio u
        JOIN rangos_unidades r ON u.id = r.unidad_id
        LEFT JOIN segmentos_globales sg ON r.segmento_asignado::inet <<= sg.rango_red::inet
        ORDER BY u.nombre ASC
    """
    
    try:
        df_res = pd.read_sql(query_resumen, engine)
        for unidad, datos in df_res.groupby('unidad'):
            with st.expander(f"🏢 {unidad}", expanded=True):
                for _, row in datos.iterrows():
                    det = obtener_detalles_red(row['red_cidr'])
                    c1, c2, c3, c4, c5 = st.columns([2, 3, 3, 1, 1])
                    c1.markdown(f"**Origen:**\n{row['nombre_global']}")
                    c2.code(row['red_cidr'])
                    c3.caption(f"GW: {det['gateway']}\nMask: {det['mask_decimal']}")
                    
                    if c4.button("✏️", key=f"ed_{row['rango_id']}"):
                        st.session_state.update({'ed_id': row['rango_id'], 'ed_ips': row['ips'], 'ed_tipo': 'rango_edit'})
                        st.rerun()
                    if c5.button("🗑️", key=f"del_{row['rango_id']}"):
                        conn = conectar_db(); cur = conn.cursor()
                        cur.execute("DELETE FROM rangos_unidades WHERE id=%s", (row['rango_id'],))
                        conn.commit(); conn.close(); st.rerun()
    except Exception as e:
        st.error(f"Error en resumen: {e}")