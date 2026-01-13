import streamlit as st
import base64

# IMPORTACIÓN DE LAS VISTAS (Asegúrate de tener la carpeta 'views' con estos archivos)
from views.segmentos_view import render_segmentos
from views.unidades_view import render_unidades
from views.grupos_view import render_grupos
from views.historial_view import render_historial

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="IPAM Corporativo CELEC",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
# Esto evita errores de 'AttributeError' al recargar la página
def init_session():
    if 'auth' not in st.session_state:
        st.session_state.auth = False
    if 'ed_id' not in st.session_state:
        st.session_state.ed_id = None
    if 'ed_nom' not in st.session_state:
        st.session_state.ed_nom = ""
    if 'ed_val' not in st.session_state:
        st.session_state.ed_val = ""
    if 'ed_tipo' not in st.session_state:
        st.session_state.ed_tipo = None

init_session()

# --- 3. ESTILO Y FONDO PERSONALIZADO ---
def agregar_fondo(archivo):
    try:
        with open(archivo, "rb") as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
                url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-attachment: fixed;
            }}
            /* Estilo para que todos los textos sean legibles sobre el fondo oscuro */
            h1, h2, h3, p, label, .stMetric, .stTabs [data-baseweb="tab"] {{
                color: white !important;
            }}
            .stDataFrame {{
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
            }}
            </style>
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Imagen 'fondo.jpg' no encontrada. Se aplicará un tema oscuro genérico.")

agregar_fondo("fondo.jpg")

# --- 4. LÓGICA DE CONTROL DE ACCESO (LOGIN) ---
if not st.session_state.auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>⚡ Sistema de Gestión IPAM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Corporativo CELEC - Control de Redes</p>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1, 1])
    
    with col_login:
        with st.form("login_form"):
            user = st.text_input("Usuario Administrador")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submit:
                if user == "admin" and password == "admin123":
                    st.session_state.auth = True
                    st.success("Acceso concedido")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# --- 5. PANEL PRINCIPAL (DASHBOARD) ---
else:
    # Barra lateral para cerrar sesión y estado
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/5087/5087579.png", width=100) # Icono genérico de red
        st.title("Admin Panel")
        st.write(f"Conectado como: **admin**")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
        st.divider()
        st.info("Estructura MVC activa: Los módulos de vista se cargan de forma independiente.")

    # Título principal
    st.markdown("# 🌐 Consola Maestra de Infraestructura")
    
    # Navegación por Pestañas (Views)
    tab0, tab1, tab2, tab3 = st.tabs([
        "🌐 Segmentos Globales", 
        "🏢 Unidades de Negocio", 
        "🏷️ Grupos de IP", 
        "📊 Monitoreo e Historial"
    ])

    with tab0:
        render_segmentos()
        
    with tab1:
        render_unidades()
        
    with tab2:
        render_grupos()
        
    with tab3:
        render_historial()

# --- 6. PIE DE PÁGINA ---
st.markdown("""
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; color: gray; font-size: 12px; padding: 10px; }
    </style>
    <div class="footer">IPAM Corporativo CELEC © 2024 - Ambiente de Gestión Segura</div>
    """, unsafe_allow_html=True)