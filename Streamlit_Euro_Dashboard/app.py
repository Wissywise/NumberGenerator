"""
We can make the generator more interesting by giving every possible number a statistical score based on frequency,
recent frequency, odd/even balance, low/high balance, and historical pair frequency, then use those scores to generate
the lines. The important change is that we won't simply say "hot = good" or "cold = good." Instead, the program
calculates several statistics and combines them into a candidate score.

What this version analyses:
For every main number 1–50, it considers:
Overall frequency — how often it has appeared historically.
Recent frequency — how often it appeared in the latest 50 draws.
Pair frequency — how often it has appeared alongside other numbers.
Odd/even balance — avoids highly unbalanced combinations.
Low/high balance — 1–25 versus 26–50.
Previous exact combinations — rejects a five-number combination that has already occurred.
Duplicate generated lines — makes the four results different.
"""
import random
from pathlib import Path
from collections import Counter
from itertools import combinations

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="EuroMillions Analyzer",
    page_icon="🎯",
    layout="wide"
)


# =========================================================
# SETTINGS
# =========================================================

DATA_URL = (
    "https://raw.githubusercontent.com/daowa89/"
    "lottery-archive/main/eu/euromillions/results.csv"
)

DATA_FOLDER = Path("data")
DATA_FILE = DATA_FOLDER / "euromillions_history.csv"

MAIN_COLUMNS = ["n1", "n2", "n3", "n4", "n5"]

NUMBER_RANGE = range(1, 51)

RECENT_DRAWS = 50


# =========================================================
# CREATE DATA FOLDER
# =========================================================

DATA_FOLDER.mkdir(exist_ok=True)


# =========================================================
# DOWNLOAD DATA
# =========================================================

@st.cache_data(ttl="1d")
def load_data():

    df = pd.read_csv(
        DATA_URL,
        parse_dates=["date"]
    )

    df = df.sort_values("date")

    df.to_csv(DATA_FILE, index=False)

    return df


# =========================================================
# NUMBER FREQUENCY
# =========================================================

def calculate_frequency(df):

    numbers = []

    for column in MAIN_COLUMNS:

        numbers.extend(
            df[column].astype(int).tolist()
        )

    return Counter(numbers)


# =========================================================
# RECENT FREQUENCY
# =========================================================

def calculate_recent_frequency(df):

    recent_df = df.tail(RECENT_DRAWS)

    numbers = []

    for column in MAIN_COLUMNS:

        numbers.extend(
            recent_df[column].astype(int).tolist()
        )

    return Counter(numbers)


# =========================================================
# PAIR FREQUENCY
# =========================================================

def calculate_pair_frequency(df):

    pair_frequency = Counter()

    for _, row in df.iterrows():

        numbers = sorted(
            int(row[column])
            for column in MAIN_COLUMNS
        )

        for pair in combinations(numbers, 2):

            pair_frequency[pair] += 1

    return pair_frequency


# =========================================================
# PREVIOUS COMBINATIONS
# =========================================================

def get_previous_combinations(df):

    previous = set()

    for _, row in df.iterrows():

        combination = tuple(
            sorted(
                int(row[column])
                for column in MAIN_COLUMNS
            )
        )

        previous.add(combination)

    return previous


# =========================================================
# NUMBER SCORES
# =========================================================

def calculate_number_scores(
    overall_frequency,
    recent_frequency
):

    scores = {}

    max_overall = max(
        overall_frequency.values()
    )

    max_recent = max(
        recent_frequency.values()
    )

    for number in NUMBER_RANGE:

        overall_score = (
            overall_frequency[number]
            / max_overall
        )

        recent_score = (
            recent_frequency[number]
            / max_recent
            if max_recent > 0
            else 0
        )

        score = (
            overall_score * 0.60
            +
            recent_score * 0.40
        )

        scores[number] = score

    return scores


# =========================================================
# COMBINATION SCORE
# =========================================================

def score_combination(
    numbers,
    number_scores,
    pair_frequency,
    max_pair_frequency
):

    number_score = sum(
        number_scores[number]
        for number in numbers
    )

    pair_score = 0

    for pair in combinations(numbers, 2):

        if max_pair_frequency > 0:

            pair_score += (
                pair_frequency[pair]
                / max_pair_frequency
            )

    # Odd / even

    odd_count = sum(
        number % 2 != 0
        for number in numbers
    )

    even_count = 5 - odd_count

    if (odd_count, even_count) in [
        (2, 3),
        (3, 2)
    ]:

        balance_score = 1.0

    elif (odd_count, even_count) in [
        (1, 4),
        (4, 1)
    ]:

        balance_score = 0.5

    else:

        balance_score = 0.0

    # Low / high

    low_count = sum(
        number <= 25
        for number in numbers
    )

    high_count = 5 - low_count

    if (low_count, high_count) in [
        (2, 3),
        (3, 2)
    ]:

        low_high_score = 1.0

    elif (low_count, high_count) in [
        (1, 4),
        (4, 1)
    ]:

        low_high_score = 0.5

    else:

        low_high_score = 0.0

    # Final score

    final_score = (
        number_score * 0.60
        +
        pair_score * 0.20
        +
        balance_score * 0.10
        +
        low_high_score * 0.10
    )

    return final_score


# =========================================================
# GENERATE LINES
# =========================================================

def generate_lines(
    number_scores,
    pair_frequency,
    max_pair_frequency,
    previous_combinations,
    number_of_lines
):

    candidates = []

    for _ in range(10000):

        numbers = tuple(
            sorted(
                random.sample(
                    NUMBER_RANGE,
                    5
                )
            )
        )

        if numbers in previous_combinations:
            continue

        score = score_combination(
            numbers,
            number_scores,
            pair_frequency,
            max_pair_frequency
        )

        candidates.append(
            (score, numbers)
        )

    candidates.sort(
        reverse=True,
        key=lambda item: item[0]
    )

    selected = []

    for score, numbers in candidates:

        if numbers not in selected:

            selected.append(numbers)

        if len(selected) == number_of_lines:

            break

    return selected


# =========================================================
# LUCKY STARS
# =========================================================

def generate_lucky_stars():

    return sorted(
        random.sample(
            range(1, 13),
            2
        )
    )


# =========================================================
# MAIN TITLE
# =========================================================

st.title("🎯 EuroMillions Historical Analyzer")

st.write(
    "Analyse historical EuroMillions results, "
    "number frequencies, recent activity, pairs, "
    "odd/even patterns and low/high patterns."
)

st.info(
    "This dashboard is a data-analysis project. "
    "Historical statistics do not predict future lottery results."
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Settings")

number_of_lines = st.sidebar.slider(
    "Number of lines",
    min_value=1,
    max_value=10,
    value=4
)

recent_draws = st.sidebar.slider(
    "Recent draws to analyse",
    min_value=10,
    max_value=200,
    value=50
)


# =========================================================
# LOAD DATA
# =========================================================

try:

    with st.spinner(
        "Downloading historical EuroMillions data..."
    ):

        df = load_data()

except Exception as error:

    st.error(
        f"Unable to download historical data: {error}"
    )

    st.stop()


# =========================================================
# SUMMARY METRICS
# =========================================================

st.header("📊 Historical Data")

latest_date = df["date"].max()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Historical draws",
    len(df)
)

col2.metric(
    "First draw",
    df["date"].min().strftime("%d/%m/%Y")
)

col3.metric(
    "Latest draw",
    latest_date.strftime("%d/%m/%Y")
)

col4.metric(
    "Unique combinations",
    len(get_previous_combinations(df))
)


# =========================================================
# CALCULATE STATISTICS
# =========================================================

overall_frequency = calculate_frequency(df)

recent_df = df.tail(recent_draws)

recent_frequency = calculate_recent_frequency(
    recent_df
)

pair_frequency = calculate_pair_frequency(df)

previous_combinations = get_previous_combinations(df)

number_scores = calculate_number_scores(
    overall_frequency,
    recent_frequency
)

max_pair_frequency = (
    max(pair_frequency.values())
    if pair_frequency
    else 1
)


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🔥 Hot & Cold",
        "📈 Charts",
        "🔢 Patterns",
        "🎯 Generate Lines"
    ]
)


# =========================================================
# TAB 1 - HOT AND COLD
# =========================================================

with tab1:

    st.subheader(
        "Main Number Frequency"
    )

    frequency_data = pd.DataFrame(
        {
            "Number": list(NUMBER_RANGE),
            "Historical": [
                overall_frequency[number]
                for number in NUMBER_RANGE
            ],
            "Recent": [
                recent_frequency[number]
                for number in NUMBER_RANGE
            ],
            "Score": [
                number_scores[number]
                for number in NUMBER_RANGE
            ]
        }
    )

    frequency_data = frequency_data.sort_values(
        "Score",
        ascending=False
    )

    st.dataframe(
        frequency_data,
        use_container_width=True,
        hide_index=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🔥 Top 10 scored numbers")

        top_numbers = frequency_data.head(10)

        st.dataframe(
            top_numbers,
            use_container_width=True,
            hide_index=True
        )

    with col2:

        st.subheader("❄️ Lowest 10 scored numbers")

        cold_numbers = frequency_data.tail(10)

        st.dataframe(
            cold_numbers,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# TAB 2 - CHARTS
# =========================================================

with tab2:

    st.subheader(
        "Historical Number Frequency"
    )

    chart_data = pd.DataFrame(
        {
            "Number": list(NUMBER_RANGE),
            "Appearances": [
                overall_frequency[number]
                for number in NUMBER_RANGE
            ]
        }
    )

    st.bar_chart(
        chart_data.set_index("Number")
    )

    st.subheader(
        "Number Scores"
    )

    score_data = pd.DataFrame(
        {
            "Number": list(NUMBER_RANGE),
            "Score": [
                number_scores[number]
                for number in NUMBER_RANGE
            ]
        }
    )

    st.bar_chart(
        score_data.set_index("Number")
    )


# =========================================================
# TAB 3 - PATTERNS
# =========================================================

with tab3:

    st.subheader(
        "Odd / Even Patterns"
    )

    odd_even_patterns = Counter()

    for _, row in df.iterrows():

        numbers = [
            int(row[column])
            for column in MAIN_COLUMNS
        ]

        odd = sum(
            number % 2 != 0
            for number in numbers
        )

        even = 5 - odd

        pattern = f"{odd} odd / {even} even"

        odd_even_patterns[pattern] += 1

    odd_even_data = pd.DataFrame(
        {
            "Pattern": list(
                odd_even_patterns.keys()
            ),
            "Draws": list(
                odd_even_patterns.values()
            )
        }
    )

    st.dataframe(
        odd_even_data.sort_values(
            "Draws",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Low / High Patterns"
    )

    low_high_patterns = Counter()

    for _, row in df.iterrows():

        numbers = [
            int(row[column])
            for column in MAIN_COLUMNS
        ]

        low = sum(
            number <= 25
            for number in numbers
        )

        high = 5 - low

        pattern = f"{low} low / {high} high"

        low_high_patterns[pattern] += 1

    low_high_data = pd.DataFrame(
        {
            "Pattern": list(
                low_high_patterns.keys()
            ),
            "Draws": list(
                low_high_patterns.values()
            )
        }
    )

    st.dataframe(
        low_high_data.sort_values(
            "Draws",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Most Frequent Number Pairs"
    )

    top_pairs = pair_frequency.most_common(20)

    pair_data = pd.DataFrame(
        [
            {
                "Pair": f"{pair[0]} + {pair[1]}",
                "Appearances": count
            }
            for pair, count in top_pairs
        ]
    )

    st.dataframe(
        pair_data,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# TAB 4 - GENERATE LINES
# =========================================================

with tab4:

    st.subheader(
        "🎯 Generate EuroMillions Lines"
    )

    st.write(
        "The generator creates candidate combinations "
        "and scores them using the historical analysis."
    )

    if st.button(
        "Generate New Lines",
        type="primary"
    ):

        with st.spinner(
            "Analysing combinations..."
        ):

            generated_lines = generate_lines(
                number_scores,
                pair_frequency,
                max_pair_frequency,
                previous_combinations,
                number_of_lines
            )

        st.success(
            f"{len(generated_lines)} lines generated."
        )

        for index, line in enumerate(
            generated_lines,
            start=1
        ):

            stars = generate_lucky_stars()

            st.markdown(
                f"""
                ### Line {index}

                **{' — '.join(
                    str(number)
                    for number in line
                )}**

                ⭐ Lucky Stars:
                **{' — '.join(
                    str(star)
                    for star in stars
                )}**
                """
            )

            # Show score
            score = score_combination(
                line,
                number_scores,
                pair_frequency,
                max_pair_frequency
            )

            st.caption(
                f"Analysis score: {score:.3f}"
            )

            st.divider()


# =========================================================
# FOOTER
# =========================================================

st.sidebar.markdown("---")

st.sidebar.write(
    "EuroMillions Analyzer"
)

st.sidebar.caption(
    "For educational and data-analysis purposes."
)

"""
The source archive says its EuroMillions data is updated automatically on draw days and currently covers draws from 
2004 onward. One statistical caution: the scoring system is useful for demonstrating data analysis, but it doesn't 
change the underlying lottery probabilities. Historical frequency, "hot/cold" status, and pair frequency do not 
establish that a number is more likely to appear in the next draw.
"""