from datetime import datetime as dt
import pandas as pd
import numpy as np
import streamlit as st
from data_processor import DataProcessor, OPERADORAS
from calculations import OnusCalculator
from ui_components import UIComponents

EXPECTED_COLUMNS = [
    "AnoBase",
    "Entidade",
    "NumTermo",
    "AnoTermo",
    "UF",
    "AreaPrestacao",
    "AreaExclusao",
    "MunicipioExclusao",
    "FrequenciaInicial",
    "FrequenciaFinal",
    "FrequenciaCentral",
    "Banda",
    "Tipo",
]

COLUMN_CONFIG = {
    "AnoBase": st.column_config.TextColumn(
        "Ano - Base",
        width=None,
        help="📜Ano - Base",
        disabled=True,
    ),
    "Entidade": st.column_config.TextColumn(
        "Entidade",
        width=None,
        help="📜Entidade",
        disabled=False,
    ),
    "UF": st.column_config.TextColumn(
        "Estado",
        width=None,
        help="📜Estado",
        disabled=True,
    ),
    "AreaPrestacao": st.column_config.TextColumn(
        "Área de Prestação",
        width=None,
        help="📜Área de Prestação",
        disabled=True,
    ),
    "AreaExclusao": st.column_config.TextColumn(
        "Área de Exclusão",
        width=None,
        help="📜Área de Exclusão",
        disabled=True,
    ),
    "MunicipioExclusao": st.column_config.TextColumn(
        "Municípios a Excluir",
        width=None,
        help="📜Municípios a Excluir",
        disabled=True,
    ),
    "FrequenciaInicial": st.column_config.NumberColumn(
        "Frequência Inicial",
        width=None,
        help="📜Frequência Inicial",
        disabled=True,
    ),
    "FrequenciaFinal": st.column_config.NumberColumn(
        "Frequência Final",
        width=None,
        help="📜Frequência Final",
        disabled=True,
    ),
    "FrequenciaCentral": st.column_config.NumberColumn(
        "Frequência Central",
        width=None,
        help="📜Frequência",
        disabled=True,
    ),
    "Banda": st.column_config.NumberColumn(
        "Banda",
        width=None,
        help="📜Banda",
        disabled=True,
    ),
    "Tipo": st.column_config.TextColumn(
        "Tipo",
        width=None,
        help="📜Tipo",
        disabled=True,
    ),
    "AnoTermo": st.column_config.NumberColumn(
        "Ano do Termo",
        width=None,
        help="📜Ano do Termo",
        disabled=False,
    ),
    "NumTermo": st.column_config.TextColumn(
        "Número do Termo",
        width=None,
        help="📜Número do Termo",
        disabled=False,
    ),
}


# Initialize components
data_processor = DataProcessor()
onus_calculator = OnusCalculator(data_processor)
ui = UIComponents()

# Setup page
ui.setup_page()
# Create tabs
aba1, aba2 = st.tabs(["Cadastro/Carregamento", "Cálculo do Ônus"])


def update_df(df=None):
    """Display data in the data editor"""
    if df is None:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    st.session_state.df = df.reset_index(drop=True)


def concat2df(row):
    """Display data in the data editor"""
    if st.session_state.df.empty:
        st.session_state.df = pd.DataFrame(row)
    else:
        st.session_state.df = pd.concat(
            [st.session_state.df, pd.DataFrame(row)], ignore_index=True
        )


@st.fragment
@st.dialog("⚠️Sustituir os dados existentes?")
def confirm_action(uploaded_df):
    if st.button("Sim, substituir dados"):
        update_df(uploaded_df)
        st.rerun()


def input_csv_data():
    """Read CSV data from file"""

    # Read the CSV file
    uploaded_df = pd.read_csv(uploaded_file, dtype="string")

    if missing_columns := [
        col for col in EXPECTED_COLUMNS if col not in uploaded_df.columns
    ]:
        st.error(
            f"O arquivo CSV não contém as seguintes colunas obrigatórias: {', '.join(missing_columns)}"
        )
    else:
        # Keep only the expected columns
        uploaded_df = uploaded_df[EXPECTED_COLUMNS]

        if not st.session_state.df.empty:
            confirm_action(uploaded_df)
        else:
            update_df(uploaded_df)
            st.success("Dados carregados com sucesso!", icon="✅")


uploaded_file = st.sidebar.file_uploader(
    "Carregar dados de um arquivo CSV",
    type="csv",
    key="uploaded_file",
)
if uploaded_file is not None:
    st.sidebar.button("Carregar dados do arquivo CSV", on_click=input_csv_data)

with aba1:
    with st.expander("Adicionar termos manualmente", expanded=True):
        first_row = st.columns(7)
        min, max = data_processor.year_range[0], data_processor.year_range[-1]
        ano = first_row[0].slider(
            "Ano Base Populacional",
            min_value=int(min),
            max_value=int(max),
            value=int(min),
        )
        uf = first_row[1].selectbox(
            "Estado", options=data_processor.get_states_for_year(ano)
        )
        area_prestacao = first_row[2].selectbox(
            "Área de Prestação", options=data_processor.get_service_areas_for_state(uf)
        )
        if not (
            options_exclusao := data_processor.get_exclusion_areas(
                ano, uf, area_prestacao
            )
        ):
            placeholder_exclusao = "Nenhuma área de exclusão disponível"
        else:
            placeholder_exclusao = "Selecione uma ou mais áreas"
        areas_exclusao = first_row[3].multiselect(
            "Áreas de Exclusão",
            options=options_exclusao,
            placeholder=placeholder_exclusao,
            help="As áreas selecionadas serão excluídas da área de prestação.",
            disabled=not options_exclusao,
        )
        municipios_restantes = data_processor.exclude_areas_from_df(
            area_prestacao, ano, uf, ", ".join(areas_exclusao)
        )["Municipio"].unique()

        mun_exclusao = first_row[4].multiselect(
            "Municípios a Excluir",
            options=sorted(municipios_restantes),
            placeholder="Selecione um ou mais municípios",
            help="Os municípios selecionados serão excluídos da área de prestação.",
            disabled=not areas_exclusao,
        )
        freq_inicial = first_row[5].number_input("Frequência Inicial(MHz)", min_value=0)
        freq_final = first_row[6].number_input("Frequência Final(MHz)", min_value=0)
        freq_central = freq_final - (freq_final - freq_inicial) / 2
        banda = freq_final - freq_inicial

        second_row = st.columns(4)
        ano_termo = second_row[0].slider(
            "Ano do Termo", min_value=2005, max_value=dt.now().year
        )
        operadora = second_row[1].selectbox("Operadora", options=OPERADORAS)
        n_termo = second_row[2].text_input("Número do Termo")
        tipo = second_row[3].selectbox("Tipo", options=["ONUS", "DEMAIS"])
        if st.button("Adicionar Termo"):
            if freq_final - freq_inicial <= 0:
                st.error("A frequência final deve ser maior que a inicial!")
            else:
                concat2df(
                    {
                        "AnoBase": [ano],
                        "Entidade": [operadora],
                        "UF": [uf],
                        "AreaPrestacao": [area_prestacao],
                        "AreaExclusao": [", ".join(areas_exclusao)],
                        "MunicipioExclusao": [", ".join(mun_exclusao)],
                        "FrequenciaInicial": [freq_inicial],
                        "FrequenciaFinal": [freq_final],
                        "FrequenciaCentral": [freq_central],
                        "Banda": [banda],
                        "Tipo": [tipo],
                        "AnoTermo": [ano_termo],
                        "NumTermo": [n_termo],
                    }
                )
                st.rerun()
    if "df" not in st.session_state:
        update_df()

    if not st.session_state.df.empty:
        with st.expander("Tabela de Termos Cadastrados (Editável)", expanded=True):
            edited_df = st.data_editor(
                st.session_state.df,
                column_config=COLUMN_CONFIG,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
            )
            update_df(edited_df)

            #     update_df(edited_df)

        # else:
        #     st.session_state.df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    # Generate final dataframe for all terms
    if not st.session_state.df.empty:
        df_termos = data_processor.gerar_tabela_final(st.session_state.df)
        with st.expander("Tabela de Municípios", expanded=True):
            st.dataframe(
                df_termos, use_container_width=True, column_config=COLUMN_CONFIG
            )

with aba2:
    if not st.session_state.df.empty:
        col_a, col_b = st.columns(2, border=True)
        with col_a:
            st.subheader("Dados para o cálculo")
            # Prepare data for calculation
            df_termos["popMun"] = df_termos["popMun"].astype("int")
            df_termos["popUF"] = df_termos["popUF"].astype("int")
            df_termos["coefPop"] = df_termos["popMun"] / df_termos["popUF"]
            # Render ônus controls
            year, entity, state, term, term_year, rol = ui.render_onus_controls(
                df_termos
            )

            # Validate inputs
            is_valid, error_message = onus_calculator.validate_calculation_inputs(
                year, entity, state, term, term_year, rol
            )

            if is_valid:
                # Calculate onus
                onus, df_factors, population_total = onus_calculator.calculate_onus(
                    year, entity, state, term, term_year, rol, df_termos
                )

                with col_b:
                    st.subheader("Estatísticas do cálculo")
                    rowa = st.columns(3)
                    rowa[0].metric("Total de municípios", value=len(df_factors))
                    rowa[1].metric("População total", value=population_total)
                    rowb = st.columns(3)
                    rowb[0].metric(
                        label=f"Ônus Termo: {term}/{term_year}",
                        value=f"R$ {np.round(onus.item(), 2)}",
                    )
                    rowb[1].metric(
                        "Ônus médio por município",
                        value=f"R$ {np.round(onus.item() / len(df_factors), 2)}",
                    )
                    rowb[2].metric(
                        "Ônus por habitante",
                        value=f"R$ {np.round(onus.item() / population_total, 5)}",
                    )

            else:
                st.error(error_message)

        # Render result
        with st.expander("Fatores por Município", expanded=True):
            # Format the dataframe for display
            df_factors["fatorFreq"] = df_factors["fatorFreq"].apply(
                lambda x: f"{x:.4f}"
            )
            df_factors["fatorPop"] = df_factors["fatorPop"].apply(lambda x: f"{x:.6f}")
            df_factors["onusMunicipio"] = df_factors["onusMunicipio"].apply(
                lambda x: f"R$ {x:.2f}"
            )

            st.dataframe(df_factors)

        # Display filtered terms with ability to delete rows
        with st.expander("Termos para a UF selecionada", expanded=False):
            df_terms = st.session_state.df[
                (st.session_state.df["UF"] == state)
                & (st.session_state.df["AnoBase"] == year)
            ]
            st.dataframe(df_terms, column_config=COLUMN_CONFIG)
