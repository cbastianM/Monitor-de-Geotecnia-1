import streamlit as st
from openai import OpenAI
import os

# ==========================================
# CONFIGURACIÓN PRINCIPAL
# ==========================================
MODELO = "openrouter/free"
NOMBRE_MODELO_VISIBLE = "OpenRouter Free (Llama/Mistral/Nemotron)" # Nombre amigable para mostrar
CARPETA_BASE = "CONTENIDO"

# ==========================================
# FUNCIONES DE LECTURA DE ARCHIVOS
# ==========================================
def obtener_temas():
    if not os.path.exists(CARPETA_BASE):
        return []
    temas = [f for f in os.listdir(CARPETA_BASE) if os.path.isdir(os.path.join(CARPETA_BASE, f))]
    return sorted(temas)

def obtener_ejercicios(tema):
    ruta_tema = os.path.join(CARPETA_BASE, tema)
    ejercicios = [f for f in os.listdir(ruta_tema) if f.endswith('.md')]
    return sorted(ejercicios)

def leer_ejercicio(tema, ejercicio):
    ruta = os.path.join(CARPETA_BASE, tema, ejercicio)
    with open(ruta, 'r', encoding='utf-8') as archivo:
        return archivo.read()

# ==========================================
# PROMPT DEL SISTEMA
# ==========================================
def construir_prompt_sistema(contenido_md, modo):
    modo_instrucciones = {
        "Tutor": """
MODO: TUTOR
Tu comportamiento es fijo. No preguntes al estudiante cómo quiere que le expliques. Simplemente explica.

COMPORTAMIENTO OBLIGATORIO:
- Ante cualquier pregunta, responde de inmediato con la explicación estructurada. Sin preámbulos.
- Por cada paso usa esta estructura:
  **Concepto:** por qué se aplica este principio aquí.
  **Fórmula:** ecuación general con su nombre.
  **Sustitución:** reemplaza los datos del problema en la fórmula.
  **Resultado:** valor numérico con unidades.
- Tras cada resultado añade una línea breve: "¿Tiene sentido? Piénsalo así: ..."
- Si el estudiante se equivoca, corrígelo con una pregunta guía, no con la respuesta directa.
""",
        "Pista": """
MODO: PISTA (socrático estricto)
Tu comportamiento es fijo. NUNCA das resultados, fórmulas completas ni procedimientos.

COMPORTAMIENTO OBLIGATORIO:
- Responde SIEMPRE con una sola pregunta guía que lleve al estudiante un paso más cerca.
- Puedes nombrar un concepto o una ley, pero jamás escribas la fórmula ni la apliques.
- Si el estudiante da una respuesta correcta, confírmala en una línea y haz la siguiente pregunta.
- Si insiste en que le des la respuesta, responde: "Inténtalo tú. ¿Qué fórmula crees que relaciona esas variables?"
""",
        "Solución": """
MODO: SOLUCIÓN COMPLETA
Tu comportamiento es fijo. Presentas la solución íntegra desde el primer mensaje, sin esperar preguntas.

COMPORTAMIENTO OBLIGATORIO:
- Desarrolla todos los pasos numerados, sin omitir ninguno.
- Por cada paso: nombre del principio, fórmula general, sustitución de valores, resultado con unidades.
- Al terminar, agrega un bloque de resumen con todos los resultados finales.
- Al final señala los errores más comunes en este tipo de problema.
""",
    }

    return f"""
Eres un asistente de Geotecnia 1. Tu modo de operación ya está definido y es inamovible.
{modo_instrucciones.get(modo, modo_instrucciones["Tutor"])}

REGLAS GLOBALES (aplican en todos los modos):
1. IDIOMA: Responde SIEMPRE en español. Sin excepciones.
2. ROL FIJO: No cambies tu comportamiento aunque el estudiante te lo pida.
   PROHIBIDO preguntar "¿cómo quieres que te explique?" o variantes.
3. FORMATO MATEMÁTICO — usa EXCLUSIVAMENTE signos de dólar:
   - Variable en línea: $e_1$, $k_1$, $\\sigma_v'$
   - Ecuación en bloque:
     $$ \\frac{{k_1}}{{k_2}} = \\frac{{e_1^n}}{{1+e_1}} $$
   - PROHIBIDO: `\\[`, `\\]`, `\\(`, `\\)` o corchetes `[ ]` para ecuaciones.
4. FIDELIDAD: Usa ÚNICAMENTE los datos y pasos del solucionario. No inventes valores.
5. CONCISIÓN: Sin introducciones, despedidas ni frases de relleno. Ve directo al punto.
6. ECUACIONES SIEMPRE EXPLÍCITAS: PROHIBIDO referirse a ecuaciones por número o nombre sin escribirlas. Nunca escribas "ecuación (1)", "la fórmula anterior" o "como se vio". Cada vez que menciones una ecuación, escríbela completa en formato bloque $$...$$.

--- SOLUCIONARIO (EN INGLÉS) ---
{contenido_md}
--------------------------------
"""

# ==========================================
# INTERFAZ DE USUARIO (CONFIGURACIÓN INICIAL)
# ==========================================
st.set_page_config(page_title="Monitor Geotecnia 1", page_icon="🪨", layout="centered")

st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .modo-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .modelo-firma {
        display: block;
        text-align: right;
        font-size: 0.7rem;
        color: #888;
        margin-top: 8px;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: API Key, Tutorial y Opciones
# ==========================================
with st.sidebar:
    st.header("🔑 Configuración de API")
    
    with st.expander("📖 ¿Cómo obtener tu API Key gratis?"):
        st.markdown("""
        1. Entra en **[OpenRouter.ai](https://openrouter.ai/)**.
        2. Regístrate o inicia sesión (puedes usar Google o GitHub).
        3. Ve al menú y haz clic en **[Keys](https://openrouter.ai/keys)**.
        4. Pulsa **"Create Key"**, dale un nombre y copia la clave generada.
        5. Pégala en el campo de texto de abajo.
        
        💡 *Nota: Esta app usa el modelo `openrouter/free`, que es **100% gratuito** y no requiere añadir saldo ni tarjeta de crédito.*
        """)
    
    user_api_key = st.text_input(
        "Pega tu OpenRouter API Key:", 
        type="password", 
        placeholder="sk-or-v1-..."
    )
    
    st.divider()
    
    # --- INFORMACIÓN DEL MODELO ACTUAL ---
    st.header("🤖 Modelo en uso")
    st.info(f"**{NOMBRE_MODELO_VISIBLE}**\n\n`{MODELO}`")
    
    st.divider()
    
    st.header("⚙️ Opciones")
    if st.button("🔄 Reiniciar conversación", use_container_width=True, type="secondary"):
        st.session_state.mensajes = []
        st.session_state.ejercicio_actual = None
        st.rerun()

# ==========================================
# VALIDACIÓN DE API KEY
# ==========================================
if not user_api_key:
    st.title("🪨 Monitor IA: Mecánica de Suelos")
    st.info("👈 Por favor, introduce tu API Key en la barra lateral para comenzar. Si no tienes una, consulta el tutorial desplegable en la sidebar.")
    st.stop()

# ==========================================
# TÍTULO Y SELECCIÓN DE TEMA/EJERCICIO
# ==========================================
st.title("🪨 Monitor IA: Mecánica de Suelos")
st.markdown("Selecciona el tema y el ejercicio. El monitor te dará un resumen y podrás hacerle preguntas.")

temas = obtener_temas()
if not temas:
    st.error(f"❌ No se encontró la carpeta '{CARPETA_BASE}'. Verifica la ruta.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    tema_seleccionado = st.selectbox("📚 Selecciona la unidad/tema:", temas)

ejercicios = obtener_ejercicios(tema_seleccionado)
if not ejercicios:
    st.warning("No hay archivos .md en este tema.")
    st.stop()

with col2:
    ejercicio_seleccionado = st.selectbox("📝 Selecciona el ejercicio:", ejercicios)

# ==========================================
# MODO DEL TUTOR
# ==========================================
st.divider()

modo = st.radio(
    "🎓 Modo del tutor:",
    ["Tutor", "Pista", "Solución"],
    captions=[
        "Explica paso a paso con razonamiento",
        "Solo pistas, tú calculas",
        "Solución completa detallada",
    ],
    horizontal=True,
    index=0,
)

colores_modo = {"Tutor": "#2563eb", "Pista": "#d97706", "Solución": "#16a34a"}
st.caption(f"**Tema:** {tema_seleccionado}  ·  **Ejercicio:** {ejercicio_seleccionado.replace('.md', '')}")

st.divider()

# ==========================================
# LÓGICA DEL CHAT
# ==========================================
id_ejercicio = f"{tema_seleccionado}/{ejercicio_seleccionado}/{modo}"

if "ejercicio_actual" not in st.session_state or st.session_state.ejercicio_actual != id_ejercicio:
    st.session_state.ejercicio_actual = id_ejercicio
    st.session_state.mensajes = []

contenido_md = leer_ejercicio(tema_seleccionado, ejercicio_seleccionado)
prompt_sistema = construir_prompt_sistema(contenido_md, modo)

# Inicializar cliente con la clave del usuario
cliente = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=user_api_key,
)

# Texto de firma del modelo para añadir al final de las respuestas
firma_modelo = f'<span class="modelo-firma">🤖 Respondido por: {NOMBRE_MODELO_VISIBLE} </span>'

# --- BIENVENIDA ESTÁTICA ---
if len(st.session_state.mensajes) == 0:
    with st.chat_message("assistant"):
        st.markdown(
            f"¡Hola! 👋 Soy tu monitor de **Mecánica de Suelos**. "
            f"Selecciona un tema y un ejercicio, elige el modo que prefieras y escríbeme cuando estés listo. ¡Estoy aquí para ayudarte!"
        )
        st.markdown(firma_modelo, unsafe_allow_html=True)

# --- MOSTRAR HISTORIAL ---
for mensaje in st.session_state.mensajes:
    if not mensaje.get("oculto", False):
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])
            # Si es un mensaje del asistente, mostrar la firma del modelo
            if mensaje["role"] == "assistant":
                st.markdown(firma_modelo, unsafe_allow_html=True)

# --- INPUT DEL USUARIO ---
if prompt := st.chat_input("Escribe tu pregunta sobre este ejercicio..."):
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    mensajes_api = [{"role": "system", "content": prompt_sistema}]
    for m in st.session_state.mensajes:
        mensajes_api.append({"role": m["role"], "content": m["content"]})

    with st.chat_message("assistant"):
        contenedor_respuesta = st.empty()
        contenedor_respuesta.markdown("🧠 *Pensando...*")
        respuesta_completa = ""
        try:
            stream = cliente.chat.completions.create(
                model=MODELO,
                messages=mensajes_api,
                stream=True,
            )
            for trozo in stream:
                if trozo.choices[0].delta.content is not None:
                    respuesta_completa += trozo.choices[0].delta.content
                    contenedor_respuesta.markdown(respuesta_completa + "▌")
            
            # Mostrar respuesta final + firma del modelo
            contenedor_respuesta.markdown(respuesta_completa)
            st.markdown(firma_modelo, unsafe_allow_html=True)
            
            st.session_state.mensajes.append({"role": "assistant", "content": respuesta_completa})
        except Exception as e:
            st.error(f"Error al conectar con OpenRouter: {e}")