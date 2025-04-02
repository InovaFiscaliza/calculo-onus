import pandas as pd
import streamlit as st
from data_processor import DataProcessor
from calculations import OnusCalculator
from ui_components import UIComponents

# Initialize components
data_processor = DataProcessor()
onus_calculator = OnusCalculator(data_processor)
ui = UIComponents()

# Setup page
ui.setup_page()

# Initialize session state for storing terms
if "df_TermosPrg" not in st.session_state:
    st.session_state.df_TermosPrg = pd.DataFrame(
        {
            "AnoBase": [],
            "Entidade": [],
            "NumTermo": [],
            "AnoTermo": [],
            "UF": [],
            "areaPrestacao": [],
            "areaExclusao": [],
            "munExclusao": [],
            "freqInicial": [],
            "freqFinal": [],
            "Freq": [],
            "Banda": [],
            "Tipo": [],
        }
    )

# Create tabs
aba1, aba2, aba3, aba4 = ui.create_tabs()

# Tab 1: Registration and Loading
with aba1:
    if form_data := ui.render_term_form(data_processor):
        new_term = pd.DataFrame([form_data])
        st.session_state.df_TermosPrg = pd.concat(
            [st.session_state.df_TermosPrg, new_term]
        )
        ui.render_success_message("Termo adicionado com sucesso!")

    if deleted_rows := ui.render_terms_editor(st.session_state.df_TermosPrg):
        st.session_state.df_TermosPrg.drop(deleted_rows, inplace=True)

    # Generate final dataframe for all terms
    if not st.session_state.df_TermosPrg.empty:
        dfTermos_Atual = pd.DataFrame()

        for i in list(st.session_state.df_TermosPrg.index):
            term = st.session_state.df_TermosPrg.loc[i]
            df_term = data_processor.generate_final_df(
                term["AnoBase"],
                term["Entidade"],
                term["NumTermo"],
                term["AnoTermo"],
                term["UF"],
                term["areaPrestacao"],
                term["areaExclusao"],
                term["munExclusao"],
                term["freqInicial"],
                term["freqFinal"],
                term["Freq"],
                term["Banda"],
                term["Tipo"],
            )
            dfTermos_Atual = pd.concat([dfTermos_Atual, df_term])

        # Store in session state for use in other tabs
        st.session_state.dfTermos_Atual = dfTermos_Atual

# Tab 2: Tables
with aba2:
    if "dfTermos_Atual" in st.session_state:
        ui.render_tables_tab(
            st.session_state.df_TermosPrg, st.session_state.dfTermos_Atual
        )
    else:
        ui.render_info_message(
            "Adicione termos na aba 'Cadastro/Carregamento' para visualizar as tabelas."
        )

# Tab 3: Maps
with aba3:
    st.subheader(":large_green_square: Área de Prestação")

    with st.container(height=100):
        # Render map controls
        if "dfTermos_Atual" in st.session_state:
            term_map, year_map, state_map, area_map, mun_codes_map = (
                ui.render_map_controls(st.session_state.dfTermos_Atual)
            )

            # Render map if all selections are made
            if all([term_map, year_map, state_map, area_map, mun_codes_map]):
                with st.container(height=600, border=False):
                    ui.render_map(state_map, mun_codes_map)
        else:
            ui.render_info_message(
                "Adicione termos na aba 'Cadastro/Carregamento' para visualizar o mapa."
            )

# Tab 4: Onus Calculation
with aba4:
    try:
        with st.container(height=450):
            # Only show calculation controls if terms have been added
            if (
                "dfTermos_Atual" in st.session_state
                and not st.session_state.dfTermos_Atual.empty
            ):
                # Prepare data for calculation
                df_data = st.session_state.dfTermos_Atual.copy()
                df_data["popMun"] = df_data["popMun"].astype(int)
                df_data["popUF"] = df_data["popUF"].astype(int)
                df_data["coefPop"] = df_data["popMun"] / df_data["popUF"]

                st.subheader("Cálculo do ônus")
                st.divider()

                # Render ônus controls
                year, entity, state, term, term_year, rol = ui.render_onus_controls(
                    df_data
                )

                # Validate inputs
                is_valid, error_message = onus_calculator.validate_calculation_inputs(
                    year, entity, state, term, term_year, rol
                )

                if is_valid:
                    # Calculate onus
                    onus, df_factors, population_total = onus_calculator.calculate_onus(
                        year, entity, state, term, term_year, rol, df_data
                    )

                    # Render result
                    ui.render_onus_result(onus, df_factors, population_total)

                    # Display filtered terms
                    st.subheader("Termos para a UF selecionada")
                    ui.render_terms_filter(st.session_state.df_TermosPrg, year, state)
                else:
                    ui.render_error_message(error_message)
            else:
                ui.render_info_message(
                    "Adicione termos na aba 'Cadastro/Carregamento' para calcular o ônus."
                )
    except Exception as e:
        ui.render_error_message(f"Erro ao calcular o ônus: {e}")
