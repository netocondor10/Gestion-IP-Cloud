import streamlit as st
import pandas as pd
from network_utils import obtener_motor, obtener_detalles_red, calcular_estado_segmento

def render_historial():
    st.title("📊 Dashboard de Control de IPs y Unidades")
    engine = obtener_motor()

    # Consulta para obtener Unidades y sus Segmentos asignados
    query = """
        SELECT u.nombre as unidad, r.segmento_asignado, r.num_ips_solicitadas
        FROM unidades_negocio u
        JOIN rangos_unidades r ON u.id = r.unidad_id
        ORDER BY u.nombre
    """
    
    try:
        df = pd.read_sql(query, engine)
        
        if df.empty:
            st.warning("⚠️ No hay segmentos asignados para mostrar en el historial.")
            return

        # Agrupar por unidad para mostrar tarjetas organizadas
        for unidad, datos in df.groupby('unidad'):
            st.markdown(f"### 🏢 Unidad: {unidad}")
            
            # Crear columnas para los segmentos de esta unidad
            cols = st.columns(len(datos) if len(datos) <= 3 else 3)
            
            for i, (_, row) in enumerate(datos.iterrows()):
                estado = calcular_estado_segmento(row['segmento_asignado'])
                detalles = obtener_detalles_red(row['segmento_asignado'])
                
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"**Segmento:** `{row['segmento_asignado']}`")
                        
                        # Métrica principal con color dinámico
                        st.markdown(f"<h4 style='color: {estado['color']};'>{estado['porcentaje']}% Ocupado</h4>", unsafe_allow_html=True)
                        
                        # Barra de progreso visual
                        st.progress(estado['porcentaje'] / 100)
                        
                        # Desglose técnico
                        c1, c2 = st.columns(2)
                        c1.metric("Libres", f"{estado['libres']}")
                        c2.metric("Ocupadas", f"{estado['ocupadas']}")
                        
                        with st.expander("Ver Detalles Técnicos"):
                            st.caption(f"**Gateway:** {detalles['gateway']}")
                            st.caption(f"**Máscara:** {detalles['mask_decimal']}")
                            st.caption(f"**Broadcast:** {detalles['broadcast']}")
            st.divider()

    except Exception as e:
        st.error(f"Error al cargar el Dashboard: {e}")

    # --- Resumen Global ---
    st.sidebar.markdown("### 📈 Resumen Global CELEC")
    total_segmentos = len(df)
    st.sidebar.metric("Total Segmentos Asignados", total_segmentos)