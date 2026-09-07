
import math
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
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

    h1 {
        color: #8d4f82 !important;
        font-weight: 700 !important;
    }

    h2, h3 {
        color: #77558f !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8e8f2 0%, #eee8fb 100%);
        border-right: 1px solid #decbe3;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: rgba(255,255,255,0.95) !important;
        border-color: #d7bfdc !important;
        border-radius: 12px !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 14px;
    }

    .result-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid #ead8ea;
        border-radius: 16px;
        padding: 15px 17px;
        min-height: 100px;
        box-shadow: 0 6px 18px rgba(112,78,126,0.08);
        margin-bottom: 8px;
    }

    .result-title {
        font-size: 0.82rem;
        color: #735570;
        margin-bottom: 7px;
        font-weight: 500;
    }

    .result-value {
        font-size: 1.34rem;
        color: #5c436e;
        font-weight: 700;
        line-height: 1.18;
        overflow-wrap: anywhere;
    }

    .soft-box {
        background: rgba(255,255,255,0.66);
        border: 1px solid #ead8ea;
        border-radius: 14px;
        padding: 12px 15px;
        margin: 8px 0 14px 0;
    }

    .block-container {
        max-width: 1280px;
        padding-top: 1.4rem;
        padding-bottom: 4rem;
    }

    .jeni-footer {
        text-align: center;
        color: #9b86a5;
        font-size: 0.82rem;
        margin-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

G = 9.81

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def a_metros(valor, unidad):
    factores = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254}
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
    factores = {"m³": 1.0, "L": 1e-3, "mL": 1e-6}
    return valor * factores[unidad]

def area_circular(D):
    return math.pi * D**2 / 4.0

def reynolds(V, D, nu):
    return V * D / nu if nu > 0 else float("nan")

def clasificar_flujo(Re, criterio):
    if criterio == "Criterio 2000 / 4000":
        if Re < 2000:
            return "Laminar"
        elif Re <= 4000:
            return "Transición"
        return "Turbulento"
    else:
        if Re < 2300:
            return "Laminar"
        elif Re <= 4000:
            return "Transición"
        return "Turbulento"

def f_poiseuille(Re):
    return 64.0 / Re if Re > 0 else None

def f_blasius(Re):
    return 0.3164 / (Re ** 0.25) if Re > 0 else None

def f_colebrook(Re, eps_rel, f0=0.02, tol=1e-12, max_iter=200):
    if Re <= 0:
        return None
    f = f0
    for _ in range(max_iter):
        argumento = eps_rel / 3.71 + 2.51 / (Re * math.sqrt(f))
        if argumento <= 0:
            return None
        nuevo = 1.0 / (-2.0 * math.log10(argumento)) ** 2
        if abs(nuevo - f) < tol:
            return nuevo
        f = nuevo
    return f

def f_guerrero(Re, eps_rel):
    if 4000 <= Re <= 1e5:
        GG, T = 4.555, 0.8764
    elif 1e5 < Re <= 3e6:
        GG, T = 6.732, 0.9104
    elif 3e6 < Re <= 1e8:
        GG, T = 8.982, 0.93
    else:
        return None, None, None
    den = math.log10(eps_rel / 3.71 + GG / (Re ** T))
    return 0.25 / (den**2), GG, T

def hf_darcy(f, L, D, V):
    return f * (L / D) * (V**2 / (2 * G))

def hf_hazen(L, Q, D, C):
    return 10.64 * L * (Q**1.85) / ((D**4.87) * (C**1.85))

def hf_manning(L, Q, D, n):
    return 10.293 * (n**2) * L * (Q**2) / (D ** (16 / 3))

def hf_local(K, V):
    return K * (V**2 / (2 * G))

def fmt(x, unidad="", dec=3):
    """Muestra resultados con máximo 3 decimales.
    Para valores muy pequeños usa notación científica con 3 decimales.
    """
    if x is None:
        return "—"
    try:
        if not np.isfinite(x):
            return "—"
    except Exception:
        return str(x)

    if x == 0:
        txt = "0"
    elif abs(x) < 0.001:
        txt = f"{x:.3e}"
    elif abs(x) >= 100000:
        txt = f"{x:,.0f}"
    else:
        txt = f"{x:.{dec}f}".rstrip("0").rstrip(".")
    return f"{txt} {unidad}".strip()

def tarjeta(titulo, valor):
    st.markdown(
        f"""
<div class="result-card">
<div class="result-title">{titulo}</div>
<div class="result-value">{valor}</div>
</div>
""",
        unsafe_allow_html=True,
    )

def entrada_geometria(prefix, D_default=1.0, D_unit="in", L_default=100.0):
    c1, c2 = st.columns(2)
    with c1:
        Dv = st.number_input(
            "Diámetro",
            min_value=0.000001,
            value=float(D_default),
            format="%.6f",
            key=f"{prefix}_Dv",
        )
        Du = st.selectbox(
            "Unidad del diámetro",
            ["in", "mm", "cm", "m"],
            index=["in", "mm", "cm", "m"].index(D_unit),
            key=f"{prefix}_Du",
        )
    with c2:
        Lv = st.number_input(
            "Longitud",
            min_value=0.0,
            value=float(L_default),
            format="%.4f",
            key=f"{prefix}_Lv",
        )
        Lu = st.selectbox(
            "Unidad de longitud",
            ["m", "cm", "mm"],
            index=0,
            key=f"{prefix}_Lu",
        )
    return a_metros(Dv, Du), a_metros(Lv, Lu)

def entrada_hidraulica(prefix, D, default="Caudal Q"):
    A = area_circular(D)
    opciones = ["Velocidad V", "Caudal Q", "Volumen y tiempo"]
    modo = st.selectbox(
        "Dato hidráulico disponible",
        opciones,
        index=opciones.index(default),
        key=f"{prefix}_modo",
    )

    if modo == "Velocidad V":
        V = st.number_input(
            "Velocidad V [m/s]",
            min_value=0.0,
            value=0.8,
            format="%.6f",
            key=f"{prefix}_V",
        )
        Q = A * V

    elif modo == "Caudal Q":
        c1, c2 = st.columns([2, 1])
        with c1:
            qv = st.number_input(
                "Caudal",
                min_value=0.0,
                value=2.0,
                format="%.6f",
                key=f"{prefix}_Qv",
            )
        with c2:
            qu = st.selectbox(
                "Unidad de Q",
                ["L/s", "L/min", "m³/s", "m³/min", "m³/h"],
                key=f"{prefix}_Qu",
            )
        Q = caudal_a_m3s(qv, qu)
        V = Q / A if A > 0 else 0.0

    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            vv = st.number_input(
                "Volumen",
                min_value=0.0,
                value=20.0,
                format="%.6f",
                key=f"{prefix}_vol",
            )
        with c2:
            vu = st.selectbox(
                "Unidad de volumen",
                ["L", "m³", "mL"],
                key=f"{prefix}_volu",
            )
        with c3:
            t = st.number_input(
                "Tiempo [s]",
                min_value=0.000001,
                value=45.0,
                format="%.6f",
                key=f"{prefix}_t",
            )
        Q = volumen_a_m3(vv, vu) / t
        V = Q / A if A > 0 else 0.0

    return A, Q, V

# ============================================================
# ENCABEZADO Y CONFIGURACIÓN GLOBAL
# ============================================================
st.title("💧 Hidráulica en tuberías")
st.caption(
    "Programa interactivo para Reynolds, Darcy–Weisbach, Hazen–Williams, "
    "Chézy–Manning, Colebrook, pérdidas localizadas, Moody y diseño de diámetro."
)

st.sidebar.header("Configuración general")
criterio = st.sidebar.selectbox(
    "Criterio para clasificar el flujo",
    ["Criterio 2000 / 4000", "Convencional: 2300 / 4000"],
    index=0,
)

usar_agua = st.sidebar.checkbox(
    "Usar agua a 25 °C (ν = 9×10⁻⁷ m²/s)",
    value=True,
)
if usar_agua:
    nu_global = 9e-7
else:
    nu_global = st.sidebar.number_input(
        "ν [m²/s]",
        min_value=1e-12,
        value=1e-6,
        format="%.10e",
    )


tabs = st.tabs(
    [
        "🏠 Inicio",
        "Darcy",
        "Hazen–Williams",
        "Chézy–Manning",
        "Colebrook",
        "Pérdidas locales",
        "Moody",
        "Diseño de diámetro",
    ]
)

# ============================================================
# INICIO
# ============================================================
with tabs[0]:
    st.header("Datos básicos y número de Reynolds")
    st.latex(r"Re=\frac{VD}{\nu}")

    D, L = entrada_geometria("ini", D_default=1.0, D_unit="in", L_default=100.0)
    A, Q, V = entrada_hidraulica("ini", D, default="Velocidad V")

    Re = reynolds(V, D, nu_global)
    reg = clasificar_flujo(Re, criterio)
    hv = V**2 / (2 * G)

    c = st.columns(4)
    with c[0]:
        tarjeta("Área A", fmt(A, "m²"))
    with c[1]:
        tarjeta("Velocidad V", fmt(V, "m/s"))
    with c[2]:
        tarjeta("Caudal Q", fmt(Q, "m³/s"))
    with c[3]:
        tarjeta("Reynolds Re", f"{Re:,.0f}")

    c = st.columns(2)
    with c[0]:
        tarjeta("Tipo de flujo", reg)
    with c[1]:
        tarjeta("Carga de velocidad V²/(2g)", fmt(hv, "m"))

    with st.expander("Fórmulas básicas"):
        st.latex(r"A=\frac{\pi D^2}{4}")
        st.latex(r"Q=AV")
        st.latex(r"V=\frac{Q}{A}")
        st.latex(r"Re=\frac{VD}{\nu}")

# ============================================================
# DARCY
# ============================================================
with tabs[1]:
    st.header("Darcy–Weisbach o fórmula universal")
    st.latex(r"h_f=f\frac{L}{D}\frac{V^2}{2g}")

    D, L = entrada_geometria("darcy", D_default=1.0, D_unit="in", L_default=100.0)
    A, Q, V = entrada_hidraulica("darcy", D, default="Caudal Q")

    Re = reynolds(V, D, nu_global)
    reg = clasificar_flujo(Re, criterio)

    st.subheader("Rugosidad")
    rug_mm = {
        "PVC / plástico / vidrio — 0.0015 mm": 0.0015,
        "Cobre — 0.0015 mm": 0.0015,
        "Galvanizado — 0.015 mm": 0.015,
        "Personalizada": None,
    }
    material = st.selectbox("Material / rugosidad", list(rug_mm.keys()), key="darcy_mat")
    if rug_mm[material] is None:
        eps_mm = st.number_input(
            "ε [mm]",
            min_value=0.0,
            value=0.015,
            format="%.6f",
            key="darcy_eps",
        )
    else:
        eps_mm = rug_mm[material]

    eps_rel = (eps_mm / 1000.0) / D
    fp = f_poiseuille(Re)
    fb = f_blasius(Re)
    fc = f_colebrook(Re, eps_rel)

    if reg == "Laminar":
        f_usado = fp
        metodo = "Poiseuille"
    else:
        f_usado = fc
        metodo = "Colebrook"

    hf = hf_darcy(f_usado, L, D, V) if f_usado is not None else None
    S = hf / L if hf is not None and L > 0 else None

    c = st.columns(4)
    with c[0]:
        tarjeta("Reynolds", f"{Re:,.0f}")
    with c[1]:
        tarjeta("Tipo de flujo", reg)
    with c[2]:
        tarjeta("Rugosidad relativa ε/D", fmt(eps_rel))
    with c[3]:
        tarjeta("Factor recomendado f", fmt(f_usado))

    st.subheader("Comparación de factores de fricción")
    st.table(
        {
            "Método": ["Poiseuille", "Blasius", "Colebrook"],
            "f": [
                fmt(fp),
                fmt(fb),
                fmt(fc),
            ],
            "Aplicación": [
                "Flujo laminar",
                "Tubos lisos, Re ≈ 3,000–100,000",
                "Flujo turbulento con rugosidad",
            ],
        }
    )

    c = st.columns(2)
    with c[0]:
        tarjeta("Pérdida por fricción h_f", fmt(hf, "m.c.a."))
    with c[1]:
        tarjeta("Pendiente hidráulica S = h_f/L", fmt(S, "m/m"))

    st.caption(f"Método recomendado usado: {metodo}.")

# ============================================================
# HAZEN-WILLIAMS
# ============================================================
with tabs[2]:
    st.header("Hazen–Williams")
    st.latex(r"h_f=\frac{10.64\,L\,Q^{1.85}}{D^{4.87}C^{1.85}}")

    D, L = entrada_geometria("hw", D_default=3.0, D_unit="in", L_default=100.0)
    A, Q, V = entrada_hidraulica("hw", D, default="Caudal Q")

    C_valores = {
        "Galvanizado": 120.0,
        "Cobre": 135.0,
        "PVC / CPVC / PEAD": 150.0,
        "Plástico": 140.0,
        "Asbesto": 140.0,
        "Concreto (promedio de 120–130)": 125.0,
        "PP-r / personalizado": None,
    }
    mat = st.selectbox("Material", list(C_valores.keys()), key="hw_mat")
    if C_valores[mat] is None:
        C = st.number_input("Coeficiente C", min_value=1.0, value=140.0, step=1.0, key="hw_C")
    else:
        C = C_valores[mat]

    hf = hf_hazen(L, Q, D, C)
    S = hf / L if L > 0 else None

    if D <= 0.0508:
        st.warning("Hazen–Williams: D debe ser mayor a 2 in.")
    if V >= 3:
        st.warning("Hazen–Williams: V debe ser menor a 3 m/s.")

    c = st.columns(4)
    with c[0]:
        tarjeta("Coeficiente C", fmt(C))
    with c[1]:
        tarjeta("Velocidad V", fmt(V, "m/s"))
    with c[2]:
        tarjeta("Pérdida h_f", fmt(hf, "m.c.a."))
    with c[3]:
        tarjeta("Pendiente S", fmt(S, "m/m"))

# ============================================================
# CHEZY-MANNING
# ============================================================
with tabs[3]:
    st.header("Chézy–Manning")
    st.latex(r"h_f=\frac{10.293\,n^2\,L\,Q^2}{D^{16/3}}")

    D, L = entrada_geometria("man", D_default=1.0, D_unit="in", L_default=100.0)
    A, Q, V = entrada_hidraulica("man", D, default="Caudal Q")

    n_tabla = {
        "Acero — n = 0.011": 0.011,
        "Liso / plástico — n = 0.008": 0.008,
        "Personalizado": None,
    }
    nmat = st.selectbox("Material / n", list(n_tabla.keys()), key="man_mat")
    if n_tabla[nmat] is None:
        n = st.number_input(
            "n",
            min_value=0.000001,
            value=0.010,
            format="%.6f",
            key="man_n",
        )
    else:
        n = n_tabla[nmat]

    hf = hf_manning(L, Q, D, n)
    S = hf / L if L > 0 else None

    c = st.columns(3)
    with c[0]:
        tarjeta("n", fmt(n))
    with c[1]:
        tarjeta("Pérdida h_f", fmt(hf, "m.c.a."))
    with c[2]:
        tarjeta("Pendiente S = h_f/L", fmt(S, "m/m"))


# ============================================================
# COLEBROOK
# ============================================================
with tabs[4]:
    st.header("Colebrook–White")
    st.latex(
        r"\frac{1}{\sqrt f}=-2\log\left("
        r"\frac{\varepsilon/D}{3.71}+\frac{2.51}{Re\sqrt f}\right)"
    )

    c1, c2 = st.columns(2)
    with c1:
        Re_c = st.number_input(
            "Reynolds Re",
            min_value=1.0,
            value=30000.0,
            step=100.0,
            key="col_Re",
        )
    with c2:
        eps_rel_c = st.number_input(
            "Rugosidad relativa ε/D",
            min_value=0.0,
            value=7.167e-4,
            format="%.8f",
            key="col_eps",
        )

    fc = f_colebrook(Re_c, eps_rel_c)
    fg, GG, T = f_guerrero(Re_c, eps_rel_c)

    c = st.columns(3)
    with c[0]:
        tarjeta("Colebrook f", fmt(fc))
    with c[1]:
        tarjeta("Guerrero f", fmt(fg) if fg is not None else "Fuera de rango")
    with c[2]:
        tarjeta("Parámetros Guerrero", f"G={GG}, T={T}" if GG is not None else "—")

    with st.expander("Ecuación modificada de Guerrero"):
        st.latex(
            r"f=\frac{0.25}{\left[\log\left("
            r"\frac{\varepsilon/D}{3.71}+\frac{G}{Re^T}\right)\right]^2}"
        )
        st.markdown(
            """
            - G = 4.555 y T = 0.8764 para 4000 ≤ Re ≤ 10⁵  
            - G = 6.732 y T = 0.9104 para 10⁵ < Re ≤ 3×10⁶  
            - G = 8.982 y T = 0.93 para 3×10⁶ ≤ Re ≤ 10⁸
            """
        )

# ============================================================
# PÉRDIDAS LOCALES
# ============================================================
with tabs[5]:
    st.header("Pérdidas localizadas")
    st.caption("Cálculo por longitudes equivalentes y métodos específicos para reducciones, ampliaciones y rejillas.")

    subtabs = st.tabs(["Longitudes equivalentes", "Reducción", "Ampliación", "Rejilla / filtro"])

    with subtabs[0]:
        st.subheader("Pérdidas por accesorios mediante longitud equivalente")
        st.latex(r"L_T=L+\sum L_e")
        st.latex(r"h_f=f\frac{L_T}{D}\frac{V^2}{2g}")

        # Tabla de longitudes equivalentes (m de tubería rectilínea)
        accesorios_le = [
            "Codo 90° radio largo",
            "Codo 90° radio medio",
            "Codo 90° radio corto",
            "Codo 45°",
            "Curva 90° R/D = 1 1/2",
            "Curva 90° R/D = 1",
            "Curva 45°",
            "Entrada normal",
            "Entrada de Borda",
            "Válvula de compuerta abierta",
            "Válvula tipo globo abierta",
            "Válvula de ángulo abierta",
            "Té paso directo",
            "Té salida lateral",
            "Té salida bilateral",
            "Válvula de pie",
            "Salida de tubería",
            "Válvula de retención tipo liviano",
            "Válvula de retención tipo pesado",
        ]

        diametros_tabla = {
            "13 mm — 1/2 in": (13, [0.3,0.4,0.5,0.2,0.2,0.3,0.2,0.2,0.4,0.1,4.9,2.6,0.3,1.0,1.0,3.6,0.4,1.1,1.6]),
            "19 mm — 3/4 in": (19, [0.4,0.6,0.7,0.3,0.3,0.4,0.2,0.2,0.5,0.1,6.7,3.6,0.4,1.4,1.4,5.6,0.5,1.6,2.4]),
            "25 mm — 1 in": (25, [0.5,0.7,0.8,0.4,0.3,0.5,0.2,0.3,0.7,0.2,8.2,4.6,0.5,1.7,1.7,7.3,0.7,2.1,3.2]),
            "32 mm — 1 1/4 in": (32, [0.7,0.9,1.1,0.5,0.4,0.6,0.3,0.4,0.9,0.2,11.3,5.6,0.7,2.3,2.3,10.0,0.9,2.7,4.0]),
            "38 mm — 1 1/2 in": (38, [0.9,1.1,1.3,0.6,0.5,0.7,0.3,0.5,1.0,0.3,13.4,6.7,0.9,2.8,2.8,11.6,1.0,3.2,4.8]),
            "50 mm — 2 in": (50, [1.1,1.4,1.7,0.8,0.6,0.9,0.4,0.7,1.5,0.4,17.4,8.5,1.1,3.5,3.5,14.0,1.5,4.2,6.4]),
            "63 mm — 2 1/2 in": (63, [1.3,1.7,2.0,0.9,0.8,1.0,0.5,0.9,1.9,0.4,21.0,10.0,1.3,4.3,4.3,17.0,1.9,5.2,8.1]),
            "75 mm — 3 in": (75, [1.6,2.1,2.5,1.2,1.0,1.3,0.6,1.1,2.2,0.5,28.0,13.0,1.6,5.2,5.2,20.0,2.2,6.3,9.7]),
            "100 mm — 4 in": (100, [2.1,2.8,3.4,1.5,1.3,1.6,0.7,1.6,3.2,0.7,34.0,17.0,2.1,6.7,6.7,23.0,3.2,6.4,12.9]),
            "125 mm — 5 in": (125, [2.7,3.7,4.2,1.9,1.6,2.1,0.9,2.0,4.0,0.9,43.0,21.0,2.7,8.4,8.4,30.0,4.0,10.4,16.1]),
            "150 mm — 6 in": (150, [3.4,4.3,4.9,2.3,1.9,2.5,1.1,2.5,5.0,1.1,51.0,26.0,3.4,10.0,10.0,39.0,5.0,12.5,19.3]),
            "200 mm — 8 in": (200, [4.3,5.5,6.4,3.0,2.4,3.3,1.5,3.5,6.0,1.4,67.0,34.0,4.3,13.0,13.0,52.0,6.0,16.0,25.0]),
            "250 mm — 10 in": (250, [5.5,6.7,7.9,3.8,3.0,4.1,1.8,4.5,7.5,1.7,85.0,43.0,5.5,16.0,16.0,65.0,7.5,20.0,32.0]),
            "300 mm — 12 in": (300, [6.1,7.9,9.5,4.6,3.6,4.8,2.2,5.5,9.0,2.1,102.0,51.0,6.1,19.0,19.0,78.0,9.0,24.0,38.0]),
            "350 mm — 14 in": (350, [7.3,9.5,10.5,5.3,4.4,5.4,2.5,6.2,11.0,2.4,120.0,60.0,7.3,22.0,22.0,90.0,11.0,28.0,45.0]),
        }

        diametro_nominal = st.selectbox(
            "Diámetro nominal de la tabla",
            list(diametros_tabla.keys()),
            index=2,
            key="le_diametro",
        )
        D_mm, le_fila = diametros_tabla[diametro_nominal]
        D = D_mm / 1000.0
        A = area_circular(D)

        c1, c2 = st.columns(2)
        with c1:
            L_real = st.number_input(
                "Longitud real de tubería L [m]",
                min_value=0.0,
                value=50.0,
                format="%.3f",
                key="le_L",
            )
        with c2:
            qv = st.number_input(
                "Caudal",
                min_value=0.0,
                value=2.0,
                format="%.3f",
                key="le_Q",
            )
            qu = st.selectbox(
                "Unidad de Q",
                ["L/s", "L/min", "m³/s", "m³/min", "m³/h"],
                key="le_Qu",
            )

        Q = caudal_a_m3s(qv, qu)
        V = Q / A if A > 0 else 0.0
        Re = reynolds(V, D, nu_global)
        reg = clasificar_flujo(Re, criterio)

        seleccionados = st.multiselect(
            "Selecciona todos los accesorios del sistema",
            accesorios_le,
            default=[],
            key="le_accesorios",
        )

        detalles = []
        Le_total = 0.0
        for acc in seleccionados:
            idx = accesorios_le.index(acc)
            Le_unit = le_fila[idx]
            cantidad = st.number_input(
                f"Cantidad — {acc}",
                min_value=1,
                value=1,
                step=1,
                key=f"le_cant_{idx}",
            )
            subtotal = Le_unit * cantidad
            Le_total += subtotal
            detalles.append({
                "Accesorio": acc,
                "Lₑ unitario [m]": round(Le_unit, 3),
                "Cantidad": cantidad,
                "Lₑ subtotal [m]": round(subtotal, 3),
            })

        if detalles:
            st.dataframe(detalles, use_container_width=True, hide_index=True)
        else:
            st.info("Selecciona uno o varios accesorios para sumar sus longitudes equivalentes.")

        L_total = L_real + Le_total

        st.subheader("Factor de fricción")
        metodo_f = st.selectbox(
            "Método para obtener f",
            ["Automático", "Colebrook", "Blasius", "Introducir f manual"],
            key="le_metodo_f",
        )

        eps_mm_tab = {
            "PVC / plástico / vidrio": 0.0015,
            "Cobre": 0.0015,
            "Galvanizado": 0.015,
            "Personalizada": None,
        }

        if metodo_f in ["Automático", "Colebrook"]:
            mat = st.selectbox(
                "Material / rugosidad",
                list(eps_mm_tab.keys()),
                key="le_mat",
            )
            if eps_mm_tab[mat] is None:
                eps_mm = st.number_input(
                    "ε [mm]",
                    min_value=0.0,
                    value=0.015,
                    format="%.4f",
                    key="le_eps",
                )
            else:
                eps_mm = eps_mm_tab[mat]
            eps_rel = (eps_mm / 1000.0) / D

        if metodo_f == "Introducir f manual":
            f_usado = st.number_input(
                "Factor de fricción f",
                min_value=0.000001,
                value=0.025,
                format="%.4f",
                key="le_fmanual",
            )
            metodo_nombre = "Manual"
        elif metodo_f == "Blasius":
            f_usado = f_blasius(Re)
            metodo_nombre = "Blasius"
        elif metodo_f == "Colebrook":
            f_usado = f_colebrook(Re, eps_rel)
            metodo_nombre = "Colebrook"
        else:
            if reg == "Laminar":
                f_usado = f_poiseuille(Re)
                metodo_nombre = "Poiseuille"
            else:
                f_usado = f_colebrook(Re, eps_rel)
                metodo_nombre = "Colebrook"

        hf_total = hf_darcy(f_usado, L_total, D, V) if f_usado is not None else None

        c = st.columns(4)
        with c[0]:
            tarjeta("Σ Lₑ accesorios", fmt(Le_total, "m"))
        with c[1]:
            tarjeta("Longitud total L_T", fmt(L_total, "m"))
        with c[2]:
            tarjeta("Factor f", fmt(f_usado))
        with c[3]:
            tarjeta("Pérdida total h_f", fmt(hf_total, "m.c.a."))

        c = st.columns(3)
        with c[0]:
            tarjeta("Velocidad V", fmt(V, "m/s"))
        with c[1]:
            tarjeta("Reynolds Re", f"{Re:,.0f}")
        with c[2]:
            tarjeta("Método de f", metodo_nombre)

        with st.expander("Desarrollo del cálculo"):
            st.latex(r"L_T=L+\sum L_e")
            st.write(
                f"L_T = {fmt(L_real, 'm')} + {fmt(Le_total, 'm')} = {fmt(L_total, 'm')}"
            )
            st.latex(r"h_f=f\frac{L_T}{D}\frac{V^2}{2g}")
            if hf_total is not None:
                st.write(
                    f"h_f = {fmt(f_usado)} × ({fmt(L_total, 'm')} / {fmt(D, 'm')}) "
                    f"× ({fmt(V, 'm/s')}² / (2×9.81)) = {fmt(hf_total, 'm.c.a.')}"
                )

    with subtabs[1]:
        st.subheader("Reducción")

        ratios = np.array([1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 5.0])
        Ks = np.array([0.08, 0.17, 0.26, 0.34, 0.37, 0.41, 0.43, 0.45, 0.46])

        c1, c2 = st.columns(2)
        with c1:
            D1 = st.number_input(
                "D1 (mayor) [m]",
                min_value=0.000001,
                value=0.05,
                format="%.6f",
                key="red_D1",
            )
        with c2:
            D2 = st.number_input(
                "D2 (menor) [m]",
                min_value=0.000001,
                value=0.025,
                format="%.6f",
                key="red_D2",
            )

        ratio = D1 / D2
        K_red = float(np.interp(ratio, ratios, Ks))
        Qr = st.number_input(
            "Q [m³/s]",
            min_value=0.0,
            value=0.001,
            format="%.6f",
            key="red_Q",
        )
        V2 = Qr / area_circular(D2)
        hred = hf_local(K_red, V2)

        c = st.columns(3)
        with c[0]:
            tarjeta("D1/D2", fmt(ratio))
        with c[1]:
            tarjeta("K interpolado", fmt(K_red))
        with c[2]:
            tarjeta("Pérdida localizada", fmt(hred, "m"))

    with subtabs[2]:
        st.subheader("Ampliación")
        st.latex(r"K=1-\frac{D_1^4}{D_2^4}")

        c1, c2 = st.columns(2)
        with c1:
            D1 = st.number_input(
                "D1 (menor) [m]",
                min_value=0.000001,
                value=0.025,
                format="%.6f",
                key="amp_D1",
            )
        with c2:
            D2 = st.number_input(
                "D2 (mayor) [m]",
                min_value=0.000001,
                value=0.05,
                format="%.6f",
                key="amp_D2",
            )

        K_amp = 1 - (D1**4) / (D2**4)
        Qa = st.number_input(
            "Q [m³/s]",
            min_value=0.0,
            value=0.001,
            format="%.6f",
            key="amp_Q",
        )
        V1 = Qa / area_circular(D1)
        hamp = hf_local(K_amp, V1)

        c = st.columns(3)
        with c[0]:
            tarjeta("K", fmt(K_amp))
        with c[1]:
            tarjeta("V1", fmt(V1, "m/s"))
        with c[2]:
            tarjeta("Pérdida localizada", fmt(hamp, "m"))

    with subtabs[3]:
        st.subheader("Rejillas y filtros")
        st.latex(r"K=C_f\left(\frac{s}{b}\right)^{4/3}\sin\theta")

        Cf_tabla = {
            "Forma 1": 2.42,
            "Forma 2": 1.83,
            "Forma 3": 1.67,
            "Forma 4": 1.03,
            "Forma 5": 0.92,
            "Forma 6": 0.76,
            "Forma 7": 1.79,
            "Personalizado": None,
        }
        forma = st.selectbox("Forma del obstáculo", list(Cf_tabla.keys()), key="rej_forma")
        if Cf_tabla[forma] is None:
            Cf = st.number_input("C_f", min_value=0.0, value=1.0, format="%.4f", key="rej_Cf")
        else:
            Cf = Cf_tabla[forma]

        c1, c2, c3 = st.columns(3)
        with c1:
            s = st.number_input("s", min_value=0.000001, value=0.01, format="%.6f", key="rej_s")
        with c2:
            b = st.number_input("b", min_value=0.000001, value=0.02, format="%.6f", key="rej_b")
        with c3:
            theta = st.number_input(
                "θ [grados]",
                min_value=0.0,
                max_value=180.0,
                value=90.0,
                key="rej_theta",
            )

        K_rej = Cf * ((s / b) ** (4 / 3)) * math.sin(math.radians(theta))
        tarjeta("K de rejilla / filtro", fmt(K_rej))

# ============================================================
# MOODY
# ============================================================
with tabs[6]:
    st.header("Diagrama de Moody")

    c1, c2 = st.columns(2)
    with c1:
        Re_m = st.number_input(
            "Reynolds",
            min_value=500.0,
            value=30000.0,
            key="moody_Re",
        )
    with c2:
        eps_m = st.number_input(
            "Rugosidad relativa ε/D",
            min_value=0.0,
            value=7.167e-4,
            format="%.8f",
            key="moody_eps",
        )

    if Re_m < 2300:
        fm = 64.0 / Re_m
    else:
        fm = f_colebrook(Re_m, eps_m)

    re_lam = np.logspace(math.log10(500), math.log10(2300), 120)
    re_turb = np.logspace(math.log10(4000), 8, 320)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.loglog(re_lam, 64.0 / re_lam, label="Laminar")

    rugosidades = [0.0, 1e-6, 1e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2]
    for rr in rugosidades:
        vals = [f_colebrook(r, rr) for r in re_turb]
        etiqueta = "Tubo liso" if rr == 0 else f"ε/D={rr:g}"
        ax.loglog(re_turb, vals, linewidth=1, label=etiqueta)

    ax.axvspan(2300, 4000, alpha=0.12, label="Transición")
    ax.scatter([Re_m], [fm], s=70, zorder=5)
    ax.annotate(
        f"Tu punto\nRe={Re_m:.2e}\nf={fm:.4f}",
        (Re_m, fm),
        textcoords="offset points",
        xytext=(10, 10),
    )
    ax.set_xlabel("Número de Reynolds, Re")
    ax.set_ylabel("Factor de fricción de Darcy, f")
    ax.set_title("Diagrama de Moody")
    ax.grid(True, which="both", alpha=0.25)
    ax.set_xlim(5e2, 1e8)
    ax.set_ylim(0.008, 0.12)
    ax.legend(fontsize=8, ncol=2)

    st.pyplot(fig)
    plt.close(fig)

    tarjeta("Factor f en tu punto", fmt(fm))

# ============================================================
# DISEÑO DE DIÁMETRO
# ============================================================
with tabs[7]:
    st.header("Diseño del diámetro con Hazen–Williams")
    st.latex(
        r"D^{4.87}=\frac{10.64\,L\,Q^{1.85}}{h_f\,C^{1.85}}"
    )

    modo_d = st.radio(
        "¿Cómo quieres definir la pérdida disponible?",
        ["Por h_f máxima", "Por carga inicial y carga mínima"],
        horizontal=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        Ld = st.number_input(
            "Longitud L [m]",
            min_value=0.000001,
            value=100.0,
            key="des_L",
        )
    with c2:
        qd = st.number_input(
            "Caudal",
            min_value=0.0,
            value=7.0,
            format="%.6f",
            key="des_Q",
        )
    with c3:
        qud = st.selectbox(
            "Unidad Q",
            ["L/s", "m³/s", "L/min"],
            key="des_Qu",
        )

    Qd = caudal_a_m3s(qd, qud)
    Cdes = st.number_input(
        "Coeficiente C",
        min_value=1.0,
        value=140.0,
        key="des_C",
    )

    if modo_d == "Por h_f máxima":
        hf_disp = st.number_input(
            "h_f máxima disponible [m.c.a.]",
            min_value=0.000001,
            value=5.0,
            key="des_hf",
        )
    else:
        c1, c2 = st.columns(2)
        with c1:
            h_ini = st.number_input(
                "Carga inicial [m.c.a.]",
                value=30.0,
                key="des_hi",
            )
        with c2:
            h_min = st.number_input(
                "Carga mínima requerida [m.c.a.]",
                value=20.0,
                key="des_hm",
            )

        hf_disp = h_ini - h_min
        if hf_disp <= 0:
            st.error("La carga inicial debe ser mayor que la carga mínima requerida.")
            hf_disp = None

    if hf_disp is not None:
        Dreq = (
            10.64 * Ld * (Qd**1.85) / (hf_disp * (Cdes**1.85))
        ) ** (1 / 4.87)

        c = st.columns(3)
        with c[0]:
            tarjeta("Diámetro requerido", fmt(Dreq, "m"))
        with c[1]:
            tarjeta("Diámetro requerido", fmt(Dreq * 1000, "mm"))
        with c[2]:
            tarjeta("Diámetro requerido", fmt(Dreq / 0.0254, "in"))

        Vreq = Qd / area_circular(Dreq)
        tarjeta("Velocidad con ese diámetro", fmt(Vreq, "m/s"))

st.markdown(
    '<div class="jeni-footer">Calculadora personal de hidráulica en tuberías 💗💜</div>',
    unsafe_allow_html=True,
)
