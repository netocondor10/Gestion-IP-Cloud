import streamlit as st
import pandas as pd
from network_utils import conectar_db, obtener_motor, obtener_detalles_red, calcular_estado_segmento

def render_historial():
    st.title("📊 Dashboard de Control de IPs y Unidades")
    engine = obtener_motor()

    # --- SECCIÓN 1: SOLICITUDES PENDIENTES (Gestión de Grupos) ---
    st.subheader("📩 Peticiones de Usuarios Pendientes")
    
    query_solicitudes = """
        SELECT s.id, u.nombre as unidad, s.nombre_grupo, s.cantidad_ips, s.estado, s.fecha_solicitud 
        FROM solicitudes_ip s 
        JOIN unidades_negocio u ON s.unidad_id = u.id 
        WHERE s.estado = 'Pendiente'
        ORDER BY s.fecha_solicitud ASC
    """
    
    try:
        df_pendientes = pd.read_sql(query_solicitudes, engine)
        if not df_pendientes.empty:
            st.info(f"Hay {len(df_pendientes)} solicitudes de grupos nuevas por procesar.")
            
            for _, sol in df_pendientes.iterrows():
                with st.expander(f"📌 {sol['unidad']} solicita IPs para: {sol['nombre_grupo']}"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**Grupo destino:** {sol['nombre_grupo']}")
                    c2.write(f"**IPs requeridas:** {sol['cantidad_ips']}")
                    c3.write(f"**Fecha:** {sol['fecha_solicitud'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Botones de Acción (Sintaxis 2026)
                    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
                    
                    if col_btn1.button("✅ Aprobar", key=f"app_{sol['id']}", width='stretch'):
                        try:
                            conn = conectar_db()
                            cur = conn.cursor()
                            # Al cambiar a 'Aprobado', calcular_estado_segmento sumará estas IPs automáticamente
                            cur.execute("UPDATE solicitudes_ip SET estado = 'Aprobado' WHERE id = %s", (sol['id'],))
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success(f"Solicitud de {sol['nombre_grupo']} aprobada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al aprobar: {e}")

                    if col_btn2.button("❌ Rechazar", key=f"rej_{sol['id']}", width='stretch'):
                        try:
                            conn = conectar_db()
                            cur = conn.cursor()
                            cur.execute("UPDATE solicitudes_ip SET estado = 'Rechazado' WHERE id = %s", (sol['id'],))
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.warning("Solicitud rechazada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al rechazar: {e}")
        else:
            st.success("✅ No hay peticiones de grupos pendientes.")
    except Exception as e:
        st.caption("Esperando primeras solicitudes de usuarios...")

    st.divider()

    # --- SECCIÓN 2: MONITOREO Y ESTADO DE SEGMENTOS ---
    st.subheader("🏢 Monitoreo de Unidades de Negocio")
    
    
    
    query_segmentos = """
        SELECT u.nombre as unidad, r.segmento_asignado, r.num_ips_solicitadas
        FROM unidades_negocio u
        JOIN rangos_unidades r ON u.id = r.unidad_id
        ORDER BY u.nombre
    """
    
    try:
        df = pd.read_sql(query_segmentos, engine)
        
        if df.empty:
            st.warning("⚠️ No hay segmentos asignados para mostrar.")
        else:
            for unidad, datos in df.groupby('unidad'):
                st.markdown(f"#### 🏢 Unidad: {unidad}")
                
                n_segmentos = len(datos)
                cols = st.columns(3 if n_segmentos >= 3 else n_segmentos)
                
                for i, (_, row) in enumerate(datos.iterrows()):
                    # Obtener estado actualizado desde el algoritmo unificado en network_utils
                    estado = calcular_estado_segmento(row['segmento_asignado'])
                    detalles = obtener_detalles_red(row['segmento_asignado'])
                    
                    with cols[i % 3]:
                        with st.container(border=True):
                            st.markdown(f"**Segmento:** `{row['segmento_asignado']}`")
                            
                            # Métrica principal con color dinámico
                            st.markdown(
                                f"<h4 style='margin:0; color: {estado['color']};'>{estado['porcentaje']}% Ocupado</h4>", 
                                unsafe_allow_html=True
                            )
                            
                            # PROTECCIÓN 2026: Asegurar que el progreso esté entre 0.0 y 1.0
                            val_progreso = min(1.0, max(0.0, estado['porcentaje'] / 100))
                            st.progress(val_progreso)
                            
                            # Desglose de disponibilidad (Usando las llaves exactas: libres, ocupadas)
                            c_met1, c_met2 = st.columns(2)
                            c_met1.metric("Libres", f"{estado['libres']}")
                            c_met2.metric("Asignadas", f"{estado['ocupadas']}")
                            
                            with st.expander("Ver Detalles Técnicos"):
                                st.caption(f"**Gateway:** {detalles['gateway']}")
                                st.caption(f"**Máscara:** {detalles['mask_decimal']}")
                                st.caption(f"**Broadcast:** {detalles['broadcast']}")
                                if estado['porcentaje'] >= 90:
                                    st.error("🚨 AGOTADO: No permite más asignaciones.")
                                elif estado['porcentaje'] >= 75:
                                    st.warning("⚠️ Crítico: Capacidad limitada.")

                st.markdown("<br>", unsafe_allow_html=True)

            # --- Sidebar de Resumen ---
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📈 Resumen Global CELEC")
            st.sidebar.metric("Total Segmentos Asignados", len(df))
            st.sidebar.metric("Unidades con Red Activa", df['unidad'].nunique())

    except Exception as e:
        st.error(f"Error al cargar el monitoreo: {e}")

st.divider()
st.caption("Consola de Administración IPAM - CELEC v2026.1")