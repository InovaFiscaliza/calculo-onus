import streamlit as st

# import folium
# from streamlit_folium import st_folium
from datetime import datetime as dt


class UIComponents:
    """
    Class containing reusable UI components for the application
    """

    @staticmethod
    def setup_page():
        """Configure the page layout and title"""
        st.set_page_config(layout="wide", page_title="Cálculo do Ônus Contratual")
        st.title("Cálculo do Ônus Contratual :vibration_mode:")

    @staticmethod
    def create_tabs():
        """Create the main application tabs"""
        return st.tabs(["Cadastro/Carregamento", "Tabelas", "Mapas", "Cálculo do Ônus"])

    def render_term_form(self, data_source):
        """
        Render the term registration form

        Args:
            data_processor: Instance of DataProcessor

        Returns:
            dict: Form data if submitted, None otherwise
        """
        with st.container(border=True):
            cols = st.columns(13)

            # Year selection
            with cols[0]:
                st.selectbox(
                    "Ano Base Populacional",
                    options=data_source.get_unique_years(),
                    key="input_anoBase",
                )

            # Operator selection
            with cols[1]:
                st.selectbox(
                    "Operadora",
                    options=data_source.get_operators_list(),
                    key="input_entidade",
                )

            # Term number
            with cols[2]:
                st.text_input(
                    "Numero do Termo", key="input_NumTermo", placeholder="Termo"
                )

            # Term year
            with cols[3]:
                listaAno = list(range(2005, dt.now().year))
                st.selectbox("Ano do Termo", key="input_AnoTermo", options=listaAno)

            # State selection
            with cols[4]:
                listaUF = data_source.get_states_for_year(
                    st.session_state.input_anoBase
                )
                st.selectbox("Estado", options=listaUF, key="input_UF")

            # Service area selection
            with cols[5]:
                listaAreas = data_source.get_service_areas_for_state(
                    st.session_state.input_UF
                )
                st.selectbox(
                    "Area de Prestação", options=listaAreas, key="input_areaPrestacao"
                )

            # Exclusion areas selection
            with cols[6]:
                listaAreasExcl = data_source.get_exclusion_areas(
                    st.session_state.input_anoBase,
                    st.session_state.input_UF,
                    st.session_state.input_areaPrestacao,
                )
                st.multiselect(
                    "Areas de Exclusão", options=listaAreasExcl, key="input_areaExcl"
                )

            # Exclusion municipalities selection
            with cols[7]:
                df_service_area = data_source.get_service_area_data(
                    st.session_state.input_anoBase,
                    st.session_state.input_UF,
                    st.session_state.input_areaPrestacao,
                )

                df_after_exclusions = data_source.apply_exclusion_areas(
                    df_service_area,
                    st.session_state.input_areaExcl,
                    st.session_state.input_anoBase,
                    st.session_state.input_UF,
                )

                listaMun_excl = df_after_exclusions["Municipio"].unique()
                st.multiselect(
                    "Exclusao de Municipios",
                    options=listaMun_excl,
                    key="input_munExclusao",
                )

            # Frequency inputs
            with cols[8]:
                st.number_input(
                    "Frequência Inicial(MHz)", key="freq_initial", min_value=0
                )

            with cols[9]:
                st.number_input("Frequência Final(MHz)", key="freq_final", min_value=0)

            with cols[10]:
                freq_central = (
                    st.session_state.freq_final
                    - (st.session_state.freq_final - st.session_state.freq_initial) / 2
                )
                st.number_input(
                    "Frequência Central",
                    key="FrequenciaCentral",
                    value=freq_central,
                    disabled=True,
                )

            with cols[11]:
                bandwidth = st.session_state.freq_final - st.session_state.freq_initial
                st.number_input("Banda(MHz)", key="BW", value=bandwidth, disabled=True)

            # Term type
            with cols[12]:
                st.selectbox("Tipo", options=["ONUS", "DEMAIS"], key="input_tipo")

            # Submit button
            with cols[0]:
                if st.button("Aplicar", key="buttonTermo"):
                    # Validate frequency values
                    if st.session_state.freq_initial <= 0:
                        st.error("A frequência inicial deve ser maior que zero.")
                        return None
                    if st.session_state.freq_final <= 0:
                        st.error("A frequência final deve ser maior que zero.")
                        return None
                    if st.session_state.freq_final <= st.session_state.freq_initial:
                        st.error(
                            "A frequência final deve ser maior que a frequência inicial."
                        )
                        return None

                    return {
                        "AnoBase": st.session_state.input_anoBase,
                        "Entidade": st.session_state.input_entidade,
                        "NumTermo": st.session_state.input_NumTermo,
                        "AnoTermo": st.session_state.input_AnoTermo,
                        "UF": st.session_state.input_UF,
                        "AreaPrestacao": st.session_state.input_areaPrestacao,
                        "AreaExclusao": "; ".join(st.session_state.input_areaExcl),
                        "MunicipioExclusao": "; ".join(
                            st.session_state.input_munExclusao
                        ),
                        "FrequenciaInicial": st.session_state.freq_initial,
                        "FrequenciaFinal": st.session_state.freq_final,
                        "FrequenciaCentral": freq_central,
                        "Banda": bandwidth,
                        "Tipo": st.session_state.input_tipo,
                    }

            return None

    def render_terms_editor(self, df_terms):
        """
        Render the terms data editor

        Args:
            df_terms: DataFrame with terms data

        Returns:
            list: Deleted row indices, if any
        """
        df_terms_copy = df_terms.copy()
        df_terms_copy.reset_index(drop=True, inplace=True)

        st.data_editor(
            df_terms_copy,
            num_rows="dynamic",
            key="dfTermoFinal",
            use_container_width=True,
            height=300,
        )

        return st.session_state.dfTermoFinal.get("deleted_rows", [])

    @staticmethod
    def render_tables_tab(df_terms, df_municipalities):
        """Render the tables tab content"""
        with st.container():
            st.subheader("Tabela de Termos Cadastrados")
            st.dataframe(df_terms, use_container_width=True)

            st.subheader("Tabela de Municípios")
            st.dataframe(df_municipalities, use_container_width=True)

    @staticmethod
    def render_map_controls(df_terms_atual):
        """
        Render map controls

        Args:
            df_terms_atual: DataFrame with terms data

        Returns:
            tuple: Selected term, year, state, service area, and municipality codes
        """
        col31, col32, col33, col34, col35 = st.columns(5)

        # Only show map controls if terms have been added
        if df_terms_atual is not None and not df_terms_atual.empty:
            with col31:
                # Select term
                terms = df_terms_atual["NumTermo"].unique()
                term_map = st.selectbox("Termo", options=terms, key="inp_termoMapa")
                df_term_map = df_terms_atual[df_terms_atual["NumTermo"] == term_map]

            with col32:
                # Select year
                years = df_term_map["AnoTermo"].unique()
                year_map = st.selectbox("Ano", options=years, key="inp_anoMapa")
                df_year_map = df_term_map[df_term_map["AnoTermo"] == year_map]

            with col33:
                # Select state
                states = df_year_map["UF"].unique()
                state_map = st.selectbox("UF", options=states, key="inp_UFmapa")
                df_state_map = df_year_map[df_year_map["UF"] == state_map]

            with col34:
                # Select service area
                areas = df_state_map["AreaPrestacao"].unique()
                area_map = st.selectbox(
                    "Área de Prestação", options=areas, key="inp_AreaPrestMapa"
                )
                df_area_map = df_state_map[df_state_map["AreaPrestacao"] == area_map]

                # Format frequency range for display
                df_area_map_freq = df_area_map.copy()
                df_area_map_freq["FrequenciaInicial"] = df_area_map[
                    "FrequenciaInicial"
                ].astype("string")
                df_area_map_freq["FrequenciaFinal"] = df_area_map[
                    "FrequenciaFinal"
                ].astype("string")
                df_area_map_freq["Faixa"] = (
                    df_area_map_freq["FrequenciaInicial"]
                    + " - "
                    + df_area_map_freq["FrequenciaFinal"]
                )

            with col35:
                # Select frequency range
                freq_ranges = df_area_map_freq["Faixa"].unique()
                freq_map = st.selectbox(
                    "Frequência Inicial", options=freq_ranges, key="inp_FreqMapa"
                )
                df_freq_map = df_area_map_freq[df_area_map_freq["Faixa"] == freq_map]

                # Get list of municipality codes for the map
                mun_codes_map = df_freq_map["codMun"].unique()
                mun_codes_map = [str(i) for i in mun_codes_map]

                return term_map, year_map, state_map, area_map, mun_codes_map

        else:
            st.info(
                "Adicione termos na aba 'Cadastro/Carregamento' para visualizar o mapa."
            )
            return None, None, None, None, None

    # @staticmethod
    # def render_map(state, mun_codes):
    #     """
    #     Render the map for a specific state and municipalities

    #     Args:
    #         state: State code (UF)
    #         mun_codes: List of municipality codes to highlight

    #     Returns:
    #         None
    #     """
    #     import geopandas as gpd

    #     try:
    #         # Load map data
    #         map_data = gpd.read_file(Path(__file__).parent / f"SHP_UFs/{state}.shp")

    #         if map_data is not None:
    #             # Create GeoDataFrame
    #             geo_df = gpd.GeoDataFrame(
    #                 map_data, geometry="geometry", crs="EPSG:3857"
    #             )

    #             # Filter for selected municipalities
    #             geo_df_area = geo_df[geo_df["geocodigo"].isin(mun_codes)]

    #             # Get map bounds
    #             lon_min, lat_min, lon_max, lat_max = map_data.total_bounds

    #             # Create Folium map
    #             map_folium = folium.Map(
    #                 location=[-15.8, -47.8],
    #                 no_touch=True,
    #                 tiles="openstreetmap",
    #                 control_scale=True,
    #                 crs="EPSG3857",
    #                 zoom_start=4,
    #                 key="mapaBase",
    #                 prefer_canvas=False,
    #                 max_bounds=True,
    #                 tooltip="tooltip",
    #             )
    #             map_folium.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])

    #             # Add feature groups
    #             group_map = folium.FeatureGroup(name="grupoMapa").add_to(map_folium)

    #             # Add state boundaries
    #             pol_sim_geo = gpd.GeoDataFrame(geo_df["geometry"]).simplify(
    #                 tolerance=0.01
    #             )
    #             pol_geo_json = pol_sim_geo.to_json()
    #             pol_geo = folium.GeoJson(
    #                 data=pol_geo_json,
    #                 style_function=lambda x: {
    #                     "fillColor": "#FF0000",
    #                     "fillOpacity": 0.2,
    #                     "weight": 0.2,
    #                     "color": "#B00000",
    #                 },
    #             )

    #             # Add service area
    #             pol_sim_geo_term = gpd.GeoDataFrame(geo_df_area["geometry"]).simplify(
    #                 tolerance=0.01
    #             )
    #             pol_geo_json_term = pol_sim_geo_term.to_json()
    #             pol_geo_term = folium.GeoJson(
    #                 data=pol_geo_json_term,
    #                 style_function=lambda x: {
    #                     "fillColor": "#4AC423",
    #                     "color": "#1C5727",
    #                     "fillOpacity": 0.5,
    #                     "weight": 0.5,
    #                 },
    #             )

    #             # Add layers to map
    #             group_map.add_child(pol_geo_term)
    #             group_map.add_child(pol_geo)

    #             # Display the map
    #             st_folium(
    #                 map_folium,
    #                 feature_group_to_add=group_map,
    #                 returned_objects=[],
    #                 zoom=4,
    #                 width=1200,
    #                 height=600,
    #             )
    #     except Exception as e:
    #         st.error(f"Erro ao carregar o mapa: {e}")

    @staticmethod
    def render_onus_controls(df_data):
        """
        Render controls for ônus calculation

        Args:
            df_data: DataFrame with terms data

        Returns:
            tuple: Selected year, entity, state, term, term year, and ROL
        """
        colA, colB, colC = st.columns(3)

        with colA:
            # Select population base year
            years = df_data["AnoBase"].unique()
            year = st.selectbox(
                "Ano da Base Populacional", options=years, key="anoBasePop"
            )

        with colB:
            # Select entity
            df_year = df_data[df_data["AnoBase"] == year]
            entities = df_year["Entidade"].unique()
            entity = st.selectbox("Operadora", options=entities, key="entidadeOnus")

        with colC:
            # Select state
            # Select state
            df_entity = df_year[df_year["Entidade"] == entity]
            states = df_entity["UF"].unique()
            state = st.selectbox("Estado", options=states, key="anoBaseUF")

        colD, colE, colF = st.columns(3)

        with colD:
            # Select term
            df_state = df_entity[df_entity["UF"] == state]
            terms = df_state["NumTermo"].unique()
            term = st.selectbox("Termo", options=terms, key="inp_TermoOnus")

        with colE:
            # Select term year
            df_term = df_state[df_state["NumTermo"] == term]
            term_years = df_term["AnoTermo"].unique()
            term_year = st.selectbox(
                "Ano do Termo", options=term_years, key="inp_AnoOnus"
            )

        with colF:
            # Input ROL
            rol = st.number_input(
                "Receita Operacional Líquida (ROL) da UF", value=1000000.00
            )

        return year, entity, state, term, term_year, rol

    @staticmethod
    def render_onus_result(df_factors):
        """
        Render the ônus calculation result

        Args:
            onus_value: Calculated ônus value
            df_factors: DataFrame with municipality factors
            population_total: Total population
        """

        # Display factors table with formatting
        if not df_factors.empty:
            st.subheader("Fatores por Município")

            # Format the dataframe for display
            df_factors["fatorFreq"] = df_factors["fatorFreq"].apply(
                lambda x: f"{x:.4f}"
            )
            df_factors["fatorPop"] = df_factors["fatorPop"].apply(lambda x: f"{x:.6f}")
            df_factors["onusMunicipio"] = df_factors["onusMunicipio"].apply(
                lambda x: f"R$ {x:.2f}"
            )

            st.dataframe(df_factors)

    @staticmethod
    def render_terms_filter(df_terms, year, state):
        """
        Render an editable filtered view of terms

        Args:
            df_terms: DataFrame with terms
            year: Year to filter by
            state: State to filter by
        """
        df_terms_filtered = df_terms.copy()

        if year:
            df_terms_filtered = df_terms_filtered[df_terms_filtered["AnoBase"] == year]

        if state:
            df_terms_filtered = df_terms_filtered[df_terms_filtered["UF"] == state]

        # Use data_editor instead of dataframe
        edited_df = st.data_editor(
            df_terms_filtered,
            num_rows="dynamic",
            use_container_width=True,
            key="terms_editor",
        )

        # Check for deleted rows
        if len(edited_df) < len(df_terms_filtered):
            deleted_indices = set(df_terms_filtered.index) - set(edited_df.index)
            return list(deleted_indices)

        return None
