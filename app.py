import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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
    df_clean['next_start'] = df_clean.groupby(['Line', 'Circuit', 'Thiết bị'])['Thời gian Bắt đầu CIP'].shift(-1)
    df_clean['time_gap_days'] = (
        (df_clean['next_start'] - df_clean['Thời gian Kết thúc CIP'])
        .dt.total_seconds() / 86400
    )
    
    return df_clean

def main():
    st.title("CIP Data Dashboard")
    
    # 1) Đọc dữ liệu gốc và làm sạch
    df_raw = load_data()
    df_clean = clean_data(df_raw)
    
    # 2) Lựa chọn line, circuit, thiết bị
    col1, col2, col3 = st.columns(3)
    
    with col1:
        lines = df_clean['Line'].unique()
        selected_line = st.selectbox("Chọn Line", lines)
    
    df_line = df_clean[df_clean['Line'] == selected_line]
    
    with col2:
        circuits = df_line['Circuit'].unique()
        selected_circuit = st.selectbox("Chọn Circuit", circuits)
    
    df_line_circuit = df_line[df_line['Circuit'] == selected_circuit]
    
    with col3:
        thiet_bi_list = df_line_circuit['Thiết bị'].unique()
        selected_thiet_bi = st.selectbox("Chọn Thiết bị", ["Tất cả"] + list(thiet_bi_list))
    
    # Lọc theo thiết bị nếu không chọn "Tất cả"
    if selected_thiet_bi != "Tất cả":
        df_filtered = df_line_circuit[df_line_circuit['Thiết bị'] == selected_thiet_bi]
    else:
        df_filtered = df_line_circuit
    
    # Kiểm tra xem có dữ liệu nào sau khi lọc không
    if df_filtered.empty:
        st.warning(f"Không có dữ liệu cho Thiết bị '{selected_thiet_bi}' trong Circuit {selected_circuit} của Line {selected_line}.")
        return
    
    # Tính tổng thời gian CIP
    df_filtered['Tổng thời gian CIP (phút)'] = (
        df_filtered['Tổng thời gian bước Xút (phút)'] +
        df_filtered['Tổng thời gian bước nước nóng (phút)']
    )
    
    # 3) Boxplot các thông số CIP theo Thiết bị
    st.subheader("1) Boxplot các thông số CIP")
    
    columns_for_boxplot = [
        "Nhiệt độ Xút Bắt đầu",
        "Nhiệt độ Xút Kết thúc",
        "Tổng thời gian bước Xút (phút)",
        "Nhiệt độ Nước nóng Bắt đầu",
        "Nhiệt độ Nước nóng Kết thúc",
        "Tổng thời gian bước nước nóng (phút)",
        "Tổng thời gian CIP (phút)"
    ]
    
    col_selected = st.selectbox("Chọn thông số để vẽ Boxplot", columns_for_boxplot)
    
    # Kiểm tra xem có đủ dữ liệu để vẽ boxplot không
    if len(df_filtered) > 0 and not df_filtered[col_selected].isna().all():
        try:
            # Sử dụng biểu đồ violin thay vì boxplot nếu chỉ có một thiết bị
            if selected_thiet_bi != "Tất cả":
                fig1, ax1 = plt.subplots(figsize=(8, 4))
                # Sử dụng stripplot khi chỉ có một thiết bị 
                # (hiển thị các điểm dữ liệu riêng lẻ)
                sns.stripplot(
                    data=df_filtered,
                    y=col_selected,
                    jitter=True,
                    size=8,
                    ax=ax1
                )
                ax1.set_title(f"{col_selected} cho {selected_thiet_bi} (Circuit: {selected_circuit}, Line: {selected_line})")
                ax1.set_ylabel(col_selected)
                st.pyplot(fig1)
            else:
                if len(df_filtered['Thiết bị'].unique()) > 1:
                    fig1, ax1 = plt.subplots(figsize=(10, 5))
                    sns.boxplot(
                        data=df_filtered,
                        x="Thiết bị",
                        y=col_selected,
                        ax=ax1
                    )
                    ax1.set_title(f"{col_selected} theo Thiết bị (Circuit: {selected_circuit}, Line: {selected_line})")
                    ax1.set_xlabel("Thiết bị")
                    ax1.set_ylabel(col_selected)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig1)
                else:
                    st.warning(f"Chỉ có một Thiết bị trong dữ liệu được lọc. Không thể tạo boxplot.")
        except Exception as e:
            st.error(f"Lỗi khi vẽ biểu đồ: {str(e)}")
            st.info("Hãy thử chọn một thông số khác hoặc kiểm tra lại dữ liệu.")
    else:
        st.warning(f"Không có đủ dữ liệu cho thông số {col_selected} để vẽ biểu đồ.")
    
    # 4) Biểu đồ thể hiện thời gian giữa hai lần CIP (time_gap_days)
    st.subheader("2) Thời gian giữa hai lần CIP")
    st.markdown(
        "- **Cách tính**: Thời gian Bắt đầu CIP của đợt sau trừ đi Thời gian Kết thúc CIP của đợt trước.\n"
        "- Đơn vị: ngày (1 ngày = 24 giờ).\n"
        "- Đường kẻ ngang (màu đỏ) biểu thị quy định 5 ngày."
    )
    
    # Lọc dữ liệu không có giá trị NA và loại bỏ giá trị âm hoặc bằng 0
    time_gap_data = df_filtered[df_filtered['time_gap_days'] > 0].copy()
    
    if not time_gap_data.empty:
        try:
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            
            # Nếu chọn một thiết bị cụ thể
            if selected_thiet_bi != "Tất cả":
                ax2.plot(
                    time_gap_data['Thời gian Bắt đầu CIP'],
                    time_gap_data['time_gap_days'],
                    marker='o', linestyle='-',
                    label=f'Khoảng thời gian (ngày)'
                )
                ax2.set_title(f"Thời gian giữa các lần CIP - {selected_thiet_bi} (Circuit: {selected_circuit}, Line: {selected_line})")
            else:
                # Nếu chọn "Tất cả", vẽ một đường cho mỗi thiết bị
                for thiet_bi in time_gap_data['Thiết bị'].unique():
                    thiet_bi_data = time_gap_data[time_gap_data['Thiết bị'] == thiet_bi]
                    ax2.plot(
                        thiet_bi_data['Thời gian Bắt đầu CIP'],
                        thiet_bi_data['time_gap_days'],
                        marker='o', linestyle='-',
                        label=thiet_bi
                    )
                ax2.set_title(f"Thời gian giữa các lần CIP theo Thiết bị (Circuit: {selected_circuit}, Line: {selected_line})")
            
            ax2.axhline(5, color='red', linestyle='--', label='Quy định 5 ngày')
            ax2.set_xlabel("Thời gian Bắt đầu CIP")
            ax2.set_ylabel("Khoảng thời gian (ngày)")
            ax2.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
            
            # Thêm bảng thống kê cơ bản về khoảng thời gian
            st.subheader("3) Thống kê về khoảng thời gian giữa các lần CIP")
            stats_df = time_gap_data.groupby('Thiết bị')['time_gap_days'].agg([
                ('Trung bình (ngày)', 'mean'),
                ('Tối thiểu (ngày)', 'min'),
                ('Tối đa (ngày)', 'max'),
                ('Số lần CIP', 'count')
            ]).reset_index()
            
            # Làm tròn số thập phân
            for col in ['Trung bình (ngày)', 'Tối thiểu (ngày)', 'Tối đa (ngày)']:
                stats_df[col] = stats_df[col].round(2)
                
            st.dataframe(stats_df)
            
        except Exception as e:
            st.error(f"Lỗi khi vẽ biểu đồ khoảng thời gian: {str(e)}")
    else:
        st.warning("Không có đủ dữ liệu về khoảng thời gian giữa các lần CIP để vẽ biểu đồ.")
    
    # 5) Hiển thị bảng dữ liệu chi tiết
    with st.expander("Xem dữ liệu chi tiết"):
        st.dataframe(df_filtered)

if __name__ == "__main__":
    main()
