import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    layout="wide"
)

# =========================
# GLOBAL STYLE
# =========================
sns.set_style("whitegrid")

plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 10

st.markdown("""
<style>
.metric-card {
    background-color: #1E1E1E;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #333333;
    text-align: center;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.metric-title {
    font-size: 15px;
    color: #CCCCCC;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 32px;
    font-weight: bold;
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)


# =========================
# HELPER STYLE
# =========================
def clean_chart(ax):
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.grid(axis="x", visible=False)


# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    data_dir = Path(__file__).resolve().parent / "data"

    day_df = pd.read_csv(data_dir / "day.csv")
    hour_df = pd.read_csv(data_dir / "hour.csv")

    day_df["dteday"] = pd.to_datetime(day_df["dteday"])
    hour_df["dteday"] = pd.to_datetime(hour_df["dteday"])

    return day_df, hour_df


day_df, hour_df = load_data()


# =========================
# DATA PREPARATION
# =========================
season_map = {
    1: "Spring",
    2: "Summer",
    3: "Fall",
    4: "Winter"
}

weather_map = {
    1: "Clear / Partly Cloudy",
    2: "Mist + Cloudy",
    3: "Light Rain / Snow",
    4: "Heavy Rain / Snow"
}

day_df["season_label"] = day_df["season"].map(season_map)
hour_df["season_label"] = hour_df["season"].map(season_map)

day_df["weather_label"] = day_df["weathersit"].map(weather_map)
hour_df["weather_label"] = hour_df["weathersit"].map(weather_map)

hour_df["day_type"] = hour_df["workingday"].map({
    1: "Working Day",
    0: "Weekend/Holiday"
})


def categorize_demand(cnt):
    if cnt < day_df["cnt"].quantile(0.33):
        return "Low"
    elif cnt < day_df["cnt"].quantile(0.66):
        return "Medium"
    else:
        return "High"


day_df["demand_cluster"] = day_df["cnt"].apply(categorize_demand)


def time_category(hour):
    if 0 <= hour <= 5:
        return "Dini Hari"
    elif 6 <= hour <= 10:
        return "Pagi"
    elif 11 <= hour <= 14:
        return "Siang"
    elif 15 <= hour <= 18:
        return "Sore"
    else:
        return "Malam"


hour_df["time_category"] = hour_df["hr"].apply(time_category)


# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.header("Filter Data")

min_date = day_df["dteday"].min()
max_date = day_df["dteday"].max()

date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range

    filtered_day = day_df[
        (day_df["dteday"] >= pd.to_datetime(start_date)) &
        (day_df["dteday"] <= pd.to_datetime(end_date))
    ].copy()

    filtered_hour = hour_df[
        (hour_df["dteday"] >= pd.to_datetime(start_date)) &
        (hour_df["dteday"] <= pd.to_datetime(end_date))
    ].copy()
else:
    filtered_day = day_df.copy()
    filtered_hour = hour_df.copy()


# =========================
# HEADER
# =========================
st.title("🚲 Bike Sharing Dashboard 🚲")

st.write("""
Dashboard ini menampilkan analisis penyewaan sepeda berdasarkan waktu,
musim, cuaca, tipe pengguna, hari kerja, serta analisis lanjutan berupa
clustering permintaan dan binning waktu.
""")


# =========================
# METRICS
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Penyewaan</div>
        <div class="metric-value">{filtered_day['cnt'].sum():,}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Casual User</div>
        <div class="metric-value">{filtered_day['casual'].sum():,}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Registered User</div>
        <div class="metric-value">{filtered_day['registered'].sum():,}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Rata-rata Harian</div>
        <div class="metric-value">{filtered_day['cnt'].mean():.0f}</div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# TREN HARIAN
# =========================
st.subheader("Tren Penyewaan Sepeda Harian")

filtered_day["rolling_avg"] = filtered_day["cnt"].rolling(window=7).mean()

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(filtered_day["dteday"], filtered_day["cnt"], alpha=0.35, label="Data Harian")
ax.plot(filtered_day["dteday"], filtered_day["rolling_avg"], color="#E76F51", label="Trend 7-day avg")
ax.set_title("Tren Penyewaan Sepeda Harian dengan Moving Average")
ax.set_xlabel("Tanggal")
ax.set_ylabel("Jumlah Penyewaan")
ax.legend()
clean_chart(ax)
st.pyplot(fig)

st.markdown("""
**Insight:** Penyewaan sepeda menunjukkan tren meningkat dari tahun 2011 ke 2012
dengan fluktuasi yang dipengaruhi faktor waktu dan musim.
""")


# =========================
# POLA PER JAM
# =========================
st.subheader("Pola Penyewaan Sepeda per Jam")

hourly_avg = filtered_hour.groupby("hr")["cnt"].mean()

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(hourly_avg.index, hourly_avg.values, marker="o", color="#4C72B0")
ax.set_title("Rata-rata Penyewaan Sepeda per Jam")
ax.set_xlabel("Jam")
ax.set_ylabel("Rata-rata Penyewaan")
ax.set_xticks(range(0, 24))
clean_chart(ax)
st.pyplot(fig)

st.markdown("""
**Insight:** Penyewaan tertinggi terjadi pada pagi dan sore hari,
yang menunjukkan pola penggunaan untuk aktivitas rutin.
""")


# =========================
# MUSIM DAN CUACA
# =========================
st.subheader("Pengaruh Musim dan Cuaca")

season_order = ["Spring", "Summer", "Fall", "Winter"]
season_colors = ["#A8DADC", "#FFE5B4", "#FFAFCC", "#BDE0FE"]

weather_order = [
    "Clear / Partly Cloudy",
    "Mist + Cloudy",
    "Light Rain / Snow",
    "Heavy Rain / Snow"
]
weather_colors = ["#A8DADC", "#FFE5B4", "#FFAFCC", "#BDE0FE"]

fig, ax = plt.subplots(1, 2, figsize=(10, 4))

sns.barplot(
    data=filtered_day,
    x="season_label",
    y="cnt",
    hue="season_label",
    order=season_order,
    palette=season_colors,
    errorbar=None,
    legend=False,
    ax=ax[0]
)

ax[0].set_title("Pengaruh Musim")
ax[0].set_xlabel("Musim")
ax[0].set_ylabel("Rata-rata Penyewaan")
clean_chart(ax[0])

for bar in ax[0].patches:
    height = bar.get_height()
    ax[0].text(
        bar.get_x() + bar.get_width() / 2,
        height + 80,
        f"{int(height):,}",
        ha="center",
        va="bottom",
        fontsize=8
    )

sns.barplot(
    data=filtered_day,
    x="weather_label",
    y="cnt",
    hue="weather_label",
    order=weather_order,
    palette=weather_colors,
    errorbar=None,
    legend=False,
    ax=ax[1]
)

ax[1].set_title("Pengaruh Cuaca")
ax[1].set_xlabel("Kondisi Cuaca")
ax[1].set_ylabel("Rata-rata Penyewaan")
ax[1].tick_params(axis="x", rotation=15)
clean_chart(ax[1])

for bar in ax[1].patches:
    height = bar.get_height()
    ax[1].text(
        bar.get_x() + bar.get_width() / 2,
        height + 80,
        f"{int(height):,}",
        ha="center",
        va="bottom",
        fontsize=8
    )

plt.tight_layout()
st.pyplot(fig)

st.markdown("""
**Insight:** Penyewaan tertinggi terjadi pada musim Fall dan saat cuaca cerah,
sedangkan cuaca buruk seperti hujan atau salju menurunkan jumlah penyewaan.
""")

# =========================
# Distribusi
# =========================
st.subheader("Distribusi Penyewaan Sepeda")

fig, ax = plt.subplots(figsize=(6,4))
sns.histplot(filtered_day["cnt"], bins=30, kde=True, color="#A8DADC", ax=ax)

ax.set_title("Distribusi Jumlah Penyewaan")
ax.set_xlabel("Jumlah Penyewaan")
ax.set_ylabel("Frekuensi")
clean_chart(ax)

st.pyplot(fig)

st.markdown("""
**Insight:** Distribusi penyewaan sepeda cenderung terpusat pada kisaran menengah dengan sedikit kemiringan ke kanan, menunjukkan adanya beberapa hari dengan penyewaan tinggi.
""")
# =========
# BOXPLOT
# =========
st.subheader("Boxplot Penyewaan Sepeda")

fig, ax = plt.subplots(figsize=(6,4))
sns.boxplot(x=filtered_day["cnt"], color="#FFCAD4", ax=ax)

ax.set_title("Boxplot Penyewaan Sepeda")
clean_chart(ax)

st.pyplot(fig)

st.markdown("""
**Insight:** Sebaran penyewaan cukup luas dengan median di tengah serta variasi nilai tinggi, meskipun tidak banyak outlier ekstrem.
""")

# ====
# KDE
# ====
st.subheader("KDE Plot Penyewaan Sepeda")

fig, ax = plt.subplots(figsize=(6,4))
sns.kdeplot(filtered_day["cnt"], fill=True, color="#4C72B0", ax=ax)

ax.set_title("KDE Plot Penyewaan")
clean_chart(ax)

st.pyplot(fig)

st.markdown("""
**Insight:** Distribusi penyewaan mendekati normal dengan puncak pada nilai menengah dan variasi permintaan yang cukup tinggi.
""")
# ============
# CORRELATION
# ============
st.subheader("Correlation Matrix Antar Variabel")

fig, ax = plt.subplots(figsize=(10,6))

corr = filtered_day.corr(numeric_only=True)

sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.5,
    ax=ax
)

ax.set_title("Correlation Matrix Antar Variabel", fontsize=14, weight='bold')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

plt.tight_layout()

st.pyplot(fig)

st.markdown("""
**Insight:** Variabel registered memiliki korelasi sangat kuat dengan jumlah penyewaan, sementara temperatur juga berpengaruh positif terhadap peningkatan penyewaan. Selain itu variabel weathersit berkorelasi negatif dengan cnt, menunjukkan bahwa kondisi cuaca buruk menurunkan jumlah penyewaan sepeda. 
""")
# ============
# SCATTER PLOT
# ============
st.subheader("Pengaruh Temperatur terhadap Penyewaan")

fig, ax = plt.subplots(figsize=(6,4))

sns.scatterplot(
    data=filtered_day,
    x='temp',
    y='cnt',
    ax=ax
)

ax.set_title("Pengaruh Temperatur terhadap Penyewaan")

st.pyplot(fig)

st.markdown("""
**Insight:** Terdapat hubungan positif antara temperatur dan jumlah penyewaan, di mana semakin tinggi suhu, penyewaan cenderung meningkat.
""")
# ========
# PAIRPLOT
# ========
st.subheader("Hubungan Antar Variabel")

pairplot_fig = sns.pairplot(
    filtered_day[['cnt','temp','hum','windspeed']],
)

st.pyplot(pairplot_fig)

st.markdown("""
**Insight:** Temperatur memiliki hubungan positif dengan penyewaan, sementara kelembapan dan kecepatan angin cenderung memiliki pengaruh negatif meskipun tidak terlalu kuat.
""")

# ========
# Q-Q PLOT
# ========
import scipy.stats as stats

st.subheader("Q-Q Plot")

fig, ax = plt.subplots(figsize=(6,4))
stats.probplot(filtered_day["cnt"], dist="norm", plot=ax)

ax.set_title("Q-Q Plot")
clean_chart(ax)

st.pyplot(fig)

st.markdown("""
**Insight:** Sebagian besar data mengikuti distribusi normal, meskipun terdapat sedikit penyimpangan pada bagian ekor.
""")

# =========================
# Countplot musim
# =========================
st.subheader("Distribusi Jumlah Hari Berdasarkan Musim")

season_order = ["Spring", "Summer", "Fall", "Winter"]
season_colors = ["#A8DADC", "#FFE5B4", "#FFAFCC", "#BDE0FE"]

fig, ax = plt.subplots(figsize=(8,5))

sns.countplot(
    data=filtered_day,
    x="season_label",
    hue="season_label",
    order=season_order,
    palette=season_colors,
    legend=False,
    ax=ax
)

ax.set_title("Distribusi Jumlah Hari Berdasarkan Musim")
ax.set_xlabel("Musim")
ax.set_ylabel("Jumlah Hari")

# label angka
for container in ax.containers:
    ax.bar_label(container, fmt='%d')

clean_chart(ax)
st.pyplot(fig)

st.markdown("""
**Insight:** Jumlah hari pada setiap musim relatif seimbang, sehingga perbedaan penyewaan lebih dipengaruhi oleh faktor musim, bukan jumlah data.
""")
# =========================
# Boxplot per musim
# =========================
st.subheader("Distribusi Penyewaan per Musim")

fig, ax = plt.subplots(figsize=(6,4))

sns.boxplot(
    data=filtered_day,
    x="season_label",
    y="cnt",
    hue="season_label",
    palette=season_colors,
    legend=False,
    ax=ax
)

ax.set_title("Distribusi Penyewaan per Musim")
clean_chart(ax)

st.pyplot(fig)

st.markdown("""
**Insight:** Penyewaan tertinggi terjadi pada Fall, dengan variasi yang cukup besar dibanding musim lainnya.
""")
# =========================
# VIOLIN PLOT CUACA
# =========================
st.subheader("Distribusi Penyewaan per Cuaca")

weather_colors = ["#A8DADC", "#FFE5B4", "#FFAFCC"]

fig, ax = plt.subplots(figsize=(6,4))

sns.violinplot(
    data=filtered_day,
    x="weather_label",
    y="cnt",
    hue="weather_label",
    palette=weather_colors,
    legend=False,
    ax=ax
)

ax.set_title("Distribusi Penyewaan per Cuaca")
ax.tick_params(axis='x', rotation=15)
clean_chart(ax)

st.pyplot(fig)

st.markdown("""
**Insight:** Penyewaan tertinggi terjadi saat cuaca cerah, sementara kondisi cuaca buruk menurunkan jumlah penyewaan.
""")

# =========================
# CASUAL VS REGISTERED
# =========================
st.subheader("Perbandingan Casual vs Registered")

user_sum = filtered_day[["casual", "registered"]].sum()
colors = ["#FFCAD4", "#A8DADC"]

fig, ax = plt.subplots(figsize=(4.5, 4.5))
ax.pie(
    user_sum,
    labels=user_sum.index,
    autopct="%1.1f%%",
    colors=colors,
    startangle=90,
    wedgeprops={"edgecolor": "white"}
)
ax.set_title("Perbandingan Casual vs Registered")
st.pyplot(fig)

st.markdown("""
**Insight:** Pengguna registered mendominasi jumlah penyewaan sepeda,
menunjukkan bahwa layanan lebih banyak digunakan oleh pelanggan tetap.
""")

# =========================
# WORKING DAY VS WEEKEND
# =========================
st.subheader("Perbandingan Working Day vs Weekend/Holiday")

daytype_analysis = (
    filtered_hour.groupby(["hr", "day_type"])["cnt"]
    .mean()
    .reset_index()
)

fig, ax = plt.subplots(figsize=(8, 4))
sns.lineplot(
    data=daytype_analysis,
    x="hr",
    y="cnt",
    hue="day_type",
    marker="o",
    ax=ax
)

ax.set_title("Perbandingan Penyewaan: Working Day vs Weekend/Holiday")
ax.set_xlabel("Jam")
ax.set_ylabel("Rata-rata Penyewaan")
ax.set_xticks(range(0, 24))
clean_chart(ax)
st.pyplot(fig)

st.markdown("""
**Insight:** Pada working day, penyewaan memuncak pada pagi dan sore hari,
sedangkan pada weekend/holiday penyewaan cenderung meningkat pada siang hari.
""")


# =========================
# CLUSTERING PERMINTAAN
# =========================
st.subheader("Analisis Lanjutan: Cluster Permintaan")

cluster_count = (
    filtered_day["demand_cluster"]
    .value_counts()
    .reindex(["Low", "Medium", "High"])
)

cluster_colors = ["#A8DADC", "#FFE5B4", "#FFAFCC"]

fig, ax = plt.subplots(figsize=(5, 3.8))
bars = ax.bar(cluster_count.index, cluster_count.values, color=cluster_colors)

ax.set_title("Distribusi Cluster Permintaan")
ax.set_xlabel("Kategori Permintaan")
ax.set_ylabel("Jumlah Hari")
clean_chart(ax)

for bar in bars:
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height + 2,
        f"{int(height)}",
        ha="center",
        va="bottom",
        fontsize=9
    )

st.pyplot(fig)

st.markdown("""
**Insight:** Distribusi kategori Low, Medium, dan High relatif seimbang,
menunjukkan tingkat permintaan penyewaan sepeda cukup stabil.
""")


# =========================
# BINNING WAKTU
# =========================
st.subheader("Analisis Lanjutan: Binning Waktu")

time_order = ["Dini Hari", "Pagi", "Siang", "Sore", "Malam"]

time_avg = (
    filtered_hour.groupby("time_category")["cnt"]
    .mean()
    .reindex(time_order)
)

time_colors = ["#CDE7F0", "#A8DADC", "#FFE5B4", "#FFAFCC", "#BDE0FE"]

fig, ax = plt.subplots(figsize=(6, 3.8))
bars = ax.bar(time_avg.index, time_avg.values, color=time_colors)

ax.set_title("Rata-rata Penyewaan Sepeda Berdasarkan Kategori Waktu")
ax.set_xlabel("Kategori Waktu")
ax.set_ylabel("Rata-rata Penyewaan")
clean_chart(ax)

max_val = max(time_avg)

for bar in bars:
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height + (0.03 * max_val),
        f"{int(height):,}",
        ha="center",
        va="bottom",
        fontsize=9
    )

ax.set_ylim(0, max_val * 1.15)
st.pyplot(fig)

st.markdown("""
**Insight:** Penyewaan tertinggi terjadi pada sore hari, diikuti siang dan pagi,
sedangkan dini hari memiliki permintaan paling rendah.
""")


# =========================
# CONCLUSION
# =========================
st.subheader("📌 Kesimpulan")

st.markdown("""
<div style="
    background-color: #F8F9FA;
    padding: 22px;
    border-radius: 15px;
    border-left: 6px solid #4C72B0;
    color: #2C2C2C;
    font-size: 16px;
    line-height: 1.7;
">
    <ol>
        <li>Pola penyewaan sepeda cenderungmeningkat dari tahun 2011 ke 2012 dengan fluktuasi harian.</li>
        <li>Jam sibuk penyewaan terjadi pada pagi dan sore hari, terutama pada working day.</li>
        <li>Musim Fall dan cuaca cerah memiliki rata-rata penyewaan tertinggi.</li>
        <li>Cluster permintaan relatif seimbang antara Low, Medium, dan High.</li>
        <li>Binning waktu menunjukkan bahwa sore hari merupakan kategori waktu dengan permintaan tertinggi.</li>
        <li>Distribusi penyewaan sepeda cenderung berada pada kisaran menengah dengan pola yang mendekati normal, menunjukkan variasi permintaan yang cukup stabil.</li>
        <li>Analisis korelasi menunjukkan bahwa temperatur dan jumlah pengguna registered memiliki pengaruh paling kuat terhadap peningkatan penyewaan sepeda.</li>
    </ol>
</div>
""", unsafe_allow_html=True)