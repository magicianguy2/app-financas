import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import re
from PIL import Image
import pytesseract

st.set_page_config(page_title="Finanças Pessoais", page_icon="💎", layout="wide")

# CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
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
    .metric-blue { color: #3b82f6; }
    .progress-bar-bg { background: #e5e7eb; border-radius: 100px; height: 12px; overflow: hidden; margin: 0.5rem 0 1rem; }
    .progress-bar-fill { background: linear-gradient(90deg, #818cf8, #6366f1); height: 100%; border-radius: 100px; transition: width 0.5s ease; }
    .progress-bar-fill-green { background: linear-gradient(90deg, #34d399, #10b981); }
    .custom-divider { border: none; height: 2px; background: linear-gradient(90deg, transparent, #e5e7eb, transparent); margin: 1.5rem 0; }
    .stButton button { background: #6366f1 !important; color: white !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; }
    .stButton button:hover { transform: scale(1.02); box-shadow: 0 4px 12px rgba(99,102,241,0.3); }
    .tab-label { font-size: 1.2rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Inicialização
if "df_dividas" not in st.session_state:
    st.session_state.df_dividas = pd.DataFrame({
        "Categoria": ["Cartão", "Conta", "Dívida", "Personalizado"],
        "Descrição": ["Fatura Junho", "Luz", "Empréstimo", "Conserto Carro"],
        "Valor Total": [2500.0, 350.0, 5000.0, 800.0],
        "Valor Pago": [0.0, 0.0, 0.0, 0.0],
        "Vencimento": ["2026-06-10", "2026-06-15", "2026-06-30", "2026-06-25"],
        "Pago": [False, False, False, False]
    })
if "df_metas" not in st.session_state:
    st.session_state.df_metas = pd.DataFrame({
        "Descrição": ["Viagem", "Emergência", "Carro"],
        "Valor Alvo": [3000.0, 5000.0, 2000.0],
        "Valor Guardado": [500.0, 200.0, 300.0]
    })
if "pagamentos_extras" not in st.session_state:
    st.session_state.pagamentos_extras = 0.0

# Funções auxiliares
def calcular_resumo_dividas(df, extra):
    total = df["Valor Total"].sum()
    pago = df.loc[df["Pago"], "Valor Total"].sum() + extra
    restante = total - pago
    return total, pago, restante

def calcular_resumo_metas(df):
    total_alvo = df["Valor Alvo"].sum()
    total_guardado = df["Valor Guardado"].sum()
    return total_alvo, total_guardado

def extrair_valor_imagem(image):
    try:
        texto = pytesseract.image_to_string(image, lang="por")
        padrao = r"R?\$?\s*([\d.,]+)"
        matches = re.findall(padrao, texto)
        if matches:
            for m in matches:
                try:
                    return float(m.replace(",", "."))
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
    if "Categoria" not in df_imp.columns:
        df_imp["Categoria"] = "Outros"
    if "Descrição" not in df_imp.columns:
        df_imp["Descrição"] = "Item importado"
    if "Valor Total" not in df_imp.columns:
        return None
    df_imp["Valor Pago"] = 0.0
    df_imp["Vencimento"] = datetime.now().strftime("%Y-%m-%d")
    df_imp["Pago"] = False
    return df_imp

# Interface
st.title("💎 Controle Financeiro")
st.caption("Dividas | Metas de Poupança")

# Abas
aba1, aba2 = st.tabs(["💰 Dívidas", "🎯 Metas"])

# ==================== ABA 1: DÍVIDAS ====================
with aba1:
    df_d = st.session_state.df_dividas
    extra = st.session_state.pagamentos_extras
    total, pago, restante = calcular_resumo_dividas(df_d, extra)

    st.subheader("📊 Resumo das Dívidas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-label">💳 Total</div>
            <div class="metric-value metric-red">R$ {total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-label">✅ Pago</div>
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

    # Régua da dívida
    progresso_d = min(pago / total, 1.0) if total > 0 else 0
    st.markdown(f"""
    <div style="margin: 0.5rem 0 1rem;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #6b7280;">
            <span>Pagamento das dívidas</span>
            <span>R$ {pago:,.2f} / R$ {total:,.2f} ({progresso_d*100:.0f}%)</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {min(progresso_d*100, 100)}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar para dívidas (importar, adicionar, pagamento extra)
    with st.sidebar:
        st.header("📂 Dívidas")
        tipo = st.radio("Importar", ["Excel (.xlsx)", "CSV", "TXT", "🖼️ Imagem"], key="tipo_d")
        uploaded = st.file_uploader("Arquivo", type=["xlsx", "csv", "txt", "png", "jpg", "jpeg"], key="upload_d")
        if uploaded is not None:
            if tipo.startswith("Excel") or tipo == "CSV":
                df_imp = processar_excel(uploaded)
            elif tipo == "TXT":
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
            else:
                image = Image.open(uploaded)
                st.image(image, caption="Imagem", width=150)
                valor = extrair_valor_imagem(image)
                if valor:
                    st.success(f"Valor: R$ {valor:.2f}")
                    nova = pd.DataFrame({
                        "Categoria": ["OCR"],
                        "Descrição": ["Item da imagem"],
                        "Valor Total": [valor],
                        "Valor Pago": [0.0],
                        "Vencimento": [datetime.now().strftime("%Y-%m-%d")],
                        "Pago": [False]
                    })
                    st.session_state.df_dividas = pd.concat([st.session_state.df_dividas, nova], ignore_index=True)
                    st.rerun()
                else:
                    st.warning("Nenhum valor encontrado.")
                df_imp = None
            if df_imp is not None and not df_imp.empty:
                df_imp["Valor Pago"] = 0.0
                df_imp["Vencimento"] = datetime.now().strftime("%Y-%m-%d")
                df_imp["Pago"] = False
                if st.button("✅ Inserir"):
                    st.session_state.df_dividas = pd.concat([st.session_state.df_dividas, df_imp], ignore_index=True)
                    st.rerun()

        st.divider()
        st.subheader("➕ Nova Dívida")
        with st.form("add_divida"):
            cat = st.text_input("Categoria", "Pessoal")
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
            venc = st.date_input("Vencimento", value=datetime.now() + timedelta(days=15))
            if st.form_submit_button("Adicionar"):
                nova = pd.DataFrame({
                    "Categoria": [cat],
                    "Descrição": [desc],
                    "Valor Total": [valor],
                    "Valor Pago": [0.0],
                    "Vencimento": [venc.strftime("%Y-%m-%d")],
                    "Pago": [False]
                })
                st.session_state.df_dividas = pd.concat([st.session_state.df_dividas, nova], ignore_index=True)
                st.rerun()

        st.divider()
        st.subheader("💰 Pagamento Extra")
        with st.form("extra_divida"):
            extra_valor = st.number_input("Valor pago (R$)", min_value=0.01, step=10.0, format="%.2f")
            if st.form_submit_button("Adicionar ao pago"):
                st.session_state.pagamentos_extras += extra_valor
                st.success(f"Adicionado R$ {extra_valor:.2f} ao total pago!")
                st.rerun()

    # Tabela de dívidas
    st.subheader("📋 Lista de Dívidas")
    df_editado = st.data_editor(
        df_d,
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
        key="editor_d"
    )
    if st.button("💾 Salvar alterações", use_container_width=True, key="save_d"):
        df_novo = st.session_state.editor_d
        df_novo["Valor Pago"] = df_novo.apply(lambda row: row["Valor Total"] if row["Pago"] else 0.0, axis=1)
        st.session_state.df_dividas = df_novo
        st.success("Salvo!")
        st.rerun()

    if len(df_d[~df_d["Pago"]]) > 0:
        if st.button(f"✅ Pagar todas as {len(df_d[~df_d['Pago']])} pendentes", use_container_width=True, key="pagar_tudo_d"):
            df_d.loc[~df_d["Pago"], "Pago"] = True
            df_d.loc[~df_d["Pago"], "Valor Pago"] = df_d.loc[~df_d["Pago"], "Valor Total"]
            st.session_state.df_dividas = df_d
            st.rerun()

    # Gráfico dívidas
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Distribuição")
        cat_data = df_d.groupby("Categoria")["Valor Total"].sum().reset_index()
        if not cat_data.empty:
            fig = go.Figure(data=[go.Pie(labels=cat_data["Categoria"], values=cat_data["Valor Total"], hole=0.5)])
            fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
    with col_g2:
        st.subheader("📈 Pagamento")
        fig = go.Figure(data=[go.Bar(x=["Total","Pago","Restante"], y=[total,pago,restante], marker_color=['#9ca3af','#10b981','#ef4444'])])
        fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

# ==================== ABA 2: METAS ====================
with aba2:
    df_m = st.session_state.df_metas
    total_alvo, total_guardado = calcular_resumo_metas(df_m)

    st.subheader("📊 Resumo das Metas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-label">🎯 Alvo Total</div>
            <div class="metric-value metric-blue">R$ {total_alvo:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-label">💰 Guardado</div>
            <div class="metric-value metric-green">R$ {total_guardado:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        restante_meta = total_alvo - total_guardado
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-label">⏳ Faltam</div>
            <div class="metric-value metric-purple">R$ {restante_meta:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    # Régua da meta
    progresso_m = min(total_guardado / total_alvo, 1.0) if total_alvo > 0 else 0
    st.markdown(f"""
    <div style="margin: 0.5rem 0 1rem;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #6b7280;">
            <span>Progresso da poupança</span>
            <span>R$ {total_guardado:,.2f} / R$ {total_alvo:,.2f} ({progresso_m*100:.0f}%)</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill progress-bar-fill-green" style="width: {min(progresso_m*100, 100)}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar para metas
    with st.sidebar:
        st.divider()
        st.header("🎯 Metas de Poupança")
        st.subheader("➕ Nova Meta")
        with st.form("add_meta"):
            desc_meta = st.text_input("Descrição da Meta")
            valor_alvo = st.number_input("Valor Alvo (R$)", min_value=0.01, step=100.0, format="%.2f")
            if st.form_submit_button("Adicionar Meta"):
                nova_meta = pd.DataFrame({
                    "Descrição": [desc_meta],
                    "Valor Alvo": [valor_alvo],
                    "Valor Guardado": [0.0]
                })
                st.session_state.df_metas = pd.concat([st.session_state.df_metas, nova_meta], ignore_index=True)
                st.rerun()

        st.subheader("💰 Adicionar à Meta")
        with st.form("add_guardado"):
            meta_selecionada = st.selectbox("Selecione a meta", df_m["Descrição"].tolist())
            valor_guardar = st.number_input("Valor a guardar (R$)", min_value=0.01, step=10.0, format="%.2f")
            if st.form_submit_button("Guardar"):
                idx = df_m[df_m["Descrição"] == meta_selecionada].index[0]
                df_m.at[idx, "Valor Guardado"] += valor_guardar
                st.session_state.df_metas = df_m
                st.success(f"R$ {valor_guardar:.2f} guardado para '{meta_selecionada}'")
                st.rerun()

    # Tabela de metas
    st.subheader("📋 Suas Metas")
    df_metas_edit = st.data_editor(
        df_m,
        column_config={
            "Descrição": st.column_config.TextColumn("Descrição"),
            "Valor Alvo": st.column_config.NumberColumn("Valor Alvo", format="R$ %.2f"),
            "Valor Guardado": st.column_config.NumberColumn("Valor Guardado", format="R$ %.2f"),
        },
        use_container_width=True,
        hide_index=True,
        key="editor_m"
    )
    if st.button("💾 Salvar metas", use_container_width=True, key="save_m"):
        st.session_state.df_metas = st.session_state.editor_m
        st.success("Metas salvas!")
        st.rerun()

    # Gráfico de metas
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    if not df_m.empty:
        fig_metas = go.Figure()
        fig_metas.add_trace(go.Bar(
            x=df_m["Descrição"],
            y=df_m["Valor Alvo"],
            name="Alvo",
            marker_color='#3b82f6'
        ))
        fig_metas.add_trace(go.Bar(
            x=df_m["Descrição"],
            y=df_m["Valor Guardado"],
            name="Guardado",
            marker_color='#10b981'
        ))
        fig_metas.update_layout(barmode='group', height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_metas, use_container_width=True)

st.caption("💾 Dados salvos na sessão. Use as abas para alternar entre dívidas e metas.")
