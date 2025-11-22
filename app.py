import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import time

# Set seaborn theme
sns.set_theme(style="whitegrid")

# Page Configuration
st.set_page_config(page_title="Food Waste Management", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1A4511;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

# ---------------Connect to MySQL--------------------
@st.cache_resource
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="1997",
            database="food_waste_management",
            autocommit=False
        )
        return conn
    except Error as e:
        st.error(f"❌ Database Connection Error: {e}")
        st.stop()

if "conn" not in st.session_state:
    st.session_state.conn = get_connection()
conn = st.session_state.conn


#------------Reusable SQL query function with error handling---------------
def run_query(query, params=None):
    try:
        cursor = conn.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(rows)
    except Error as e:
        st.error(f"❌ Query Error: {e}")
        return pd.DataFrame()

# --------------Read the four dataframes--------------
@st.cache_data()
def load_data(_refresh_trigger):
    df_provider = run_query("SELECT * FROM providers_data")
    df_receiver = run_query("SELECT * FROM receivers_data")
    df_food = run_query("SELECT * FROM food_listings_data")
    df_claim = run_query("SELECT * FROM claims_data")
    return df_provider, df_receiver, df_food, df_claim

def refresh_data():
    st.session_state.refresh_trigger += 1
    st.cache_data.clear()

df_provider, df_receiver, df_food, df_claim = load_data(st.session_state.refresh_trigger)

# Header
try:
    st.image("image.jpg", width= 'stretch')
except:
    st.markdown("<div class='main-header'>🍽️ Food Waste Management System</div>", unsafe_allow_html=True)

st.markdown(
    """
    <p style='text-align: center; color: #1A4511; font-size:18px;'>
        🥗 Food is precious — let's make sure none goes to waste
    </p>
    """,
    unsafe_allow_html=True
)

# ------------------ Enhanced Filter Options --------------------
with st.sidebar:
    st.markdown("### 🔍 Filter Options")
    
    with st.expander("🍴 Food Listing Filters", expanded=True):
        # Defensive checks when dataframes may be empty
        provider_cities = sorted(df_provider['City'].dropna().unique().tolist()) if not df_provider.empty else []
        food_types = sorted(df_food['Food_Type'].dropna().unique().tolist()) if not df_food.empty else []
        provider_types = sorted(df_provider['Type'].dropna().unique().tolist()) if not df_provider.empty else []
        meal_types = sorted(df_food['Meal_Type'].dropna().unique().tolist()) if not df_food.empty else []

        col1, col2 = st.columns(2)
        
        with col1:
            city = st.selectbox("📍 City", options=["All"] + provider_cities, key="filter_city")
            food_type = st.selectbox("🥘 Food Type", options=["All"] + food_types, key="filter_food_type")
        
        with col2:
            provider_type = st.selectbox("🏪 Provider Type", options=["All"] + provider_types, key="filter_provider_type")
            meal_type = st.selectbox("⏰ Meal Type", options=["All"] + meal_types, key="filter_meal_type")
        
        # Text search
        search_term = st.text_input("🔎 Search Food Name", "", key="filter_search")

    # Apply filters
    df_filtered = df_food.copy() if not df_food.empty else pd.DataFrame()
    
    if city != "All" and not df_filtered.empty:
        # some data uses 'Location' and provider uses 'City' - keep original logic
        df_filtered = df_filtered[df_filtered['Location'] == city]
    if provider_type != "All" and not df_filtered.empty:
        df_filtered = df_filtered[df_filtered['Provider_Type'] == provider_type]
    if food_type != "All" and not df_filtered.empty:
        df_filtered = df_filtered[df_filtered['Food_Type'] == food_type]
    if meal_type != "All" and not df_filtered.empty:
        df_filtered = df_filtered[df_filtered['Meal_Type'] == meal_type]
    if search_term and not df_filtered.empty:
        df_filtered = df_filtered[df_filtered['Food_Name'].str.contains(search_term, case=False, na=False)]
    
    st.markdown(f"**{len(df_filtered)} listings found**")
    
    with st.expander("📋 Filtered Results", expanded=False):
        if len(df_filtered) > 0:
            st.dataframe(df_filtered, width= 'stretch', height=300)
        else:
            st.info("No listings match your filters")
    
    # Export filtered data
    if len(df_filtered) > 0:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Filtered Data",
            data=csv,
            file_name=f"filtered_listings_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="export_filtered"
        )

#--------------------------------Navigation---------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔍 Query Insights", "🛠️ CRUD Operations", "📞 Contact Providers"])

with tab1:
    st.header("📊 Dashboard Overview")
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_providers = len(df_provider)
        st.metric("🏪 Total Providers", total_providers)
    
    with col2:
        total_receivers = len(df_receiver)
        st.metric("🤝 Total Receivers", total_receivers)
    
    with col3:
        active_listings = len(df_food)
        st.metric("📋 Active Listings", active_listings)
    
    with col4:
        total_claims = len(df_claim)
        st.metric("✅ Total Claims", total_claims)
    
    st.markdown("---")
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Top 10 Cities by Food Listings")

        if not df_food.empty:
            city_counts = df_food['Location'].value_counts().reset_index()
            city_counts.columns = ['City', 'Count']
            city_counts = city_counts.head(10)   # 🔥 Top 10 cities
        else:
            city_counts = pd.DataFrame(columns=['City', 'Count'])

        # Seaborn bar chart
        fig, ax = plt.subplots(figsize=(8, 4))
        if not city_counts.empty:
            sns.barplot(data=city_counts, x='City', y='Count', palette='viridis', ax=ax)
            ax.set_xlabel("City")
            ax.set_ylabel("Count")
            ax.set_title("Top 10 Cities by Food Listings")
            plt.xticks(rotation=45)
        else:
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            ax.axis('off')

        plt.tight_layout()
        st.pyplot(fig)

    
    with col2:
        st.subheader("🥘 Food Type Distribution")
        if not df_food.empty:
            food_type_counts = df_food['Food_Type'].value_counts()
        else:
            food_type_counts = pd.Series(dtype=int)
        # Matplotlib pie (donut)
        fig, ax = plt.subplots(figsize=(6, 6))
        if not food_type_counts.empty:
            labels = food_type_counts.index.tolist()
            sizes = food_type_counts.values
            palette = sns.color_palette("Set3", n_colors=len(labels))
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=palette, pctdistance=0.85)
            centre_circle = plt.Circle((0,0),0.60,fc='white')
            fig.gca().add_artist(centre_circle)
            ax.set_title("Food Type Distribution")
        else:
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            ax.axis('off')
        plt.tight_layout()
        st.pyplot(fig)
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⏰ Meal Type Analysis")
        if not df_food.empty:
            meal_counts = df_food['Meal_Type'].value_counts().reset_index()
            meal_counts.columns = ['Meal Type', 'Count']
        else:
            meal_counts = pd.DataFrame(columns=['Meal Type', 'Count'])
        fig, ax = plt.subplots(figsize=(8, 4))
        if not meal_counts.empty:
            sns.barplot(data=meal_counts, x='Meal Type', y='Count', palette='Set2', ax=ax)
            ax.set_title("Meal Type Distribution")
            plt.xticks(rotation=45)
        else:
            ax.text(0.5, 0.5, "No data available", ha='center', va='center')
            ax.axis('off')
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        st.subheader("📊 Claim Status Breakdown")
        if not df_claim.empty:
            status_counts = df_claim['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
        else:
            status_counts = pd.DataFrame(columns=['Status', 'Count'])
        fig, ax = plt.subplots(figsize=(8, 4))
        if not status_counts.empty:
            # Use explicit color ordering if keys present
            status_order = status_counts['Status'].tolist()
            # create palette mapping for known statuses
            palette_map = {'Completed': '#28a745', 'Pending': '#ffc107', 'Cancelled': '#dc3545'}
            colors = [palette_map.get(s, '#6c757d') for s in status_order]
            sns.barplot(data=status_counts, x='Status', y='Count', palette=colors, ax=ax)
            ax.set_title("Claim Status Breakdown")
            plt.xticks(rotation=45)
        else:
            ax.text(0.5, 0.5, "No claims data available", ha='center', va='center')
            ax.axis('off')
        plt.tight_layout()
        st.pyplot(fig)
    
    # Charts Row 3
    st.subheader("🏪 Provider Type vs Food Quantity")
    if not df_food.empty:
        provider_qty = df_food.groupby('Provider_Type')['Quantity'].sum().reset_index()
    else:
        provider_qty = pd.DataFrame(columns=['Provider_Type', 'Quantity'])
    fig, ax = plt.subplots(figsize=(8, 4))
    if not provider_qty.empty:
        sns.barplot(data=provider_qty, x='Provider_Type', y='Quantity', palette='Blues', ax=ax)
        ax.set_title("Food Quantity by Provider Type")
        plt.xticks(rotation=45)
    else:
        ax.text(0.5, 0.5, "No data available", ha='center', va='center')
        ax.axis('off')
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown("---")
    
    # Data Tables
    st.subheader("📋 Data Tables")
    
    table_options = {
        "Providers": df_provider,
        "Receivers": df_receiver,
        "Food Listings": df_food,
        "Claims": df_claim
    }
    
    for table_name, df in table_options.items():
        with st.expander(f"📄 {table_name} ({len(df)} records)"):
            st.dataframe(df, width= 'stretch', height=300)
            
            # Export button for each table
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Export {table_name}",
                data=csv,
                file_name=f"{table_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key=f"export_{table_name}"
            )

with tab2:
    st.header("🔍 SQL Query Insights")
    
    queries = {
        "1. Providers and Receivers by City" : 
        """SELECT City, SUM(num_providers) as Total_providers, SUM(num_receivers) as Total_receivers
        FROM (
            SELECT City, COUNT(*) AS num_providers, 0 AS num_receivers
            FROM providers_data
            GROUP BY City
            UNION ALL
            SELECT City, 0 AS num_providers, COUNT(*) AS num_receivers
            FROM receivers_data
            GROUP BY City
        ) AS alias
        GROUP BY City""",
        
        "2. Top Contributing Provider Type" :
        """SELECT Provider_Type, SUM(Quantity) as total_quantity
        FROM food_listings_data
        GROUP BY Provider_Type
        ORDER BY total_quantity DESC""",

        "3. Provider Contact by City" : "DYNAMIC_CITY_QUERY",

        "4. Top Receivers by Claims" : 
        """SELECT c.Receiver_ID, r.Name, COUNT(c.Claim_ID) as total_claims
        FROM claims_data c
        JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY c.Receiver_ID, r.Name
        ORDER BY total_claims DESC
        LIMIT 10""",

        "5. Total Available Food Quantity" :
        """SELECT SUM(f.Quantity) as total_quantity
        FROM food_listings_data f""",

        "6. City with Most Listings" :
        """SELECT Location, COUNT(*) as listing_count
        FROM food_listings_data
        GROUP BY Location
        ORDER BY listing_count DESC""",

        "7. Most Common Food Types" :
        """SELECT Food_Type, COUNT(*) as count_
        FROM food_listings_data
        GROUP BY Food_Type
        ORDER BY count_ DESC""",

        "8. Claims per Food Item" :
        """SELECT f.Food_Name, COUNT(c.Claim_ID) as no_of_claims
        FROM food_listings_data f
        JOIN claims_data c ON f.Food_ID = c.Food_ID
        GROUP BY f.Food_Name
        ORDER BY no_of_claims DESC""",

        "9. Provider with Most Successful Claims" :
        """SELECT p.Provider_ID, p.Name, COUNT(c.Claim_ID) as successful_claims
        FROM providers_data p
        JOIN food_listings_data f ON p.Provider_ID = f.Provider_ID
        JOIN claims_data c ON f.Food_ID = c.Food_ID
        WHERE c.Status = "Completed"
        GROUP BY p.Provider_ID, p.Name
        ORDER BY successful_claims DESC
        LIMIT 10""",

        "10. Claim Status Percentages" :
        """SELECT
        ROUND(SUM(CASE WHEN Status = "Pending" THEN 1 ELSE 0 END) * 100.0 /COUNT(*), 2) AS Pending_Percentage,
        ROUND(SUM(CASE WHEN Status = "Cancelled" THEN 1 ELSE 0 END) * 100.0 /COUNT(*), 2) AS Cancelled_Percentage,
        ROUND(SUM(CASE WHEN Status = "Completed" THEN 1 ELSE 0 END) * 100.0 /COUNT(*), 2) AS Completed_Percentage
        FROM claims_data""",

        "11. Average Quantity per Receiver" :
        """SELECT c.Receiver_ID, r.Name, AVG(f.Quantity) AS average_quantity
        FROM claims_data c
        JOIN food_listings_data f ON c.Food_ID = f.Food_ID
        JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY c.Receiver_ID, r.Name
        ORDER BY average_quantity DESC""",

        "12. Most Claimed Meal Type" :
        """SELECT f.Meal_Type, COUNT(c.Claim_ID) as claim_count
        FROM claims_data c
        JOIN food_listings_data f ON c.Food_ID = f.Food_ID 
        GROUP BY f.Meal_Type
        ORDER BY claim_count DESC""",

        "13. Total Donations by Provider" :
        """SELECT p.Provider_ID, p.Name, COALESCE(SUM(f.Quantity), 0) as total_quantity
        FROM providers_data p
        LEFT JOIN food_listings_data f ON p.Provider_ID = f.Provider_ID
        GROUP BY p.Provider_ID, p.Name
        ORDER BY total_quantity DESC""",

        "14. Most Active City (Providers)" : 
        """SELECT p.City, COUNT(DISTINCT p.Provider_ID) AS active_providers
        FROM providers_data p
        JOIN food_listings_data f ON p.Provider_ID = f.Provider_ID
        GROUP BY p.City
        ORDER BY active_providers DESC""",

        "15. Top Receiver Type by Claims" :
        """SELECT r.Type, SUM(f.Quantity) as total_quantity
        FROM receivers_data r
        JOIN claims_data c ON r.Receiver_ID = c.Receiver_ID
        JOIN food_listings_data f ON c.Food_ID = f.Food_ID
        GROUP BY r.Type
        ORDER BY total_quantity DESC""",

        "16. Food Listing Duration" :
        """SELECT f.Food_ID, f.Food_Name, c.Claim_ID, 
               DATEDIFF(c.Timestamp, f.Expiry_Date) AS stay_time_days
        FROM food_listings_data f
        JOIN claims_data c ON f.Food_ID = c.Food_ID 
        ORDER BY f.Food_ID""",

        "17. Provider Type Food Variety" :
        """SELECT f.Provider_Type, COUNT(DISTINCT Food_Name) as variety_count
        FROM food_listings_data f
        GROUP BY f.Provider_Type
        ORDER BY variety_count DESC""",

        "18. Receiver Success Rate" : 
        """SELECT c.Receiver_ID, r.Name,
               ROUND(SUM(CASE WHEN Status = "Completed" THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate,
               COUNT(*) as total_claims
        FROM claims_data c
        JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY c.Receiver_ID, r.Name
        HAVING COUNT(*) > 0
        ORDER BY success_rate DESC""",

        "19. Busiest Claim Day" :
        """SELECT 
               CASE WEEKDAY(c.timestamp)
                   WHEN 0 THEN 'Monday'
                   WHEN 1 THEN 'Tuesday'
                   WHEN 2 THEN 'Wednesday'
                   WHEN 3 THEN 'Thursday'
                   WHEN 4 THEN 'Friday'
                   WHEN 5 THEN 'Saturday'
                   WHEN 6 THEN 'Sunday'
               END AS Day_Name,
               COUNT(*) as claim_count
        FROM claims_data c
        GROUP BY WEEKDAY(c.timestamp), Day_Name
        ORDER BY claim_count DESC""",

        "20. Average Quantity by Meal Type" :
        """SELECT Meal_Type, ROUND(AVG(Quantity), 2) AS average_quantity
        FROM food_listings_data
        GROUP BY Meal_Type
        ORDER BY average_quantity DESC""",

        "21. Listed vs Claimed Quantities" :
        """SELECT 
            ROUND((SELECT AVG(Quantity) FROM food_listings_data), 2) AS avg_listed_quantity,
            ROUND((SELECT AVG(f.Quantity) FROM food_listings_data f 
                JOIN claims_data c ON f.Food_ID = c.Food_ID), 2) AS avg_claimed_quantity""",

        "22. Food Type with Highest Wastage" :
        """SELECT f.Food_Type, SUM(f.Quantity) AS wasted_quantity
        FROM food_listings_data f
        LEFT JOIN claims_data c ON f.Food_ID = c.Food_ID
        WHERE c.Claim_ID IS NULL
        GROUP BY f.Food_Type
        ORDER BY wasted_quantity DESC""",

        "23. Receivers with Zero Completed Claims" :
        """SELECT r.Receiver_ID, r.Name, r.Type
        FROM receivers_data r
        LEFT JOIN claims_data c ON r.Receiver_ID = c.Receiver_ID AND c.Status = 'Completed'
        GROUP BY r.Receiver_ID, r.Name, r.Type
        HAVING COUNT(c.Claim_ID) = 0""",

        "24. Food Preferences by Receiver Type" :
        """SELECT r.Type AS Receiver_Type, f.Food_Type, COUNT(*) AS claim_count
        FROM claims_data c
        JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
        JOIN food_listings_data f ON c.Food_ID = f.Food_ID
        GROUP BY r.Type, f.Food_Type
        ORDER BY Receiver_Type, claim_count DESC""",

        "25. Top Cities with Cancelled Claims" :
        """SELECT f.Location, COUNT(*) AS cancelled_claims
        FROM claims_data c
        JOIN food_listings_data f ON f.Food_ID = c.Food_ID
        WHERE c.Status = 'Cancelled'
        GROUP BY f.Location
        ORDER BY cancelled_claims DESC
        LIMIT 10"""
    }

    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_query = st.selectbox("📝 Choose a query to run", list(queries.keys()))
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_button = st.button("▶️ Run Query", type="primary", width= 'stretch')

    if run_button or selected_query:
        with st.spinner("⏳ Running query..."):
            if queries[selected_query] == "DYNAMIC_CITY_QUERY":
                city_options = sorted(df_provider["City"].unique().tolist()) if not df_provider.empty else []
                selected_city = st.selectbox("📍 Select a City", city_options)
                result_df = run_query("SELECT * FROM providers_data WHERE City = %s", (selected_city,))
            else:
                result_df = run_query(queries[selected_query])
            
            if not result_df.empty:
                st.success(f"✅ Query returned {len(result_df)} rows")
                st.dataframe(result_df.reset_index(drop=True), width= 'stretch', height=400)
                
                # Export query results
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Results",
                    data=csv,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("ℹ️ Query returned no results")

with tab3:
    st.header("🛠️ Manage Food Listings")
    
    mode = st.radio("Select Operation", ["➕ Add", "✏️ Update", "🗑️ Remove"], horizontal=True)
    
    st.markdown("---")
    
    if mode == "➕ Add":
        st.subheader("➕ Add New Food Listing")
        
        with st.form("add_listing_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                food_id = st.number_input("🆔 Food ID", min_value=1, step=1)
                food_name = st.text_input("🍽️ Food Name", max_chars=100)
                quantity = st.number_input("📦 Quantity", min_value=1, step=1)
            
            with col2:
                expiry_date = st.date_input("📅 Expiry Date", min_value=datetime.now().date())
                provider_id = st.selectbox("🏪 Provider ID", sorted(df_provider['Provider_ID'].unique()) if not df_provider.empty else [1])
                provider_type = st.selectbox("🏢 Provider Type", sorted(df_provider['Type'].unique()) if not df_provider.empty else ["Unknown"])
            
            with col3:
                location = st.selectbox("📍 Location", sorted(df_provider['City'].unique()) if not df_provider.empty else ["Unknown"])
                food_type = st.selectbox("🥘 Food Type", sorted(df_food['Food_Type'].unique()) if not df_food.empty else ["Unknown"])
                meal_type = st.selectbox("⏰ Meal Type", sorted(df_food['Meal_Type'].unique()) if not df_food.empty else ["Unknown"])
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submitted = st.form_submit_button("➕ Add Listing", type="primary", width= 'stretch')
            
            if submitted:
                # Validation
                if not food_name or food_name.strip() == "":
                    st.error("❌ Food name cannot be empty!")
                elif not df_food.empty and df_food['Food_ID'].isin([food_id]).any():
                    st.error(f"❌ Food ID {food_id} already exists. Please use a different ID.")
                elif expiry_date < datetime.now().date():
                    st.error("❌ Expiry date must be in the future!")
                else:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO food_listings_data 
                            (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (int(food_id), food_name.strip(), int(quantity), expiry_date, int(provider_id), provider_type, location, food_type, meal_type))
                        conn.commit()
                        cursor.close()
                        
                        st.success(f"✅ Listing '{food_name}' added successfully!")
                        refresh_data()
                        time.sleep(1)
                        st.rerun()
                    except Error as e:
                        st.error(f"❌ Error adding listing: {e}")
                        conn.rollback()

    elif mode == "✏️ Update":
        st.subheader("✏️ Update Existing Listing")
        
        if df_food.empty:
            st.warning("⚠️ No listings available to update")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                listing_id = st.selectbox("🔍 Select Listing ID to Update", sorted(df_food['Food_ID'].unique()), key="update_listing_id")
            
            if listing_id:
                row = df_food[df_food['Food_ID'] == listing_id].iloc[0]
                
                st.markdown("#### Current Listing Details:")
                current_data = pd.DataFrame([{
                    "Food ID": row['Food_ID'],
                    "Name": row['Food_Name'],
                    "Quantity": row['Quantity'],
                    "Expiry Date": row['Expiry_Date']
                }])
                st.dataframe(current_data, width= 'stretch', hide_index=True)
                
                st.markdown("---")
                st.markdown("#### Update Fields:")
                
                with st.form("update_listing_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_qty = st.number_input("📦 New Quantity", value=int(row['Quantity']), min_value=1)
                    
                    with col2:
                        # Handle expiry date to avoid min_value issue
                        current_expiry = pd.to_datetime(row['Expiry_Date']).date()
                        today = datetime.now().date()
                        # Use the later date between current expiry and today
                        default_expiry = max(current_expiry, today)
                        
                        new_expiry = st.date_input("📅 New Expiry Date", 
                                                  value=default_expiry,
                                                  min_value=today)
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        submitted = st.form_submit_button("💾 Update Listing", type="primary", width= 'stretch')
                    
                    if submitted:
                        if new_expiry < datetime.now().date():
                            st.error("❌ Expiry date must be in the future!")
                        else:
                            try:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE food_listings_data SET Quantity=%s, Expiry_Date=%s WHERE Food_ID=%s",
                                    (int(new_qty), new_expiry, int(listing_id))
                                )
                                conn.commit()
                                cursor.close()
                                
                                st.success(f"✅ Listing ID {listing_id} updated successfully!")
                                refresh_data()
                                time.sleep(1)
                                st.rerun()
                            except Error as e:
                                st.error(f"❌ Error updating listing: {e}")
                                conn.rollback()

    elif mode == "🗑️ Remove":
        st.subheader("🗑️ Remove Listing")
        
        if df_food.empty:
            st.warning("⚠️ No listings available to remove")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                listing_id = st.selectbox("🔍 Select Listing ID to Delete", sorted(df_food['Food_ID'].unique()), key="delete_listing_id")
            
            if listing_id:
                listing_data = df_food[df_food['Food_ID'] == listing_id]
                
                st.markdown("#### ⚠️ Listing Selected for Deletion:")
                st.dataframe(listing_data, width= 'stretch', hide_index=True)
                
                st.markdown("---")
                
                with st.form("delete_listing_form"):
                    st.warning("⚠️ This action cannot be undone!")

                    confirm = st.checkbox("I confirm this deletion")

                    submitted = st.form_submit_button("🗑️ Delete Listing", type="primary")

                    if submitted:
                        if not confirm:
                            st.error("❌ Please confirm the deletion before proceeding.")
                        else:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM food_listings_data WHERE Food_ID=%s", (int(listing_id),))
                                conn.commit()
                                cursor.close()

                                st.success(f"✅ Listing ID {listing_id} deleted successfully!")
                                refresh_data()
                                st.rerun()

                            except Error as e:
                                st.error(f"❌ Error deleting listing: {e}")
                                conn.rollback()

with tab4:
    st.header("📞 Provider Contact Information")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_option = st.radio("Search by:", ["Provider ID", "Provider Name", "City"], horizontal=True)
    
    st.markdown("---")
    
    if search_option == "Provider ID":
        provider_id = st.number_input("🆔 Enter Provider ID", 
                                     min_value=1, 
                                     step=1, 
                                     max_value=int(df_provider['Provider_ID'].max()) if not df_provider.empty else 1,
                                     key="contact_provider_id")
        
        if st.button("🔍 Search", type="primary", key="search_by_id"):
            with st.spinner("Searching..."):
                result = run_query("SELECT * FROM providers_data WHERE Provider_ID = %s", (provider_id,))
                
                if not result.empty:
                    st.success(f"✅ Found provider!")
                    
                    # Display provider details in a nice card format
                    provider = result.iloc[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div style='background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
                            <h4 style='color: #1A4511; margin-bottom: 1rem;'>📋 Basic Information</h4>
                            <p><strong>🆔 Provider ID:</strong> {provider['Provider_ID']}</p>
                            <p><strong>🏢 Name:</strong> {provider['Name']}</p>
                            <p><strong>🏪 Type:</strong> {provider['Type']}</p>
                            <p><strong>📍 City:</strong> {provider['City']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div style='background-color: #e8f5e9; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
                            <h4 style='color: #1A4511; margin-bottom: 1rem;'>📞 Contact Details</h4>
                            <p><strong>📧 Email:</strong> {provider.get('Email', 'N/A')}</p>
                            <p><strong>☎️ Phone:</strong> {provider.get('Phone', 'N/A')}</p>
                            <p><strong>🏠 Address:</strong> {provider.get('Address', 'N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show provider's food listings
                    st.markdown("---")
                    st.subheader("🍽️ Current Food Listings")
                    
                    provider_listings = df_food[df_food['Provider_ID'] == provider_id] if not df_food.empty else pd.DataFrame()
                    
                    if not provider_listings.empty:
                        st.dataframe(provider_listings, width= 'stretch', height=300)
                        
                        # Statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📋 Total Listings", len(provider_listings))
                        with col2:
                            st.metric("📦 Total Quantity", int(provider_listings['Quantity'].sum()))
                        with col3:
                            st.metric("🥘 Food Types", provider_listings['Food_Type'].nunique())
                    else:
                        st.info("ℹ️ No current listings for this provider")
                else:
                    st.error(f"❌ No provider found with ID {provider_id}")
    
    elif search_option == "Provider Name":
        provider_names = sorted(df_provider['Name'].unique().tolist()) if not df_provider.empty else []
        provider_name = st.selectbox("🏢 Select Provider Name", provider_names, key="contact_provider_name")
        
        if st.button("🔍 Search", type="primary", key="search_by_name"):
            with st.spinner("Searching..."):
                result = run_query("SELECT * FROM providers_data WHERE Name = %s", (provider_name,))
                
                if not result.empty:
                    st.success(f"✅ Found {len(result)} provider(s)!")
                    
                    for idx, provider in result.iterrows():
                        with st.expander(f"🏪 {provider['Name']} - ID: {provider['Provider_ID']}", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"""
                                <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 8px;'>
                                    <p><strong>🆔 Provider ID:</strong> {provider['Provider_ID']}</p>
                                    <p><strong>🏪 Type:</strong> {provider['Type']}</p>
                                    <p><strong>📍 City:</strong> {provider['City']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown(f"""
                                <div style='background-color: #e8f5e9; padding: 1rem; border-radius: 8px;'>
                                    <p><strong>📧 Email:</strong> {provider.get('Email', 'N/A')}</p>
                                    <p><strong>☎️ Phone:</strong> {provider.get('Phone', 'N/A')}</p>
                                    <p><strong>🏠 Address:</strong> {provider.get('Address', 'N/A')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Show listings for this specific provider
                            provider_listings = df_food[df_food['Provider_ID'] == provider['Provider_ID']] if not df_food.empty else pd.DataFrame()
                            if not provider_listings.empty:
                                st.markdown("##### 🍽️ Current Listings:")
                                st.dataframe(provider_listings, width= 'stretch', height=200)
                else:
                    st.error(f"❌ No provider found with name '{provider_name}'")
    
    else:  # Search by City
        cities = sorted(df_provider['City'].unique().tolist()) if not df_provider.empty else []
        city = st.selectbox("📍 Select City", cities, key="contact_city")
        
        if st.button("🔍 Search", type="primary", key="search_by_city"):
            with st.spinner("Searching..."):
                result = run_query("SELECT * FROM providers_data WHERE City = %s", (city,))
                
                if not result.empty:
                    st.success(f"✅ Found {len(result)} provider(s) in {city}!")
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🏪 Total Providers", len(result))
                    with col2:
                        provider_types = result['Type'].nunique()
                        st.metric("🏢 Provider Types", provider_types)
                    with col3:
                        city_listings = df_food[df_food['Location'] == city] if not df_food.empty else pd.DataFrame()
                        st.metric("📋 Total Listings", len(city_listings))
                    
                    st.markdown("---")
                    
                    # Display all providers in the city
                    for idx, provider in result.iterrows():
                        with st.expander(f"🏪 {provider['Name']} - {provider['Type']}", expanded=False):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"""
                                <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 8px;'>
                                    <p><strong>🆔 ID:</strong> {provider['Provider_ID']}</p>
                                    <p><strong>🏢 Name:</strong> {provider['Name']}</p>
                                    <p><strong>🏪 Type:</strong> {provider['Type']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown(f"""
                                <div style='background-color: #e8f5e9; padding: 1rem; border-radius: 8px;'>
                                    <p><strong>📧 Email:</strong> {provider.get('Email', 'N/A')}</p>
                                    <p><strong>☎️ Phone:</strong> {provider.get('Phone', 'N/A')}</p>
                                    <p><strong>🏠 Address:</strong> {provider.get('Address', 'N/A')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Export all providers in city
                    st.markdown("---")
                    csv = result.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📥 Export All Providers in {city}",
                        data=csv,
                        file_name=f"providers_{city}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )
                else:
                    st.error(f"❌ No providers found in {city}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:gray; font-size:14px;">
    Made with 💚 by <b>Niladri Giri</b><br>
            <p style='font-size: 0.9rem;'>Connecting food providers with those in need</p>
    <span style="font-size:12px;">Powered by Streamlit and MySQL</span>
</div>
""", unsafe_allow_html=True)
