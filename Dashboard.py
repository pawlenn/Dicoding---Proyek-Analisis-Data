import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

# Helper function yang dibutuhkan untuk menyiapkan berbagai dataframe

def create_monthly_data (df) :
    monthly_data = df.groupby(df['dteday'].dt.to_period('M'))[['cnt']].sum().reset_index()
    # Konversi dteday dari Period[M] ke datetime
    monthly_data['dteday'] = monthly_data['dteday'].dt.to_timestamp()

    # Buat kolom 'Year' dan 'Month'
    monthly_data['Year'] = monthly_data['dteday'].dt.year
    monthly_data['Month'] = monthly_data['dteday'].dt.strftime('%B')

    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data['Month'] = pd.Categorical(monthly_data['Month'], categories=month_order, ordered=True)
    return monthly_data

def create_temp_cnt_df(df):
    t_min = -8
    t_max = 39

    temp_cnt_data = pd.DataFrame({
        'temp_celsius': df['temp'] * (t_max - t_min) + t_min,
        'cnt': df['cnt']
    })

    # Bins Temperatur (Celcius) dengan rentang 5 derajat
    bins = list(range(int(temp_cnt_data['temp_celsius'].min()), int(temp_cnt_data['temp_celsius'].max()) + 5, 5))
    temp_cnt_data['temp_range'] = pd.cut(temp_cnt_data['temp_celsius'], bins, right=False)
    return temp_cnt_data

def create_comp_data(df):
    comp_data = df.groupby(df['dteday'].dt.to_period('M'))[['casual','registered']].sum().reset_index()
    return comp_data

def create_casual_dom_df (df):
    casual_dom_df = df[df['casual'] > df['registered']]
    return casual_dom_df

def create_hourly_user (df):
    hourly_user = df.groupby('hr')['cnt'].mean().reset_index()
    return hourly_user

def create_rush_hour(df):
    def categorize_time(hour):
        if 7 <= hour <= 9 or 16 <= hour <= 19:
            return "Jam Sibuk"
        else:
            return "Jam Santai"

    df["hr"] = df["hr"].astype(int) #ubah menjadi integer
    df["time_category"] = df["hr"].apply(categorize_time)
    df.groupby("time_category")["cnt"].sum()
    return df

def create_day_category (df) :
    def categorize_day(row):
        if row["holiday"] == 1:
            return "Holiday"
        elif row["workingday"] == 1:
            return "Weekday"
        else:
            return "Weekend"

    # Buat kolom baru berdasarkan kategori hari
    df["day_category"] = df.apply(categorize_day, axis=1)
    return df


# Load cleaned data
final_day_df = pd.read_csv("day_data.csv")
final_hour_df = pd.read_csv("hour_data.csv")

datetime_columns = ["dteday"]

final_day_df.sort_values(by="dteday", inplace=True)
final_day_df.reset_index(inplace=True)
for column in datetime_columns:
    final_day_df[column] = pd.to_datetime(final_day_df[column])

final_hour_df.sort_values(by="dteday", inplace=True)
final_hour_df.reset_index(inplace=True)
for column in datetime_columns:
    final_hour_df[column] = pd.to_datetime(final_hour_df[column])

# Filter data
min_date = final_day_df["dteday"].min()
max_date = final_day_df["dteday"].max()

with st.sidebar:
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_day_df = final_day_df[(final_day_df["dteday"] >= str(start_date)) & 
                (final_day_df["dteday"] <= str(end_date))]
main_hour_df = final_hour_df[(final_hour_df["dteday"] >= str(start_date)) & 
                (final_hour_df["dteday"] <= str(end_date))]

# Menyiapkan berbagai dataframe
monthly_data = create_monthly_data(main_day_df)
temp_cnt_data = create_temp_cnt_df(main_day_df)
grouped_temp = temp_cnt_data.groupby('temp_range')['cnt'].mean().reset_index()
comp_data = create_comp_data(main_day_df)
casual_dom_df = create_casual_dom_df(main_hour_df)
hourly_user = create_hourly_user(main_hour_df)
rush_hour = create_rush_hour(main_hour_df)
day_category = create_day_category(main_day_df)

st.header(':sparkles: Bike Sharing Dashboard :sparkles:')

# plot tren pengguna 2011 vs 2012
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    Total_User  = monthly_data.cnt.sum()
    st.metric("Total Pengguna", value=Total_User)

with col2:
    maks_user = monthly_data.cnt.max()
    st.metric("Pengguna Bulanan Terbesar", value=maks_user)

fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(data=monthly_data, x='Month', y='cnt', hue='Year', marker='o', palette=["#008174", "#000181"], ax=ax)

ax.set_title('Total Pengguna Bulanan pada 2011 dan 2012', fontsize=14)
ax.set_xlabel('Bulan', fontsize=12)
ax.set_ylabel('Total Pengguna', fontsize=12)
ax.set_xticklabels(monthly_data['Month'].unique(), rotation=45)
ax.legend(title="Year")
ax.grid(True)

st.pyplot(fig)

# plot rentang suhu
st.subheader("Pengaruh Suhu terhadap Jumlah Pengguna Sepeda")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Scatter Plot
sns.scatterplot(x=temp_cnt_data['temp_celsius'], y=temp_cnt_data['cnt'], ax=axes[0])
axes[0].set_title("Korelasi antara Suhu dan Total Pengguna")
axes[0].set_xlabel("Suhu (Celsius)")
axes[0].set_ylabel("Total Pengguna")

# Bar Chart (rata-rata 'cnt' per kategori temp_range)
bar_data = grouped_temp.groupby('temp_range', observed=True)['cnt'].mean().reset_index()
# Highlight bar ke-7 (jumlah paling besar)
colors = ["#D3D3D3"] * len(bar_data)
colors[6] = "#72BCD4"

sns.barplot(x='temp_range', y='cnt', data=bar_data, palette=colors, ax=axes[1])
axes[1].set_title("Rata-rata Pengguna Berdasarkan Rentang Suhu")
axes[1].set_xlabel("Suhu (Celsius)")
axes[1].set_ylabel("Total Pengguna")

# Menghapus legenda jika ada
if axes[1].get_legend() is not None:
    axes[1].get_legend().remove()

plt.suptitle("Pengaruh Suhu terhadap Jumlah Pengguna Sepeda", fontsize=20)
plt.subplots_adjust(hspace=0.5)

st.pyplot(fig)

# plot tren pengguna casual vs terdaftar
st.subheader("Tren Jumlah Casual dan Registered Users Seiring Waktu")

# dteday adalah period dan ubah ke datetime
comp_data['dteday'] = comp_data['dteday'].dt.to_timestamp()
comp_data.set_index('dteday', inplace=True)

fig, ax = plt.subplots(figsize=(10, 5))

sns.lineplot(data=comp_data, x=comp_data.index, y='casual', label='Casual Users', color="#008174", ax=ax)
sns.lineplot(data=comp_data, x=comp_data.index, y='registered', label='Registered Users', color="#000181", ax=ax)

ax.set_title("Tren Jumlah Casual dan Registered Users Seiring Waktu")
ax.set_xlabel("Waktu (Bulan)")
ax.set_ylabel("Jumlah Pengguna")
ax.grid(True)
ax.legend()

st.pyplot(fig)

# Plot kondisi pengguna casual > terdaftar

st.subheader("Kondisi saat Pengguna Casual Dominan")
    
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
# Plot 1: Faktor Weekday/Weekend
colors = ["#D3D3D3", "#72BCD4"]  # Weekend (0) abu-abu, Workday (1) biru
sns.countplot(x="workingday", data=casual_dom_df, palette=colors, ax=axes[0, 0])
axes[0, 0].set_title("Jenis Hari (0 = Weekend/Holiday, 1 = Workday)")
axes[0, 0].set_xlabel('Jenis Hari')
axes[0, 0].set_ylabel('Total Pengguna Casual')
    
# Plot 2: Faktor Musim
season_colors = ["#D3D3D3", "#72BCD4", "#D3D3D3", "#D3D3D3"]  # Summer (2) biru
sns.countplot(x="season", data=casual_dom_df, palette=season_colors, ax=axes[0, 1])
axes[0, 1].set_title("Musim")
axes[0, 1].set_xticklabels(['Spring', 'Summer', 'Fall', 'Winter'])
axes[0, 1].set_xlabel('Jenis Musim')
axes[0, 1].set_ylabel('Total Pengguna Casual')
    
# Plot 3: Faktor Temperatur
sns.scatterplot(x=casual_dom_df['temp'], y=casual_dom_df['casual'], ax=axes[1, 0])
axes[1, 0].set_xlabel('Suhu (Dinormalisasi dalam Celcius)')
axes[1, 0].set_ylabel('Total Pengguna Casual')
axes[1, 0].set_title("Temperatur")
    
# Plot 4: Faktor Kecepatan Angin
sns.scatterplot(x=casual_dom_df['windspeed'], y=casual_dom_df['casual'], ax=axes[1, 1])
axes[1, 1].set_xlabel('Kecepatan Angin (Telah dinormalisasi)')
axes[1, 1].set_ylabel('Total Pengguna Casual')
axes[1, 1].set_title("Kecepatan Angin")
    
plt.subplots_adjust(hspace=0.5)
st.pyplot(fig)

# plot pola penggunaan dalam satu hari

st.subheader("Pola Penggunaan Rental Bike dalam Sehari")
    
fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(x=hourly_user['hr'], y=hourly_user['cnt'], marker='o', color="#72BCD4", ax=ax)
    
ax.set_xlabel("Jam dalam Sehari")
ax.set_ylabel("Rata-rata Jumlah Pengguna")
ax.set_title("Pola Penggunaan Rental Bike dalam Sehari")
ax.set_xticks(range(0, 24))  # Pastikan semua jam terlihat dengan jelas
ax.grid()
    
st.pyplot(fig)

# plot rush hour
st.subheader("Perbandingan Penggunaan Rental Bike antara Jam Sibuk dan Jam Santai")

fig, ax = plt.subplots(figsize=(7, 5))

sns.barplot(
    x="time_category",
    y="cnt",
    hue="time_category",
    data=rush_hour,
    palette=["#D3D3D3", "#72BCD4"],
    ax=ax
)
ax.set_xlabel("Kategori Waktu")
ax.set_ylabel("Total Rental Bike")

st.pyplot(fig)

# plot kategori hari
st.subheader("Total Jumlah Rental Bike Berdasarkan Kategori Hari")

# Membuat satu figure untuk kategori hari
fig, ax = plt.subplots(figsize=(6, 4))

# Plot: Total Jumlah Rental Bike Berdasarkan Kategori Hari
sns.barplot(
    x="day_category",
    y="cnt",
    data=day_category,
    estimator=sum,
    hue="day_category",
    palette={"Weekday": "#72BCD4", "Weekend": "#D3D3D3", "Holiday": "#FFB347"},
    ax=ax
)
ax.set_xlabel("Kategori Hari")
ax.set_ylabel("Total Rentals")

# Menampilkan figure di Streamlit
st.pyplot(fig)
