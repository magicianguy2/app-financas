import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import io
import re
from PIL import Image
import pytesseract

st.set_page_config(page_title="Finanças Pessoais", page_icon="💎", layout="wide")

# CSS bonito
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main { background: #f7f8fc; }
    .glass-card {
        background: rgba(255,255,255,0.8);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0 8px 32px rgba(0,0,0,0.05);
        transition: 0.3s;
    }
    .glass-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.08); }
    .metric-value { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
    .metric-label { font-size: 0.8rem; color: #6b7280; text-transform: uppercase; font-weight: 600; }
    .metric-green { color: #10b981; }
    .metric-red { color: #ef4444; }
    .metric-purple { color: #6366f1; }
    .progress-bar-bg { background: #e5e7eb; border-radius: 100px; height: 12px; overflow: hidden; margin: 0.5rem 0 1rem; }
    .progress-bar-fill { background: linear-gradient(90deg, #818cf8, #6366f1); height: 100%; border-radius: 100px; transition: width 0.5s ease; }
    .custom-divider { border: none; height: 2px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent); margin: 1.5rem 0; }
    .stButton button { background: #6366f1 !important; color: white !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; }
    .stButton button:hover { transform: scale(1.02); box-shadow: 0 4px 12px rgba(99,102,241,0.3); }
</style>
""", unsafe_allow_html=True)

# CORREÇÃO 1: Inicializar a coluna de vencimento como datetime real do Pandas
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "Categoria": ["Cartão", "Conta", "Dívida", "Personalizado"],
        "Descrição": ["Fatura Junho", "Luz", "Empréstimo", "Conserto Carro"],
        "Valor Total": [2500.0, 350.0, 5000.0, 800.0],
        "Valor Pago": [0.0, 0.0, 0.0, 0.0],
        "Vencimento": pd.to_datetime(["2026-06-10", "2026-06-15", "2026-06-30", "2026-06-25"]),
        "Pago": [False, False, False, False]
    })
    st.session_state.meta = 5000.0

df = st.session_state.df
meta = st.session_state.meta

# Funções
def calcular_resumo(df):
    total = df["Valor Total"].sum()
    pago = df.loc[df["Pago"], "Valor Total"].sum()
    restante = total - pago
    return total, pago, restante

def extrair_valor_imagem(image):
    try:
        texto = pytesseract.image_to_string(image, lang="por")
        padrao = r"R?\$?\s*([\d.,]+)"
        matches = re.findall(padrao, texto)
        if matches:
            for m in matches:
                try:
                    v = float(m.replace(",", "."))
                    return v
                except:
                    pass
        return None
    except:
        return None

def processar_excel(uploaded):
    try:
        df_imp = pd.read_excel(uploaded)
    except:
        return None
    # Padronizar colunas
    if "Categoria" not in df_imp.columns:
        df_imp["Categoria"] = "Outros"
    if "Descrição" not in df_imp.columns:
        df_imp["Descrição"] = "Item importado"
    if "Valor Total" not in df_imp.columns:
        return None
    df_imp["Valor Pago"] = 0.0
    # CORREÇÃO 2: Garantir datetime no formato correto ao importar
    df_imp["Vencimento"] = pd.to_datetime(datetime.now().date())
    df_imp["Pago"] = False
    return df_imp

# Interface
st.title("💎 Finanças Pessoais")
st.caption("Controle suas dívidas, importe arquivos, edite e marque como pago.")

total, pago, restante = calcular_resumo(df)
progresso = min(pago / meta, 1.0) if meta > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">💰 Dívida Total</div>
        <div class="metric-value metric-red">R$ {total:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">✅ Já Pago</div>
        <div class="metric-value metric-green">R$ {pago:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">⏳ Restante</div>
        <div class="metric-value metric-purple">R$ {restante:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">🎯 Meta Mensal</div>
        <div class="metric-value metric-purple">R$ {meta:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style="margin: 0.5rem 0 1rem;">
    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #6b7280;">
        <span>Progresso da meta</span>
        <span>R$ {pago:,.2f} / R$ {meta:,.2f} ({progresso*100:.0f}%)</span>
    </div>
    <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width: {progresso*100}%;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📂 Importar Dados")
    tipo = st.radio("Tipo", ["Excel (.xlsx)", "CSV", "TXT estruturado", "🖼️ Imagem (OCR)"])
    uploaded = st.file_uploader("Selecione o arquivo", type=["xlsx", "csv", "txt", "png", "jpg", "jpeg"])
    
    if uploaded is not None:
        if tipo.startswith("Excel"):
            df_imp = processar_excel(uploaded)
        elif tipo == "CSV":
            df_imp = processar_excel(uploaded)  # reuso
        elif tipo.startswith("TXT"):
            content = uploaded.read().decode("utf-8")
            lines = content.strip().split("\n")
            dados = []
            for line in lines:
                match = re.match(r"^(.*?):\s*R?\$?\s*([\d.,]+)\s*[-–]\s*(.*)$", line)
                if match:
                    cat, val_str, desc = match.groups()
                    try:
                        val = float(val_str.replace(",", "."))
                        dados.append({"Categoria": cat.strip(), "Descrição": desc.strip(), "Valor Total": val})
                    except:
                        pass
            df_imp = pd.DataFrame(dados) if dados else None
        else:  # Imagem
            image = Image.open(uploaded)
            st.image(image, caption="Imagem enviada", width=150)
            valor = extrair_valor_imagem(image)
            if valor:
                st.success(f"Valor detectado: R$ {valor:.2f}")
                # CORREÇÃO 3: Nova linha usando datetime real para consistência
                nova = pd.DataFrame({
                    "Categoria": ["OCR"],
                    "Descrição": ["Item da imagem"],
                    "Valor Total": [valor],
                    "Valor Pago": [0.0],
                    "Vencimento": [pd.to_datetime(datetime.now().date())],
                    "Pago": [False]
                })
                st.session_state.df = pd.concat([st.session_state.df, nova], ignore_index=True)
                st.rerun()
            else:
                st.warning("Nenhum valor encontrado na imagem.")
            df_imp = None
        
        if df_imp is not None and not df_imp.empty:
            df_imp["Valor Pago"] = 0.0
            df_imp["Vencimento"] = pd.to_datetime(datetime.now().date())
            df_imp["Pago"] = False
            if st.button("✅ Inserir na lista"):
                st.session_state.df = pd.concat([st.session_state.df, df_imp], ignore_index=True)
                st.rerun()
    
    st.divider()
    st.header("🎯 Meta")
    nova_meta = st.number_input("Meta mensal (R$)", min_value=0.0, value=meta, step=100.0)
    if nova_meta != meta:
        st.session_state.meta = nova_meta
        st.rerun()
    
    st.divider()
    st.header("➕ Nova Dívida")
    with st.form("add_form"):
        cat = st.text_input("Categoria", "Pessoal")
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        venc = st.date_input("Vencimento", value=datetime.now() + timedelta(days=15))
        if st.form_submit_button("Adicionar"):
            # CORREÇÃO 4: Garantindo datetime na inserção manual
            nova = pd.DataFrame({
                "Categoria": [cat],
                "Descrição": [desc],
                "Valor Total": [valor],
                "Valor Pago": [0.0],
                "Vencimento": [pd.to_datetime(venc)],
                "Pago": [False]
            })
            st.session_state.df = pd.concat([st.session_state.df, nova], ignore_index=True)
            st.rerun()

# Tabela
st.subheader("📋 Suas Dívidas")

# CORREÇÃO 5: Capturamos o dataframe editado diretamente do retorno da função,
# evitando problemas de sincronia de estado e dicionários brutos do session_state.
df_editado = st.data_editor(
    df,
    column_config={
        "Categoria": st.column_config.TextColumn("Categoria"),
        "Descrição": st.column_config.TextColumn("Descrição"),
        "Valor Total": st.column_config.NumberColumn("Valor Total", format="R$ %.2f"),
        "Valor Pago": st.column_config.NumberColumn("Valor Pago", format="R$ %.2f", disabled=True),
        "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "Pago": st.column_config.CheckboxColumn("Pago?"),
    },
    use_container_width=True,
    hide_index=True,
    key="editor_key" # Alterado o nome da key para não colidir com variáveis locais
)

if st.button("💾 Salvar alterações", use_container_width=True):
    # Agora calculamos os valores pagos diretamente com o dataframe retornado pelo editor
    df_editado["Valor Pago"] = df_editado.apply(lambda row: row["Valor Total"] if row["Pago"] else 0.0, axis=1)
    st.session_state.df = df_editado
    st.success("Salvo!")
    st.rerun()

if len(df[~df["Pago"]]) > 0:
    if st.button(f"✅ Pagar todas as {len(df[~df['Pago']])} pendentes", use_container_width=True):
        df.loc[~df["Pago"], "Valor Pago"] = df.loc[~df["Pago"], "Valor Total"]
        df.loc[~df["Pago"], "Pago"] = True
        st.session_state.df = df
        st.rerun()

# Gráficos
st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.subheader("📊 Distribuição")
    cat_data = df.groupby("Categoria")["Valor Total"].sum().reset_index()
    if not cat_data.empty:
        fig = go.Figure(data=[go.Pie(labels=cat_data["Categoria"], values=cat_data["Valor Total"], hole=0.5)])
        fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
with col_g2:
    st.subheader("📈 Pagamento")
    fig = go.Figure(data=[go.Bar(x=["Total","Pago","Restante"], y=[total,pago,restante], marker_color=['#9ca3af','#10b981','#ef4444'])])
    fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

st.caption("💾 Dados salvos na sessão (recarregue a página para resetar).")
