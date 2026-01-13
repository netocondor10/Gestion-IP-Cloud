import streamlit as st
import pandas as pd
from network_utils import conectar_db, obtener_motor, crear_usuario_unidad, obtener_usuarios_registrados

def render_admin_users():
    st.subheader("👤 Gestión de Usuarios por Unidad")
    engine = obtener_motor()
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Crear / Resetear Usuario")
        df_u = pd.read_sql("SELECT id, nombre FROM unidades_negocio", engine)
        
        with st.form("f_crear_usuario", clear_on_submit=True):
            unidad_sel = st.selectbox("Asignar a Unidad", options=df_u['id'], 
                                     format_func=lambda x: df_u[df_u['id']==x]['nombre'].values[0])
            nuevo_user = st.text_input("Nombre de Usuario (Login)")
            pass_temp = st.text_input("Contraseña Temporal", type="password")
            
            if st.form_submit_button("Generar Credenciales"):
                if nuevo_user and pass_temp:
                    if crear_usuario_unidad(unidad_sel, nuevo_user, pass_temp):
                        st.success(f"✅ Usuario '{nuevo_user}' listo.")
                        st.rerun()
                else:
                    st.error("Complete todos los campos")

    with col2:
        st.markdown("#### Usuarios Activos")
        df_users = obtener_usuarios_registrados()
        if df_users.empty:
            st.info("No hay usuarios creados.")
        else:
            for _, row in df_users.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**{row['unidad']}**")
                    c2.code(row['username'])
                    if c3.button("Reset", key=f"res_{row['id']}"):
                        # Al hacer clic, cargamos el username arriba para resetear
                        st.info(f"Use el formulario para resetear a: {row['username']}")