import streamlit as st

# ===== EXTENSIONS BLACK STAR V1.4.4 =====
def montant_facture_depuis_marchandise(cargo):
    """Prix facturé à BLACK STAR = achat fournisseur + marge ATL."""
    qte = float(cargo["cartons"] or 0)
    achat = float(cargo["unit_purchase_price"] or 0) * qte
    marge = float(cargo["atl_margin_per_carton"] or 0) * qte
    return round(achat + marge, 2)

def paiement_net_fournisseur(achat_total, charges_locales):
    """Paiement net fournisseur ATL après déduction des charges locales du conteneur."""
    return round(float(achat_total or 0) - float(charges_locales or 0), 2)
# =========================================

import streamlit.components.v1 as components
import sqlite3
import hashlib
import secrets
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from io import BytesIO


def get_container_invoice_amount(conn, container_id):
    """Montant d'achat facturé pour le conteneur sélectionné."""
    if not container_id:
        return 0.0
    row = conn.execute(
        "SELECT amount_ht FROM invoices WHERE container_id=? ORDER BY id DESC LIMIT 1",
        (container_id,)
    ).fetchone()
    if row is None:
        return 0.0
    return round(float(row["amount_ht"] or 0), 2)


st.set_page_config(
    page_title="BLACK STAR DISTRIBUTION V1.4.4",
    page_icon="🍠",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB = Path(__file__).with_name("black_star.db")


APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "logo_black_star.png"

st.markdown("""
<style>
/* === BLACK STAR DISTRIBUTION - single responsive interface === */
.block-container {
    padding-top: 0.65rem !important;
    padding-bottom: 1rem !important;
    max-width: 1500px;
}
header[data-testid="stHeader"] {
    height: 42px !important;
    min-height: 42px !important;
    visibility: visible !important;
}
[data-testid="stSidebar"] {
    visibility: visible !important;
}
@media (min-width: 901px) {
    [data-testid="stSidebar"] { width: 255px !important; min-width: 255px !important; }
}
@media (max-width: 900px) {
    [data-testid="stSidebar"] { width: min(82vw, 300px) !important; min-width: 0 !important; }
}
[data-testid="stSidebar"] .block-container {
    padding-top: 0.8rem !important;
}
.bsd-logo-login {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 auto 0.35rem auto;
}
.bsd-logo-login img {
    width: min(145px, 42vw);
    max-height: 78px;
    object-fit: contain;
}
.bsd-login-title {
    text-align: center !important;
    font-size: clamp(1.25rem, 3vw, 1.75rem) !important;
    line-height: 1.15 !important;
    margin: 0.1rem 0 0.2rem 0 !important;
}
.bsd-login-subtitle {
    text-align: center !important;
    font-size: clamp(.78rem, 2vw, .98rem) !important;
    margin: 0 auto .9rem auto !important;
}
h1, h2, h3 {
    text-align: center;
}
.stButton > button, .stFormSubmitButton > button {
    min-height: 2.15rem !important;
    height: 2.15rem !important;
    padding: 0.25rem 0.8rem !important;
    border-radius: 7px !important;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button {
    background: #168447 !important;
    border-color: #168447 !important;
    color: white !important;
}
.bsd-logout button {
    background: #1769aa !important;
    border-color: #1769aa !important;
    color: white !important;
    width: 130px !important;
    min-width: 130px !important;
}
[data-testid="stSidebar"] .stRadio > div {
    gap: .35rem !important;
}
[data-testid="stSidebar"] label {
    margin-bottom: .12rem !important;
}
@media (max-width: 900px) {
    .block-container {
        padding-left: .8rem !important;
        padding-right: .8rem !important;
    }
    [data-testid="stSidebar"] {
        min-width: 230px;
        width: 230px;
    }
    .stDataFrame, [data-testid="stDataEditor"] {
        width: 100% !important;
    }
}
@media (max-width: 640px) {
    .block-container {
        padding-left: .55rem !important;
        padding-right: .55rem !important;
        padding-top: .35rem !important;
    }
    [data-testid="stSidebar"] {
        width: 245px !important;
    }
    .bsd-logo-login img {
        width: min(170px, 55vw);
        max-height: 90px;
    }
    .stButton > button, .stFormSubmitButton > button {
        width: auto !important;
        min-height: 2.05rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: .45rem !important;
    }
    .stMetric {
        padding: .45rem !important;
    }
}

/* RESTORED SIDEBAR — one navigation for every screen size */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    display: block !important;
}

    .sidebar-name {{text-align:center; font-weight:750; font-size:.88rem; margin:0 0 6px 0;}}
    [data-testid="stSidebar"] .sidebar-logo {{display:flex; justify-content:center; align-items:center; margin:0 auto 5px auto;}}
    [data-testid="stSidebar"] .sidebar-logo img {{display:block; margin:0 auto;}}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        padding-top:4px !important; padding-bottom:4px !important;
        margin-bottom:2px !important; font-size:.98rem !important; line-height:1.15 !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        min-height:31px !important; height:31px !important; padding:0 12px !important;
    }}
    .login-page {{width:100%; display:flex; flex-direction:column; align-items:center; text-align:center; padding-top:8px;}}
    .login-brand {{width:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; margin:0 auto 10px auto;}}
    .login-brand img {{display:block; width:min(120px,32vw); max-height:72px; object-fit:contain; margin:0 auto 5px auto;}}
    .login-brand h1 {{font-size:1.28rem !important; margin:0 !important; text-align:center !important;}}
    .login-brand p {{font-size:.80rem; line-height:1.25; max-width:340px; margin:3px auto 0 auto; color:#64748b; text-align:center;}}
    .login-form-wrap {{width:100%; max-width:300px; margin:0 auto;}}
    .login-form-wrap [data-testid="stTextInput"] {{max-width:300px; margin-left:auto; margin-right:auto;}}
    .login-form-wrap [data-testid="stForm"] {{max-width:300px; margin-left:auto; margin-right:auto;}}
    @media (max-width:900px) {{
        .login-brand img {{width:105px; max-height:64px;}}
        .login-brand h1 {{font-size:1.12rem !important;}}
        .login-brand p {{font-size:.76rem; max-width:310px;}}
        .login-form-wrap, .login-form-wrap [data-testid="stTextInput"], .login-form-wrap [data-testid="stForm"] {{max-width:285px;}}
    }}

/* Ajustements finaux V1.4.1.1 */
header[data-testid="stHeader"] {
    height: 42px !important;
    min-height: 42px !important;
}
.bsd-login-title {
    font-size: 1.10rem !important;
}
.login-brand img {
    width: min(88px, 25vw) !important;
    max-height: 58px !important;
}
.login-brand h1 {
    font-size: 1.08rem !important;
    line-height: 1.12 !important;
}
.login-brand p {
    font-size: .80rem !important;
    margin-top: .15rem !important;
}
.login-form-wrap,
.login-form-wrap [data-testid="stTextInput"],
.login-form-wrap [data-testid="stForm"] {
    max-width: 285px !important;
}
[data-testid="stSidebar"] .sidebar-logo img {
    width: 72px !important;
    max-height: 52px !important;
    object-fit: contain !important;
}
@media (max-width: 640px) {
    .login-brand img {
        width: 76px !important;
        max-height: 50px !important;
    }
    .login-brand h1 {
        font-size: 1rem !important;
    }
}

/* ================= V1.4.1.1 FINAL DISPLAY CORRECTIONS ================= */
.main .block-container {
    padding-top: 1.45rem !important;   /* interface légèrement abaissée */
}
[data-testid="stSidebar"] {
    position: relative !important;
}
[data-testid="stSidebar"] .sidebar-logo,
[data-testid="stSidebar"] [data-testid="stImage"] {
    display: flex !important;
    justify-content: center !important;
}
[data-testid="stSidebar"] [data-testid="stImage"] img {
    width: 72px !important;
    max-height: 56px !important;
    object-fit: contain !important;
    margin: 0 auto !important;
}
.login-page,
.login-brand {
    width: 100% !important;
    text-align: center !important;
    align-items: center !important;
    justify-content: center !important;
}
.login-brand img {
    display: block !important;
    width: 82px !important;
    max-height: 58px !important;
    object-fit: contain !important;
    margin: 0 auto 6px auto !important;
}
.login-brand h1 {
    font-size: 1.02rem !important;
    line-height: 1.15 !important;
    margin: 0 !important;
    text-align: center !important;
}
.login-brand p {
    font-size: .82rem !important;
    margin: .25rem auto 0 auto !important;
    text-align: center !important;
}
.login-form-wrap {
    max-width: 285px !important;
    margin: 0 auto !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #1769aa !important;
    color: #ffffff !important;
    border: none !important;
    min-height: 32px !important;
}
h1 {
    font-size: 1.28rem !important;
}
h2 {
    font-size: 1.08rem !important;
}
@media (max-width: 900px) {
    .main .block-container {
        padding-top: 1.05rem !important;
    }
    h1 {
        font-size: 1.15rem !important;
    }
}

/* ===== BLACK STAR DISTRIBUTION V1.4.4 ===== */

/* Logo connexion */
.login-brand img {
    width: 102px !important;
    max-height: 70px !important;
    object-fit: contain !important;
    display: block !important;
    margin: 0 auto 6px auto !important;
}

/* Logo panneau gauche : légèrement plus grand et remonté */
[data-testid="stSidebar"] .sidebar-logo,
[data-testid="stSidebar"] [data-testid="stImage"] {
    display:flex !important;
    justify-content:center !important;
    margin-top:-2px !important;
    margin-bottom:4px !important;
}
[data-testid="stSidebar"] [data-testid="stImage"] img {
    width:88px !important;
    max-height:64px !important;
    object-fit:contain !important;
    margin:0 auto !important;
}

/* Menus légèrement plus grands, tout en restant compacts */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size:1.02rem !important;
    line-height:1.18 !important;
    padding-top:4px !important;
    padding-bottom:4px !important;
    margin-bottom:1px !important;
}

/* Petit écran : le panneau peut défiler pour garder tous les éléments accessibles */
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top:.2rem !important;
    padding-bottom:.5rem !important;
    overflow-y:auto !important;
}

/* Ligne séparatrice et bouton Déconnexion juste sous Paramètres */
[data-testid="stSidebar"] hr {
    margin:.45rem 0 !important;
}
[data-testid="stSidebar"] .stButton > button {
    min-height:34px !important;
    font-size:.93rem !important;
}

/* Interface légèrement abaissée */
.main .block-container {
    padding-top:1.25rem !important;
}

/* Tableau de bord : cartes compactes en colonnes */
[data-testid="stHorizontalBlock"] {
    gap:.65rem !important;
}
[data-testid="stMetric"] {
    min-width:0 !important;
    padding:8px 10px !important;
}

/* Lisibilité renforcée pour le thème sombre */
.dark-theme,
.dark-theme .main,
.dark-theme .main h1,
.dark-theme .main h2,
.dark-theme .main h3,
.dark-theme .main p,
.dark-theme .main label,
.dark-theme .main span,
.dark-theme .main div {
    color:#f8fafc !important;
}
.dark-theme [data-testid="stMetric"] {
    background:#1f2937 !important;
    border-color:#475569 !important;
}
.dark-theme [data-testid="stMetric"] * {
    color:#f8fafc !important;
}
.dark-theme [data-testid="stDataFrame"],
.dark-theme [data-testid="stTable"] {
    color:#f8fafc !important;
}

@media (max-width:900px) {
    .main .block-container {
        padding-top:.95rem !important;
        padding-left:.7rem !important;
        padding-right:.7rem !important;
    }
    .login-brand img {
        width:92px !important;
        max-height:64px !important;
    }
    [data-testid="stSidebar"] [data-testid="stImage"] img {
        width:82px !important;
        max-height:60px !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        font-size:.98rem !important;
    }
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:.2rem!important;padding-bottom:.4rem!important;overflow-y:auto!important;}[data-testid="stSidebar"] .stButton>button{min-height:32px!important;margin:.1rem 0!important;}[data-testid="stSidebar"] hr{margin:.3rem 0!important;}

/* V1.4.1.1 */
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label,
.stTextInput label,.stNumberInput label,.stSelectbox label,.stDateInput label,.stTextArea label{
font-weight:700!important;font-size:1.03rem!important;}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:.05rem!important;padding-bottom:.25rem!important;}
[data-testid="stSidebar"] img{display:block!important;margin-left:auto!important;margin-right:auto!important;}
[data-testid="stSidebar"] hr{margin:.30rem 0!important;}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Database
# -----------------------------
def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def q(sql, params=(), fetch=False, many=False):
    c = conn()
    cur = c.cursor()
    if many:
        cur.executemany(sql, params)
    else:
        cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    c.commit()
    c.close()
    return rows

def init_db():
    q("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )""")
    q("""CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")
    q("""CREATE TABLE IF NOT EXISTS app_settings(
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""")
    q("""CREATE TABLE IF NOT EXISTS containers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        container_type TEXT NOT NULL,
        container_no TEXT NOT NULL,
        seal_no TEXT,
        origin TEXT NOT NULL DEFAULT 'Ghana',
        departure_port TEXT NOT NULL DEFAULT 'Tema',
        arrival_port TEXT NOT NULL DEFAULT 'Anvers',
        final_destination TEXT NOT NULL DEFAULT 'France',
        departure_date TEXT,
        arrival_date TEXT,
        customs_date TEXT,
        delivery_date TEXT,
        status TEXT NOT NULL DEFAULT 'En cours de chargement',
        notes TEXT,
        created_at TEXT NOT NULL
    )""")
    try:
        cols=[r["name"] for r in q("PRAGMA table_info(containers)",fetch=True)]
        if "status" not in cols: q("ALTER TABLE containers ADD COLUMN status TEXT NOT NULL DEFAULT 'En cours de chargement'")
        if "local_charges" not in cols: q("ALTER TABLE containers ADD COLUMN local_charges REAL NOT NULL DEFAULT 0")
    except Exception: pass
    q("""CREATE TABLE IF NOT EXISTS cargo(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        variety TEXT NOT NULL,
        cartons REAL NOT NULL,
        kg_per_carton REAL NOT NULL DEFAULT 0,
        unit_purchase_price REAL NOT NULL DEFAULT 0,
        purchase_currency TEXT NOT NULL DEFAULT 'EUR',
        atl_margin_per_carton REAL NOT NULL DEFAULT 0,
        FOREIGN KEY(container_id) REFERENCES containers(id) ON DELETE CASCADE
    )""")
    # V1.4.2 migrations
    try:
        cargo_cols={r["name"] for r in q("PRAGMA table_info(cargo)",fetch=True)}
        if "supplier" not in cargo_cols: q("ALTER TABLE cargo ADD COLUMN supplier TEXT")
        if "local_charges" not in cargo_cols: q("ALTER TABLE cargo ADD COLUMN local_charges REAL NOT NULL DEFAULT 0")
    except Exception: pass
    q("""CREATE TABLE IF NOT EXISTS atl_supplier_invoices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        supplier TEXT NOT NULL,
        invoice_date TEXT,
        product TEXT NOT NULL,
        quantity REAL NOT NULL DEFAULT 0,
        unit_price REAL NOT NULL DEFAULT 0,
        weight REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0,
        currency TEXT NOT NULL DEFAULT 'EUR',
        notes TEXT,
        FOREIGN KEY(container_id) REFERENCES containers(id) ON DELETE CASCADE
    )""")
    q("""CREATE TABLE IF NOT EXISTS atl_supplier_payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_invoice_id INTEGER NOT NULL,
        payment_date TEXT,
        amount REAL NOT NULL DEFAULT 0,
        method TEXT,
        reference TEXT,
        notes TEXT,
        FOREIGN KEY(supplier_invoice_id) REFERENCES atl_supplier_invoices(id) ON DELETE CASCADE
    )""")

    q("""CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'EUR',
        expense_date TEXT,
        payer TEXT NOT NULL DEFAULT 'BLACK STAR DISTRIBUTION',
        status TEXT NOT NULL DEFAULT 'À payer',
        reference TEXT,
        FOREIGN KEY(container_id) REFERENCES containers(id) ON DELETE CASCADE
    )""")
    q("""CREATE TABLE IF NOT EXISTS invoices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        invoice_no TEXT NOT NULL,
        issuer TEXT NOT NULL,
        recipient TEXT NOT NULL,
        invoice_date TEXT,
        due_date TEXT,
        amount_ht REAL NOT NULL DEFAULT 0,
        tax REAL NOT NULL DEFAULT 0,
        currency TEXT NOT NULL DEFAULT 'EUR',
        notes TEXT,
        FOREIGN KEY(container_id) REFERENCES containers(id) ON DELETE CASCADE
    )""")
    q("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'EUR',
        payment_type TEXT NOT NULL DEFAULT 'Paiement',
        method TEXT,
        reference TEXT,
        notes TEXT,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    )""")
    q("""CREATE TABLE IF NOT EXISTS credits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        container_id INTEGER NOT NULL,
        credit_no TEXT NOT NULL,
        credit_date TEXT NOT NULL,
        reason TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'EUR',
        notes TEXT,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY(container_id) REFERENCES containers(id) ON DELETE CASCADE
    )""")
    q("""CREATE TABLE IF NOT EXISTS damages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        variety TEXT,
        damage_date TEXT NOT NULL,
        cartons REAL NOT NULL DEFAULT 0,
        kg REAL NOT NULL DEFAULT 0,
        description TEXT NOT NULL,
        estimated_loss REAL NOT NULL DEFAULT 0,
        credit_amount REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Constatée',
        notes TEXT,
        FOREIGN KEY(container_id) REFERENCES containers(id) ON DELETE CASCADE
    )""")
    q("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        event_date TEXT NOT NULL,
        event_type TEXT NOT NULL,
        description TEXT,
        amount REAL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(container_id) REFERENCES containers(id) ON DELETE CASCADE
    )""")
    if not q("SELECT id FROM users LIMIT 1", fetch=True):
        salt = secrets.token_hex(16)
        pwd = hashlib.sha256((salt + "admin123").encode()).hexdigest()
        q("INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
          ("admin", salt + ":" + pwd, "admin", datetime.now().isoformat(timespec="seconds")))

def hash_password(password, stored=None):
    if stored:
        salt = stored.split(":", 1)[0]
    else:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt + ":" + digest

def verify_password(password, stored):
    return hash_password(password, stored) == stored

init_db()

THEMES = {
    "emeraude": {"label":"Émeraude","primary":"#198754","sidebar":"#0f3d2e","surface":"#f6fbf8","accent":"#198754","button":"#198754","button_hover":"#157347"},
    "bleu_marine": {"label":"Bleu marine","primary":"#1d4ed8","sidebar":"#0b1f3a","surface":"#f5f8ff","accent":"#2563eb","button":"#2563eb","button_hover":"#1d4ed8"},
    "ardoise": {"label":"Ardoise professionnelle","primary":"#334155","sidebar":"#1f2937","surface":"#f8fafc","accent":"#475569","button":"#475569","button_hover":"#334155"},
    "violet": {"label":"Violet élégant","primary":"#6d4aff","sidebar":"#2f2459","surface":"#faf9ff","accent":"#6d4aff","button":"#6d4aff","button_hover":"#5938dc"},
    "terracotta": {"label":"Terracotta classique","primary":"#b4533c","sidebar":"#4a2720","surface":"#fffaf8","accent":"#b4533c","button":"#b4533c","button_hover":"#963f2d"},
}

def get_setting(key, default=None):
    rows=q("SELECT value FROM app_settings WHERE key=?",(key,),fetch=True)
    return rows[0]["value"] if rows else default

def set_setting(key, value):
    q("INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,value))

def active_theme():
    key=get_setting("theme","emeraude")
    return key if key in THEMES else "emeraude"

# -----------------------------
# Helpers
# -----------------------------
def euro(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")

def today():
    return date.today().isoformat()

def display_date(v):
    if not v:
        return ""
    try:
        return datetime.fromisoformat(v).strftime("%d-%m-%Y")
    except Exception:
        return v

def options_from_table(table, col):
    rows = q(f"SELECT DISTINCT {col} AS v FROM {table} WHERE {col} IS NOT NULL AND {col}<>'' ORDER BY {col}", fetch=True)
    return [r["v"] for r in rows]

def log_event(container_id, event_date, event_type, description="", amount=None):
    q("""INSERT INTO events(container_id,event_date,event_type,description,amount,created_at)
         VALUES(?,?,?,?,?,?)""",
      (container_id, event_date, event_type, description, amount, datetime.now().isoformat(timespec="seconds")))

def container_df():
    rows = q("SELECT * FROM containers ORDER BY id DESC", fetch=True)
    return pd.DataFrame([dict(r) for r in rows])

def invoice_status(invoice_id):
    inv = q("SELECT * FROM invoices WHERE id=?", (invoice_id,), fetch=True)[0]
    paid = q("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE invoice_id=?", (invoice_id,), fetch=True)[0]["s"]
    credits = q("SELECT COALESCE(SUM(amount),0) s FROM credits WHERE invoice_id=?", (invoice_id,), fetch=True)[0]["s"]
    net = inv["amount_ht"] + inv["tax"] - credits
    if net <= 0:
        status = "Avoir total"
    elif paid >= net - 0.005:
        status = "Soldée"
    elif paid > 0:
        status = "Paiement partiel"
    elif credits > 0:
        status = "Avoir en attente"
    else:
        status = "En instance de paiement"
    return net, paid, credits, status

def container_financials(cid):
    cargo=q("""SELECT COALESCE(SUM(cartons*unit_purchase_price),0) purchase,
                     COALESCE(SUM(cartons*atl_margin_per_carton),0) atl_margin,
                     COALESCE(SUM(cartons),0) cartons
              FROM cargo WHERE container_id=?""",(cid,),fetch=True)[0]
    exp=q("""SELECT
        COALESCE(SUM(CASE WHEN category='Ghana' OR payer='A.T.L AFRO LIMITED COMPANY' THEN amount ELSE 0 END),0) atl_charges,
        COALESCE(SUM(CASE WHEN category='Ghana' THEN amount ELSE 0 END),0) ghana,
        COALESCE(SUM(CASE WHEN category='Fret maritime' THEN amount ELSE 0 END),0) freight,
        COALESCE(SUM(CASE WHEN category='Anvers / Belgique' THEN amount ELSE 0 END),0) belgium,
        COALESCE(SUM(CASE WHEN category='France' THEN amount ELSE 0 END),0) france,
        COALESCE(SUM(CASE WHEN category='Autre' THEN amount ELSE 0 END),0) other,
        COALESCE(SUM(CASE WHEN NOT(category='Ghana' OR payer='A.T.L AFRO LIMITED COMPANY') THEN amount ELSE 0 END),0) bsd_expenses
        FROM expenses WHERE container_id=?""",(cid,),fetch=True)[0]
    cr=q("SELECT COALESCE(SUM(amount),0) s FROM credits WHERE container_id=?",(cid,),fetch=True)[0]['s']
    cartons=float(cargo['cartons'] or 0); purchase=float(cargo['purchase'] or 0)
    # BLACK STAR purchase price is the invoice value: supplier purchase + ATL margin.
    invoice_value=purchase+float(cargo['atl_margin'] or 0)
    bsd_total=invoice_value+float(exp['bsd_expenses'] or 0)-float(cr or 0)
    # ATL margin is a profit, never an ATL expense.
    atl_charges=float(exp['atl_charges'] or 0)
    container_charge=float(q("SELECT COALESCE(local_charges,0) v FROM containers WHERE id=?",(cid,),fetch=True)[0]['v'] or 0)
    atl_total=purchase-container_charge+atl_charges
    return {**dict(cargo),**dict(exp),'credits':float(cr or 0),'local_charges':container_charge,'invoice_value':invoice_value,
            'cost_total':bsd_total,'per_carton':bsd_total/cartons if cartons else 0,
            'atl_total':atl_total,'atl_per_carton':atl_total/cartons if cartons else 0}

LOGO = Path(__file__).parent / "logo_black_star.png"


def pdf_report(dataframe, title="Rapport BLACK STAR DISTRIBUTION", subtitle="Gestion des importations d'ignames"):
    """Génère un PDF simple et professionnel à partir d'un DataFrame."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleBS", parent=styles["Title"], alignment=TA_CENTER, fontSize=17, spaceAfter=8)
    sub_style = ParagraphStyle("SubBS", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9, textColor=colors.HexColor("#64748b"), spaceAfter=14)
    body=[]
    if LOGO.exists():
        img=Image(str(LOGO), width=105, height=48)
        img.hAlign='CENTER'
        body += [img, Spacer(1,8)]
    body += [Paragraph(title, title_style), Paragraph(subtitle, sub_style)]
    df=dataframe.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col]=df[col].map(lambda x: f"{x:,.2f}".replace(","," ") if pd.notna(x) else "")
        else:
            df[col]=df[col].fillna("").astype(str)
    data=[list(df.columns)] + df.astype(str).values.tolist()
    # Keep wide reports readable by limiting font size and repeating header.
    tbl=Table(data, repeatRows=1, hAlign='CENTER')
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#111827')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),6.5),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#d1d5db')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f8fafc')]),
        ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))
    body.append(tbl)
    body += [Spacer(1,12), Paragraph(f"Document généré le {datetime.now().strftime('%d-%m-%Y à %H:%M')}", styles['Normal'])]
    doc.build(body)
    return buffer.getvalue()

def selected_container():
    rows = q("SELECT id, code, container_no FROM containers ORDER BY id DESC", fetch=True)
    if not rows:
        return None
    labels = {f'{r["container_no"]}': r["id"] for r in rows}
    label = st.selectbox("Conteneur", list(labels.keys()))
    return labels[label]

# -----------------------------
# Professional UI / session persistence
# -----------------------------
theme = THEMES[active_theme()]
st.markdown(f"""
<style>
/* Thème actif */
[data-testid="stAppViewContainer"] {{
    background: {theme['surface']} !important;
}}
[data-testid="stHeader"] {{
    background: {theme['surface']} !important;
}}
.main .block-container {{
    max-width: 1500px;
    padding-top: 1.05rem !important;
    padding-bottom: 1rem !important;
    padding-left: 2vw;
    padding-right: 2vw;
}}
h1 {{
    text-align: center !important;
    font-size: 1.28rem !important;
    margin: .10rem 0 .35rem !important;
}}
h2 {{
    text-align: center !important;
    font-size: 1.08rem !important;
    margin: .15rem 0 .30rem !important;
}}
h3 {{
    text-align: center !important;
    font-size: .98rem !important;
}}
.app-subtitle {{
    text-align: center;
    color: {theme['primary']} !important;
    margin: 0 0 .65rem 0;
    font-size: .82rem;
}}
[data-testid="stSidebar"] {{
    background: {theme['sidebar']} !important;
}}
[data-testid="stSidebar"] * {{
    color: white !important;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] label {{
    padding: 4px 0 !important;
    margin-bottom: 2px !important;
    border-radius: 8px;
    font-size: .95rem !important;
    line-height: 1.15 !important;
}}
[data-testid="stSidebar"] .sidebar-logo {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 auto 4px auto;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: #1769aa !important;
    border-color: #1769aa !important;
    color: white !important;
    font-weight: 650 !important;
}}
.stButton > button,
.stFormSubmitButton > button {{
    border-radius: 7px;
    min-height: 30px;
    height: 30px;
    padding: 0 11px;
    background: {theme['button']} !important;
    color: white !important;
    border: 1px solid {theme['button']} !important;
    font-weight: 600;
    font-size: .88rem;
}}
.stButton > button:hover,
.stFormSubmitButton > button:hover {{
    background: {theme['button_hover']} !important;
    border-color: {theme['button_hover']} !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
textarea {{
    border-color: {theme['accent']} !important;
}}
[data-testid="stSelectbox"] [role="combobox"] {{
    border-color: {theme['accent']} !important;
}}
[data-testid="stMetric"] {{
    border: 1px solid rgba(100,116,139,.18);
    border-radius: 12px;
    padding: 8px;
    background: white;
    box-shadow: 0 3px 12px rgba(15,23,42,.04);
}}
@media (max-width:900px) {{
    .main .block-container {{
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding-left: .75rem !important;
        padding-right: .75rem !important;
        padding-top: .75rem !important;
    }}
    h1 {{
        font-size: 1.14rem !important;
    }}
    h2 {{
        font-size: 1rem !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

def create_session(user_id):
    """Crée un jeton de session persistant."""
    token = secrets.token_urlsafe(32)
    q("INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)", (token, user_id, datetime.now().isoformat(timespec="seconds")))
    st.session_state.auth_token = token
    try:
        st.query_params["auth_token"] = token
    except Exception:
        pass
    return token


def restore_session():
    """Restaure une session valide après actualisation de l'application."""
    if st.session_state.get("auth", False) and st.session_state.get("user"):
        return True

    token = st.session_state.get("auth_token")
    if not token:
        try:
            token = st.query_params.get("auth_token")
        except Exception:
            token = None

    if isinstance(token, (list, tuple)):
        token = token[0] if token else None
    if not token:
        return False

    rows = q("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND u.active=1 LIMIT 1", (str(token),), fetch=True)
    if rows:
        st.session_state.auth = True
        st.session_state.user = dict(rows[0])
        st.session_state.auth_token = str(token)
        return True

    st.session_state.auth = False
    st.session_state.user = None
    st.session_state.auth_token = None
    try:
        del st.query_params["auth_token"]
    except Exception:
        pass
    return False


def clear_session():
    """Déconnecte proprement l'utilisateur."""
    token = st.session_state.get("auth_token")
    if not token:
        try:
            token = st.query_params.get("auth_token")
        except Exception:
            token = None
    if token:
        try:
            q("DELETE FROM sessions WHERE token=?", (str(token),))
        except Exception:
            pass
    st.session_state.auth = False
    st.session_state.user = None
    st.session_state.auth_token = None
    try:
        del st.query_params["auth_token"]
    except Exception:
        pass


def notify(message, kind="success"):
    try:
        st.toast(message, icon="✅" if kind=="success" else "⚠️")
    except Exception:
        pass
    if kind == "success": st.success(message)
    else: st.warning(message)

def desktop_right_click(table, row_id, label):
    """Installe un vrai menu contextuel global : clic droit n'importe où sur la page.
    Le menu agit sur l'enregistrement actuellement sélectionné dans le bloc de gestion.
    """
    import json
    payload=json.dumps({"table":str(table),"id":str(row_id),"label":str(label)})
    html=f"""
    <script>
    (()=>{{
      const target={payload};
      const doc=window.parent.document;
      let menu=doc.getElementById('bsd-global-context-menu');
      if(!menu){{
        menu=doc.createElement('div'); menu.id='bsd-global-context-menu';
        menu.innerHTML=`<div data-act="edit">✏️ Modifier</div><div data-act="delete">🗑️ Supprimer</div>`;
        Object.assign(menu.style,{{position:'fixed',display:'none',zIndex:'2147483647',minWidth:'190px',background:'#fff',border:'1px solid #cbd5e1',borderRadius:'9px',boxShadow:'0 12px 30px rgba(0,0,0,.20)',padding:'5px',fontFamily:'Arial,sans-serif'}});
        menu.querySelectorAll('div').forEach(x=>{{Object.assign(x.style,{{padding:'10px 12px',cursor:'pointer',fontSize:'14px'}}); x.addEventListener('mouseenter',()=>x.style.background='#f1f5f9'); x.addEventListener('mouseleave',()=>x.style.background='transparent');}});
        doc.body.appendChild(menu);
        doc.addEventListener('click',()=>menu.style.display='none');
        doc.addEventListener('contextmenu',e=>{{
          e.preventDefault();
          menu.dataset.x=String(e.clientX); menu.dataset.y=String(e.clientY);
          menu.style.left=Math.min(e.clientX,Math.max(0,doc.documentElement.clientWidth-210))+'px';
          menu.style.top=Math.min(e.clientY,Math.max(0,doc.documentElement.clientHeight-100))+'px';
          menu.style.display='block';
        }});
        menu.addEventListener('click',e=>{{
          const act=e.target.closest('[data-act]')?.dataset.act; if(!act) return;
          const u=new URL(window.parent.location.href);
          u.searchParams.set('ctx_table',menu.dataset.table||'');
          u.searchParams.set('ctx_id',menu.dataset.id||'');
          u.searchParams.set('ctx_action',act);
          window.parent.location.href=u.toString();
        }});
      }}
      menu.dataset.table=target.table; menu.dataset.id=target.id; menu.dataset.label=target.label;
    }})();
    </script>
    """
    components.html(html,height=1,scrolling=False)


def consume_context_action(table,row_id):
    t=st.query_params.get("ctx_table"); rid=st.query_params.get("ctx_id"); action=st.query_params.get("ctx_action")
    if t==table and str(rid)==str(row_id) and action in ("edit","delete"):
        for k in ["ctx_table","ctx_id","ctx_action"]:
            if k in st.query_params: del st.query_params[k]
        return action
    return None

def context_menu(table, row_id, label, delete_sql=None):
    """Petit menu ⋮ réutilisable pour modifier/supprimer une ligne."""
    edit_key=f"editing_{table}_{row_id}"
    desktop_right_click(table,row_id,label)
    action=consume_context_action(table,row_id)
    if action=="edit":
        st.session_state[edit_key]=True
        st.rerun()
    if action=="delete":
        if delete_sql:
            for sql, params in delete_sql: q(sql, params)
        else: q(f"DELETE FROM {table} WHERE id=?", (row_id,))
        notify(f"{label} supprimé(e).")
        st.rerun()
    with st.popover("⋮", use_container_width=False):
        edit=st.button("✏️ Modifier", key=f"ctx_edit_{table}_{row_id}", use_container_width=True)
        delete=st.button("🗑️ Supprimer", key=f"ctx_del_{table}_{row_id}", use_container_width=True)
    if edit:
        st.session_state[edit_key]=True
        st.rerun()
    if delete:
        if delete_sql:
            for sql, params in delete_sql:
                q(sql, params)
        else:
            q(f"DELETE FROM {table} WHERE id=?", (row_id,))
        notify(f"{label} supprimé(e).")
        st.rerun()
    return st.session_state.get(edit_key, False), edit_key


# Marqueur de lisibilité du thème actif
try:
    active_theme_name = str(st.session_state.get("theme", st.session_state.get("app_theme", ""))).lower()
    if "sombre" in active_theme_name or "dark" in active_theme_name:
        st.markdown("<div class='dark-theme'></div>", unsafe_allow_html=True)
except Exception:
    pass

# -----------------------------
# Login
# -----------------------------
if "auth" not in st.session_state:
    st.session_state.auth = False
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if not st.session_state.auth:
    restore_session()

if not st.session_state.auth:
    # Connexion compacte et centrée sur Desktop, tablette et téléphone.
    st.markdown("<div class='login-page'>", unsafe_allow_html=True)
    if LOGO.exists():
        import base64
        logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()
        st.markdown(
            f"<div class='login-brand'>"
            f"<img src='data:image/png;base64,{logo_b64}' alt='BLACK STAR DISTRIBUTION'>"
            f"<h1>BLACK STAR DISTRIBUTION</h1>"
            f"<p>Gestion des importations</p>"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown("<div class='login-brand'><h1>BLACK STAR DISTRIBUTION</h1><p>Gestion des importations</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='login-form-wrap'>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Identifiant", key="login_username")
        p = st.text_input("Mot de passe", type="password", key="login_password")
        ok = st.form_submit_button("Se connecter")
        if ok:
            row = q("SELECT * FROM users WHERE username=? AND active=1", (u,), fetch=True)
            if row and verify_password(p, row[0]["password_hash"]):
                st.session_state.auth = True
                st.session_state.user = dict(row[0])
                create_session(row[0]["id"])
                notify("Connexion réussie.")
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
if LOGO.exists():
    st.sidebar.markdown("<div class='sidebar-logo'>", unsafe_allow_html=True)
    st.sidebar.image(str(LOGO), width=72)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<div class='sidebar-name'>BLACK STAR DISTRIBUTION</div>", unsafe_allow_html=True)
st.sidebar.caption(f"Connecté : {st.session_state.user['username']}")
MENU_ITEMS = [
    "Tableau de bord", "Conteneurs", "Marchandises", "Charges",
    "Factures", "Paiements", "Avoirs", "Avaries", "Chronologie",
    "Rapports", "Simulation", "Paramètres"
]
if "nav_request" in st.session_state:
    requested = st.session_state.pop("nav_request")
    if requested in MENU_ITEMS:
        st.session_state.page_nav = requested

page = st.sidebar.radio("Menu", MENU_ITEMS, key="page_nav")
st.sidebar.divider()
st.sidebar.markdown("<div class='bsd-logout'>", unsafe_allow_html=True)
if st.sidebar.button("Déconnexion", key="logout_btn", use_container_width=True):
    clear_session()
    st.rerun()
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Navigation unique : sur mobile, Streamlit affiche automatiquement la sidebar comme tiroir.
# Aucune seconde navigation n'est créée dans le contenu principal.

if page == "Tableau de bord":
    st.title("Tableau de bord")
    st.markdown("<div class='app-subtitle'>Suivi et gestion des importations</div>", unsafe_allow_html=True)
else:
    st.title(page)

# -----------------------------
# Dashboard
# -----------------------------
if page == "Tableau de bord":
    cdf = container_df()
    total_cont = len(cdf)
    in_transit = len(cdf[(cdf["departure_date"].notna()) & (cdf["arrival_date"].isna())]) if not cdf.empty else 0
    rows = q("SELECT COALESCE(SUM(cartons),0) c FROM cargo", fetch=True)
    cartons = rows[0]["c"]
    rows = q("SELECT COALESCE(SUM(amount),0) a FROM expenses", fetch=True)
    expenses_total = rows[0]["a"]
    rows = q("SELECT COALESCE(SUM(amount),0) a FROM credits", fetch=True)
    credits_total = rows[0]["a"]
    cols = st.columns(5)
    cols[0].metric("Conteneurs", total_cont)
    cols[1].metric("En transit", in_transit)
    cols[2].metric("Cartons", f"{cartons:,.0f}")
    cols[3].metric("Charges", euro(expenses_total))
    cols[4].metric("Avoirs", euro(credits_total))
    if not cdf.empty:
        cdf["Départ"] = cdf["departure_date"].apply(display_date)
        cdf["Arrivée Anvers"] = cdf["arrival_date"].apply(display_date)
        st.subheader("Derniers conteneurs")
        st.dataframe(cdf[["code","container_no","seal_no","Départ","Arrivée Anvers","final_destination"]], use_container_width=True, hide_index=True)
    invs = q("SELECT id, invoice_no, amount_ht, tax FROM invoices ORDER BY id DESC", fetch=True)
    if invs:
        data=[]
        for r in invs:
            net, paid, credit, status = invoice_status(r["id"])
            data.append({"Facture":r["invoice_no"],"Montant":net,"Payé":paid,"Solde":max(net-paid,0),"Statut":status})
        st.subheader("Situation des factures")
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

# -----------------------------
# Containers
# -----------------------------
elif page == "Conteneurs":
    tab1, tab2 = st.tabs(["Liste", "Nouveau conteneur"])
    with tab1:
        df = container_df()
        search = st.text_input("Recherche instantanée", placeholder="Numéro conteneur, scellé, code...")
        if not df.empty and search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            df = df[mask]
        if not df.empty:
            df["Départ"] = df["departure_date"].apply(display_date)
            df["Arrivée"] = df["arrival_date"].apply(display_date)
            df["Statut"] = df["status"] if "status" in df.columns else "En cours de chargement"
            st.dataframe(df[["code","container_type","container_no","seal_no","departure_port","arrival_port","Départ","Arrivée","Statut","final_destination"]], use_container_width=True, hide_index=True)
            st.caption("Sélectionnez un conteneur pour afficher ou modifier ses données.")
            cid = selected_container()
            if cid:
                r = q("SELECT * FROM containers WHERE id=?", (cid,), fetch=True)[0]
                with st.expander("Modifier le conteneur", expanded=False):
                    with st.form("edit_container"):
                        a,b,c = st.columns(3)
                        code = a.text_input("Code", r["code"])
                        ctype = b.selectbox("Type", ["20 pieds","40 pieds","40 pieds HC","Autre"], index=["20 pieds","40 pieds","40 pieds HC","Autre"].index(r["container_type"]) if r["container_type"] in ["20 pieds","40 pieds","40 pieds HC","Autre"] else 1)
                        cno = c.text_input("Numéro du conteneur", r["container_no"])
                        d,e,f = st.columns(3)
                        seal = d.text_input("Numéro de scellé", r["seal_no"] or "")
                        origin = e.text_input("Origine", r["origin"])
                        dep_port = f.text_input("Port de départ", r["departure_port"])
                        g,h,i = st.columns(3)
                        arr_port = g.text_input("Port d'arrivée", r["arrival_port"])
                        dest = h.text_input("Destination finale", r["final_destination"])
                        dep = i.date_input("Date départ", datetime.fromisoformat(r["departure_date"]).date() if r["departure_date"] else date.today())
                        j,k,l = st.columns(3)
                        arr = j.date_input("Date arrivée Anvers", datetime.fromisoformat(r["arrival_date"]).date() if r["arrival_date"] else date.today())
                        customs = k.date_input("Date dédouanement", datetime.fromisoformat(r["customs_date"]).date() if r["customs_date"] else date.today())
                        delivery = l.date_input("Date livraison France", datetime.fromisoformat(r["delivery_date"]).date() if r["delivery_date"] else date.today())
                        statuses=["En cours de chargement","En transit","Arrivé au port...","Livré à l’entrepôt du client"]
                        current=r["status"] if "status" in r.keys() and r["status"] in statuses else statuses[0]
                        container_status=st.selectbox("Statut du conteneur",statuses,index=statuses.index(current))
                        local_charge2 = st.number_input("Charges locales du conteneur", min_value=0.0, value=float(r["local_charges"] or 0), step=0.01)
                        notes = st.text_area("Notes", r["notes"] or "")
                        save = st.form_submit_button("Enregistrer")
                        if save:
                            q("""UPDATE containers SET code=?,container_type=?,container_no=?,seal_no=?,origin=?,departure_port=?,arrival_port=?,final_destination=?,departure_date=?,arrival_date=?,customs_date=?,delivery_date=?,status=?,local_charges=?,notes=? WHERE id=?""",
                              (code,ctype,cno,seal,origin,dep_port,arr_port,dest,dep.isoformat(),arr.isoformat(),customs.isoformat(),delivery.isoformat(),container_status,local_charge2,notes,cid))
                            notify("Conteneur mis à jour avec succès.")
                            st.rerun()
                    if st.button("Supprimer ce conteneur", type="secondary"):
                        q("DELETE FROM containers WHERE id=?", (cid,))
                        notify("Conteneur supprimé.")
                        st.rerun()
        else:
            st.info("Aucun conteneur enregistré.")
    with tab2:
        with st.form("new_container"):
            a,b,c = st.columns(3)
            code = a.text_input("Code interne", f"CNT-{date.today().strftime('%Y%m%d')}-")
            ctype = b.selectbox("Type de conteneur", ["40 pieds HC","40 pieds","20 pieds","Autre"])
            cno = c.text_input("Numéro du conteneur")
            d,e,f = st.columns(3)
            seal = d.text_input("Numéro de scellé")
            origin = e.text_input("Origine", "Ghana")
            dep_port = f.text_input("Port de départ", "Tema")
            g,h,i = st.columns(3)
            arr_port = g.text_input("Port d'arrivée", "Anvers")
            dest = h.text_input("Destination finale", "France")
            dep = i.date_input("Date de départ Ghana", date.today())
            j,k,l = st.columns(3)
            arr = j.date_input("Date d'arrivée Anvers", date.today())
            customs = k.date_input("Date de dédouanement", date.today())
            delivery = l.date_input("Date de livraison France", date.today())
            container_status=st.selectbox("Statut du conteneur",["En cours de chargement","En transit","Arrivé au port...","Livré à l’entrepôt du client"])
            local_charge = st.number_input("Charges locales du conteneur", min_value=0.0, value=0.0, step=0.01, help="Charge globale du conteneur, déduite du paiement net fournisseur ATL.")
            notes = st.text_area("Notes")
            save = st.form_submit_button("Créer le conteneur", use_container_width=True)
            if save:
                if not code.strip() or not cno.strip():
                    st.error("Le code et le numéro du conteneur sont obligatoires.")
                else:
                    try:
                        q("""INSERT INTO containers(code,container_type,container_no,seal_no,origin,departure_port,arrival_port,final_destination,departure_date,arrival_date,customs_date,delivery_date,status,local_charges,notes,created_at)
                             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (code.strip(),ctype,cno.strip(),seal,origin,dep_port,arr_port,dest,dep.isoformat(),arr.isoformat(),customs.isoformat(),delivery.isoformat(),container_status,local_charge,notes,datetime.now().isoformat(timespec="seconds")))
                        notify("Conteneur créé avec succès.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ce code de conteneur existe déjà.")

# -----------------------------
# Cargo
# -----------------------------
elif page == "Marchandises":
    cid = selected_container()
    if cid:
        st.subheader("Marchandises")
        current_charge=float(q("SELECT COALESCE(local_charges,0) v FROM containers WHERE id=?",(cid,),fetch=True)[0]["v"] or 0)
        with st.form("container_local_charge"):
            charge=st.number_input("Charges locales du conteneur", min_value=0.0, value=current_charge, step=0.01, help="Cette charge s'applique à l'ensemble du conteneur et non à un produit individuel.")
            if st.form_submit_button("Enregistrer les charges locales"):
                q("UPDATE containers SET local_charges=? WHERE id=?",(charge,cid))
                notify("Charges locales du conteneur mises à jour."); st.rerun()
        with st.form("cargo"):
            a,b,c,d = st.columns(4)
            supplier=a.text_input("Fournisseur")
            variety=b.selectbox("Variété", ["Pona","White Yam"])
            cartons=c.number_input("Cartons", min_value=0.0, step=1.0)
            kg=d.number_input("Kg/carton", min_value=0.0, step=0.5)
            e,f,g = st.columns(3)
            price=e.number_input("Prix achat/carton", min_value=0.0, step=0.01)
            margin=f.number_input("Marge ATL/carton", min_value=0.0, step=0.01)
            cur=g.selectbox("Devise", ["EUR","GHS","USD"])
            if st.form_submit_button("Ajouter"):
                q("""INSERT INTO cargo(container_id,variety,cartons,kg_per_carton,unit_purchase_price,purchase_currency,atl_margin_per_carton,supplier)
                     VALUES(?,?,?,?,?,?,?,?)""", (cid,variety,cartons,kg,price,cur,margin,supplier))
                log_event(cid,today(),"Marchandise ajoutée",f"{supplier} — {variety}: {cartons:g} cartons")
                notify("Ligne de marchandise ajoutée."); st.rerun()
        rows=q("SELECT * FROM cargo WHERE container_id=? ORDER BY id DESC",(cid,),fetch=True)
        if rows:
            cno=q("SELECT container_no FROM containers WHERE id=?",(cid,),fetch=True)[0]["container_no"]
            data=[]
            for r in rows:
                achat=float(r['cartons'])*float(r['unit_purchase_price'])
                marge=float(r['cartons'])*float(r['atl_margin_per_carton'])
                facture=achat+marge
                net=achat-float(current_charge or 0)
                data.append({"N° Conteneur":cno,"Fournisseur":r['supplier'] or "","Variété":r['variety'],"Cartons":r['cartons'],"Kg/carton":r['kg_per_carton'],"Prix achat/carton":r['unit_purchase_price'],"Marge ATL/carton":r['atl_margin_per_carton'],"Charges locales conteneur":current_charge,"Prix facturé BLACK STAR":facture,"Paiement net fournisseur ATL":net,"Devise":r['purchase_currency']})
            df=pd.DataFrame(data); st.dataframe(df,use_container_width=True,hide_index=True)
            a1,a2,a3=st.columns(3)
            a1.metric("Total des cartons",f"{df['Cartons'].sum():,.0f}")
            a2.metric("Prix facturé à BLACK STAR",euro(df['Prix facturé BLACK STAR'].sum()))
            a3.metric("Paiement net fournisseurs ATL",euro(df['Paiement net fournisseur ATL'].sum()))
    else: st.info("Créez d'abord un conteneur.")

# -----------------------------
# Expenses
# -----------------------------
elif page == "Charges":
    cid = selected_container()
    if cid:
        st.info("Le fret maritime est saisi ici et est toujours comptabilisé comme charge prise en charge par BLACK STAR DISTRIBUTION.")
        with st.form("expense"):
            a,b,c = st.columns(3)
            category = a.selectbox("Catégorie", ["Ghana","Fret maritime","Anvers / Belgique","France","Autre"])
            desc = b.text_input("Description")
            amount = c.number_input("Montant", min_value=0.0, step=0.01)
            d,e,f = st.columns(3)
            currency = d.selectbox("Devise", ["EUR","GHS","USD"])
            edate = e.date_input("Date", date.today())
            payer = f.selectbox("Payeur", ["BLACK STAR DISTRIBUTION","A.T.L AFRO LIMITED COMPANY"])
            status = st.selectbox("Statut", ["À payer","Payée","Partielle"])
            ref = st.text_input("Référence")
            if st.form_submit_button("Ajouter la charge"):
                q("""INSERT INTO expenses(container_id,category,description,amount,currency,expense_date,payer,status,reference)
                     VALUES(?,?,?,?,?,?,?,?,?)""",(cid,category,desc,amount,currency,edate.isoformat(),payer,status,ref))
                log_event(cid,edate.isoformat(),"Charge",f"{category}: {desc}",amount)
                notify("Charge enregistrée avec succès.")
                st.rerun()
        rows = q("SELECT * FROM expenses WHERE container_id=? ORDER BY expense_date DESC,id DESC", (cid,), fetch=True)
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            cno=q("SELECT container_no FROM containers WHERE id=?",(cid,),fetch=True)[0]["container_no"]
            df.insert(0,"N°_Conteneur",cno)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Total charges enregistrées", euro(df["amount"].sum()))
            labels={f"#{r['id']} — {r['category']} — {r['description'] or 'Sans description'} — {euro(r['amount'])}":r['id'] for r in rows}
            selected_label=st.selectbox("Charge à gérer",list(labels.keys()),key=f"expense_select_{cid}")
            rid=labels[selected_label]
            editing,key=context_menu("expenses",rid,"Charge",[("DELETE FROM expenses WHERE id=?",(rid,))])
            if editing:
                r=next(x for x in rows if x['id']==rid)
                with st.form(f"edit_expense_{rid}"):
                    a,b,c=st.columns(3)
                    cat2=a.selectbox("Catégorie",["Ghana","Fret maritime","Anvers / Belgique","France","Autre"],index=["Ghana","Fret maritime","Anvers / Belgique","France","Autre"].index(r['category']))
                    desc2=b.text_input("Description",r['description'] or "")
                    amount2=c.number_input("Montant",min_value=0.0,value=float(r['amount']),step=0.01)
                    d,e,f=st.columns(3)
                    cur2=d.selectbox("Devise",["EUR","GHS","USD"],index=["EUR","GHS","USD"].index(r['currency']) if r['currency'] in ["EUR","GHS","USD"] else 0)
                    date2=e.date_input("Date",datetime.fromisoformat(r['expense_date']).date() if r['expense_date'] else date.today())
                    payer2=f.selectbox("Payeur",["BLACK STAR DISTRIBUTION","A.T.L AFRO LIMITED COMPANY"],index=["BLACK STAR DISTRIBUTION","A.T.L AFRO LIMITED COMPANY"].index(r['payer']))
                    status2=st.selectbox("Statut",["À payer","Payée","Partielle"],index=["À payer","Payée","Partielle"].index(r['status']))
                    ref2=st.text_input("Référence",r['reference'] or "")
                    if st.form_submit_button("Enregistrer les modifications"):
                        q("UPDATE expenses SET category=?,description=?,amount=?,currency=?,expense_date=?,payer=?,status=?,reference=? WHERE id=?",(cat2,desc2,amount2,cur2,date2.isoformat(),payer2,status2,ref2,rid))
                        notify("Charge modifiée avec succès.")
                        st.rerun()
    else:
        st.info("Créez d'abord un conteneur.")

# -----------------------------
# Invoices
# -----------------------------
elif page == "Factures":
    st.subheader("Factures")
    # Liste chronologique de toutes les factures
    if st.button("📋 Liste des factures", use_container_width=False):
        st.session_state["show_invoice_list"] = True
    if st.session_state.get("show_invoice_list", False):
        all_rows=q("""SELECT i.*, c.container_no FROM invoices i JOIN containers c ON c.id=i.container_id
                       ORDER BY COALESCE(i.invoice_date,'9999-12-31') ASC, i.id ASC""",fetch=True)
        if all_rows:
            inv_data=[]
            for r in all_rows:
                net,paid,credit,status=invoice_status(r['id'])
                inv_data.append({"Date":display_date(r['invoice_date']),"N° Facture":r['invoice_no'],"N° Conteneur":r['container_no'],"Expéditeur":r['issuer'],"Destinataire":r['recipient'],"Montant Facture":r['amount_ht'],"Devise":r['currency'],"Payé":paid,"Solde":max(net-paid,0),"Statut":status})
            st.dataframe(pd.DataFrame(inv_data),use_container_width=True,hide_index=True)
        else:
            st.info("Aucune facture enregistrée.")
    cid=selected_container()
    if cid:
        cargo_rows=q("SELECT * FROM cargo WHERE container_id=?",(cid,),fetch=True)
        auto_amount=round(sum(montant_facture_depuis_marchandise(r) for r in cargo_rows),2)
        cno=q("SELECT container_no FROM containers WHERE id=?",(cid,),fetch=True)[0]['container_no']
        existing=q("SELECT * FROM invoices WHERE container_id=? ORDER BY id DESC",(cid,),fetch=True)
        st.divider(); st.subheader(f"Facture BLACK STAR DISTRIBUTION — {cno}")
        st.info(f"Montant Facture automatique depuis Marchandises : {euro(auto_amount)}")
        with st.form("invoice_new"):
            a,b,c=st.columns(3); no=a.text_input("Numéro de facture"); issuer=b.text_input("Expéditeur","A.T.L AFRO LIMITED COMPANY"); recipient=c.text_input("Destinataire","BLACK STAR DISTRIBUTION")
            d,e,f=st.columns(3); inv_date=d.date_input("Date facture",date.today()); due=e.date_input("Échéance",date.today()); f.number_input("Montant Facture",min_value=0.0,value=float(auto_amount),step=0.01,disabled=True,key=f"invoice_amount_new_{cid}")
            cur=st.selectbox("Devise",["EUR","GHS","USD"],key=f"invoice_cur_new_{cid}"); notes=st.text_area("Notes",key=f"invoice_notes_new_{cid}")
            if st.form_submit_button("Créer la facture"):
                if not no.strip(): st.error("Le numéro de facture est obligatoire.")
                else:
                    q("INSERT INTO invoices(container_id,invoice_no,issuer,recipient,invoice_date,due_date,amount_ht,tax,currency,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(cid,no.strip(),issuer,recipient,inv_date.isoformat(),due.isoformat(),auto_amount,0.0,cur,notes))
                    log_event(cid,inv_date.isoformat(),"Facture créée",no,auto_amount); notify("Facture créée avec montant automatique."); st.rerun()
        rows=q("SELECT i.*,c.container_no FROM invoices i JOIN containers c ON c.id=i.container_id WHERE i.container_id=? ORDER BY i.id DESC",(cid,),fetch=True)
        if rows:
            st.markdown("### Factures de ce conteneur")
            data=[]
            for r in rows:
                net,paid,credit,status=invoice_status(r['id']); data.append({"Date":display_date(r['invoice_date']),"N° Facture":r['invoice_no'],"N° Conteneur":r['container_no'],"Montant":r['amount_ht'],"Avoirs":credit,"Payé":paid,"Solde":max(net-paid,0),"Statut":status})
            st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
            labels={f"#{r['id']} — {r['invoice_no']} — {r['container_no']}":r['id'] for r in rows}
            selected_label=st.selectbox("Facture à gérer",list(labels.keys()),key=f"invoice_manage_{cid}")
            rid=labels[selected_label]
            editing,key=context_menu("invoices",rid,"Facture",[("DELETE FROM invoices WHERE id=?",(rid,))])
            if editing:
                r=next(x for x in rows if x['id']==rid)
                with st.form(f"edit_invoice_{rid}"):
                    a,b,c=st.columns(3); no2=a.text_input("Numéro de facture",r['invoice_no']); issuer2=b.text_input("Expéditeur",r['issuer']); recipient2=c.text_input("Destinataire",r['recipient'])
                    d,e,f=st.columns(3); id2=d.date_input("Date facture",datetime.fromisoformat(r['invoice_date']).date() if r['invoice_date'] else date.today()); due2=e.date_input("Échéance",datetime.fromisoformat(r['due_date']).date() if r['due_date'] else date.today()); f.number_input("Montant Facture",min_value=0.0,value=float(auto_amount),step=0.01,disabled=True,key=f"invoice_amount_edit_{rid}")
                    cur2=st.selectbox("Devise",["EUR","GHS","USD"],index=["EUR","GHS","USD"].index(r['currency']) if r['currency'] in ["EUR","GHS","USD"] else 0,key=f"invoice_cur_edit_{rid}")
                    notes2=st.text_area("Notes",r['notes'] or "",key=f"invoice_notes_edit_{rid}")
                    if st.form_submit_button("Enregistrer les modifications"):
                        q("UPDATE invoices SET invoice_no=?,issuer=?,recipient=?,invoice_date=?,due_date=?,amount_ht=?,tax=0,currency=?,notes=? WHERE id=?",(no2.strip(),issuer2,recipient2,id2.isoformat(),due2.isoformat(),auto_amount,cur2,notes2,rid))
                        notify("Facture modifiée avec succès."); st.rerun()
        st.divider(); st.subheader("A.T.L AFRO LIMITED COMPANY — Factures fournisseurs")
        with st.form("atl_supplier_invoice"):
            a,b,c=st.columns(3); supplier=a.text_input("Fournisseur ATL"); product=b.selectbox("Désignation du produit",["Pona","White Yam"]); idate=c.date_input("Date facture fournisseur",date.today())
            d,e,f=st.columns(3); qty=d.number_input("Quantité",min_value=0.0,step=1.0); unit=e.number_input("Prix unitaire",min_value=0.0,step=0.01); weight=f.number_input("Poids total",min_value=0.0,step=0.5)
            total=round(qty*unit,2); st.caption(f"Total automatique : {total:,.2f}"); cur2=st.selectbox("Devise fournisseur",["EUR","GHS","USD"],key=f"atlcur_{cid}"); notes2=st.text_area("Notes fournisseur")
            if st.form_submit_button("Enregistrer la facture fournisseur"):
                q("INSERT INTO atl_supplier_invoices(container_id,supplier,invoice_date,product,quantity,unit_price,weight,total,currency,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(cid,supplier,idate.isoformat(),product,qty,unit,weight,total,cur2,notes2)); notify("Facture fournisseur ATL enregistrée."); st.rerun()
        atlrows=q("SELECT * FROM atl_supplier_invoices WHERE container_id=? ORDER BY id DESC",(cid,),fetch=True)
        if atlrows:
            ad=[]
            for r in atlrows:
                paid=q("SELECT COALESCE(SUM(amount),0) s FROM atl_supplier_payments WHERE supplier_invoice_id=?",(r['id'],),fetch=True)[0]['s']
                ad.append({"Date":display_date(r['invoice_date']),"Fournisseur":r['supplier'],"Produit":r['product'],"Quantité":r['quantity'],"Prix unitaire":r['unit_price'],"Poids":r['weight'],"Total":r['total'],"Payé":paid,"Solde":max(float(r['total'])-float(paid),0)})
            st.dataframe(pd.DataFrame(ad),use_container_width=True,hide_index=True)
    else: st.info("Créez d'abord un conteneur.")

# -----------------------------
# Payments
# -----------------------------
elif page == "Paiements":
    invs = q("""SELECT i.id, i.invoice_no, i.amount_ht total, c.container_no
                FROM invoices i JOIN containers c ON c.id=i.container_id ORDER BY i.id DESC""", fetch=True)
    if invs:
        labels={f'{r["invoice_no"]} — N° Conteneur : {r["container_no"]}':r["id"] for r in invs}
        label=st.selectbox("Facture",list(labels.keys()))
        iid=labels[label]
        net,paid,credit,status=invoice_status(iid)
        a,b,c=st.columns(3)
        a.metric("Net facture",euro(net)); b.metric("Total payé",euro(paid)); c.metric("Solde",euro(max(net-paid,0)))
        with st.form("payment"):
            d,e,f=st.columns(3)
            pdate=d.date_input("Date paiement",date.today())
            amount= e.number_input("Montant",min_value=0.0,step=0.01)
            ptype=f.selectbox("Type",["Acompte / avance","Paiement","Solde"])
            method=st.selectbox("Mode",["Virement bancaire","Espèces","Chèque","Autre"])
            ref=st.text_input("Référence bancaire")
            notes=st.text_area("Notes")
            if st.form_submit_button("Enregistrer le paiement"):
                cid=q("SELECT container_id FROM invoices WHERE id=?",(iid,),fetch=True)[0]["container_id"]
                q("""INSERT INTO payments(invoice_id,payment_date,amount,currency,payment_type,method,reference,notes)
                     VALUES(?,?,?,?,?,?,?,?)""",(iid,pdate.isoformat(),amount,"EUR",ptype,method,ref,notes))
                log_event(cid,pdate.isoformat(),"Paiement",f"{ptype} — {label}",amount)
                notify("Paiement enregistré avec succès.")
                st.rerun()
        rows=q("""SELECT p.*,c.container_no FROM payments p JOIN invoices i ON i.id=p.invoice_id JOIN containers c ON c.id=i.container_id WHERE p.invoice_id=? ORDER BY p.payment_date DESC,p.id DESC""",(iid,),fetch=True)
        if rows:
            pdf=pd.DataFrame([dict(r) for r in rows]); pdf.insert(0,"N° Conteneur",pdf.pop("container_no"))
            st.dataframe(pdf,use_container_width=True,hide_index=True)
            labels={f"#{r['id']} — {r['payment_type']} — {euro(r['amount'])} — {display_date(r['payment_date'])}":r['id'] for r in rows}
            selected_label=st.selectbox("Paiement à gérer",list(labels.keys()),key=f"payment_select_{iid}")
            rid=labels[selected_label]
            editing,key=context_menu("payments",rid,"Paiement",[("DELETE FROM payments WHERE id=?",(rid,))])
            if editing:
                r=next(x for x in rows if x['id']==rid)
                with st.form(f"edit_payment_{rid}"):
                    a,b,c=st.columns(3)
                    pd2=a.date_input("Date paiement",datetime.fromisoformat(r['payment_date']).date())
                    amount2=b.number_input("Montant",min_value=0.0,value=float(r['amount']),step=0.01)
                    pt2=c.selectbox("Type",["Acompte / avance","Paiement","Solde"],index=["Acompte / avance","Paiement","Solde"].index(r['payment_type']))
                    method2=st.selectbox("Mode",["Virement bancaire","Espèces","Chèque","Autre"],index=["Virement bancaire","Espèces","Chèque","Autre"].index(r['method']) if r['method'] in ["Virement bancaire","Espèces","Chèque","Autre"] else 0)
                    ref2=st.text_input("Référence bancaire",r['reference'] or "")
                    notes2=st.text_area("Notes",r['notes'] or "")
                    if st.form_submit_button("Enregistrer les modifications"):
                        q("UPDATE payments SET payment_date=?,amount=?,payment_type=?,method=?,reference=?,notes=? WHERE id=?",(pd2.isoformat(),amount2,pt2,method2,ref2,notes2,rid))
                        notify("Paiement modifié avec succès.")
                        st.rerun()
    else:
        st.info("Aucune facture.")

# -----------------------------
# Credits
# -----------------------------
elif page == "Avoirs":
    invs=q("""SELECT i.id,i.invoice_no,c.container_no FROM invoices i JOIN containers c ON c.id=i.container_id ORDER BY i.id DESC""",fetch=True)
    if invs:
        labels={f'{r["invoice_no"]} — N° Conteneur : {r["container_no"]}':(r["id"],r["container_no"]) for r in invs}
        label=st.selectbox("Facture concernée",list(labels.keys()))
        iid=labels[label][0]
        cid=q("SELECT container_id FROM invoices WHERE id=?",(iid,),fetch=True)[0]["container_id"]
        with st.form("credit"):
            a,b,c=st.columns(3)
            no=a.text_input("Numéro d'avoir")
            cdate=b.date_input("Date de l'avoir",date.today())
            amount=c.number_input("Montant de l'avoir",min_value=0.0,step=0.01)
            reason=st.selectbox("Motif",["Avarie marchandise","Cartons endommagés","Ignames pourries","Quantité manquante","Erreur de facturation","Produit non conforme","Autre"])
            notes=st.text_area("Commentaire")
            if st.form_submit_button("Enregistrer l'avoir"):
                q("""INSERT INTO credits(invoice_id,container_id,credit_no,credit_date,reason,amount,currency,notes)
                     VALUES(?,?,?,?,?,?,?,?)""",(iid,cid,no,cdate.isoformat(),reason,amount,"EUR",notes))
                log_event(cid,cdate.isoformat(),"Avoir",f"{no} — {reason}",amount)
                notify("Avoir enregistré avec succès.")
                st.rerun()
        rows=q("""SELECT cr.*,i.invoice_no,c.container_no FROM credits cr JOIN invoices i ON i.id=cr.invoice_id JOIN containers c ON c.id=cr.container_id
                  WHERE cr.invoice_id=? ORDER BY cr.id DESC""",(iid,),fetch=True)
        if rows:
            cdf=pd.DataFrame([dict(r) for r in rows]); cdf.insert(0,"N° Conteneur",cdf.pop("container_no"))
            st.dataframe(cdf,use_container_width=True,hide_index=True)
            labels={f"#{r['id']} — {r['credit_no']} — {euro(r['amount'])}":r['id'] for r in rows}
            selected_label=st.selectbox("Avoir à gérer",list(labels.keys()),key=f"credit_select_{iid}")
            rid=labels[selected_label]
            editing,key=context_menu("credits",rid,"Avoir",[("DELETE FROM credits WHERE id=?",(rid,))])
            if editing:
                r=next(x for x in rows if x['id']==rid)
                with st.form(f"edit_credit_{rid}"):
                    a,b,c=st.columns(3)
                    no2=a.text_input("Numéro d'avoir",r['credit_no'])
                    cd2=b.date_input("Date de l'avoir",datetime.fromisoformat(r['credit_date']).date())
                    amount2=c.number_input("Montant",min_value=0.0,value=float(r['amount']),step=0.01)
                    reason2=st.selectbox("Motif",["Avarie marchandise","Cartons endommagés","Ignames pourries","Quantité manquante","Erreur de facturation","Produit non conforme","Autre"],index=["Avarie marchandise","Cartons endommagés","Ignames pourries","Quantité manquante","Erreur de facturation","Produit non conforme","Autre"].index(r['reason']) if r['reason'] in ["Avarie marchandise","Cartons endommagés","Ignames pourries","Quantité manquante","Erreur de facturation","Produit non conforme","Autre"] else 0)
                    notes2=st.text_area("Commentaire",r['notes'] or "")
                    if st.form_submit_button("Enregistrer les modifications"):
                        q("UPDATE credits SET credit_no=?,credit_date=?,reason=?,amount=?,notes=? WHERE id=?",(no2,cd2.isoformat(),reason2,amount2,notes2,rid))
                        notify("Avoir modifié avec succès.")
                        st.rerun()
    else: st.info("Aucune facture.")

# -----------------------------
# Damages
# -----------------------------
elif page == "Avaries":
    cid=selected_container()
    if cid:
        with st.form("damage"):
            a,b,c,d=st.columns(4)
            variety=a.selectbox("Variété",["Pona","White Yam","Non précisée"])
            ddate=b.date_input("Date du constat",date.today())
            cartons=c.number_input("Cartons concernés",min_value=0.0,step=1.0)
            kg=d.number_input("Kg concernés",min_value=0.0,step=0.5)
            desc=st.text_input("Description de l'avarie")
            loss=st.number_input("Perte estimée (€)",min_value=0.0,step=0.01)
            credit=st.number_input("Avoir obtenu (€)",min_value=0.0,step=0.01)
            status=st.selectbox("Statut",["Constatée","Déclarée","Avoir demandé","Avoir obtenu","Clôturée"])
            notes=st.text_area("Notes / référence")
            if st.form_submit_button("Enregistrer l'avarie"):
                q("""INSERT INTO damages(container_id,variety,damage_date,cartons,kg,description,estimated_loss,credit_amount,status,notes)
                     VALUES(?,?,?,?,?,?,?,?,?,?)""",(cid,variety,ddate.isoformat(),cartons,kg,desc,loss,credit,status,notes))
                log_event(cid,ddate.isoformat(),"Avarie",desc,loss)
                notify("Avarie enregistrée avec succès.")
                st.rerun()
        rows=q("SELECT * FROM damages WHERE container_id=? ORDER BY damage_date DESC,id DESC",(cid,),fetch=True)
        if rows:
            df=pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df,use_container_width=True,hide_index=True)
            labels={f"#{r['id']} — {r['variety']} — {r['cartons']:g} cartons — {r['description']}":r['id'] for r in rows}
            selected_label=st.selectbox("Avarie à gérer",list(labels.keys()),key=f"damage_select_{cid}")
            rid=labels[selected_label]
            editing,key=context_menu("damages",rid,"Avarie",[("DELETE FROM damages WHERE id=?",(rid,))])
            if editing:
                r=next(x for x in rows if x['id']==rid)
                with st.form(f"edit_damage_{rid}"):
                    a,b,c,d=st.columns(4)
                    variety2=a.selectbox("Variété",["Pona","White Yam","Non précisée"],index=["Pona","White Yam","Non précisée"].index(r['variety']) if r['variety'] in ["Pona","White Yam","Non précisée"] else 0)
                    dd2=b.date_input("Date du constat",datetime.fromisoformat(r['damage_date']).date())
                    cartons2=c.number_input("Cartons concernés",min_value=0.0,value=float(r['cartons']),step=1.0)
                    kg2=d.number_input("Kg concernés",min_value=0.0,value=float(r['kg']),step=0.5)
                    desc2=st.text_input("Description",r['description'])
                    loss2=st.number_input("Perte estimée (€)",min_value=0.0,value=float(r['estimated_loss']),step=0.01)
                    credit2=st.number_input("Avoir obtenu (€)",min_value=0.0,value=float(r['credit_amount']),step=0.01)
                    status2=st.selectbox("Statut",["Constatée","Déclarée","Avoir demandé","Avoir obtenu","Clôturée"],index=["Constatée","Déclarée","Avoir demandé","Avoir obtenu","Clôturée"].index(r['status']))
                    notes2=st.text_area("Notes / référence",r['notes'] or "")
                    if st.form_submit_button("Enregistrer les modifications"):
                        q("UPDATE damages SET variety=?,damage_date=?,cartons=?,kg=?,description=?,estimated_loss=?,credit_amount=?,status=?,notes=? WHERE id=?",(variety2,dd2.isoformat(),cartons2,kg2,desc2,loss2,credit2,status2,notes2,rid))
                        notify("Avarie modifiée avec succès.")
                        st.rerun()
            a,b=st.columns(2)
            a.metric("Perte estimée",euro(df["estimated_loss"].sum()))
            b.metric("Avoir obtenu",euro(df["credit_amount"].sum()))
    else: st.info("Créez d'abord un conteneur.")

# -----------------------------
# Timeline
# -----------------------------
elif page == "Chronologie":
    cid=selected_container()
    if cid:
        rows=q("""SELECT event_date,event_type,description,amount,created_at
                  FROM events WHERE container_id=? ORDER BY event_date,id""",(cid,),fetch=True)
        if rows:
            df=pd.DataFrame([dict(r) for r in rows])
            df["Date"]=df["event_date"].apply(display_date)
            df["Montant"]=df["amount"].apply(lambda x:euro(x) if x is not None else "")
            st.dataframe(df[["Date","event_type","description","Montant","created_at"]],use_container_width=True,hide_index=True)
        else: st.info("Aucun événement enregistré.")
    else: st.info("Créez d'abord un conteneur.")

# -----------------------------
# Reports
# -----------------------------
elif page == "Rapports":
    rows=q("SELECT id,container_no FROM containers ORDER BY id DESC",fetch=True)
    if rows:
        bsd=[]; atl=[]
        for r in rows:
            f=container_financials(r["id"])
            bsd.append({"N° Conteneur":r["container_no"],"Cartons":f["cartons"],"Achat":f["purchase"],"Fret":f["freight"],"Anvers":f["belgium"],"France":f["france"],"Autres charges":f["other"],"Avoirs":f["credits"],"Coût total":f["cost_total"],"Coût/carton":f["per_carton"]})
            atl.append({"N° Conteneur":r["container_no"],"Cartons":f["cartons"],"Achat fournisseur":f["purchase"],"Charges locales déduites":f.get("local_charges",0),"Charges Ghana / ATL":f["atl_charges"],"Coût net ATL":f["atl_total"],"Marge ATL (bénéfice)":f["atl_margin"]})
        st.subheader("BLACK STAR DISTRIBUTION")
        df=pd.DataFrame(bsd); st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("Exporter BLACK STAR en PDF",pdf_report(df,"Rapport BLACK STAR DISTRIBUTION","Coût hors Marge ATL et Charges Ghana"),"rapport_black_star.pdf","application/pdf")
        st.plotly_chart(px.bar(df,x="N° Conteneur",y=["Fret","Anvers","France","Autres charges"],barmode="stack",title="Charges BLACK STAR par N° Conteneur"),use_container_width=True)
        st.divider(); st.subheader("A.T.L AFRO LIMITED COMPANY")
        dfa=pd.DataFrame(atl); st.dataframe(dfa,use_container_width=True,hide_index=True)
        st.download_button("Exporter A.T.L en PDF",pdf_report(dfa,"Rapport A.T.L AFRO LIMITED COMPANY","Éléments propres à A.T.L"),"rapport_atl.pdf","application/pdf")
        st.plotly_chart(px.bar(dfa,x="N° Conteneur",y=["Charges locales déduites","Charges Ghana / ATL"],barmode="stack",title="Éléments A.T.L par N° Conteneur"),use_container_width=True)
    else: st.info("Aucun conteneur.")

# -----------------------------
# Simulation
# -----------------------------
elif page == "Simulation":
    st.subheader("Simulation de revente par produit")
    cid=selected_container()
    if cid:
        rows=q("SELECT * FROM cargo WHERE container_id=?",(cid,),fetch=True)
        pct=st.number_input("Pourcentage de revente / majoration (%)",min_value=0.0,max_value=500.0,value=20.0,step=1.0)
        simrows=[]
        for variety in ["Pona","White Yam"]:
            rs=[r for r in rows if r['variety']==variety]
            cartons=sum(float(r['cartons']) for r in rs)
            achat=sum(float(r['cartons'])*float(r['unit_purchase_price']) for r in rs)
            marge_atl=sum(float(r['cartons'])*float(r['atl_margin_per_carton']) for r in rs)
            base=achat+marge_atl
            sale=base*(1+pct/100)
            simrows.append({"Produit":variety,"Cartons":cartons,"Coût de base":base,"Prix revente simulé":sale,"Marge de revente":sale-base})
        st.subheader("Simulation Pona et White Yam")
        sdf=pd.DataFrame(simrows); st.dataframe(sdf,use_container_width=True,hide_index=True)
        total_cartons=sdf['Cartons'].sum(); total_cost=sdf['Coût de base'].sum(); total_sale=sdf['Prix revente simulé'].sum()
        st.divider(); st.subheader("Simulation globale du conteneur")
        a,b,c=st.columns(3); a.metric("Total cartons",f"{total_cartons:,.0f}"); b.metric("Coût global",euro(total_cost)); c.metric("Revente globale simulée",euro(total_sale))
        d,e=st.columns(2); d.metric("Marge globale simulée",euro(total_sale-total_cost)); e.metric("Prix moyen simulé/carton",euro(total_sale/total_cartons if total_cartons else 0))
    else: st.info("Créez d'abord un conteneur.")

# -----------------------------
# Settings / users
# -----------------------------
elif page == "Paramètres":
    st.markdown("### Thème")
    current=active_theme()
    theme_labels={v["label"]:k for k,v in THEMES.items()}
    selected=st.selectbox("Choisir le thème", list(theme_labels.keys()), index=list(theme_labels.values()).index(current))
    new_theme=theme_labels[selected]
    if new_theme!=current:
        set_setting("theme",new_theme)
        notify("Thème appliqué.")
        st.rerun()
    st.divider()
    st.subheader("Utilisateurs")
    if st.session_state.user["role"]=="admin":
        with st.form("new_user"):
            a,b,c=st.columns(3)
            username=a.text_input("Nom utilisateur")
            password=b.text_input("Mot de passe",type="password")
            role=c.selectbox("Rôle",["user","admin"])
            if st.form_submit_button("Créer utilisateur"):
                if username and password:
                    try:
                        q("INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",(username,hash_password(password),role,datetime.now().isoformat(timespec="seconds")))
                        notify("Utilisateur créé avec succès.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ce nom d'utilisateur existe déjà.")
        rows=q("SELECT id,username,role,active,created_at FROM users ORDER BY id",fetch=True)
        if rows: st.dataframe(pd.DataFrame([dict(r) for r in rows]),use_container_width=True,hide_index=True)
    else:
        st.info("Gestion des utilisateurs réservée à l'administrateur.")
