import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
from babel.numbers import format_currency
import datetime

sns.set(style='dark')

# Fungsi-fungsi pengolahan data
def create_orders_items(df):
    orders_items = df.groupby(pd.Grouper(key='order_purchase_date', freq='W')).agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    orders_items.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    return orders_items

def create_product_category_merge(df):
    product_category_merge = df.groupby(by='product_category_name')['order_item_id'].sum().sort_values(ascending=False).reset_index()
    return product_category_merge

def create_customer_geolocation(df):
    customer_geolocation = df.groupby(by='customer_state').customer_id.nunique().reset_index()
    customer_geolocation.rename(columns={'customer_id': 'customer_count'}, inplace=True)
    return customer_geolocation

def create_merged_order_payments(df):
    merged_order_payments = df.groupby(by='payment_type').order_id.nunique().reset_index()
    merged_order_payments.rename(columns={'order_id': 'order_count'}, inplace=True)
    return merged_order_payments

def create_geographic_df(df):
    geographic_df = df.groupby(by='customer_state').customer_id.nunique().reset_index()
    geographic_df.rename(columns={'customer_id' : 'customer_count'}, inplace=True)
    return geographic_df

def create_rfm(df):
    rfm = df.groupby(by='short_customer_id', as_index=False).agg({
        'order_purchase_timestamp': 'max',
        'order_id': 'nunique',
        'price': 'sum'
    })
    rfm.columns = ['short_customer_id', 'order_purchase_timestamp', 'frequency', 'monetary']
    rfm["order_purchase_timestamp"] = rfm["order_purchase_timestamp"].dt.date
    recent_date = orders_items['order_purchase_date'].dt.date.max()
    rfm['recency'] = rfm['order_purchase_timestamp'].apply(lambda x: (recent_date - x).days)
    rfm.drop('order_purchase_timestamp', axis=1, inplace=True)
    return rfm

all_df = os.path.join(os.path.dirname(__file__), "all_df.csv")

datetime_columns = ('order_purchase_date', 'order_purchase_timestamp')
all_df.sort_values(by='order_purchase_date', inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df['order_purchase_date'].min()
max_date = all_df['order_purchase_date'].max()

# Ambil daftar metode pembayaran unik dari data
payment_methods = all_df['payment_type'].unique()

# Widget calendar untuk filter tanggal
with st.sidebar:
    st.image("olistlogo.png")
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date, max_value=max_date, value=[min_date, max_date]
    )
# Widget multiselect untuk metode pembayaran
    selected_payments = st.multiselect("Pilih Metode Pembayaran:", options=payment_methods, default=payment_methods)
    

# Filter berdasarkan rentang tanggal
main_df = all_df[(all_df['order_purchase_date'] >= str(start_date)) &
                 (all_df['order_purchase_date'] <= str(end_date))]
# Filter berdasarkan metode pembayaran
main_df = main_df[all_df['payment_type'].isin(selected_payments)]

# Pengolahan data setelah filter tanggal
orders_items = create_orders_items(main_df)
product_category_merge = create_product_category_merge(main_df)
customer_geolocation = create_customer_geolocation(main_df)
merged_order_payments = create_merged_order_payments(main_df)
geographic_df = create_geographic_df(main_df)
rfm = create_rfm(main_df)

# Dashboard
st.header('Olist Public E-Commerce :sparkles:')

st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = orders_items.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    previous_total_revenue = orders_items.revenue.iloc[-2] if len(orders_items) > 1 else 0
    st.metric("Total Revenue", value=previous_total_revenue, delta=format_currency(previous_total_revenue, "BRL", locale='pt_BR'))

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    orders_items["order_purchase_date"],
    orders_items["order_count"],
    linewidth=2,
    color="red"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
plt.grid(color='grey')
st.pyplot(fig)

st.subheader('Number of Customer by State') 

fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(
    x="customer_state", 
    y="customer_count",
    data=geographic_df.sort_values(by="customer_count", ascending=False),
    palette=colors,
    ax=ax
)
ax.set_title(None)
ax.set_ylabel('customer_id', fontsize=10)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=12)
ax.tick_params(axis='x', labelsize=12)
st.pyplot(fig)

st.subheader('Most Used Payment Method')

fig, ax = plt.subplots(figsize=(20, 10))
colors = ['lightblue']
sns.barplot(
    x='payment_type',
    y='order_count',
    data=merged_order_payments.sort_values(by='payment_type', ascending=False),
    palette=colors,
    ax=ax
)
ax.set_title(None)
ax.set_ylabel('Count', size=20)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=20)
st.pyplot(fig)

st.subheader('Best Customers Based On RFM Parameters')

col1, col2, col3 = st.columns(3)

with col1:
    recency_avg = round(rfm.recency.mean(), 1)
    st.metric('Avg Recency (days) :', value=recency_avg)

with col2:
    frequency_avg = round(rfm.frequency.mean(), 2)
    st.metric('Avg Frequency :', value=frequency_avg)

with col3:
    frequency_avg = format_currency(rfm.monetary.mean(), 'BRL', locale='pt_BR')
    st.metric('Avg Monetary :', value=frequency_avg)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y='recency', x='short_customer_id', data=rfm.sort_values(by='recency', ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel('customer_id', fontsize=25)
ax[0].set_title('By Recency (days)', loc='center', fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=28)

sns.barplot(y='frequency', x='short_customer_id', data=rfm.sort_values(by='frequency', ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel('customer_id', fontsize=25)
ax[1].set_title('By Frequency', loc='center', fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=28)

sns.barplot(y="monetary", x="short_customer_id", data=rfm.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel('customer_id', fontsize=25)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=28)

st.pyplot(fig)
