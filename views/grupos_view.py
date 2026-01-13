import streamlit as st
import pandas as pd
from network_utils import conectar_db, obtener_motor

def render_grupos():
    st.subheader("🏷️ Grupos de Red")
    c1, c2 = st.columns([1, 2])
    engine = obtener_motor()
    
    with c1:
        with st.form("f_grp"):
            n_g = st.text_input("Nombre del Grupo", value=st.session_state.ed_nom if st.session_state.ed_tipo == 'grp' else "")
            if st.form_submit_button("Confirmar", width='stretch'):
                conn = conectar_db(); cur = conn.cursor()
                if st.session_state.ed_id and st.session_state.ed_tipo == 'grp':
                    cur.execute("UPDATE grupos_ip SET nombre=%s WHERE id=%s", (n_g, st.session_state.ed_id))
                else:
                    cur.execute("INSERT INTO grupos_ip (nombre) VALUES (%s)", (n_g,))
                conn.commit(); conn.close()
                st.session_state.update({'ed_id': None, 'ed_nom': "", 'ed_tipo': None})
                st.rerun()

    with c2:
        df_g = pd.read_sql("SELECT id, nombre FROM grupos_ip ORDER BY id DESC", engine)
        for _, row in df_g.iterrows():
            g1, g2, g3 = st.columns([4, 1, 1])
            g1.write(row['nombre'])
            if g2.button("✏️", key=f"eg_{row['id']}"):
                st.session_state.update({'ed_id': row['id'], 'ed_nom': row['nombre'], 'ed_tipo': 'grp'})
                st.rerun()
            if g3.button("🗑️", key=f"dg_{row['id']}"):
                conn = conectar_db(); cur = conn.cursor()
                cur.execute("DELETE FROM grupos_ip WHERE id=%s", (row['id'],)); conn.commit(); conn.close()
                st.rerun()