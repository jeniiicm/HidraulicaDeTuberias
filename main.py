
import math
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Hidráulica en tuberías",
    page_icon="💧",
    layout="wide",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 220, 238, 0.55), transparent 32%),
            radial-gradient(circle at top right, rgba(226, 214, 255, 0.55), transparent 30%),
            linear-gradient(180deg, #fffafd 0%, #fbf8ff 100%);
        color: #3f3550;
    }

    /* Encabezados */
    h1 {
        color: #8d4f82 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    h2, h3 {
        color: #77558f !important;
        font-weight: 600 !important;
    }

    p, label, .stMarkdown {
        color: #463b52;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8e8f2 0%, #eee8fb 100%);
        border-right: 1px solid #decbe3;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #784c78 !important;
    }

    /* Inputs */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.93) !important;
        border-color: #d7bfdc !important;
        border-radius: 12px !important;
    }

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #a979b1 !important;
        box-shadow: 0 0 0 1px #a979b1 !important;
    }

    /* Botones y checks */
    .stButton > button {
        background: linear-gradient(90deg, #dca6c8 0%, #b9a3dc 100%);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.55rem 1rem;
        box-shadow: 0 4px 12px rgba(137, 92, 137, 0.14);
    }

    .stButton > button:hover {
        filter: brightness(0.98);
        color: #ffffff;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid #ead8ea;
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 6px 18px rgba(112, 78, 126, 0.08);
    }

    div[data-testid="stMetricLabel"] {
        color: #735570 !important;
        font-weight: 500;
    }

    div[data-testid="stMetricValue"] {
        color: #5c436e !important;
        font-weight: 700;
    }

    /* Expander */
    details {
        background: rgba(255, 255, 255, 0.62);
        border: 1px solid #eadbea !important;
        border-radius: 14px !important;
    }

    /* Tablas */
    div[data-testid="stTable"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #ead8ea;
    }

    /* Alertas */
    div[data-testid="stAlert"] {
        border-radius: 14px;
        border: 1px solid rgba(180, 150, 193, 0.35);
    }

    /* Código y fórmulas */
    code {
        border-radius: 8px !important;
    }

    .katex {
        color: #4f405d !important;
    }

    /* Separación agradable entre secciones */
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* Pie visual */
    .jeni-footer {
        margin-top: 2.5rem;
        text-align: center;
        color: #9b86a5;
        font-size: 0.82rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Funciones de apoyo
# -----------------------------
def a_metros(valor, unidad):
    factores = {
        "m": 1.0,
        "cm": 0.01,
        "mm": 0.001,
        "in": 0.0254,
    }
    return valor * factores[unidad]

def caudal_a_m3s(valor, unidad):
    factores = {
        "m³/s": 1.0,
        "L/s": 1e-3,
        "L/min": 1e-3 / 60.0,
        "m³/min": 1.0 / 60.0,
        "m³/h": 1.0 / 3600.0,
    }
    return valor * factores[unidad]

def volumen_a_m3(valor, unidad):
    factores = {
        "m³": 1.0,
        "L": 1e-3,
        "mL": 1e-6,
    }
    return valor * factores[unidad]

def colebrook(re, eps_rel, f0=0.02, tol=1e-10, max_iter=100):
    """Resuelve Colebrook por iteración de punto fijo."""
    if re <= 0:
        return None
    f = f0
    for _ in range(max_iter):
        interior = eps_rel / 3.7 + 2.51 / (re * math.sqrt(f))
        if interior <= 0:
            return None
        f_nuevo = 1.0 / (-2.0 * math.log10(interior)) ** 2
        if abs(f_nuevo - f) < tol:
            return f_nuevo
        f = f_nuevo
    return f

def clasificar_flujo(re, criterio):
    if criterio == "Apuntes: 2000 / 4000":
        if re < 2000:
            return "Laminar"
        elif re <= 4000:
            return "Transición"
        return "Turbulento"
    else:
        if re < 2300:
            return "Laminar"
        elif re <= 4000:
            return "Transición"
        return "Turbulento"

def factor_blasius(re):
    if re <= 0:
        return None
    return 0.3164 / (re ** 0.25)

def factor_laminar(re):
    if re <= 0:
        return None
    return 64.0 / re

def f_moody(re, eps_rel):
    """Factor Darcy para dibujar el diagrama."""
    if re < 2300:
        return 64.0 / re
    # Haaland para trazado rápido y estable.
    return 1.0 / (-1.8 * math.log10((eps_rel / 3.7) ** 1.11 + 6.9 / re)) ** 2

# -----------------------------
# Encabezado
# -----------------------------
st.title("💧 Hidráulica en tuberías")
st.caption(
    "Calculadora de flujo, Reynolds, factor de fricción, Darcy–Weisbach y diagrama de Moody."
)

with st.expander("¿Qué calcula este programa?"):
    st.markdown(
        """
        Con los datos que normalmente vienen en un ejercicio puede calcular:

        - Área de la tubería
        - Caudal, velocidad o caudal a partir de volumen/tiempo
        - Número de Reynolds y tipo de flujo
        - Rugosidad relativa ε/D
        - Factor de fricción de Darcy por Poiseuille, Blasius y Colebrook
        - Pérdida de carga por fricción con Darcy–Weisbach
        - Carga de velocidad V²/(2g)
        - Ubicación aproximada del punto en un diagrama de Moody

        **Nota:** el programa usa el factor de fricción de **Darcy**, no el de Fanning.
        """
    )

# -----------------------------
# Barra lateral: propiedades
# -----------------------------
st.sidebar.header("Configuración")

criterio = st.sidebar.selectbox(
    "Criterio para clasificar el flujo",
    ["Apuntes: 2000 / 4000", "Convencional: 2300 / 4000"],
    index=0,
)

st.sidebar.subheader("Viscosidad cinemática ν")
usar_agua = st.sidebar.checkbox("Usar agua a 25 °C", value=True)

if usar_agua:
    nu = 9e-7
    st.sidebar.caption("ν = 9×10⁻⁷ m²/s, como en tus apuntes.")
else:
    nu = st.sidebar.number_input(
        "ν [m²/s]",
        min_value=1e-12,
        value=1.0e-6,
        format="%.10e",
    )

st.sidebar.subheader("Rugosidad absoluta ε")
materiales_mm = {
    "PVC / plástico / vidrio": 0.0015,
    "Cobre": 0.0015,
    "Galvanizado (valor usado en tus apuntes)": 0.015,
    "Personalizada": None,
}

material = st.sidebar.selectbox("Material", list(materiales_mm.keys()))
if materiales_mm[material] is None:
    eps_mm = st.sidebar.number_input(
        "ε [mm]", min_value=0.0, value=0.015, format="%.6f"
    )
else:
    eps_mm = materiales_mm[material]
    st.sidebar.write(f"ε = {eps_mm:g} mm")

eps = eps_mm / 1000.0

# -----------------------------
# Datos de entrada
# -----------------------------
st.header("1. Datos del ejercicio")

c1, c2, c3 = st.columns(3)

with c1:
    D_val = st.number_input(
        "Diámetro",
        min_value=0.000001,
        value=1.0,
        format="%.6f",
    )
    D_uni = st.selectbox("Unidad del diámetro", ["in", "mm", "cm", "m"], index=0)
    D = a_metros(D_val, D_uni)

with c2:
    L_val = st.number_input(
        "Longitud de tubería",
        min_value=0.0,
        value=100.0,
        format="%.3f",
    )
    L_uni = st.selectbox("Unidad de longitud", ["m", "cm", "mm"], index=0)
    L = a_metros(L_val, L_uni)

with c3:
    modo = st.selectbox(
        "Dato hidráulico disponible",
        [
            "Velocidad V",
            "Caudal Q",
            "Volumen y tiempo",
        ],
    )

A = math.pi * D**2 / 4.0

if modo == "Velocidad V":
    v = st.number_input(
        "Velocidad V [m/s]",
        min_value=0.0,
        value=0.5,
        format="%.6f",
    )
    Q = A * v

elif modo == "Caudal Q":
    q1, q2 = st.columns([2, 1])
    with q1:
        Q_val = st.number_input(
            "Caudal",
            min_value=0.0,
            value=20.0,
            format="%.6f",
        )
    with q2:
        Q_uni = st.selectbox("Unidad de Q", ["L/s", "L/min", "m³/s", "m³/min", "m³/h"])
    Q = caudal_a_m3s(Q_val, Q_uni)
    v = Q / A if A > 0 else 0.0

else:
    q1, q2, q3 = st.columns(3)
    with q1:
        vol_val = st.number_input(
            "Volumen recolectado",
            min_value=0.0,
            value=20.0,
            format="%.6f",
        )
    with q2:
        vol_uni = st.selectbox("Unidad de volumen", ["L", "m³", "mL"])
    with q3:
        t = st.number_input(
            "Tiempo [s]",
            min_value=0.000001,
            value=45.0,
            format="%.6f",
        )
    vol = volumen_a_m3(vol_val, vol_uni)
    Q = vol / t
    v = Q / A if A > 0 else 0.0

# -----------------------------
# Cálculos principales
# -----------------------------
Re = v * D / nu if nu > 0 else float("nan")
regimen = clasificar_flujo(Re, criterio)
eps_rel = eps / D if D > 0 else float("nan")
hv = v**2 / (2 * 9.81)

f_poiseuille = factor_laminar(Re)
f_blasius = factor_blasius(Re)
f_colebrook = colebrook(Re, eps_rel)

if regimen == "Laminar":
    f_recomendado = f_poiseuille
    metodo_recomendado = "Poiseuille (f = 64/Re)"
elif regimen == "Turbulento":
    f_recomendado = f_colebrook
    metodo_recomendado = "Colebrook"
else:
    f_recomendado = f_colebrook
    metodo_recomendado = "Colebrook (zona de transición: usar con cautela)"

hf = (
    f_recomendado * (L / D) * hv
    if f_recomendado is not None and D > 0
    else None
)

# -----------------------------
# Resultados
# -----------------------------
st.header("2. Resultados")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Diámetro D", f"{D:.6g} m")
r2.metric("Área A", f"{A:.6g} m²")
r3.metric("Velocidad V", f"{v:.6g} m/s")
r4.metric("Caudal Q", f"{Q:.6g} m³/s")

r5, r6, r7, r8 = st.columns(4)
r5.metric("Reynolds Re", f"{Re:,.0f}")
r6.metric("Tipo de flujo", regimen)
r7.metric("ε/D", f"{eps_rel:.6e}")
r8.metric("V²/(2g)", f"{hv:.6g} m")

st.subheader("Factor de fricción")

tabla = {
    "Método": [],
    "Factor f": [],
    "Aplicación": [],
}

tabla["Método"].append("Poiseuille")
tabla["Factor f"].append(f"{f_poiseuille:.6f}" if f_poiseuille else "—")
tabla["Aplicación"].append("Flujo laminar")

tabla["Método"].append("Blasius")
tabla["Factor f"].append(f"{f_blasius:.6f}" if f_blasius else "—")
tabla["Aplicación"].append("Tubo liso; aprox. Re 3,000–100,000")

tabla["Método"].append("Colebrook")
tabla["Factor f"].append(f"{f_colebrook:.6f}" if f_colebrook else "—")
tabla["Aplicación"].append("Flujo turbulento con rugosidad")

st.table(tabla)

if 3000 <= Re <= 100000:
    st.caption(
        f"Blasius = {f_blasius:.6f} y Colebrook = {f_colebrook:.6f}. "
        "Puedes comparar ambos, como en tus apuntes."
    )

st.success(
    f"Factor recomendado por el programa: f = {f_recomendado:.6f} — {metodo_recomendado}"
    if f_recomendado
    else "No se pudo calcular el factor de fricción."
)

if regimen == "Transición":
    st.warning(
        "El flujo está en la zona de transición. El factor de fricción puede ser inestable; "
        "conviene reportar que el resultado es aproximado."
    )

st.subheader("Pérdida de carga por fricción — Darcy–Weisbach")
st.latex(r"h_f=f\frac{L}{D}\frac{V^2}{2g}")

if hf is not None:
    st.metric("h_f", f"{hf:.6f} m.c.a.")
else:
    st.write("No disponible.")

# -----------------------------
# Desarrollo paso a paso
# -----------------------------
st.header("3. Desarrollo paso a paso")

st.markdown("**Área de la tubería**")
st.latex(r"A=\frac{\pi D^2}{4}")
st.code(f"A = π({D:.6g})²/4 = {A:.6g} m²")

if modo != "Velocidad V":
    st.markdown("**Velocidad**")
    st.latex(r"V=\frac{Q}{A}")
    st.code(f"V = {Q:.6g} / {A:.6g} = {v:.6g} m/s")

st.markdown("**Número de Reynolds**")
st.latex(r"Re=\frac{VD}{\nu}")
st.code(f"Re = ({v:.6g})({D:.6g}) / ({nu:.6e}) = {Re:.3f}")

st.markdown("**Rugosidad relativa**")
st.latex(r"\frac{\varepsilon}{D}")
st.code(f"ε/D = {eps:.6e} / {D:.6g} = {eps_rel:.6e}")

if f_colebrook:
    st.markdown("**Ecuación de Colebrook**")
    st.latex(
        r"\frac{1}{\sqrt{f}}=-2\log_{10}\left(\frac{\varepsilon/D}{3.7}+\frac{2.51}{Re\sqrt{f}}\right)"
    )
    st.code(f"f ≈ {f_colebrook:.6f}")

if hf is not None:
    st.markdown("**Darcy–Weisbach**")
    st.code(
        f"h_f = ({f_recomendado:.6f})({L:.6g}/{D:.6g})({v:.6g}²/(2·9.81)) = {hf:.6f} m"
    )

# -----------------------------
# Moody
# -----------------------------
st.header("4. Diagrama de Moody")

if st.checkbox("Mostrar diagrama de Moody", value=True):
    re_vals_lam = np.logspace(math.log10(500), math.log10(2300), 120)
    re_vals_turb = np.logspace(math.log10(4000), 8, 320)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.loglog(re_vals_lam, 64.0 / re_vals_lam, label="Laminar")

    rugosidades = [0.0, 1e-6, 1e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2]
    for rr in rugosidades:
        f_vals = [f_moody(r, rr) for r in re_vals_turb]
        etiqueta = "Tubo liso" if rr == 0 else f"ε/D={rr:g}"
        ax.loglog(re_vals_turb, f_vals, linewidth=1, label=etiqueta)

    ax.axvspan(2300, 4000, alpha=0.12, label="Transición")

    if Re > 0 and f_recomendado:
        ax.scatter([Re], [f_recomendado], s=70, zorder=5)
        ax.annotate(
            f"Tu punto\nRe={Re:.2e}\nf={f_recomendado:.4f}",
            (Re, f_recomendado),
            textcoords="offset points",
            xytext=(10, 10),
        )

    ax.set_xlabel("Número de Reynolds, Re")
    ax.set_ylabel("Factor de fricción de Darcy, f")
    ax.set_title("Diagrama de Moody aproximado")
    ax.grid(True, which="both", alpha=0.25)
    ax.set_xlim(5e2, 1e8)
    ax.set_ylim(0.008, 0.12)
    ax.legend(fontsize=8, ncol=2)

    st.pyplot(fig)
    plt.close(fig)

st.info(
    "Consejo: para tus ejercicios puedes introducir directamente el diámetro, la longitud "
    "y uno de estos datos: velocidad, caudal o volumen + tiempo. El programa obtiene lo demás."
)


st.markdown(
    '<div class="jeni-footer">Calculadora personal de hidráulica en tuberías 💗💜</div>',
    unsafe_allow_html=True,
)
