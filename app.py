import streamlit as str_ui
import pandas as pd
import plotly.express as px
import os
import datetime
from database.connection import SessionLocal, init_db
from controllers.app_controller import AppController

init_db()
str_ui.set_page_config(page_title="Vision & Speech AI", layout="wide")

if "db" not in str_ui.session_state:
    str_ui.session_state.db = SessionLocal()

controller = AppController(str_ui.session_state.db)

str_ui.title("🎛️ Plataforma Avançada de Visão Computacional & Speech-to-Text")
str_ui.markdown("---")

str_ui.sidebar.header("🔌 Status de Conexão")
if str_ui.session_state.db.bind.url.host:
    str_ui.sidebar.success(f"Conectado ao Banco: \n`{str_ui.session_state.db.bind.url.host}`")
else:
    str_ui.sidebar.warning("Rodando em Banco Local (Fallback SQLite).")

menu = str_ui.sidebar.radio("Navegação do Sistema", ["Real-time Capture", "Histórico & Analytics"])

if menu == "Real-time Capture":
    str_ui.header("📸 Captura de Mídia Integrada")
    col1, col2 = str_ui.columns(2)

    with col1:
        str_ui.subheader("Webcam Input")
        camera_photo = str_ui.camera_input("Foque no objetivo e capture a foto")
        str_ui.subheader("Comentário em Áudio")
        audio_file = str_ui.file_uploader("Opcional: Suba uma gravação (.wav)", type=["wav"])

    with col2:
        if camera_photo:
            str_ui.subheader("Visualização da Foto")
            str_ui.image(camera_photo, caption="Captura Pronta", use_column_width=True)
            if str_ui.button("⚡ Executar Pipeline de Processamento Automatizado"):
                with str_ui.spinner("Analisando frames..."):
                    img_bytes = camera_photo.getvalue()
                    aud_bytes = audio_file.getvalue() if audio_file else None
                    registro = controller.processar_fluxo_completo(img_bytes, aud_bytes)
                    str_ui.success("Análise persistida com sucesso!")
                    str_ui.json(registro.json_resultado)
                    if registro.transcricao:
                        str_ui.info(f"🗣️ Transcrição: {registro.transcricao}")
else:
    str_ui.header("📊 Painel Analítico & Histórico")
    col_f1, col_f2, col_f3 = str_ui.columns(3)
    with col_f1:
        search_query = str_ui.text_input("🔍 Buscar texto")
    with col_f2:
        start_d = str_ui.date_input("Data de Início", datetime.date.today() - datetime.timedelta(days=7))
    with col_f3:
        end_d = str_ui.date_input("Data Fim", datetime.date.today())

    registros = controller.listar_historico(search_query, start_d, end_d)
    if registros:
        data_dicts = [{"Data": r.created_at, "Pessoas": r.quantidade_pessoas, "Rostos": r.rostos, "Luminosidade": r.luminosidade, "Nitidez": r.nitidez} for r in registros]
        df = pd.DataFrame(data_dicts)
        
        db_col1, db_col2 = str_ui.columns(2)
        with db_col1:
            str_ui.plotly_chart(px.line(df, x="Data", y="Pessoas", title="Contagem Volumétrica"), use_container_width=True)
        with db_col2:
            str_ui.plotly_chart(px.histogram(df, x="Luminosidade", title="Luminosidade"), use_container_width=True)

        str_ui.subheader("💾 Exportação de Dados")
        exp_col1, exp_col2 = str_ui.columns(2)
        with exp_col1:
            str_ui.download_button("Exportar em CSV", data=df.to_csv(index=False), file_name="historico.csv", mime="text/csv")
        with exp_col2:
            str_ui.download_button("Exportar em JSON", data=df.to_json(orient="records"), file_name="historico.json", mime="application/json")

        for reg in registros:
            with str_ui.expander(f"Registro #{reg.id} - {reg.created_at.strftime('%d/%m/%Y %H:%M:%S')}"):
                c1, c2 = str_ui.columns([1, 2])
                with c1:
                    if os.path.exists(reg.image_path):
                        str_ui.image(reg.image_path, use_column_width=True)
                with c2:
                    str_ui.write(f"**Descrição:** {reg.descricao}")
                    str_ui.write(f"**Objetos:** {reg.objetos}")
                    if reg.transcricao:
                        str_ui.info(f"🗣️ Transcrição: {reg.transcricao}")
                    if str_ui.button(f"🗑️ Excluir Registro #{reg.id}", key=f"del_{reg.id}"):
                        controller.deletar_registro(reg.id)
                        str_ui.rerun()
