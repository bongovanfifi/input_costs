import streamlit as st
import datetime as dt
from sqlalchemy import text

# Initialize session state


conn = st.connection("db", type="sql")
st.title("Ingredient Cost Entry")
ingredients = conn.query("select * from ingredients")

st.markdown(
    """
<style>
    .stDataFrame {
        width: 100%;
    }
    .stDataFrame > div {
        width: 100%;
    }
    .stDataFrame [data-testid="stTable"] {
        width: 100%;
    }
    .stDataFrame [data-testid="stTable"] table {
        width: 100%;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child {
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)


def display_ingredient_status():
    """Display all ingredient status tables"""
    missing_query = """
    SELECT i.name
    FROM ingredients i
    LEFT JOIN prices p ON i.id = p.ingredient_id
    WHERE p.id IS NULL
    ORDER BY i.name;
    """

    old_prices_query = """
    WITH latest_prices AS (
        SELECT 
            ingredient_id,
            MAX(date) as latest_date
        FROM prices
        GROUP BY ingredient_id
    )
    SELECT 
        i.name,
        p.price,
        p.unit,
        p.quantity,
        datetime(p.date, 'unixepoch') as last_updated
    FROM ingredients i
    JOIN latest_prices lp ON i.id = lp.ingredient_id
    JOIN prices p ON p.ingredient_id = i.id AND p.date = lp.latest_date
    WHERE lp.latest_date < unixepoch() - 7776000
    ORDER BY p.date ASC;
    """

    current_prices_query = """
    SELECT 
        i.name,
        p.price,
        p.unit,
        p.quantity,
        datetime(p.date, 'unixepoch') as last_updated
    FROM ingredients i
    JOIN prices p ON i.id = p.ingredient_id
    WHERE p.id IN (
        SELECT MAX(id)
        FROM prices
        GROUP BY ingredient_id
    )
    AND p.date >= unixepoch() - 7776000
    ORDER BY i.name;
    """

    st.subheader("Missing Ingredients")
    missing = conn.query(missing_query, ttl=0)
    if missing.empty:
        st.success("✅ No Missing Ingredients")
    else:
        st.dataframe(missing)

    st.subheader("Prices Older Than 3 Months")
    old_prices = conn.query(old_prices_query, ttl=0)
    if old_prices.empty:
        st.success("✅ All prices that are not missing are up to date")
    else:
        st.dataframe(old_prices)

    st.subheader("Current Prices")
    current_prices = conn.query(current_prices_query, ttl=0)
    st.dataframe(current_prices)


with st.form("price_entry", clear_on_submit=True):
    ingredient = st.selectbox(
        "Ingredient", ingredients["name"].tolist(), key="ingredient"
    )
    available_units = ("g", "kg", "lb", "gal")
    if ingredients[ingredients["name"] == ingredient].iloc[0]["unit_ok"] == 1:
        available_units += "unit"

    cost = st.number_input(
        "Cost ($)", min_value=0.00, step=0.01, format="%.2f", key="cost"
    )
    quantity = st.number_input("Quantity", min_value=0, key="quantity")
    unit = st.selectbox("Unit", available_units, key="unit")

    if st.form_submit_button("Save"):
        if cost <= 0 or quantity <= 0:
            st.exception(ValueError("Cost and quantity must be greater than 0"))
        else:
            ingredient_id = int(
                ingredients[ingredients["name"] == ingredient]["id"].iloc[0]
            )
            timestamp = int(dt.datetime.now().timestamp())
            try:
                with conn.session as session:
                    session.execute(
                        text(
                            """
                        INSERT INTO prices 
                        (ingredient_name, date, price, unit, quantity, ingredient_id) 
                        VALUES (:name, :date, :price, :unit, :quantity, :ingredient_id)
                        """
                        ),
                        params={
                            "name": ingredient,
                            "date": timestamp,
                            "price": cost,
                            "unit": unit,
                            "quantity": quantity,
                            "ingredient_id": ingredient_id,
                        },
                    )
                    session.commit()
                st.success(f"{ingredient} price saved!")
            except Exception as e:
                st.exception(e)

# Display status tables if needed
display_ingredient_status()

with st.expander("Comment Box"):
    st.markdown(
        """
    Let me know if:
    * The form is missing ingredients.
    * The form is missing units.
    * Some ingredient should have the unit option and does not.
    * Something about the form could be improved.
    * You saw a particularly nice bird.
    """
    )
    with st.form("feedback_form", clear_on_submit=True):
        comment = st.text_area(
            """Comment""",
            placeholder="Example: Cinnamon is missing from the ingredients list!",
            max_chars=500,
        )
        if st.form_submit_button("Submit Feedback"):
            if comment.strip():
                timestamp = int(dt.datetime.now().timestamp())
                try:
                    with conn.session as session:
                        session.execute(
                            text(
                                "INSERT INTO comments (date, comment) VALUES (:date, :comment)"
                            ),
                            params={"date": timestamp, "comment": comment},
                        )
                        session.commit()
                    st.success("Comment submitted!")
                except Exception as e:
                    st.exception(e)
