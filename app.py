import streamlit as st
import pandas as pd
import re
import time

st.set_page_config(layout="wide")

# =========================
# 🎨 OCULTAR APENAS GITHUB
# =========================
st.markdown("""
<style>

/* 🔥 Esconde botão Fork + GitHub */
button[title="Fork this app"],
button[aria-label="Fork this app"] {
    display: none !important;
}

/* 🔥 fallback geral (pega o container do header direito) */
header div:has(svg) {
    display: none !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# 🔐 SENHAS (SECRETS)
# =========================
USER_PASSWORD = st.secrets["USER_PASSWORD"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# =========================
# 🔐 CONTROLE DE ACESSO
# =========================
if "acesso" not in st.session_state:
    st.session_state.acesso = None

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
# 📦 ESTADO INICIAL
# =========================
def init_state():
    defaults = {
        "pagina": "prova",
        "indice": 0,
        "respostas": {},
        "finalizado": False,
        "timer_inicio": None,
        "timer_ativo": False,
        "resultado": None
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================
# 🔧 FUNÇÕES
# =========================
def limpar(txt):
    if pd.isna(txt):
        return ""
    return re.sub(r"\s+", " ", str(txt)).strip()

def formatar(seg):
    h = seg // 3600
    m = (seg % 3600) // 60
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def calcular_tempo():
    total = 3 * 60 * 60

    if st.session_state.timer_ativo:
        passado = int(time.time() - st.session_state.timer_inicio)
        restante = max(0, total - passado)
    else:
        restante = total

    return restante, total

# =========================
# 📊 CARREGAR PERGUNTAS
# =========================
df = pd.read_excel("Perguntas.xlsx")
df.columns = df.columns.str.strip()

questoes = []
for _, row in df.iterrows():
    questoes.append({
        "pergunta": limpar(row["PERGUNTA"]),
        "opcoes": [limpar(row[c]) for c in ["A","B","C","D","E"]],
        "resposta": limpar(row["RESPOSTA"])
    })

# =========================
# 🏁 FINALIZAR PROVA
# =========================
def finalizar():
    acertos = sum(
        1 for i, r in st.session_state.respostas.items()
        if r == questoes[i]["resposta"]
    )

    total = len(questoes)
    nota = (acertos / total) * 10

    st.session_state.resultado = {
        "nota": round(nota, 1),
        "acertos": acertos,
        "total": total
    }

    st.session_state.finalizado = True

# =========================
# 🎯 LAYOUT
# =========================
col1, col2, col3 = st.columns([1.2, 4, 1.6])

# =========================
# 📘 MENU
# =========================
with col1:
    st.markdown("## 📘 Menu")

    if st.button("🏠 Iniciar Prova"):
        st.session_state.pagina = "prova"

    if st.button("📊 Resultados"):
        st.session_state.pagina = "resultado"

    if st.session_state.acesso == "admin":
        st.markdown("---")
        st.success("🔐 ADMIN")

# =========================
# 📄 CONTEÚDO
# =========================
with col2:

    if st.session_state.pagina == "prova":

        idx = st.session_state.indice
        q = questoes[idx]
        total = len(questoes)

        st.markdown("### Simulador de Provas")

        restante, total_tempo = calcular_tempo()

        # 🔥 COR DINÂMICA DO TEMPO
        cor = "red" if restante < 600 else "white"

        st.markdown(f"<h3 style='color:{cor}'>⏱️ {formatar(restante)}</h3>", unsafe_allow_html=True)
        st.progress(restante / total_tempo)

        if restante == 0 and not st.session_state.finalizado:
            finalizar()

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
                if st.button("🏁 Finalizar Prova"):
                    finalizar()
            else:
                if st.button("🔁 Refazer Prova"):
                    st.session_state.respostas = {}
                    st.session_state.finalizado = False
                    st.session_state.indice = 0
                    st.session_state.timer_ativo = False

        with c3:
            if st.button("➡ Próxima") and idx < total-1:
                st.session_state.indice += 1
                st.rerun()

        # =========================
        # 📊 RESULTADO IMEDIATO
        # =========================
        if st.session_state.finalizado:
            r = st.session_state.resultado

            st.success(f"Nota: {r['nota']}")
            st.write(f"Acertos: {r['acertos']} de {r['total']}")

            st.markdown("### 📋 Revisão")

            for i, q in enumerate(questoes):
                user = st.session_state.respostas.get(i)
                correta = q["resposta"]

                if user == correta:
                    st.success(f"{i+1}. Correta ({correta})")
                else:
                    st.error(f"{i+1}. Errada (Sua: {user} | Correta: {correta})")

# =========================
# 🔢 NAVEGAÇÃO
# =========================
with col3:

    st.markdown("### Navegação")

    total = len(questoes)
    cols = 5

    for i in range(0, total, cols):
        linhas = st.columns(cols)

        for j, idx in enumerate(range(i, min(i+cols, total))):
            with linhas[j]:
                if st.button(str(idx+1)):
                    st.session_state.indice = idx
                    st.rerun()
                    
