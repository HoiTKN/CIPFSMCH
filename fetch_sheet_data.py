import os
import gspread
import pandas as pd
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Phạm vi truy cập, chỉ cần quyền đọc Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_credentials_from_env():
    """
    Hàm này lấy client_id, client_secret, refresh_token từ biến môi trường,
    tạo Credentials và tự động refresh token nếu cần.
    """
    client_id = os.environ["CLIENT_ID"]       # Tương ứng secrets.CLIENT_ID
    client_secret = os.environ["CLIENT_SECRET"]  # Tương ứng secrets.CLIENT_SECRET
    refresh_token = os.environ["REFRESH_TOKEN"]  # Tương ứng secrets.REFRESH_TOKEN

    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": SCOPES,
        "token": ""  # Access token để trống, sẽ được refresh
    }

    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    # Nếu token đã hết hạn, tự refresh
    if not creds.valid:
        creds.refresh(Request())

    return creds

def fetch_data_from_sheet():
    """
    Hàm này:
    1. Lấy credentials
    2. Kết nối Google Sheet qua gspread
    3. Mở Sheet theo SHEET_ID
    4. Đọc dữ liệu, chuyển thành DataFrame
    5. Trả về DataFrame
    """
    creds = get_credentials_from_env()
    client = gspread.authorize(creds)

    # Lấy sheet_id từ biến môi trường (đã lưu trong GitHub Secrets)
    sheet_id = os.environ["SHEET_ID"]
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"

    # Mở Google Sheet
    workbook = client.open_by_url(sheet_url)
    worksheet = workbook.get_worksheet(0)  # Lấy sheet đầu tiên (gid=0)

    # Đọc toàn bộ dữ liệu thành list of dict
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def main():
    # Gọi hàm fetch_data_from_sheet
    df = fetch_data_from_sheet()

    # Lưu dữ liệu ra file CSV để sử dụng sau (VD: data.csv)
    df.to_csv("data.csv", index=False)
    print("Dữ liệu đã được lưu vào data.csv thành công.")

if __name__ == "__main__":
    main()
