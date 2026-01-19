import streamlit as st
import base64
import pandas as pd
from network_utils import obtener_motor, generar_hash

# IMPORTACIÓN DE LAS VISTAS
from views.segmentos_view import render_segmentos
from views.unidades_view import render_unidades
from views.grupos_view import render_grupos
from views.historial_view import render_historial
from views.admin_users_view import render_admin_users
from views.usuario_view import render_usuario

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="IPAM Corporativo CELEC",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
def init_session():
    if 'auth' not in st.session_state:
        st.session_state.auth = False
    if 'perfil' not in st.session_state:
        st.session_state.perfil = None
    if 'usuario' not in st.session_state:
        st.session_state.usuario = None
    if 'unidad_id' not in st.session_state:
        st.session_state.unidad_id = None
    # Estados de edición para formularios
    if 'ed_id' not in st.session_state: st.session_state.ed_id = None
    if 'ed_tipo' not in st.session_state: st.session_state.ed_tipo = None

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
        st.markdown("<style>.stApp {background-color: #111;}</style>", unsafe_allow_html=True)

agregar_fondo("fondo.jpg")

# --- 4. LÓGICA DE LOGIN ---
def verificar_login(user, password):
    # Credenciales maestras de Administrador
    if user == "admin" and password == "admin123":
        st.session_state.auth = True
        st.session_state.perfil = "Administrador"
        st.session_state.usuario = "admin"
        st.session_state.unidad_id = None
        return True
    
    # Verificación en BD para Usuarios de Unidad
    try:
        engine = obtener_motor()
        hash_intento = generar_hash(password)
        query = f"SELECT unidad_id, username FROM usuarios_unidades WHERE username = '{user}' AND password_hash = '{hash_intento}'"
        res = pd.read_sql(query, engine)
        
        if not res.empty:
            st.session_state.auth = True
            st.session_state.perfil = "Usuario"
            st.session_state.usuario = res['username'][0]
            # IMPORTANTE: Casting a int para evitar el error 'None' en SQL
            st.session_state.unidad_id = int(res['unidad_id'][0]) 
            return True
    except Exception as e:
        st.error(f"Error de conexión a la base de datos: {e}")
    return False

# --- 5. INTERFAZ DE CONTROL (LOGIN O DASHBOARD) ---
if not st.session_state.auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>⚡ Sistema de Gestión IPAM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Corporativo CELEC - Control de Redes</p>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Iniciar Sesión", use_container_width=True):
                if verificar_login(user_input, pass_input):
                    st.success("Acceso concedido")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

else:
    # BARRA LATERAL (Sidebar)
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/5087/5087579.png", width=100)
        st.title("Panel de Control")
        st.write(f"👤 Usuario: **{st.session_state.usuario}**")
        st.write(f"🔰 Perfil: **{st.session_state.perfil}**")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            # Limpiar estado al cerrar sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.divider()
        st.info("Estructura MVC activa: Módulos cargados independientemente.")

    # NAVEGACIÓN SEGÚN PERFIL
    if st.session_state.perfil == "Administrador":
        st.markdown("# 🌐 Consola Maestra de Infraestructura")
        tabs = st.tabs([
            "🌐 Segmentos Globales", 
            "🏢 Unidades de Negocio", 
            "👤 Gestión de Usuarios", 
            "🏷️ Grupos de IP", 
            "📊 Monitoreo e Historial"
        ])

        with tabs[0]: render_segmentos()
        with tabs[1]: render_unidades()
        with tabs[2]: render_admin_users()
        with tabs[3]: render_grupos()
        with tabs[4]: render_historial()
    
    else:
        # Interfaz del Usuario de Unidad de Negocio
        st.markdown(f"# 🔍 Portal de Consulta")
        render_usuario()

# --- 6. PIE DE PÁGINA ---
st.markdown("""
    <div style="position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; color: gray; font-size: 12px; padding: 10px; background-color: rgba(0,0,0,0.5);">
        IPAM Corporativo CELEC © 2024 - Ambiente de Gestión Segura
    </div>
    """, unsafe_allow_html=True)