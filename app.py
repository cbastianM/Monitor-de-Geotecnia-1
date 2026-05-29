"""
GeoTutor — Visor de Soluciones + Asistente IA
Mecánica de Suelos · Dos columnas
"""
import streamlit as st
import os
from openai import OpenAI

# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════
CARPETA_CONTENIDO = "CONTENIDO"
OPENROUTER_MODEL  = "openrouter/free"

# ═══════════════════════════════════════════════════════════════════
# HELPERS DE ARCHIVOS
# ═══════════════════════════════════════════════════════════════════
def listar_temas() -> list[str]:
    if not os.path.exists(CARPETA_CONTENIDO):
        return []
    return sorted([
        d for d in os.listdir(CARPETA_CONTENIDO)
        if os.path.isdir(os.path.join(CARPETA_CONTENIDO, d))
    ])

def listar_ejercicios(tema: str) -> list[str]:
    ruta = os.path.join(CARPETA_CONTENIDO, tema)
    if not os.path.isdir(ruta):
        return []
    return sorted([f for f in os.listdir(ruta) if f.endswith(".md")])

def cargar_md(tema: str, archivo: str) -> tuple[str | None, str | None]:
    ruta = os.path.join(CARPETA_CONTENIDO, tema, archivo)
    try:
        with open(ruta, encoding="utf-8") as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)

# ═══════════════════════════════════════════════════════════════════
# HELPERS DE API KEY
# ═══════════════════════════════════════════════════════════════════
def obtener_api_key() -> str:
    """Retorna solo la key ingresada manualmente por el usuario en esta sesión."""
    return st.session_state.get("user_api_key", "")

# ═══════════════════════════════════════════════════════════════════
# HELPERS DE IA
# ═══════════════════════════════════════════════════════════════════
def llamar_ia(api_key: str, mensajes: list, sys_prompt: str) -> str:
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            max_tokens=1024,
            messages=[{"role": "system", "content": sys_prompt}] + mensajes,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {e}"

def build_system_prompt(tema: str, archivo: str, contenido: str) -> str:
    return f"""Eres GeoTutor IA, asistente experto en Mecánica de Suelos.
El estudiante revisa: {archivo.replace('.md', '')} (Tema: {tema}).

Contenido del ejercicio que el estudiante tiene frente a él:
---
{contenido}
---

Instrucciones:
- Responde dudas sobre este ejercicio y teoría relacionada.
- Explica pasos, fórmulas y conceptos con claridad.
- Usa LaTeX inline ($...$) para ecuaciones cuando ayude.
- Respuestas concisas (2–4 párrafos salvo que pidan más detalle).
- Si la pregunta no es de ingeniería/suelos, redirige amablemente.
Idioma: español."""

# ═══════════════════════════════════════════════════════════════════
# COMPONENTES UI
# ═══════════════════════════════════════════════════════════════════
def render_solicitud_api_key():
    """Bloque que se muestra cuando no hay API key."""
    st.markdown("""
**Necesitas una API key de OpenRouter** para activar el asistente.

**¿Cómo obtenerla?**

1. Ve a [openrouter.ai](https://openrouter.ai) y crea una cuenta gratuita.
2. En el menú lateral entra a **Keys** → **Create Key**.
3. Copia la key (`sk-or-v1-...`) y pégala abajo.

> Con el modelo `openrouter/free` no necesitas agregar créditos.
""")
    nueva_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-v1-...",
        key="input_api_key",
    )
    if st.button("Guardar y activar", type="primary", use_container_width=True):
        if nueva_key.strip():
            st.session_state["user_api_key"] = nueva_key.strip()
            st.rerun()
        else:
            st.warning("Pega tu API key primero.")

def render_chat(api_key: str, tema: str, archivo: str, contenido_md: str, chat_key: str):
    """Bloque completo del chat (input arriba, mensajes abajo)."""
    mensajes = st.session_state[chat_key]
    ctx = contenido_md or "(Archivo no disponible)"

    # Input arriba
    with st.form("chat_form", clear_on_submit=True):
        pregunta = st.text_input(
            "Pregunta", placeholder="Escribe tu duda aquí...",
            label_visibility="collapsed",
        )
        c_env, c_lim = st.columns([4, 1])
        enviar = c_env.form_submit_button("Enviar →", use_container_width=True, type="primary")
        limpiar = c_lim.form_submit_button("🗑️", use_container_width=True)

    if limpiar:
        st.session_state[chat_key] = []
        st.rerun()

    if enviar and pregunta.strip():
        mensajes.append({"role": "user", "content": pregunta.strip()})
        with st.spinner("Pensando..."):
            respuesta = llamar_ia(api_key, mensajes, build_system_prompt(tema, archivo, ctx))
        mensajes.append({"role": "assistant", "content": respuesta})
        st.session_state[chat_key] = mensajes
        st.rerun()

    # Sugerencias
    st.caption("Sugerencias rápidas:")
    sugerencias = [
        "¿Cuál es la fórmula clave?", "Explícame el Paso 1",
        "¿Qué unidades se usan?",     "Dame un ejemplo similar",
    ]
    c1, c2 = st.columns(2)
    for i, (col, sug) in enumerate(zip([c1, c2, c1, c2], sugerencias)):
        if col.button(sug, key=f"sug_{i}", use_container_width=True):
            mensajes.append({"role": "user", "content": sug})
            with st.spinner("Pensando..."):
                respuesta = llamar_ia(api_key, mensajes, build_system_prompt(tema, archivo, ctx))
            mensajes.append({"role": "assistant", "content": respuesta})
            st.session_state[chat_key] = mensajes
            st.rerun()

    # Historial de mensajes
    with st.container(height=480, border=True):
        if not mensajes:
            st.markdown(
                "<div style='color:#94a3b8;text-align:center;padding:2.5rem 1rem;'>"
                "<div style='font-size:2rem;'>🤖</div>"
                "Tengo acceso a la solución de la izquierda.<br>"
                "<span style='font-size:0.88rem;'>"
                "Pregúntame sobre cualquier paso, fórmula o concepto."
                "</span></div>",
                unsafe_allow_html=True,
            )
        for msg in mensajes:
            css = "msg-user" if msg["role"] == "user" else "msg-ai"
            st.markdown(f"<div class='{css}'>{msg['content']}</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG + CSS
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="GeoTutor", page_icon="🪨", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; max-width: 100% !important; }
    .msg-user {
        background: #3b82f6; color: white;
        padding: 0.55rem 1rem; border-radius: 14px 14px 4px 14px;
        margin: 4px 0; font-size: 0.9rem;
    }
    .msg-ai {
        background: #f1f5f9; color: #1e293b;
        border: 1px solid #e2e8f0;
        padding: 0.6rem 1rem; border-radius: 14px 14px 14px 4px;
        margin: 4px 0; font-size: 0.9rem; line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# BARRA SUPERIOR
# ═══════════════════════════════════════════════════════════════════
temas = listar_temas()
if not temas:
    st.error(f"No se encontró la carpeta `{CARPETA_CONTENIDO}/` o está vacía.")
    st.stop()

top_titulo, top_tema, top_ejercicio = st.columns([0.8, 1.5, 2])

with top_titulo:
    st.markdown("## 🪨 GeoTutor")

with top_tema:
    tema_sel = st.selectbox("Tema", temas)

with top_ejercicio:
    ejercicios = listar_ejercicios(tema_sel)
    if not ejercicios:
        st.warning("No hay archivos .md en este tema.")
        st.stop()
    archivo_sel = st.selectbox("Ejercicio", ejercicios)

st.divider()

# ═══════════════════════════════════════════════════════════════════
# ESTADO
# ═══════════════════════════════════════════════════════════════════
api_key = obtener_api_key()
contenido_md, error_md = cargar_md(tema_sel, archivo_sel)
chat_key = f"chat_{tema_sel}_{archivo_sel}"
if chat_key not in st.session_state:
    st.session_state[chat_key] = []

# ═══════════════════════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════════════════════
col_sol, col_chat = st.columns([1.15, 0.85], gap="medium")

with col_sol:
    if error_md:
        st.warning(f"⚠️ {error_md}")
    else:
        st.markdown(contenido_md)

with col_chat:
    st.markdown("**🤖 Asistente GeoTutor IA**")
    if not api_key:
        render_solicitud_api_key()
    else:
        # Mini-indicador de key activa + botón para cambiarla
        c_info, c_btn = st.columns([3, 1])
        c_info.success("API key activa ✓", icon="🔑")
        if c_btn.button("Cambiar", use_container_width=True):
            st.session_state.pop("user_api_key", None)
            st.rerun()
        render_chat(api_key, tema_sel, archivo_sel, contenido_md, chat_key)
