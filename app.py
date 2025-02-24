# file: app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_data():
    # Đọc dữ liệu CSV
    df = pd.read_csv("data.csv")
    # Chuyển cột 'date' thành dạng datetime nếu cần
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
    # Sắp xếp theo thời gian
    df = df.sort_values(by="date")
    return df

def main():
    st.title("CIP Data Dashboard")

    # Load data
    df = load_data()
    
    # Lọc dữ liệu theo line (nếu sau này có nhiều line)
    lines = df['line'].unique()
    selected_line = st.selectbox("Chọn line", lines)
    df_line = df[df['line'] == selected_line]
    
    st.subheader(f"1) Thống kê mô tả - Line: {selected_line}")
    st.write(df_line.describe())

    # Vẽ các biểu đồ
    plot_time_series(df_line)
    plot_bar_compliance(df_line)
    plot_boxplot(df_line)
    plot_correlation(df_line)

def plot_time_series(df_line):
    st.subheader("2) Biểu đồ xu hướng (Time-series)")
    # Ví dụ: vẽ biểu đồ thời gian tuần hoàn xút
    fig, ax = plt.subplots()
    ax.plot(df_line['date'], df_line['time_alkali'], marker='o', label='Time Alkali (min)')
    # Vẽ ngưỡng chuẩn 30 phút
    ax.axhline(30, color='red', linestyle='--', label='Chuẩn >= 30')
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Time (min)")
    ax.set_title("Alkali Circulation Time Over Time")
    ax.legend()
    
    st.pyplot(fig)
    
    # Tương tự, bạn có thể vẽ nhiệt độ xút, độ dẫn điện xút, ...
    # Hoặc tạo checkbox để người dùng chọn tham số cần hiển thị

def plot_bar_compliance(df_line):
    st.subheader("3) Tần suất vi phạm / % tuân thủ")
    # Ví dụ đếm số lần time_alkali < 30
    df_line['compliance_alkali_time'] = df_line['time_alkali'] >= 30
    compliance_count = df_line['compliance_alkali_time'].value_counts()
    
    fig, ax = plt.subplots()
    compliance_count.plot(kind='bar', ax=ax)
    ax.set_title("Compliance (True = Đạt, False = Không đạt)")
    st.pyplot(fig)
    
    # Tương tự cho temp_alkali, cond_alkali, time_hotwater, temp_hotwater

def plot_boxplot(df_line):
    st.subheader("4) Boxplot phân bố giá trị")
    # Lấy các cột cần thiết
    columns_to_plot = ['time_alkali','temp_alkali','cond_alkali','time_hotwater','temp_hotwater']
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df_line[columns_to_plot], ax=ax)
    ax.set_title("Boxplot of CIP Parameters")
    st.pyplot(fig)

def plot_correlation(df_line):
    st.subheader("5) Ma trận tương quan (Correlation Heatmap)")
    # Lấy các cột số
    numeric_cols = ['time_alkali','temp_alkali','cond_alkali','time_hotwater','temp_hotwater']
    corr = df_line[numeric_cols].corr()
    
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, cmap="YlGnBu", ax=ax)
    ax.set_title("Correlation Heatmap")
    st.pyplot(fig)

if __name__ == "__main__":
    main()
