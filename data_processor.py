import pandas as pd
import geopandas as gpd

AREA_PREST = "df_Mun_UF_Area.csv"
BASE_POP = "pop_2014_2022.csv"


class DataProcessor:
    def __init__(self):
        """Initialize the DataProcessor class"""
        self.dfAreaPrest = None
        self.dfBasePop = None
        self.load_data()

    def load_data(self):
        """Load the necessary data files"""
        try:
            self.dfAreaPrest = pd.read_csv(AREA_PREST, dtype="string")
            self.dfBasePop = pd.read_csv(BASE_POP, dtype="string")

            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def get_unique_years(self):
        """Get list of unique years from population data"""
        return list(self.dfBasePop["AnoBase"].unique())

    def get_operators_list(self):
        """Get list of operators"""
        return [
            "ALGAR",
            "BRISANET",
            "CLARO",
            "LIGGA TELECOM",
            "LIGUE",
            "OI",
            "SERCOMTEL",
            "TIM",
            "VIVO",
            "WINITY",
        ]

    def get_states_for_year(self, year):
        """Get list of states available for a specific year"""
        if year is None:
            return []
        df_year = self.dfBasePop[self.dfBasePop["AnoBase"] == year]
        return sorted(df_year["UF"].unique())

    def get_service_areas_for_state(self, state):
        """Get list of service areas for a specific state"""
        if state is None:
            return []
        df_state = self.dfAreaPrest[self.dfAreaPrest["UF"] == state]
        return list(df_state["AreaPrestacao"].unique())

    def get_population_data_for_year_state(self, year, state):
        """Get population data for a specific year and state"""
        df_year = self.dfBasePop[self.dfBasePop["AnoBase"] == year]
        return df_year[df_year["UF"] == state]

    def get_area_population_data(self, year, state):
        """Merge area and population data for a specific year and state"""
        df_area_state = self.dfAreaPrest[self.dfAreaPrest["UF"] == state]
        df_pop_year_state = self.get_population_data_for_year_state(year, state)

        df_merged = df_area_state.merge(df_pop_year_state, how="left", on="codMun")
        df_merged.drop_duplicates(inplace=True)

        if "UF_x" in df_merged.columns and "UF_y" in df_merged.columns:
            df_merged.drop("UF_x", axis=1, inplace=True)
            df_merged.rename(columns={"UF_y": "UF"}, inplace=True)

        return df_merged

    def get_service_area_data(self, year, state, service_area):
        """Get data for a specific service area"""
        df_area_pop = self.get_area_population_data(year, state)
        return df_area_pop[df_area_pop["AreaPrestacao"] == service_area]

    def get_exclusion_areas(self, year, state, main_service_area):
        """Get eligible exclusion areas for a service area"""
        df_area_pop = self.get_area_population_data(year, state)
        df_main_area = self.get_service_area_data(year, state, main_service_area)

        # Get all areas except the main one and 'Toda UF'
        all_areas = list(df_area_pop["AreaPrestacao"].unique())
        if "Toda UF" in all_areas:
            all_areas.remove("Toda UF")
        if main_service_area in all_areas and main_service_area != "Toda UF":
            all_areas.remove(main_service_area)

        # Create set of municipalities in the main service area
        main_area_mun_codes = set(df_main_area["codMun"])

        # Find eligible exclusion areas (those that are subsets of the main area)
        eligible_areas = []
        for area in all_areas:
            df_area = df_area_pop[df_area_pop["AreaPrestacao"] == area]
            area_mun_codes = set(df_area["codMun"])

            if (
                area_mun_codes.issubset(main_area_mun_codes)
                and area_mun_codes != main_area_mun_codes
            ):
                eligible_areas.append(area)

        return eligible_areas

    def apply_exclusion_areas(self, df_service_area, exclusion_areas, year, state):
        """Apply exclusion areas to a service area dataframe"""
        if not exclusion_areas:
            return df_service_area

        df_area_pop = self.get_area_population_data(year, state)
        df_exclusion = pd.DataFrame()

        for area in exclusion_areas:
            df_area = df_area_pop[df_area_pop["AreaPrestacao"] == area]
            df_exclusion = pd.concat([df_exclusion, df_area])

        excluded_mun_codes = df_exclusion["codMun"].unique()
        return df_service_area.loc[~df_service_area["codMun"].isin(excluded_mun_codes)]

    def apply_exclusion_municipalities(self, df_service_area, exclusion_municipalities):
        """Apply exclusion municipalities to a service area dataframe"""
        if not exclusion_municipalities:
            return df_service_area

        df_exclusion = pd.DataFrame()

        for municipality in exclusion_municipalities:
            df_mun = df_service_area[df_service_area["Municipio"] == municipality]
            df_exclusion = pd.concat([df_exclusion, df_mun])

        excluded_mun_codes = df_exclusion["codMun"].unique()
        return df_service_area.loc[~df_service_area["codMun"].isin(excluded_mun_codes)]

    def generate_final_df(
        self,
        year_base,
        entity,
        term_num,
        term_year,
        state,
        service_area,
        exclusion_areas,
        exclusion_municipalities,
        freq_ini,
        freq_fin,
        freq,
        bandwidth,
        term_type,
    ):
        """Generate the final dataframe for a term"""
        # Get service area data
        df_service_area = self.get_service_area_data(year_base, state, service_area)

        # Apply exclusions
        df_after_area_exclusion = self.apply_exclusion_areas(
            df_service_area, exclusion_areas, year_base, state
        )
        df_final = self.apply_exclusion_municipalities(
            df_after_area_exclusion, exclusion_municipalities
        )

        # Add term information
        df_final["AreaExclusao"] = str(exclusion_areas)
        df_final["MunExclusao"] = str(exclusion_municipalities)
        df_final["AnoBase"] = year_base
        df_final["Entidade"] = entity
        df_final["NumTermo"] = term_num
        df_final["AnoTermo"] = term_year
        df_final["FreqIni"] = freq_ini
        df_final["FreqFin"] = freq_fin
        df_final["Freq"] = freq
        df_final["Banda"] = bandwidth
        df_final["TIPO"] = term_type

        return df_final

    def load_map(self, state):
        """Load map data for a specific state"""
        try:
            return gpd.read_file(f"SHP_UFs/{state}.shp")
        except Exception as e:
            print(f"Error loading map for state {state}: {e}")
            return None

    def calculate_onus(
        self, year_base, entity, state, term_num, term_year, rol_uf, df_data
    ):
        """Calculate the onus for a specific term"""
        # Filter data for the base year
        df_data.drop_duplicates(inplace=True)
        df_year_base = df_data[df_data["AnoBase"] == year_base]

        # Calculate total population
        pop_total = (
            df_year_base[["Municipio", "popMun"]].drop_duplicates()["popMun"].sum()
        )

        # Count frequencies
        df_count_freq = pd.DataFrame(df_year_base.Freq.value_counts())
        df_data_count_freq = df_year_base.merge(df_count_freq, how="inner", on="Freq")

        # Filter for entity, state, and term
        df_entity = df_data_count_freq[df_data_count_freq["Entidade"] == entity]
        df_state = df_entity[df_entity["UF"] == state]
        df_term_num = df_state[df_state["NumTermo"] == term_num]
        df_term = df_term_num[df_term_num["AnoTermo"] == term_year]

        # Calculate bandwidth/frequency ratio
        df_term["BW_Freq"] = df_term["Banda"] / df_term["Freq"]

        # Get list of municipalities in the term
        mun_codes = list(df_term["codMun"].unique())

        # Get other terms for comparison
        df_other_entity = df_data_count_freq[df_data_count_freq["Entidade"] == entity]
        df_other_state = df_other_entity[df_other_entity["UF"] == state]
        df_other_terms = df_other_state[df_other_state["NumTermo"] != term_num]
        df_other_terms["BW_Freq"] = df_other_terms["Banda"] / df_other_terms["Freq"]

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
