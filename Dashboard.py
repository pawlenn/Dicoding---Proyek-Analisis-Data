import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')
st.markdown("# Penggunaan Sewa Sepeda 🚴‍♀️", unsafe_allow_html=True)

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

# Sidebar: Pilih Rentang Tanggal
st.sidebar.subheader("📅 Pilih Rentang Tanggal")

# Pastikan tidak ada NaT (Not a Time) sebelum mengambil min/max date
if final_day_df["dteday"].isna().sum() > 0:
    st.error("Data memiliki nilai tanggal yang hilang. Periksa dataset Anda.")
else:
    min_date = final_day_df["dteday"].min()
    max_date = final_day_df["dteday"].max()

    if pd.notna(min_date) and pd.notna(max_date):
        # Pilihan rentang tanggal langsung tanpa pemilihan tahun
        start_date, end_date = st.sidebar.date_input(
            "Rentang Tanggal",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

        # Filter data berdasarkan rentang tanggal yang dipilih
        day_filtered = final_day_df[
            (final_day_df["dteday"] >= pd.to_datetime(start_date)) &
            (final_day_df["dteday"] <= pd.to_datetime(end_date))
        ]
        
        hour_filtered = final_hour_df[
            (final_hour_df["dteday"] >= pd.to_datetime(start_date)) &
            (final_hour_df["dteday"] <= pd.to_datetime(end_date))
        ]
    else:
        st.error("Rentang tanggal tidak valid. Periksa dataset Anda.")

# Filter Data berdasarkan Rentang Tanggal
day_filtered = day_filtered[
    (day_filtered["dteday"] >= pd.to_datetime(start_date)) & 
    (day_filtered["dteday"] <= pd.to_datetime(end_date))
]

hour_filtered = hour_filtered[
    (hour_filtered["dteday"] >= pd.to_datetime(start_date)) & 
    (hour_filtered["dteday"] <= pd.to_datetime(end_date))
]

# Hitung metrik utama
total_sewa = day_filtered["cnt"].sum()
avg_sewa = day_filtered["cnt"].mean()
top_day = day_filtered.loc[day_filtered["cnt"].idxmax(), "dteday"].date()

# Tampilkan di sidebar
st.sidebar.metric("Total Sewa", total_sewa)
st.sidebar.metric("Rata-rata Sewa per Hari", round(avg_sewa, 2))
st.sidebar.text(f"Hari Sewa Tertinggi: {top_day}")

# Membuat dataframe
monthly_data = create_monthly_data(day_filtered)
temp_cnt_df = create_temp_cnt_df(day_filtered)
grouped_temp = temp_cnt_df.groupby('temp_range')['cnt'].mean().reset_index()
comp_data = create_comp_data(day_filtered)
casual_dom_df = create_casual_dom_df(hour_filtered)
hourly_user = create_hourly_user(hour_filtered) 
rush_hour = create_rush_hour(hour_filtered)

# plot tren pengguna 2011 vs 2012
st.subheader('Tren Pengguna Sewa Sepeda 2011 dan 2012')

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
ax.set_ylim(0, None)  # Pastikan batas bawah 0
ax.set_xticklabels(monthly_data['Month'].unique(), rotation=45)
ax.legend(title="Year")
ax.grid(True)

st.pyplot(fig)

# Plot rentang suhu
st.subheader("Jumlah Pengguna Sewa Sepeda Berdasarkan Rentang Suhu")
fig, ax = plt.subplots(figsize=(7, 5))

bar_data = grouped_temp.groupby('temp_range', observed=True)['cnt'].mean().reset_index()
colors = ["#D3D3D3"] * len(bar_data)
if len(colors) > 6:
    colors[6] = "#72BCD4"

sns.barplot(x='temp_range', y='cnt', data=bar_data, palette=colors, ax=ax)
ax.set_xlabel("Suhu (Celsius)")
ax.set_ylabel("Total Pengguna")
ax.set_ylim(0, None)  # Pastikan batas bawah 0

if ax.get_legend() is not None:
    ax.get_legend().remove()

plt.tight_layout()
st.pyplot(fig)

# plot tren pengguna casual vs terdaftar
st.subheader("Tren Jumlah Pengguna Casual dan Terdaftar Seiring Waktu")

comp_data['dteday'] = comp_data['dteday'].dt.to_timestamp()
comp_data.set_index('dteday', inplace=True)

fig, ax = plt.subplots(figsize=(10, 5))

sns.lineplot(data=comp_data, x=comp_data.index, y='casual', label='Pengguna Casual', color="#008174", ax=ax)
sns.lineplot(data=comp_data, x=comp_data.index, y='registered', label='Pengguna Terdaftar', color="#000181", ax=ax)

ax.set_xlabel("Waktu (Bulan)")
ax.set_ylabel("Jumlah Pengguna")
ax.set_ylim(0, None)  # Pastikan batas bawah 0
ax.grid(True)
ax.legend()

st.pyplot(fig)

# Plot kondisi pengguna casual > terdaftar
st.subheader("Kondisi saat Pengguna Casual Dominan")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

colors = ["#D3D3D3", "#72BCD4"]
sns.countplot(x="workingday", data=casual_dom_df, palette=colors, ax=axes[0])
axes[0].set_title("Jenis Hari (0 = Weekend/Holiday, 1 = Workday)")
axes[0].set_xlabel('Jenis Hari')
axes[0].set_ylabel('Total Pengguna Casual')
axes[0].set_ylim(0, None)  # Pastikan batas bawah 0

season_colors = ["#D3D3D3", "#72BCD4", "#D3D3D3", "#D3D3D3"]
sns.countplot(x="season", data=casual_dom_df, palette=season_colors, ax=axes[1])
axes[1].set_title("Musim")
axes[1].set_xticklabels(['Spring', 'Summer', 'Fall', 'Winter'])
axes[1].set_xlabel('Jenis Musim')
axes[1].set_ylabel('Total Pengguna Casual')
axes[1].set_ylim(0, None)  # Pastikan batas bawah 0

plt.tight_layout()
st.pyplot(fig)

# Plot pengguna sewaa sepeda dalam satu hari
fig, axes = plt.subplots(1, 2, figsize=(15, 5))

st.subheader("Penggunaan Sewa Sepeda dalam Satu Hari")

# Pola Penggunaan Rental Bike dalam Sehari
axes[0].set_title("Pola Penggunaan Sewa Sepeda dalam Sehari")
sns.lineplot(x=hourly_user['hr'], y=hourly_user['cnt'], marker='o', color="#72BCD4", ax=axes[0])
axes[0].set_xlabel("Jam dalam Sehari")
axes[0].set_ylabel("Rata-rata Jumlah Pengguna")
axes[0].set_ylim(0, None)  # Pastikan batas bawah 0
axes[0].set_xticks(range(0, 24))
axes[0].grid()

# Perbandingan Penggunaan Rental Bike antara Jam Sibuk dan Jam Santai
axes[1].set_title("Perbandingan Penggunaan Sewa Sepeda antara Jam Sibuk dan Jam Santai")
sns.barplot(
    x="time_category",
    y="cnt",
    hue="time_category",
    data=rush_hour,
    palette=["#D3D3D3", "#72BCD4"],
    ax=axes[1]
)
axes[1].set_xlabel("Kategori Waktu")
axes[1].set_ylabel("Total Rental Bike")
axes[1].set_ylim(0, None)  # Pastikan batas bawah 0

st.pyplot(fig)
