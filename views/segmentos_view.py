import streamlit as st
import pandas as pd
from network_utils import conectar_db, obtener_motor, verificar_colision

def render_segmentos():
    st.subheader("🌐 Segmentos Globales")
    c1, c2 = st.columns([1, 2])
    engine = obtener_motor()

    with c1:
        with st.form("f_seg", clear_on_submit=True):
            n = st.text_input("Nombre", value=st.session_state.ed_nom if st.session_state.ed_tipo == 'seg' else "")
            r = st.text_input("Rango CIDR", value=st.session_state.ed_val if st.session_state.ed_tipo == 'seg' else "")
            # Cambio de use_container_width a width='stretch'
            if st.form_submit_button("Guardar", width='stretch'):
                col, red_ch = verificar_colision(r, "segmentos_globales", "rango_red", st.session_state.ed_id if st.session_state.ed_tipo == 'seg' else None)
                if col: st.error(f"Colisión con {red_ch}")
                else:
                    conn = conectar_db(); cur = conn.cursor()
                    if st.session_state.ed_id and st.session_state.ed_tipo == 'seg':
                        cur.execute("UPDATE segmentos_globales SET nombre=%s, rango_red=%s WHERE id=%s", (n, r, st.session_state.ed_id))
                    else:
                        cur.execute("INSERT INTO segmentos_globales (nombre, rango_red) VALUES (%s, %s)", (n, r))
                    conn.commit(); conn.close()
                    st.session_state.update({'ed_id': None, 'ed_nom': "", 'ed_val': "", 'ed_tipo': None})
                    st.rerun()

    with c2:
        df = pd.read_sql("SELECT id, nombre, rango_red FROM segmentos_globales ORDER BY id DESC", engine)
        for _, row in df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            col1.write(row['nombre'])
            col2.code(row['rango_red'])
            if col3.button("✏️", key=f"es_{row['id']}"):
                st.session_state.update({'ed_id': row['id'], 'ed_nom': row['nombre'], 'ed_val': row['rango_red'], 'ed_tipo': 'seg'})
                st.rerun()
            if col4.button("🗑️", key=f"ds_{row['id']}"):
                conn = conectar_db(); cur = conn.cursor()
                cur.execute("DELETE FROM segmentos_globales WHERE id=%s", (row['id'],)); conn.commit(); conn.close()
                st.rerun()