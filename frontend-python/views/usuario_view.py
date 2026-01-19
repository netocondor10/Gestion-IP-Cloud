import streamlit as st
import pandas as pd
import ipaddress
from network_utils import (
    obtener_motor, 
    obtener_detalles_red, 
    calcular_estado_segmento, 
    enviar_solicitud_ip,
    verificar_capacidad_disponible  # Asegúrate de añadir esta función a network_utils
)

def render_usuario():
    u_id = st.session_state.get('unidad_id')
    u_nom = st.session_state.get('usuario')
    engine = obtener_motor()

    # --- 1. VALIDACIÓN DE SEGURIDAD ---
    if u_id is None:
        st.warning("⚠️ Su usuario no tiene una Unidad de Negocio vinculada.")
        if st.button("Reintentar Inicio de Sesión", width='stretch'):
            st.session_state.auth = False
            st.rerun()
        return

    st.title(f"🔍 Panel de Gestión: {u_nom}")
    
    # --- 2. CARGA DE DATOS PREVIA ---
    # Cargamos los segmentos una sola vez para usarlos en todas las pestañas
    query_red = f"""
        SELECT r.id, r.segmento_asignado, sg.nombre as red_maestra 
        FROM rangos_unidades r 
        LEFT JOIN segmentos_globales sg ON r.segmento_asignado::inet <<= sg.rango_red::inet 
        WHERE r.unidad_id = {int(u_id)}
    """
    try:
        df_red = pd.read_sql(query_red, engine)
    except:
        df_red = pd.DataFrame()

    # --- 3. NAVEGACIÓN POR PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Mis Segmentos", "🔎 Buscador de IPs", "📩 Solicitar IPs"])

    # --- TAB 1: VISUALIZACIÓN DE REDES ASIGNADAS ---
    with tab1:
        st.subheader("Infraestructura de Red Asignada")
        if df_red.empty:
            st.info("No hay segmentos asignados actualmente para su unidad.")
        else:
            for _, row in df_red.iterrows():
                detalles = obtener_detalles_red(row['segmento_asignado'])
                estado = calcular_estado_segmento(row['segmento_asignado'])
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.markdown(f"### `{row['segmento_asignado']}`")
                        st.caption(f"Origen: {row['red_maestra']}")
                        st.markdown(f"**Uso:** <span style='color:{estado['color']};'>{estado['porcentaje']}%</span>", unsafe_allow_html=True)
                    
                    with c2:
                        st.write(f"**GW:** `{detalles['gateway']}`")
                        st.write(f"**Mask:** `{detalles['mask_decimal']}`")
                        st.caption(f"Rango: {detalles['primera_usable']} - {detalles['ultima_usable']}")
                    
                    with c3:
                        st.metric("Libres", estado['libres'])
                        txt = f"UNIDAD: {u_nom}\nSEGMENTO: {row['segmento_asignado']}\nGATEWAY: {detalles['gateway']}\nMASCARA: {detalles['mask_decimal']}"
                        st.download_button("📝 Ficha", txt, file_name=f"red_{row['id']}.txt", key=f"dl_{row['id']}", width='stretch')

    # --- TAB 2: BUSCADOR DE DISPONIBILIDAD ---
    with tab2:
        st.subheader("Verificador de Direccionamiento")
        ip_test = st.text_input("Ingrese una IP para verificar pertenencia:", placeholder="Ej: 10.x.x.x")
        
        if ip_test:
            try:
                ip_obj = ipaddress.IPv4Address(ip_test)
                pertenece = False
                if not df_red.empty:
                    for _, row in df_red.iterrows():
                        if ip_obj in ipaddress.IPv4Network(row['segmento_asignado']):
                            pertenece = True
                            break
                    
                    if pertenece:
                        st.success(f"✅ La dirección {ip_test} pertenece a sus segmentos autorizados.")
                    else:
                        st.error(f"❌ La dirección {ip_test} está fuera de su rango asignado.")
                else:
                    st.warning("No tiene segmentos para validar.")
            except:
                st.error("Formato de dirección IP no válido.")

    # --- TAB 3: SOLICITAR IPs POR GRUPO CON CONTROL DE CUPO ---
    with tab3:
        st.subheader("Nueva Solicitud por Grupo de Red")
        st.markdown("Solicite bloques adicionales. El sistema validará si sus segmentos actuales tienen espacio.")
        
        try:
            df_grupos_db = pd.read_sql("SELECT nombre FROM grupos_ip", engine)
            opciones_grupos = df_grupos_db['nombre'].tolist()
        except:
            opciones_grupos = ["Servidores", "Cámaras CCTV", "Telefonía IP", "Red WiFi", "Estaciones de Trabajo"]

        with st.form("form_peticion_ip_2026"):
            col_a, col_b = st.columns(2)
            grupo_sel = col_a.selectbox("Seleccione el Grupo Destino", options=opciones_grupos)
            cantidad = col_b.number_input("Cantidad de IPs requeridas", min_value=1, max_value=254, value=5)
            justificacion = st.text_input("Justificación / Proyecto", placeholder="Ej: Expansión de servidores")
            
            if st.form_submit_button("Enviar Solicitud al Admin", width='stretch'):
                # ALGORITMO DE VALIDACIÓN DE CUPO
                pueden_pedir = False
                if not df_red.empty:
                    for _, red in df_red.iterrows():
                        tiene_espacio, disponible = verificar_capacidad_disponible(red['segmento_asignado'], cantidad)
                        if tiene_espacio:
                            pueden_pedir = True
                            break
                
                if pueden_pedir:
                    if enviar_solicitud_ip(u_id, grupo_sel, cantidad):
                        st.success(f"✅ Solicitud enviada. Disponibilidad verificada en sus segmentos.")
                        st.rerun()
                    else:
                        st.error("Error al registrar la solicitud.")
                else:
                    st.error(f"❌ No hay cupo suficiente. Sus segmentos no tienen {cantidad} IPs disponibles.")

        # --- LISTADO DE SEGUIMIENTO ---
        st.markdown("### 📋 Estatus de Solicitudes por Grupo")
        query_solicitudes = f"""
            SELECT nombre_grupo as "Grupo", 
                   cantidad_ips as "IPs Solicitadas", 
                   estado as "Estado", 
                   fecha_solicitud as "Fecha"
            FROM solicitudes_ip 
            WHERE unidad_id = {int(u_id)}
            ORDER BY fecha_solicitud DESC
        """
        try:
            df_sol = pd.read_sql(query_solicitudes, engine)
            if not df_sol.empty:
                st.dataframe(df_sol, width='stretch', hide_index=True)
            else:
                st.caption("No registra solicitudes previas.")
        except:
            st.info("La tabla de solicitudes se activará cuando realice su primer pedido.")

# --- PIE DE PÁGINA ---
st.divider()
st.caption("Sistema IPAM CELEC - Vista de Usuario Final")