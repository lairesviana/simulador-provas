import streamlit as st
import pandas as pd
import re
import datetime
import time

st.set_page_config(layout="wide")

# =========================
# 🔐 CONTROLE DE ACESSO
# =========================
TOKEN_VALIDO = st.secrets["TOKEN"]

if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False

params = st.query_params

# 1️⃣ Se veio pelo link com token → libera direto
if "token" in params and params["token"] == TOKEN_VALIDO:
    st.session_state.acesso_liberado = True

# 2️⃣ Se ainda não liberado → mostra login e PARA TUDO
if not st.session_state.acesso_liberado:

    st.markdown("## 🔒 Acesso restrito")

    senha = st.text_input("Digite a senha de acesso", type="password")

    if senha == TOKEN_VALIDO:
        st.session_state.acesso_liberado = True
        st.rerun()
    else:
        st.stop()

# 👉 A PARTIR DAQUI O APP NORMAL (SEM INTERFERÊNCIA)

# =========================
# ESTADO GLOBAL
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
    duracao_total = 3 * 60 * 60

    if st.session_state.timer_ativo:
        tempo_passado = int(time.time() - st.session_state.timer_inicio)
        tempo_restante = max(0, duracao_total - tempo_passado)
    else:
        tempo_restante = duracao_total

    return tempo_restante, duracao_total

def formatar_tempo(seg):
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def cor_tempo(seg):
    if seg < 600:
        return "#ff4b4b"
    elif seg < 1800:
        return "#facc15"
    else:
        return "var(--text-color)"

# =========================
# AÇÕES
# =========================
def finalizar_prova(auto=False):
    acertos = sum(
        1 for i, r in st.session_state.respostas.items()
        if r == questoes[i]["resposta"]
    )

    total = len(questoes)
    nota = (acertos / total) * 10

    resultado = {
        "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "nota": round(nota, 1),
        "acertos": acertos,
        "total": total,
        "modo": "Tempo esgotado" if auto else "Finalizado"
    }

    st.session_state.historico.append(resultado)
    st.session_state.ultimo_resultado = resultado
    st.session_state.finalizado = True

def refazer_prova():
    st.session_state.respostas = {}
    st.session_state.indice = 0
    st.session_state.finalizado = False
    st.session_state.timer_inicio = None
    st.session_state.timer_ativo = False

# =========================
# LOAD
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
# LAYOUT
# =========================
col1, col2, col3 = st.columns([1.2, 4, 1.6])

# =========================
# MENU
# =========================
with col1:
    st.markdown("## 📘 Menu")

    if st.button("🏠 Iniciar Prova", use_container_width=True):
        st.session_state.pagina = "prova"

    if st.button("📊 Resultados", use_container_width=True):
        st.session_state.pagina = "resultado"

# =========================
# CONTEÚDO
# =========================
with col2:

    if st.session_state.pagina == "prova":

        idx = st.session_state.indice
        q = questoes[idx]
        total = len(questoes)

        st.markdown("### Simulador de Provas")

        tempo_restante, total_tempo = calcular_tempo()

        st.markdown(
            f"<div style='text-align:right; font-size:20px; color:{cor_tempo(tempo_restante)};'>⏱️ {formatar_tempo(tempo_restante)}</div>",
            unsafe_allow_html=True
        )

        st.progress(tempo_restante / total_tempo)

        if tempo_restante == 0 and not st.session_state.finalizado:
            finalizar_prova(auto=True)
            st.rerun()

        st.write(f"Questão {idx+1} de {total}")
        st.progress(len(st.session_state.respostas)/total)

        st.write(q["pergunta"])

        letras = ["A","B","C","D","E"]
        opcoes = [f"{letras[i]}) {q['opcoes'][i]}" for i in range(5)]

        resposta = st.session_state.respostas.get(idx)
        index = letras.index(resposta) if resposta else None

        escolha = st.radio("", opcoes, index=index, disabled=st.session_state.finalizado)

        if escolha and not st.session_state.finalizado:
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
                if st.button("🏁 Finalizar Prova"):
                    finalizar_prova()
            else:
                if st.button("🔁 Refazer Prova"):
                    refazer_prova()

        with c3:
            if st.button("Próxima ➡") and idx < total-1:
                st.session_state.indice += 1
                st.rerun()

        if st.session_state.finalizado:

            r = st.session_state.ultimo_resultado

            st.markdown("## 📊 Resultado Final")
            st.success(f"Nota: {r['nota']:.1f}")
            st.write(f"Acertos: {r['acertos']} / {r['total']}")
            st.write(f"Modo: {r['modo']}")
            st.write(f"Data: {r['data']}")

    elif st.session_state.pagina == "resultado":

        st.markdown("## 📊 Histórico")

        if st.session_state.historico:
            st.dataframe(pd.DataFrame(st.session_state.historico))
        else:
            st.info("Nenhuma prova realizada.")

# =========================
# NAVEGAÇÃO
# =========================
with col3:

    if st.session_state.pagina == "prova":

        st.markdown("### Navegação")

        total = len(questoes)
        cols_por_linha = 5

        linhas = [
            list(range(i, min(i+cols_por_linha, total)))
            for i in range(0, total, cols_por_linha)
        ]

        for linha in linhas:
            cols = st.columns(cols_por_linha)

            for j, i in enumerate(linha):
                with cols[j]:
                    if st.button(str(i+1), key=f"nav_{i}"):
                        st.session_state.indice = i
                        st.rerun()
                        
