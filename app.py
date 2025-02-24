import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_data():
    """Đọc dữ liệu gốc từ file CSV mà không đổi tên cột."""
    df = pd.read_csv("data.csv")
    return df

def clean_data(df):
    """
    1) Tách các dòng outlier (có 0 ở Lưu lượng hồi, Tổng thời gian bước Xút, Tổng thời gian bước nước nóng).
    2) Chuyển cột thời gian bắt đầu/ kết thúc CIP sang datetime.
    3) Chuyển các cột thời gian Xút / Nước nóng sang phút (tạo thêm cột (phút)).
    4) Tính khoảng cách giữa 2 lần CIP liên tiếp (time_gap_days).
    """
    # 1) Tách outlier
    outlier_condition = (
        (df['Lưu lượng hồi (l/h)'] == 0) |
        (df['Tổng thời gian bước Xút'] == 0) |
        (df['Tổng thời gian bước nước nóng'] == 0)
    )
    df_outliers = df[outlier_condition].copy()
    df_clean = df[~outlier_condition].copy()
    
    # 2) Chuyển "Thời gian Bắt đầu CIP" / "Thời gian Kết thúc CIP" sang datetime
    df_clean['Thời gian Bắt đầu CIP'] = pd.to_datetime(
        df_clean['Thời gian Bắt đầu CIP'],
        format="%d/%m/%y %H:%M",
        errors='coerce'
    )
    df_clean['Thời gian Kết thúc CIP'] = pd.to_datetime(
        df_clean['Thời gian Kết thúc CIP'],
        format="%d/%m/%y %H:%M",
        errors='coerce'
    )
    
    # 3) Chuyển "Tổng thời gian bước Xút" & "Tổng thời gian bước nước nóng" sang số phút
    def convert_to_minutes(t_str):
        try:
            td = pd.to_timedelta(t_str)  # "0:31" -> 31 phút
            return td.total_seconds() / 60
        except:
            return None

    df_clean['Tổng thời gian bước Xút (phút)'] = df_clean['Tổng thời gian bước Xút'].apply(convert_to_minutes)
    df_clean['Tổng thời gian bước nước nóng (phút)'] = df_clean['Tổng thời gian bước nước nóng'].apply(convert_to_minutes)
    
    # Sắp xếp dữ liệu theo (Line, Circuit, Thời gian Bắt đầu CIP)
    df_clean.sort_values(by=['Line', 'Circuit', 'Thời gian Bắt đầu CIP'], inplace=True)
    
    # 4) Tính khoảng cách giữa 2 lần CIP liên tiếp
    df_clean['next_start'] = df_clean.groupby(['Line', 'Circuit'])['Thời gian Bắt đầu CIP'].shift(-1)
    df_clean['time_gap_days'] = (
        (df_clean['next_start'] - df_clean['Thời gian Kết thúc CIP'])
        .dt.total_seconds() / 86400
    )
    
    return df_clean, df_outliers

def main():
    st.title("CIP Data Dashboard")
    
    # 1) Đọc dữ liệu gốc và làm sạch
    df_raw = load_data()
    df_clean, df_outliers = clean_data(df_raw)
    
    # Thông tin cơ bản về quá trình làm sạch
    st.subheader("1) Thống kê dữ liệu (sau khi làm sạch)")
    st.write(f"- Số dòng dữ liệu gốc: **{df_raw.shape[0]}**")
    st.write(f"- Số dòng bị loại bỏ (outliers): **{df_outliers.shape[0]}**")
    st.write(f"- Số dòng còn lại sau khi làm sạch: **{df_clean.shape[0]}**")
    
    # Nếu không còn dữ liệu nào sau khi làm sạch thì dừng
    if df_clean.empty:
        st.warning("Dữ liệu sau khi làm sạch không còn dòng nào để phân tích.")
        return
    
    # 2) Lựa chọn line, circuit
    lines = df_clean['Line'].unique()
    selected_line = st.selectbox("Chọn Line", lines)
    df_line = df_clean[df_clean['Line'] == selected_line]
    
    circuits = df_line['Circuit'].unique()
    selected_circuit = st.selectbox("Chọn Circuit", circuits)
    df_line_circuit = df_line[df_line['Circuit'] == selected_circuit]
    
    # 3) Boxplot các thông số CIP theo Circuit
    st.subheader("2) Boxplot các thông số CIP theo Circuit")
    st.markdown("Bạn có thể chọn thông số muốn so sánh trên trục tung (y). Trục hoành (x) là Circuit.")
    
    columns_for_boxplot = [
        "Nhiệt độ Xút Bắt đầu",
        "Nhiệt độ Xút Kết thúc",
        "Tổng thời gian bước Xút (phút)",
        "Nhiệt độ Nước nóng Bắt đầu",
        "Nhiệt độ Nước nóng Kết thúc",
        "Tổng thời gian bước nước nóng (phút)"
    ]
    col_selected = st.selectbox("Chọn cột để vẽ Boxplot", columns_for_boxplot)
    
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    sns.boxplot(
        data=df_line,
        x="Circuit",
        y=col_selected,
        ax=ax1
    )
    ax1.set_title(f"Boxplot của '{col_selected}' theo Circuit (Line: {selected_line})")
    ax1.set_xlabel("Circuit")
    ax1.set_ylabel(col_selected)
    st.pyplot(fig1)
    
    # 4) Boxplot thể hiện "Tổng thời gian CIP" (Xút + Nước nóng)
    st.subheader("3) Boxplot Tổng thời gian CIP (phút) theo Circuit")
    # Tạo cột mới: "Tổng thời gian CIP (phút)"
    df_line['Tổng thời gian CIP (phút)'] = (
        df_line['Tổng thời gian bước Xút (phút)'] +
        df_line['Tổng thời gian bước nước nóng (phút)']
    )
    
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    sns.boxplot(
        data=df_line,
        x="Circuit",
        y="Tổng thời gian CIP (phút)",
        ax=ax2
    )
    ax2.set_title(f"Tổng thời gian CIP (phút) theo Circuit (Line: {selected_line})")
    ax2.set_xlabel("Circuit")
    ax2.set_ylabel("Tổng thời gian CIP (phút)")
    st.pyplot(fig2)
    
    # 5) Biểu đồ thể hiện thời gian giữa hai lần CIP (time_gap_days)
    st.subheader("4) Thời gian giữa hai lần CIP (time_gap_days)")
    st.markdown(
        "- **Cách tính**: Thời gian Bắt đầu CIP của đợt sau trừ đi Thời gian Kết thúc CIP của đợt trước.\n"
        "- Đơn vị: ngày (1 ngày = 24 giờ).\n"
        "- Đường kẻ ngang (màu đỏ) biểu thị quy định 5 ngày."
    )
    
    # Lấy data cho line+circuit đã chọn
    df_line_circuit['time_gap_days'] = df_line_circuit['time_gap_days'].fillna(0)
    
    # Vẽ biểu đồ line
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.plot(
        df_line_circuit['Thời gian Bắt đầu CIP'],
        df_line_circuit['time_gap_days'],
        marker='o', linestyle='-',
        label='Time Gap (days)'
    )
    ax3.axhline(5, color='red', linestyle='--', label='Quy định 5 ngày')
    ax3.set_xlabel("Thời gian Bắt đầu CIP")
    ax3.set_ylabel("Time Gap (ngày)")
    ax3.set_title(f"Thời gian giữa các lần CIP - (Line: {selected_line}, Circuit: {selected_circuit})")
    ax3.legend()
    st.pyplot(fig3)

if __name__ == "__main__":
    main()
