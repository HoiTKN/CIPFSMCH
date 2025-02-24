import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_data():
    # Đọc dữ liệu từ file CSV
    df = pd.read_csv("data.csv")
    
    # Đổi tên cột cho phù hợp với quá trình phân tích
    df.rename(columns={
        "Line": "line",
        "Thời gian Bắt đầu CIP": "date",
        "Tổng thời gian bước Xút": "time_alkali",
        "Độ dẫn điện Xút Bắt đầu": "cond_alkali",
        "Nhiệt độ Xút Bắt đầu": "temp_alkali",
        "Tổng thời gian bước nước nóng": "time_hotwater",
        "Nhiệt độ Nước nóng Bắt đầu": "temp_hotwater"
    }, inplace=True)
    
    # Chuyển đổi cột 'date' sang dạng datetime với định dạng dd/mm/yy HH:MM
    df['date'] = pd.to_datetime(df['date'], format="%d/%m/%y %H:%M")
    
    # Hàm chuyển đổi thời gian dạng "HH:MM" thành số phút (float)
    def convert_time_to_minutes(time_str):
        try:
            td = pd.to_timedelta(time_str)
            return td.total_seconds() / 60
        except Exception as e:
            return None
    
    # Chuyển đổi các cột thời gian sang số phút
    df['time_alkali'] = df['time_alkali'].apply(convert_time_to_minutes)
    df['time_hotwater'] = df['time_hotwater'].apply(convert_time_to_minutes)
    
    # Sắp xếp dữ liệu theo cột 'date'
    df = df.sort_values(by="date")
    return df

def main():
    st.title("CIP Data Dashboard")
    
    # Load và hiển thị dữ liệu
    df = load_data()
    
    # Lọc dữ liệu theo line (hiện tại chỉ có MMB, nhưng mở rộng khi có thêm line)
    lines = df['line'].unique()
    selected_line = st.selectbox("Chọn line", lines)
    df_line = df[df['line'] == selected_line]
    
    st.subheader(f"1) Thống kê mô tả - Line: {selected_line}")
    st.write(df_line.describe())
    
    # Vẽ các biểu đồ trực quan
    plot_time_series(df_line)
    plot_bar_compliance(df_line)
    plot_boxplot(df_line)
    plot_correlation(df_line)

def plot_time_series(df_line):
    st.subheader("2) Biểu đồ xu hướng (Time-series)")
    # Vẽ biểu đồ xu hướng cho thời gian tuần hoàn xút (time_alkali)
    fig, ax = plt.subplots()
    ax.plot(df_line['date'], df_line['time_alkali'], marker='o', label='Time Alkali (min)')
    # Vẽ đường ngưỡng chuẩn: >=30 phút
    ax.axhline(30, color='red', linestyle='--', label='Chuẩn >= 30 phút')
    ax.set_xlabel("Date")
    ax.set_ylabel("Thời gian (phút)")
    ax.set_title("Thời gian tuần hoàn xút theo thời gian")
    ax.legend()
    st.pyplot(fig)

def plot_bar_compliance(df_line):
    st.subheader("3) Tần suất vi phạm / % tuân thủ")
    # Xác định việc tuân thủ đối với thời gian xút: True nếu >=30 phút, False nếu không
    df_line['compliance_alkali'] = df_line['time_alkali'] >= 30
    compliance_count = df_line['compliance_alkali'].value_counts()
    
    fig, ax = plt.subplots()
    compliance_count.plot(kind='bar', ax=ax)
    ax.set_title("Tuân thủ thời gian xút (True = Đạt, False = Không đạt)")
    st.pyplot(fig)

def plot_boxplot(df_line):
    st.subheader("4) Boxplot phân bố giá trị")
    # Chọn các cột số để vẽ boxplot
    columns_to_plot = ['time_alkali', 'temp_alkali', 'cond_alkali', 'time_hotwater', 'temp_hotwater']
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df_line[columns_to_plot], ax=ax)
    ax.set_title("Boxplot của các chỉ số CIP")
    st.pyplot(fig)

def plot_correlation(df_line):
    st.subheader("5) Ma trận tương quan (Correlation Heatmap)")
    # Chọn các cột số để tính ma trận tương quan
    numeric_cols = ['time_alkali', 'temp_alkali', 'cond_alkali', 'time_hotwater', 'temp_hotwater']
    corr = df_line[numeric_cols].corr()
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, cmap="YlGnBu", ax=ax)
    ax.set_title("Ma trận tương quan")
    st.pyplot(fig)

if __name__ == "__main__":
    main()
