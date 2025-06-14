# drive_handler.py (서비스 계정 기반)

import datetime
import fitz  # PyMuPDF
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account

# ─────────────────────────────────────────────
# 1. Google Drive API 인증 (서비스 계정)
# ─────────────────────────────────────────────
def get_drive_service_from_secrets(secret_dict):
    creds = service_account.Credentials.from_service_account_info(secret_dict)
    return build("drive", "v3", credentials=creds)

# ─────────────────────────────────────────────
# 2. 주차 계산 함수
# ─────────────────────────────────────────────
def get_current_week(start_date: datetime.date, today: datetime.date) -> int:
    return ((today - start_date).days // 7) + 1

# ─────────────────────────────────────────────
# 3. 해당 주차/지난주차 PDF 텍스트 추출
# ─────────────────────────────────────────────
def get_weekly_files(service, folder_id, week_num):
    def get_text_from_week(week_keyword):
        query = f"'{folder_id}' in parents and name contains '{week_keyword}' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        files = results.get("files", [])

        for file in files:
            if "pdf" in file["mimeType"]:
                file_id = file["id"]
                request = service.files().get_media(fileId=file_id)
                file_bytes = io.BytesIO(request.execute())
                doc = fitz.open("pdf", file_bytes.read())
                return "\n".join([page.get_text() for page in doc])
        return None

    this_week_text = get_text_from_week(f"{week_num}주차")
    last_week_text = get_text_from_week(f"{week_num - 1}주차") if week_num > 1 else None
    return last_week_text, this_week_text
