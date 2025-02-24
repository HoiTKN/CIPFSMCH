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
    4) Tính tổng thời gian CIP từ thời gian bắt đầu đến kết thúc.
    5) Tính khoảng cách giữa 2 lần CIP liên tiếp (time_gap_days).
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
        if pd.isna(t_str) or t_str == '0:00' or t_str == '':
            return 0
        try:
            parts = t_str.split(':')
            if len(parts) == 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours * 60 + minutes
            return 0
        except:
            return 0

    df_clean['Tổng thời gian bước Xút (phút)'] = df_clean['Tổng thời gian bước Xút'].apply(convert_to_minutes)
    df_clean['Tổng thời gian bước nước nóng (phút)'] = df_clean['Tổng thời gian bước nước nóng'].apply(convert_to_minutes)
    
    # 4) Tính tổng thời gian CIP (từ bắt đầu đến kết thúc)
    # Đảm bảo dữ liệu datetime hợp lệ trước khi tính toán
    valid_times = (~df_clean['Thời gian Bắt đầu CIP'].isna()) & (~df_clean['Thời gian Kết thúc CIP'].isna())
    df_clean.loc[valid_times, 'Tổng thời gian CIP (phút)'] = (
        (df_clean.loc[valid_times, 'Thời gian Kết thúc CIP'] - 
         df_clean.loc[valid_times, 'Thời gian Bắt đầu CIP']).dt.total_seconds() / 60
    )
    
    # Sắp xếp dữ liệu theo (Line, Circuit, Thiết bị, Thời gian Bắt đầu CIP)
    df_clean.sort_values(by=['Line', 'Circuit', 'Thiết bị', 'Thời gian Bắt đầu CIP'], inplace=True)
    
    # 5) Tính khoảng cách giữa 2 lần CIP liên tiếp cho cùng một thiết bị
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
    
    # Không cần tính lại tổng thời gian CIP vì đã tính trong hàm clean_data
    
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
            # Tính trung bình thời gian giữa các lần CIP cho mỗi thiết bị
            avg_time_gap = time_gap_data.groupby('Thiết bị')['time_gap_days'].mean().reset_index()
            avg_time_gap = avg_time_gap.sort_values('time_gap_days', ascending=False)
            
            # Vẽ biểu đồ cột thể hiện khoảng thời gian trung bình giữa các lần CIP theo thiết bị
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            bars = ax2.bar(
                avg_time_gap['Thiết bị'],
                avg_time_gap['time_gap_days'],
                color='skyblue'
            )
            
            # Thêm đường kẻ ngang biểu thị quy định 5 ngày
            ax2.axhline(5, color='red', linestyle='--', label='Quy định 5 ngày')
            
            # Thêm giá trị số ngày lên đỉnh mỗi cột
            for bar in bars:
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.1,
                    f'{height:.1f}',
                    ha='center',
                    va='bottom'
                )
            
            ax2.set_title(f"Thời gian trung bình giữa các lần CIP theo Thiết bị (Circuit: {selected_circuit}, Line: {selected_line})")
            ax2.set_xlabel("Thiết bị")
            ax2.set_ylabel("Thời gian trung bình (ngày)")
            ax2.set_ylim(0, max(avg_time_gap['time_gap_days']) * 1.2)  # Đặt giới hạn trục y để có không gian cho số
            ax2.legend()
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig2)
            
            # Thêm biểu đồ tỷ lệ tuân thủ quy định 5 ngày
            st.subheader("3) Tỷ lệ tuân thủ quy định 5 ngày")
            
            # Tính tỷ lệ tuân thủ cho mỗi thiết bị
            compliance_data = time_gap_data.groupby('Thiết bị').apply(
                lambda x: pd.Series({
                    'total_cips': len(x),
                    'compliant_cips': sum(x['time_gap_days'] <= 5),
                })
            ).reset_index()
            
            compliance_data['compliance_rate'] = (compliance_data['compliant_cips'] / compliance_data['total_cips'] * 100).round(1)
            compliance_data = compliance_data.sort_values('compliance_rate', ascending=False)
            
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            bars = ax3.bar(
                compliance_data['Thiết bị'],
                compliance_data['compliance_rate'],
                color='lightgreen'
            )
            
            # Thêm giá trị phần trăm lên đỉnh mỗi cột
            for bar in bars:
                height = bar.get_height()
                ax3.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 1,
                    f'{height:.1f}%',
                    ha='center',
                    va='bottom'
                )
            
            ax3.set_title(f"Tỷ lệ tuân thủ quy định 5 ngày theo Thiết bị (Circuit: {selected_circuit}, Line: {selected_line})")
            ax3.set_xlabel("Thiết bị")
            ax3.set_ylabel("Tỷ lệ tuân thủ (%)")
            ax3.set_ylim(0, 105)  # Giới hạn đến 105% để có không gian cho số
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig3)
            
            # Thêm bảng thống kê chi tiết về khoảng thời gian
            st.subheader("4) Thống kê chi tiết về khoảng thời gian giữa các lần CIP")
            
            # Tạo bảng thống kê rộng hơn với nhiều thông tin
            stats_df = time_gap_data.groupby('Thiết bị').agg(
                Trung_bình_ngày=('time_gap_days', 'mean'),
                Tối_thiểu_ngày=('time_gap_days', 'min'),
                Tối_đa_ngày=('time_gap_days', 'max'),
                Độ_lệch_chuẩn=('time_gap_days', 'std'),
                Số_lần_CIP=('time_gap_days', 'count'),
                Tỷ_lệ_tuân_thủ=('time_gap_days', lambda x: (sum(x <= 5) / len(x) * 100)),
                Số_lần_vượt_quy_định=('time_gap_days', lambda x: sum(x > 5))
            ).reset_index()
            
            # Làm tròn số thập phân
            numeric_cols = ['Trung_bình_ngày', 'Tối_thiểu_ngày', 'Tối_đa_ngày', 'Độ_lệch_chuẩn', 'Tỷ_lệ_tuân_thủ']
            stats_df[numeric_cols] = stats_df[numeric_cols].round(2)
            
            # Đổi tên cột để hiển thị tiếng Việt đẹp hơn
            stats_df.columns = ['Thiết bị', 'Trung bình (ngày)', 'Tối thiểu (ngày)', 'Tối đa (ngày)', 
                             'Độ lệch chuẩn (ngày)', 'Số lần CIP', 'Tỷ lệ tuân thủ (%)', 'Số lần vượt quy định']
            
            # Sắp xếp theo tỷ lệ tuân thủ giảm dần
            stats_df = stats_df.sort_values('Tỷ lệ tuân thủ (%)', ascending=False)
            
            st.dataframe(stats_df)
            
        except Exception as e:
            st.error(f"Lỗi khi vẽ biểu đồ khoảng thời gian: {str(e)}")
    else:
        st.warning("Không có đủ dữ liệu về khoảng thời gian giữa các lần CIP để vẽ biểu đồ.")
    
    # 5) Phân tích hiệu suất CIP
    st.subheader("5) Phân tích hiệu suất CIP")
    
    if not df_filtered.empty and 'Tổng thời gian CIP (phút)' in df_filtered.columns:
        try:
            # Tính trung bình thời gian CIP cho mỗi thiết bị
            avg_cip_duration = df_filtered.groupby('Thiết bị')['Tổng thời gian CIP (phút)'].mean().reset_index()
            avg_cip_duration = avg_cip_duration.sort_values('Tổng thời gian CIP (phút)', ascending=False)
            
            # Vẽ biểu đồ thời gian CIP trung bình theo thiết bị
            fig4, ax4 = plt.subplots(figsize=(10, 6))
            bars = ax4.bar(
                avg_cip_duration['Thiết bị'],
                avg_cip_duration['Tổng thời gian CIP (phút)'],
                color='lightcoral'
            )
            
            # Thêm giá trị lên đỉnh mỗi cột
            for bar in bars:
                height = bar.get_height()
                ax4.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.5,
                    f'{height:.1f}',
                    ha='center',
                    va='bottom'
                )
            
            ax4.set_title(f"Thời gian CIP trung bình theo Thiết bị (Circuit: {selected_circuit}, Line: {selected_line})")
            ax4.set_xlabel("Thiết bị")
            ax4.set_ylabel("Thời gian trung bình (phút)")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig4)
            
            # 6) Phân tích xu hướng nhiệt độ
            st.subheader("6) Phân tích xu hướng nhiệt độ")
            
            temp_columns = [
                ("Nhiệt độ Xút", "Nhiệt độ Xút Bắt đầu", "Nhiệt độ Xút Kết thúc"),
                ("Nhiệt độ Nước nóng", "Nhiệt độ Nước nóng Bắt đầu", "Nhiệt độ Nước nóng Kết thúc")
            ]
            
            for temp_type, start_col, end_col in temp_columns:
                if start_col in df_filtered.columns and end_col in df_filtered.columns:
                    # Tính chênh lệch nhiệt độ
                    df_filtered[f'Chênh lệch {temp_type}'] = df_filtered[end_col] - df_filtered[start_col]
                    
                    # Tính trung bình chênh lệch nhiệt độ cho mỗi thiết bị
                    avg_temp_diff = df_filtered.groupby('Thiết bị')[f'Chênh lệch {temp_type}'].mean().reset_index()
                    avg_temp_diff = avg_temp_diff.sort_values(f'Chênh lệch {temp_type}', ascending=False)
                    
                    # Vẽ biểu đồ chênh lệch nhiệt độ trung bình
                    fig5, ax5 = plt.subplots(figsize=(10, 6))
                    bars = ax5.bar(
                        avg_temp_diff['Thiết bị'],
                        avg_temp_diff[f'Chênh lệch {temp_type}'],
                        color='lightblue'
                    )
                    
                    # Thêm giá trị lên đỉnh mỗi cột
                    for bar in bars:
                        height = bar.get_height()
                        ax5.text(
                            bar.get_x() + bar.get_width()/2.,
                            height + 0.2,
                            f'{height:.1f}°C',
                            ha='center',
                            va='bottom'
                        )
                    
                    ax5.set_title(f"Chênh lệch {temp_type} trung bình theo Thiết bị (Circuit: {selected_circuit}, Line: {selected_line})")
                    ax5.set_xlabel("Thiết bị")
                    ax5.set_ylabel("Chênh lệch nhiệt độ trung bình (°C)")
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig5)
            
            # 7) Phân tích hiệu quả lưu lượng
            st.subheader("7) Phân tích hiệu quả lưu lượng")
            
            if 'Lưu lượng hồi (l/h)' in df_filtered.columns:
                # Tính trung bình lưu lượng hồi cho mỗi thiết bị
                avg_flow = df_filtered.groupby('Thiết bị')['Lưu lượng hồi (l/h)'].mean().reset_index()
                avg_flow = avg_flow.sort_values('Lưu lượng hồi (l/h)', ascending=False)
                
                fig6, ax6 = plt.subplots(figsize=(10, 6))
                bars = ax6.bar(
                    avg_flow['Thiết bị'],
                    avg_flow['Lưu lượng hồi (l/h)'],
                    color='lightsalmon'
                )
                
                # Thêm giá trị lên đỉnh mỗi cột
                for bar in bars:
                    height = bar.get_height()
                    ax6.text(
                        bar.get_x() + bar.get_width()/2.,
                        height + 100,
                        f'{height:.0f}',
                        ha='center',
                        va='bottom'
                    )
                
                ax6.set_title(f"Lưu lượng hồi trung bình theo Thiết bị (Circuit: {selected_circuit}, Line: {selected_line})")
                ax6.set_xlabel("Thiết bị")
                ax6.set_ylabel("Lưu lượng hồi trung bình (l/h)")
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig6)
            
        except Exception as e:
            st.error(f"Lỗi khi phân tích hiệu suất CIP: {str(e)}")
    
    # 8) Hiển thị bảng dữ liệu chi tiết
    with st.expander("Xem dữ liệu chi tiết"):
        # Hiển thị các cột quan trọng trước
        columns_to_display = [
            'Thiết bị', 'Line', 'Circuit', 'Chương trình CIP',
            'Thời gian Bắt đầu CIP', 'Thời gian Kết thúc CIP', 'Tổng thời gian CIP (phút)',
            'Lưu lượng hồi (l/h)', 'time_gap_days'
        ]
        # Lọc các cột có tồn tại trong dataframe
        existing_cols = [col for col in columns_to_display if col in df_filtered.columns]
        # Thêm các cột còn lại
        remaining_cols = [col for col in df_filtered.columns if col not in existing_cols]
        ordered_cols = existing_cols + remaining_cols
        
        st.dataframe(df_filtered[ordered_cols])

if __name__ == "__main__":
    main()
