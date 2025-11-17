import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="BestDeal – Grocery Price Compare",
    page_icon="🛒",
    layout="centered",
)

# ------------------------ SESSION STATE ------------------------
if "location" not in st.session_state:
    st.session_state.location = None
if "products" not in st.session_state:
    st.session_state.products = []
if "view" not in st.session_state:
    st.session_state.view = "card"


# ------------------------ HEADER ------------------------
st.title("🛒 BestDeal")
st.caption("Compare grocery prices across Flipkart Minutes, Blinkit, Zepto & Instamart")


# ------------------------ STEP 1 – LOCATION ------------------------
st.subheader("📍 Step 1: Set Location")

col1, col2 = st.columns([3, 1])
with col1:
    manual_location = st.text_input(
        "Enter location manually",
        value=st.session_state.location or ""
    )
with col2:
    st.write("")
    if st.button("Set"):
        st.session_state.location = manual_location

if st.button("Use Auto Location"):
    try:
        res = requests.get(f"{BACKEND_URL}/get-location").json()
        loc = res.get("formatted_location")
        if loc:
            st.session_state.location = loc
    except:
        st.error("Auto location failed.")

if st.session_state.location:
    st.success(f"📍 Location set: **{st.session_state.location}**")


# ------------------------ STEP 2 – SEARCH ------------------------
st.subheader("🔎 Step 2: Search Product")

query = st.text_input("Enter product name (e.g., Onion, Milk, Eggs)")

if st.button("Search"):
    if not query.strip():
        st.warning("Enter a valid product name.")
    elif not st.session_state.location:
        st.error("Set your location first.")
    else:
        with st.spinner("Fetching best prices…"):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/search",
                    json={"product": query, "location": st.session_state.location}
                ).json()

                results = res.get("results", {})

                data = []
                for source, items in results.items():
                    for p in items:
                        p["source"] = source
                        data.append(p)

                st.session_state.products = data
                st.success(f"Found {len(data)} products!")
            except Exception as e:
                st.error(f"Server error: {e}")


# ------------------------ STEP 3 – RESULTS ------------------------
if st.session_state.products:
    st.subheader("🧾 Results")

    df = pd.DataFrame(st.session_state.products)

    # -------------------- FILTERS --------------------
    st.markdown("### 🔍 Filters & Sorting")

    colA, colB, colC = st.columns([2, 2, 2])

    # Vendor Filter
    vendor_list = sorted(df["source"].unique())
    with colA:
        selected_vendors = st.multiselect("Vendor", vendor_list, default=vendor_list)

    # Discount Filter
    with colB:
        only_discount = st.checkbox("Discount Only")

    # Price Range Filter
    df["price_num"] = pd.to_numeric(df["price"].str.replace("₹", "").str.replace(",", ""), errors="coerce")
    min_price, max_price = df["price_num"].min(), df["price_num"].max()

    with colC:
        price_min, price_max = st.slider(
            "Price Range",
            float(min_price),
            float(max_price),
            (float(min_price), float(max_price))
        )

    # Apply filters
    filtered_df = df[
        (df["source"].isin(selected_vendors)) &
        (df["price_num"] >= price_min) &
        (df["price_num"] <= price_max)
    ]

    if only_discount:
        filtered_df = filtered_df[filtered_df["discount"].astype(str).str.contains("%")]

    # -------------------- SORTING --------------------
    st.markdown("### ↕ Sorting")

    sort_by = st.selectbox(
        "Sort By",
        ["Price: Low → High", "Price: High → Low", "Discount", "Delivery Time", "Vendor", "Name"]
    )

    def extract_delivery_minutes(x):
        try:
            t = x.lower().split()
            if "min" in t:
                return float(t[0])
            elif "hour" in t:
                return float(t[0]) * 60
        except:
            pass
        return 9999

    filtered_df["delivery_mins"] = filtered_df["delivery_time"].apply(extract_delivery_minutes)

    if sort_by == "Price: Low → High":
        filtered_df = filtered_df.sort_values("price_num")
    elif sort_by == "Price: High → Low":
        filtered_df = filtered_df.sort_values("price_num", ascending=False)
    elif sort_by == "Discount":
        filtered_df["discount_num"] = filtered_df["discount"].str.extract(r'(\d+)').astype(float)
        filtered_df = filtered_df.sort_values("discount_num", ascending=False)
    elif sort_by == "Delivery Time":
        filtered_df = filtered_df.sort_values("delivery_mins")
    elif sort_by == "Vendor":
        filtered_df = filtered_df.sort_values("source")
    elif sort_by == "Name":
        filtered_df = filtered_df.sort_values("name")

    # ------------------------ VIEW MODE ------------------------
    view = st.radio("View as", ["Card View", "Table View"], horizontal=True)

    # ------------------------ CARD VIEW ------------------------
    if view == "Card View":
        st.markdown("### 🛍️ Products")

        cols = st.columns(3)

        if filtered_df.empty:
            st.warning("No items match filters.")
        else:
            for i, row in filtered_df.iterrows():
                col = cols[i % 3]
                with col:
                    with st.container(border=True):
                        if row.get("image_url"):
                            st.image(row["image_url"], width=150)

                        st.markdown(f"**{row['name']}**")
                        st.write(f"💰 **{row['price']}**")
                        st.write(f"🏷️ MRP: {row.get('mrp', '-')}")
                        st.write(f"⚖️ {row.get('weight', '-')}")
                        st.write(f"🛍️ {row['source']}")
                        st.write(f"🚚 {row.get('delivery_time', '-')}")
                        
                        if row.get("product_url"):
                            st.link_button("Open Product", row["product_url"])

    # ------------------------ TABLE VIEW ------------------------
    else:
        st.markdown("### 📊 Table View")

        tbl = filtered_df.copy()
        tbl.drop(columns=["image_url", "price_num", "delivery_mins"], inplace=True, errors="ignore")

        st.dataframe(tbl, use_container_width=True)

        st.download_button(
            "💾 Download CSV",
            tbl.to_csv(index=False),
            "bestdeal_prices.csv",
            mime="text/csv"
        )


# ------------------------ FOOTER ------------------------
st.markdown("---")
st.caption("Built with ❤️ for smart grocery shopping")
