import pandas as pd


class OnusCalculator:
    """
    Class responsible for performing ônus calculations based on term data
    """

    def __init__(self, data_processor):
        """
        Initialize the calculator with a data processor instance

        Args:
            data_processor: An instance of DataProcessor to access data
        """
        self.data_processor = data_processor

    def calculate_onus(
        self, year_base, entity, state, term_num, term_year, rol_uf, df_data
    ):
        """
        Calculate the ônus for a specific term

        Args:
            year_base: Base year for population data
            entity: Entity (operator) name
            state: State code (UF)
            term_num: Term number
            term_year: Term year
            rol_uf: Revenue (ROL) for the state
            df_data: DataFrame with term data

        Returns:
            tuple: (total_onus, factors_dataframe, total_population)
        """
        # Ensure data is clean
        df_data = df_data.copy()
        df_data.drop_duplicates(inplace=True)

        # Filter data for the base year
        df_year_base = df_data[df_data["AnoBase"] == year_base]

        # Calculate total population for the service area
        pop_total = (
            df_year_base[["Municipio", "popMun"]].drop_duplicates()["popMun"].sum()
        )

        # Count frequencies and prepare data
        df_count_freq = self._count_frequencies(df_year_base)
        df_data_count_freq = df_year_base.merge(df_count_freq, how="inner", on="Freq")

        # Get term data
        df_term = self._get_term_data(
            df_data_count_freq, entity, state, term_num, term_year
        )

        # Get other terms data for comparison
        df_other_terms = self._get_other_terms_data(
            df_data_count_freq, entity, state, term_num
        )

        # Calculate factors and ônus for each municipality
        df_factors, total_onus = self._calculate_municipality_factors(
            df_term, df_other_terms, pop_total, rol_uf
        )

        return total_onus, df_factors, pop_total

    def _count_frequencies(self, df):
        """Count frequency occurrences in the dataframe"""
        return pd.DataFrame(df.Freq.value_counts())

    def _get_term_data(self, df, entity, state, term_num, term_year):
        """Filter dataframe to get data for the specific term"""
        # Filter by entity, state, term number and year
        df_entity = df[df["Entidade"] == entity]
        df_state = df_entity[df_entity["UF"] == state]
        df_term_num = df_state[df_state["NumTermo"] == term_num]
        df_term = df_term_num[df_term_num["AnoTermo"] == term_year]

        # Calculate bandwidth/frequency ratio
        df_term["BW_Freq"] = df_term["Banda"].astype("float") / df_term["Freq"].astype(
            "float"
        )

        return df_term

    def _get_other_terms_data(self, df, entity, state, term_num):
        """Filter dataframe to get data for other terms from the same entity and state"""
        # Filter by entity and state, excluding the specific term
        df_entity = df[df["Entidade"] == entity]
        df_state = df_entity[df_entity["UF"] == state]
        df_other_terms = df_state[df_state["NumTermo"] != term_num]

        # Calculate bandwidth/frequency ratio
        df_other_terms["BW_Freq"] = df_other_terms["Banda"] / df_other_terms["Freq"]

        return df_other_terms

    def _calculate_municipality_factors(
        self, df_term, df_other_terms, pop_total, rol_uf
    ):
        """Calculate factors and ônus for each municipality"""
        # Get list of municipalities in the term
        mun_codes = list(df_term["codMun"].unique())

        # Initialize results
        df_factors = pd.DataFrame()
        total_onus = 0

        # Calculate for each municipality
        for mun_code in mun_codes:
            # Population factor
            pop_mun = df_term[df_term["codMun"] == mun_code]["popMun"].unique()
            factor_pop = pop_mun / pop_total

            # Frequency factor
            freq_numerator = (
                df_term[df_term["codMun"] == mun_code]["BW_Freq"].unique().sum()
            )
            freq_denominator = freq_numerator

            # Add other terms' frequencies if they exist for this municipality
            other_terms_mun = df_other_terms[df_other_terms["codMun"] == mun_code]
            if not other_terms_mun.empty:
                freq_denominator += other_terms_mun["BW_Freq"].unique().sum()

            # Calculate frequency factor
            factor_freq = (
                freq_numerator / freq_denominator if freq_denominator > 0 else 0
            )

            # Calculate ônus for this municipality
            mun_onus = factor_freq * factor_pop * 0.02 * rol_uf
            total_onus += mun_onus[0] if isinstance(mun_onus, pd.Series) else mun_onus

            # Add to factors dataframe
            mun_name = df_term[df_term["codMun"] == mun_code]["Municipio"].unique()
            df_factor_row = pd.DataFrame(
                {
                    "Municipio": mun_name,
                    "codMun": mun_code,
                    "fatorFreq": factor_freq,
                    "fatorPop": factor_pop,
                    "onusMunicipio": mun_onus,
                }
            )
            df_factors = pd.concat([df_factors, df_factor_row])

        return df_factors, total_onus

    def validate_calculation_inputs(
        self, year_base, entity, state, term_num, term_year, rol_uf
    ):
        """
        Validate inputs for ônus calculation

        Returns:
            tuple: (is_valid, error_message)
        """
        if not year_base:
            return False, "Ano base não selecionado"

        if not entity:
            return False, "Entidade não selecionada"

        if not state:
            return False, "UF não selecionada"

        if not term_num:
            return False, "Termo não selecionado"

        if not term_year:
            return False, "Ano do termo não selecionado"

        return (False, "ROL deve ser maior que zero") if rol_uf <= 0 else (True, "")

    def format_onus_result(self, onus_value):
        """Format the ônus result as currency"""
        return "R$ {:.2f}".format(onus_value)

    def get_summary_statistics(self, df_factors):
        """
        Calculate summary statistics for the ônus calculation

        Returns:
            dict: Summary statistics
        """
        if df_factors.empty:
            return {}

        return {
            "total_municipalities": len(df_factors),
            "max_onus": df_factors["onusMunicipio"].max(),
            "min_onus": df_factors["onusMunicipio"].min(),
            "avg_onus": df_factors["onusMunicipio"].mean(),
            "total_onus": df_factors["onusMunicipio"].sum(),
        }
