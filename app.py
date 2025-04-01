import pandas as pd
import folium
import streamlit as st
import datetime as dt
from streamlit_folium import st_folium
from data_processor import DataProcessor

# In app.py, add the import for OnusCalculator
from calculations import OnusCalculator

# Initialize the data processor and calculator
data_processor = DataProcessor()
onus_calculator = OnusCalculator(data_processor)

# Configure the page
st.set_page_config(layout='wide')
st.title("Cálculo do Ônus Contratual :vibration_mode:")
st.divider()

# Initialize session state for storing terms
if 'input_anoBase' not in st.session_state:
    st.session_state.input_anoBase = None
if 'input_entidade' not in st.session_state:
    st.session_state.input_entidade = None
if 'input_NumTermo' not in st.session_state:
    st.session_state.input_NumTermo = None
if 'input_AnoTermo' not in st.session_state:
    st.session_state.input_AnoTermo = None
if 'input_UF' not in st.session_state:
    st.session_state.input_UF = None
if 'input_areaPrestacao' not in st.session_state:
    st.session_state.input_areaPrestacao = None
if 'input_areaExcl' not in st.session_state:
    st.session_state.input_areaExcl = None
if 'input_munExclusao' not in st.session_state:
    st.session_state.input_munExclusao = None
if 'input_freqInicial' not in st.session_state:
    st.session_state.input_freqInicial = None
if 'input_freqFinal' not in st.session_state:
    st.session_state.input_freqFinal = None
if 'input_tipo' not in st.session_state:
    st.session_state.input_tipo = None

if 'df_TermosPrg' not in st.session_state:
    st.session_state.df_TermosPrg = pd.DataFrame({
        'AnoBase': [],
        'Entidade': [],
        'NumTermo': [],
        'AnoTermo': [],
        'UF': [],
        'areaPrestacao': [],
        'areaExclusao': [],
        'munExclusao': [],
        'freqInicial': [],
        'freqFinal': [],
        'Freq': [],
        'Banda': [],
        'Tipo': []
    })

# Function to add a new term to the dataframe
def add_term_to_df():
    """Add a new term to the dataframe based on user inputs"""
    new_term = {
        'AnoBase': [st.session_state.input_anoBase],
        'Entidade': [st.session_state.input_entidade],
        'NumTermo': [st.session_state.input_NumTermo],
        'AnoTermo': [st.session_state.input_AnoTermo],
        'UF': [st.session_state.input_UF],
        'areaPrestacao': [st.session_state.input_areaPrestacao],
        'areaExclusao': [st.session_state.input_areaExcl],
        'munExclusao': [st.session_state.input_munExclusao],
        'freqInicial': [st.session_state.input_freqInicial],
        'freqFinal': [st.session_state.input_freqFinal],
        'Freq': [st.session_state.input_freqFinal - (
                st.session_state.input_freqFinal - st.session_state.input_freqInicial) / 2],
        'Banda': [st.session_state.input_freqFinal - st.session_state.input_freqInicial],
        'Tipo': [st.session_state.input_tipo]
    }
    new_term_df = pd.DataFrame(new_term)
    st.session_state.df_TermosPrg = pd.concat([st.session_state.df_TermosPrg, new_term_df])

# Create tabs
aba1, aba2, aba3, aba4 = st.tabs(['Cadastro/Carregamento', 'Tabelas', 'Mapas', 'Cálculo do Ônus'])

# Tab 1: Registration and Loading
with aba1:
    with st.container(border=True):
        dfTermoCol = st.columns(13)
        
        with dfTermoCol[0]:
            # Get list of available years
            listaAnoBase = data_processor.get_unique_years()
            st.selectbox('Ano Base Populacional', options=listaAnoBase, key='input_anoBase')
        
        with dfTermoCol[1]:
            # Get list of operators
            listaOP = data_processor.get_operators_list()
            st.selectbox('Operadora', options=listaOP, key='input_entidade')
        
        with dfTermoCol[2]:
            st.text_input('Numero do Termo', key='input_NumTermo', placeholder='Termo')
        
        with dfTermoCol[3]:
            listaAno = list(range(2005, dt.date.today().year))
            st.selectbox('Ano do Termo', key='input_AnoTermo', options=listaAno)
        
        with dfTermoCol[4]:
            # Get list of states for the selected year
            listaUF = data_processor.get_states_for_year(st.session_state.input_anoBase)
            st.selectbox('Estado', options=listaUF, key='input_UF')
        
        with dfTermoCol[5]:
            # Get list of service areas for the selected state
            listaAreas = data_processor.get_service_areas_for_state(st.session_state.input_UF)
            st.selectbox('Area de Prestação', options=listaAreas, key='input_areaPrestacao')
        
        with dfTermoCol[6]:
            # Get eligible exclusion areas
            listaAreasExcl = data_processor.get_exclusion_areas(
                st.session_state.input_anoBase,
                st.session_state.input_UF,
                st.session_state.input_areaPrestacao
            )
            areasExcl = st.multiselect('Areas de Exclusão', options=listaAreasExcl, key='input_areaExcl')
        
        with dfTermoCol[7]:
            # Get service area data with exclusions applied
            df_service_area = data_processor.get_service_area_data(
                st.session_state.input_anoBase,
                st.session_state.input_UF,
                st.session_state.input_areaPrestacao
            )
            
            # Apply exclusion areas
            df_after_exclusions = data_processor.apply_exclusion_areas(
                df_service_area,
                st.session_state.input_areaExcl,
                st.session_state.input_anoBase,
                st.session_state.input_UF
            )
            
            # Get list of municipalities after exclusions
            listaMun_excl = df_after_exclusions['Municipio'].unique()
            mun_excl = st.multiselect('Exclusao de Municipios', options=listaMun_excl, key='input_munExclusao')
        
        with dfTermoCol[8]:
            st.number_input('Frequencia Incial', key='input_freqInicial')
        
        with dfTermoCol[9]:
            st.number_input('Frequência Final', key='input_freqFinal')
        
        with dfTermoCol[10]:
            freq_central = st.session_state.input_freqFinal - (
                    st.session_state.input_freqFinal - st.session_state.input_freqInicial) / 2
            st.number_input('Frequência Central', key='Freq', value=freq_central, disabled=True)
        
        with dfTermoCol[11]:
            bandwidth = st.session_state.input_freqFinal - st.session_state.input_freqInicial
            st.number_input('Banda', key='BW', value=bandwidth, disabled=True)
        
        with dfTermoCol[12]:
            st.selectbox('Tipo', options=['ONUS', 'DEMAIS'], key='input_tipo')
        
        with dfTermoCol[0]:
            if st.button('Aplicar', key='buttonTermo'):
                add_term_to_df()
        
        # Reset index and display the dataframe
        st.session_state.df_TermosPrg.reset_index(drop=True, inplace=True)
        edited_df = st.data_editor(
            st.session_state.df_TermosPrg, 
            num_rows='dynamic', 
            key='dfTermoFinal', 
            use_container_width=True,
            height=300
        )
        
        # Handle deleted rows
        if st.session_state.dfTermoFinal["deleted_rows"] != []:
            st.session_state.df_TermosPrg.drop(
                st.session_state.dfTermoFinal['deleted_rows'],
                inplace=True
            )
        
        # Generate final dataframe for all terms
        if not st.session_state.df_TermosPrg.empty:
            dfTermos_Atual = pd.DataFrame()
            
            for i in list(st.session_state.df_TermosPrg.index):
                term = st.session_state.df_TermosPrg.loc[i]
                df_term = data_processor.generate_final_df(
                    term['AnoBase'],
                    term['Entidade'],
                    term['NumTermo'],
                    term['AnoTermo'],
                    term['UF'],
                    term['areaPrestacao'],
                    term['areaExclusao'],
                    term['munExclusao'],
                    term['freqInicial'],
                    term['freqFinal'],
                    term['Freq'],
                    term['Banda'],
                    term['Tipo']
                )
                dfTermos_Atual = pd.concat([dfTermos_Atual, df_term])
            
            # Store in session state for use in other tabs
            st.session_state.dfTermos_Atual = dfTermos_Atual

# Tab 2: Tables
with aba2:
    with st.container():
        st.subheader('Tabela de Termos Cadastrados')
        st.dataframe(st.session_state.df_TermosPrg, use_container_width=True)
        
        st.subheader('Tabela de Municípios')
        if 'dfTermos_Atual' in st.session_state:
            st.dataframe(st.session_state.dfTermos_Atual, use_container_width=True)

# Tab 3: Maps
with aba3:
    try:
        st.subheader(':large_green_square: Área de Prestação')
        
        with st.container(height=100):
            col31, col32, col33, col34, col35, col3x, col3y, col3z, col3k, col3l = st.columns(10)
            
            # Only show map controls if terms have been added
            if 'dfTermos_Atual' in st.session_state and not st.session_state.dfTermos_Atual.empty:
                with col31:
                    # Select term
                    terms = st.session_state.dfTermos_Atual['NumTermo'].unique()
                    term_map = st.selectbox('Termo', options=terms, key='inp_termoMapa')
                    df_term_map = st.session_state.dfTermos_Atual[
                        st.session_state.dfTermos_Atual['NumTermo'] == st.session_state.inp_termoMapa
                    ]
                
                with col32:
                    # Select year
                    years = df_term_map['AnoTermo'].unique()
                    year_map = st.selectbox('Ano', options=years, key="inp_anoMapa")
                    df_year_map = df_term_map[df_term_map['AnoTermo'] == st.session_state.inp_anoMapa]
                
                with col33:
                    # Select state
                    states = df_year_map['UF'].unique()
                    state_map = st.selectbox('UF', options=states, key='inp_UFmapa')
                    df_state_map = df_year_map[df_year_map['UF'] == st.session_state.inp_UFmapa]
                
                with col34:
                    # Select service area
                    areas = df_state_map['AreaPrestacao'].unique()
                    area_map = st.selectbox('Área de Prestação', options=areas, key='inp_AreaPrestMapa')
                    df_area_map = df_state_map[df_state_map['AreaPrestacao'] == st.session_state.inp_AreaPrestMapa]
                    
                    # Format frequency range for display
                    df_area_map_freq = df_area_map.copy()
                    df_area_map_freq['FreqIni'] = df_area_map['FreqIni'].apply(lambda x: str(x))
                    df_area_map_freq['FreqFin'] = df_area_map['FreqFin'].apply(lambda x: str(x))
                    df_area_map_freq['Faixa'] = df_area_map_freq['FreqIni'] + ' - ' + df_area_map_freq['FreqFin']
                
                with col35:
                    # Select frequency range
                    freq_ranges = df_area_map_freq['Faixa'].unique()
                    freq_map = st.selectbox('Frequência Inicial', options=freq_ranges, key='inp_FreqMapa')
                    df_freq_map = df_area_map_freq[df_area_map_freq['Faixa'] == st.session_state.inp_FreqMapa]
                    
                    # Get list of municipality codes for the map
                    mun_codes_map = df_freq_map['codMun'].unique()
                    mun_codes_map = [str(i) for i in mun_codes_map]
                
                # Display the map
                with st.container(height=600, border=False):
                    # Load map data
                    map_data = data_processor.load_map(st.session_state.inp_UFmapa)
                    
                    if map_data is not None:
                        # Create GeoDataFrame
                        import geopandas as gpd
                        geo_df = gpd.GeoDataFrame(map_data, geometry='geometry', crs='EPSG:3857')
                        
                        # Filter for selected municipalities
                        geo_df_area = geo_df[geo_df['geocodigo'].isin(mun_codes_map)]
                        
                        # Get map bounds
                        lon_min, lat_min, lon_max, lat_max = map_data.total_bounds
                        
                        # Create Folium map
                        map_folium = folium.Map(
                            location=[-15.8, -47.8],
                            no_touch=True,
                            tiles='openstreetmap',
                            control_scale=True,
                            crs='EPSG:3857',
                            zoom_start=4,
                            key='mapaBase',
                            prefer_canvas=False,
                            max_bounds=True,
                            tooltip='tooltip'
                        )
                        map_folium.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])
                        
                        # Add feature groups
                        group_map = folium.FeatureGroup(name='grupoMapa').add_to(map_folium)
                        
                        # Add state boundaries
                        pol_sim_geo = gpd.GeoDataFrame(geo_df["geometry"]).simplify(tolerance=0.01)
                        pol_geo_json = pol_sim_geo.to_json()
                        pol_geo = folium.GeoJson(
                            data=pol_geo_json, 
                            style_function=lambda x: {
                                'fillColor': '#FF0000',
                                "fillOpacity": 0.2,
                                "weight": 0.2,
                                "color": "#B00000"
                            }
                        )
                        
                        # Add service area
                        pol_sim_geo_term = gpd.GeoDataFrame(geo_df_area["geometry"]).simplify(tolerance=0.01)
                        pol_geo_json_term = pol_sim_geo_term.to_json()
                        pol_geo_term = folium.GeoJson(
                            data=pol_geo_json_term, 
                            style_function=lambda x: {
                                'fillColor': '#4AC423',
                                "color": "#1C5727",
                                "fillOpacity": 0.5,
                                'weight': 0.5
                            }
                        )
                        
                        # Add layers to map
                        group_map.add_child(pol_geo_term)
                        group_map.add_child(pol_geo)
                        
                        # Display the map
                        st_folium(
                            map_folium,
                            feature_group_to_add=group_map,
                            returned_objects=[],
                            zoom=4,
                            width=1200,
                            height=600
                        )
            else:
                st.info("Adicione termos na aba 'Cadastro/Carregamento' para visualizar o mapa.")
    except Exception as e:
        st.error(f"Erro ao carregar o mapa: {e}")

# Tab 4: Onus Calculation
with aba4:
    try:
        with st.container(height=450):
            # Only show calculation controls if terms have been added
            if 'dfTermos_Atual' in st.session_state and not st.session_state.dfTermos_Atual.empty:
                # Prepare data for calculation
                df_data = st.session_state.dfTermos_Atual.copy()
                df_data['popMun'] = df_data['popMun'].astype(int)
                df_data['popUF'] = df_data['popUF'].astype(int)
                df_data['coefPop'] = df_data['popMun'] / df_data['popUF']
                
                st.subheader('Cálculo do ônus')
                st.divider()
                colA, colB, colC, colD, colE, colF = st.columns(6)
                
                with colA:
                    # Select population base year
                    years = df_data['AnoBase'].unique()
                    st.selectbox('Ano da Base Populacional', options=years, key='anoBasePop')
                
                with colB:
                    # Select entity
                    df_year = df_data[df_data['AnoBase'] == st.session_state.anoBasePop]
                    entities = df_year['Entidade'].unique()
                    st.selectbox('Operadora', options=entities, key='entidadeOnus')
                
                with colC:
                    # Select state
                    df_entity = df_year[df_year['Entidade'] == st.session_state.entidadeOnus]
                    states = df_entity['UF'].unique()
                    st.selectbox('Estado', options=states, key='anoBaseUF')
                
                with colD:
                    # Select term
                    df_state = df_entity[df_entity['UF'] == st.session_state.anoBaseUF]
                    terms = df_state['NumTermo'].unique()
                    st.selectbox('Termo', options=terms, key='inp_TermoOnus')
                
                with colE:
                    # Select term year
                    df_term = df_state[df_state['NumTermo'] == st.session_state.inp_TermoOnus]
                    term_years = df_term['AnoTermo'].unique()
                    st.selectbox('Ano do Termo', options=term_years, key='inp_AnoOnus')
                
                with colF:
                    # Input ROL
                    rol = st.number_input("Receita Operacional Líquida (ROL) da UF", value=1000000.00)
                
                with colB:
                    # Display term identification
                    st.subheader('')
                    st.subheader('')
                    st.subheader(
                        f":abacus:ÔNUS - Termo {st.session_state.inp_TermoOnus}/{str(st.session_state.inp_AnoOnus).split('.')[0]}")
                
                with colC:
                    # Validate inputs
                    is_valid, error_message = onus_calculator.validate_calculation_inputs(
                        st.session_state.anoBasePop,
                        st.session_state.entidadeOnus,
                        st.session_state.anoBaseUF,
                        st.session_state.inp_TermoOnus,
                        st.session_state.inp_AnoOnus,
                        rol
                    )
                    
                    if is_valid:
                        # Calculate onus using the calculator
                        onus, df_factors, population_total = onus_calculator.calculate_onus(
                            st.session_state.anoBasePop,
                            st.session_state.entidadeOnus,
                            st.session_state.anoBaseUF,
                            st.session_state.inp_TermoOnus,
                            st.session_state.inp_AnoOnus,
                            rol,
                            df_data
                        )
                        
                        # Display formatted result
                        st.subheader('')
                        st.subheader('')
                        st.subheader(onus_calculator.format_onus_result(onus))
                        st.subheader('')
                        
                        # Get and display summary statistics
                        if stats := onus_calculator.get_summary_statistics(df_factors):
                            with st.expander("Estatísticas do cálculo"):
                                st.write(f"Total de municípios: {stats['total_municipalities']}")
                                st.write(f"Ônus máximo por município: {onus_calculator.format_onus_result(stats['max_onus'])}")
                                st.write(f"Ônus mínimo por município: {onus_calculator.format_onus_result(stats['min_onus'])}")
                                st.write(f"Ônus médio por município: {onus_calculator.format_onus_result(stats['avg_onus'])}")
                    else:
                        st.error(error_message)
                
                # Display terms table
                df_terms_onus = st.session_state.df_TermosPrg
                df_terms_onus_year = df_terms_onus[df_terms_onus['AnoBase'] == st.session_state.anoBasePop]
                df_terms_onus_state = df_terms_onus_year[df_terms_onus_year['UF'] == st.session_state.anoBaseUF]
                st.dataframe(df_terms_onus_state)
                
                # Display factors table
                if 'df_factors' in locals() and not df_factors.empty:
                    st.subheader("Fatores por Município")
                    st.dataframe(df_factors)
            else:
                st.info("Adicione termos na aba 'Cadastro/Carregamento' para calcular o ônus.")
    except Exception as e:
        st.error(f"Erro ao calcular o ônus: {e}")
