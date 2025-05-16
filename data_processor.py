from functools import cached_property
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
AREA_PREST = ROOT / "data/df_Mun_UF_Area.csv"
BASE_POP = ROOT / "data/pop_2014_2024.csv"
OPERADORAS = [
    "ALGAR",
    "BRISANET",
    "CLARO",
    "CLOUD2U",
    "COPEL",
    "COZANI",
    "GARLIAVA",
    "LIGGA TELECOM",
    "LIGUE",
    "NEXTEL",
    "OI",
    "OPTIONS",
    "SERCOMTEL",
    "TELEFONICA",
    "TIM",
    "TPA",
    "VIVO",
    "WINITY",
]


class DataProcessor:
    def __init__(self):
        """Initialize the DataProcessor class"""
        self.load_data()

    def load_data(self):
        """Load the necessary data files"""
        try:
            self.df_area = pd.read_csv(AREA_PREST, dtype="string")
            self.df_pop = pd.read_csv(BASE_POP, dtype="string")
        except Exception as e:
            print(f"Error loading data: {e}")

    @cached_property
    def year_range(self):
        """Get list of unique years from population data"""
        return sorted(self.df_pop["AnoBase"].unique().tolist())

    def get_states_for_year(self, year):
        """Get list of states available for a specific year"""
        # if year is None:
        #     return []
        return sorted(
            self.df_pop.loc[self.df_pop["AnoBase"] == str(year), "UF"].unique()
        )

    def get_service_areas_for_state(self, state):
        """Get list of service areas for a specific state"""
        # if state is None:
        #     return []
        df_state = self.df_area[self.df_area["UF"] == state]
        return list(df_state["AreaPrestacao"].unique())

    def get_population_data_for_year_state(self, year, state):
        """Get population data for a specific year and state"""
        df_year = self.df_pop[self.df_pop["AnoBase"] == str(year)]
        return df_year[df_year["UF"] == state]

    def get_area_population_data(self, year, state):
        """Merge area and population data for a specific year and state"""
        df_area_state = self.df_area[self.df_area["UF"] == state]
        df_pop_year_state = self.get_population_data_for_year_state(year, state)

        df_merged = df_area_state.merge(
            df_pop_year_state, how="left", on=["codMun", "UF"]
        )

        return df_merged.drop_duplicates()

    def get_service_area_data(self, year, state, service_area):
        """Get data for a specific service area"""
        df_area_pop = self.get_area_population_data(year, state)
        return df_area_pop[df_area_pop["AreaPrestacao"] == str(service_area)]

    def get_exclusion_areas(self, year, state, main_service_area):
        """Get eligible exclusion areas for a service area"""
        df_area_pop = self.get_area_population_data(year, state)
        df_main_area = self.get_service_area_data(year, state, main_service_area)

        # Get all areas except the main one and 'Toda UF'
        exclude = ["Toda UF", main_service_area]
        all_areas = [
            x for x in df_area_pop["AreaPrestacao"].unique() if x not in exclude
        ]

        # Create set of municipalities in the main service area
        main_area_mun_codes = set(df_main_area["codMun"])

        # Find eligible exclusion areas (those that are subsets of the main area)
        eligible_areas = []
        for area in all_areas:
            df_area = df_area_pop[df_area_pop["AreaPrestacao"] == area]
            area_mun_codes = set(df_area["codMun"])

            if area_mun_codes < main_area_mun_codes:
                eligible_areas.append(area)

        return eligible_areas

    def exclude_areas_from_df(self, area_prestacao, year, state, areas_a_excluir: str):
        """Apply exclusion areas to a service area dataframe and returns a list of municipalities"""
        df_service_area = self.get_service_area_data(
            year,
            state,
            area_prestacao,
        )
        if not areas_a_excluir:
            return df_service_area

        df_area_pop = self.get_area_population_data(year, state)

        areas_a_excluir = areas_a_excluir.split(", ")

        cidades_a_excluir = df_area_pop.loc[
            df_area_pop["AreaPrestacao"].isin(areas_a_excluir), "codMun"
        ]

        return df_service_area[~df_service_area["codMun"].isin(cidades_a_excluir)]

    def exclude_cities_from_df(self, df_service_area, cidades_a_excluir: str):
        """Apply exclusion municipalities to a service area dataframe"""
        if not cidades_a_excluir:
            return df_service_area

        cidades_a_excluir = cidades_a_excluir.split(", ")

        cidades_a_excluir = df_service_area.loc[
            df_service_area["Municipio"].isin(cidades_a_excluir), "codMun"
        ]

        return df_service_area.loc[~df_service_area["codMun"].isin(cidades_a_excluir)]

    def gerar_tabela_final(self, df):
        """Generate the final dataframe for a term"""
        final_rows = []
        for row in df.itertuples():
            year_base = row.AnoBase
            state = row.UF
            area_prestacao = row.AreaPrestacao
            areas_exclusao = row.AreaExclusao
            municipios_exclusao = row.MunicipioExclusao

            # Apply exclusions
            tabela_com_areas_excluidas = self.exclude_areas_from_df(
                area_prestacao, year_base, state, areas_exclusao
            )
            tabela_final = self.exclude_cities_from_df(
                tabela_com_areas_excluidas, municipios_exclusao
            )

            tabela_final["AreaExclusao"] = areas_exclusao
            tabela_final["MunicipioExclusao"] = municipios_exclusao
            tabela_final["AnoBase"] = str(year_base)
            tabela_final["Entidade"] = row.Entidade
            tabela_final["NumTermo"] = row.NumTermo
            tabela_final["AnoTermo"] = row.AnoTermo
            tabela_final[ "FrequenciaInicial"] = row.FrequenciaInicial
            tabela_final["FrequenciaFinal"] = row.FrequenciaFinal
            tabela_final["FrequenciaCentral"] = row.FrequenciaCentral
            tabela_final["Banda"] = row.Banda
            tabela_final["Tipo"] = row.Tipo
            final_rows.append(tabela_final)

        return pd.concat(final_rows, ignore_index=True).drop_duplicates()

    # def load_map(self, state):
    #     """Load map data for a specific state"""
    #     try:
    #         return gpd.read_file(f"SHP_UFs/{state}.shp")
    #     except Exception as e:
    #         print(f"Error loading map for state {state}: {e}")
    #         return None

    def calculate_onus(
        self, year_base, entity, state, term_num, term_year, rol_uf, df_data
    ):
        """Calculate the onus for a specific term"""
        # Filter data for the base year
        df_data.drop_duplicates(inplace=True)
        df_year_base = df_data[df_data["AnoBase"] == str(year_base)]

        # Calculate total population
        pop_total = (
            df_year_base[["Municipio", "popMun"]].drop_duplicates()["popMun"].sum()
        )

        # Count frequencies
        df_count_freq = pd.DataFrame(df_year_base.FrequenciaCentral.value_counts())
        df_data_count_freq = df_year_base.merge(
            df_count_freq, how="inner", on="FrequenciaCentral"
        )

        # Filter for entity, state, and term
        df_entity = df_data_count_freq[df_data_count_freq["Entidade"] == entity]
        df_state = df_entity[df_entity["UF"] == state]
        df_term_num = df_state[df_state["NumTermo"] == term_num]
        df_term = df_term_num[df_term_num["AnoTermo"] == term_year]

        # Calculate bandwidth/frequency ratio
        df_term["BW_Freq"] = df_term["Banda"] / df_term["FrequenciaCentral"]

        # Get list of municipalities in the term
        mun_codes = list(df_term["codMun"].unique())

        # Get other terms for comparison
        df_other_entity = df_data_count_freq[df_data_count_freq["Entidade"] == entity]
        df_other_state = df_other_entity[df_other_entity["UF"] == state]
        df_other_terms = df_other_state[df_other_state["NumTermo"] != term_num]
        df_other_terms["BW_Freq"] = (
            df_other_terms["Banda"] / df_other_terms["FrequenciaCentral"]
        )

        # Calculate factors for each municipality
        df_factors = pd.DataFrame()
        total_onus = 0

        for mun_code in mun_codes:
            # Population factor
            pop_factor = (
                df_term[df_term["codMun"] == mun_code]["popMun"].unique() / pop_total
            )

            # Frequency factor
            freq_numerator = (
                df_term[df_term["codMun"] == mun_code]["BW_Freq"].unique().sum()
            )
            freq_denominator = (
                freq_numerator
                + df_other_terms[df_other_terms["codMun"] == mun_code]["BW_Freq"]
                .unique()
                .sum()
            )
            freq_factor = freq_numerator / freq_denominator

            # Calculate onus for this municipality
            mun_onus = freq_factor * pop_factor * 0.02 * rol_uf
            total_onus += mun_onus

            # Add to factors dataframe
            mun_name = df_term[df_term["codMun"] == mun_code]["Municipio"].unique()
            df_factor_row = pd.DataFrame(
                {
                    "Municipio": mun_name,
                    "codMun": mun_code,
                    "fatorFreq": freq_factor,
                    "fatorPop": pop_factor,
                    "onusMunicipio": mun_onus,
                }
            )
            df_factors = pd.concat([df_factors, df_factor_row])

        return total_onus[0], df_factors, pop_total
