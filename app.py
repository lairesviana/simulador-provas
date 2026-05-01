import streamlit as st
import pandas as pd
import re
import datetime
import time

st.set_page_config(layout="wide")

# =========================
# 🔐 SEGURANÇA
# =========================
USER_PASSWORD = st.secrets["USER_PASSWORD"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

if "acesso" not in st.session_state:
    st.session_state.acesso = None  # None, "user", "admin"

# =========================
# 🔑 LOGIN
# =========================
if st.session_state.acesso is None:

    st.markdown("## 🔒 Acesso ao Sistema")

    senha = st.text_input("Digite a senha", type="password")

    if senha:
        if senha == ADMIN_PASSWORD:
            st.session_state.acesso = "admin"
            st.rerun()

        elif senha == USER_PASSWORD:
            st.session_state.acesso = "user"
            st.rerun()

        else:
            st.error("Senha inválida")

    st.stop()

# =========================
# ESTADO
# =========================
def init_state():
    defaults = {
        "pagina": "prova",
        "indice": 0,
        "respostas": {},
        "historico": [],
        "finalizado": False,
        "timer_inicio": None,
        "timer_ativo": False,
        "ultimo_resultado": None
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================
# UTIL
# =========================
def limpar(texto):
    if pd.isna(texto):
        return ""
    return re.sub(r"\s+", " ", str(texto)).strip()

# =========================
# TIMER
# =========================
def calcular_tempo():
    total = 3 * 60 * 60

    if st.session_state.timer_ativo:
        passado = int(time.time() - st.session_state.timer_inicio)
        restante = max(0, total - passado)
    else:
        restante = total

    return restante, total

def formatar(seg):
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# =========================
# LOAD EXCEL
# =========================
df = pd.read_excel("Perguntas.xlsx")
df.columns = df.columns.str.strip()

questoes = [
    {
        "pergunta": limpar(r["PERGUNTA"]),
        "opcoes": [limpar(r[c]) for c in ["A","B","C","D","E"]],
        "resposta": limpar(r["RESPOSTA"])
    }
    for _, r in df.iterrows()
]

# =========================
# FINALIZAR
# =========================
def finalizar():
    acertos = sum(
        1 for i, r in st.session_state.respostas.items()
        if r == questoes[i]["resposta"]
    )

    total = len(questoes)
    nota = (acertos / total) * 10

    resultado = {
        "nota": round(nota, 1),
        "acertos": acertos,
        "total": total
    }

    st.session_state.ultimo_resultado = resultado
    st.session_state.finalizado = True

# =========================
# LAYOUT
# =========================
col1, col2, col3 = st.columns([1.2, 4, 1.6])

# =========================
# MENU
# =========================
with col1:
    st.markdown("## 📘 Menu")

    if st.button("🏠 Iniciar Prova"):
        st.session_state.pagina = "prova"

    if st.button("📊 Resultados"):
        st.session_state.pagina = "resultado"

    # 🔥 VISÍVEL SÓ PARA ADMIN
    if st.session_state.acesso == "admin":
        st.markdown("---")
        st.success("Modo ADMIN ativado")

# =========================
# CONTEÚDO
# =========================
with col2:

    if st.session_state.pagina == "prova":

        idx = st.session_state.indice
        q = questoes[idx]
        total = len(questoes)

        st.markdown("### Simulador de Provas")

        restante, total_tempo = calcular_tempo()

        st.write(f"⏱️ {formatar(restante)}")
        st.progress(restante / total_tempo)

        st.write(f"Questão {idx+1} de {total}")
        st.progress(len(st.session_state.respostas)/total)

        st.write(q["pergunta"])

        letras = ["A","B","C","D","E"]
        opcoes = [f"{letras[i]}) {q['opcoes'][i]}" for i in range(5)]

        resposta = st.session_state.respostas.get(idx)
        index = letras.index(resposta) if resposta else None

        escolha = st.radio("", opcoes, index=index)

        if escolha:
            st.session_state.respostas[idx] = escolha[0]

            if not st.session_state.timer_ativo:
                st.session_state.timer_inicio = time.time()
                st.session_state.timer_ativo = True

        st.markdown("---")

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("⬅ Anterior") and idx > 0:
                st.session_state.indice -= 1
                st.rerun()

        with c2:
            if not st.session_state.finalizado:
                if st.button("🏁 Finalizar"):
                    finalizar()
            else:
                if st.button("🔁 Refazer"):
                    st.session_state.respostas = {}
                    st.session_state.finalizado = False
                    st.session_state.indice = 0

        with c3:
            if st.button("➡ Próxima") and idx < total-1:
                st.session_state.indice += 1
                st.rerun()

        if st.session_state.finalizado:
            r = st.session_state.ultimo_resultado
            st.success(f"Nota: {r['nota']}")
            st.write(f"Acertos: {r['acertos']}/{r['total']}")

# =========================
# NAVEGAÇÃO
# =========================
with col3:

    st.markdown("### Navegação")

    total = len(questoes)
    colunas = 5

    for i in range(0, total, colunas):
        cols = st.columns(colunas)
        for j, idx in enumerate(range(i, min(i+colunas, total))):
            with cols[j]:
                if st.button(str(idx+1)):
                    st.session_state.indice = idx
                    st.rerun()
                    
