# drive_handler.py (with binary + debugging)

import datetime
import fitz  # PyMuPDF
import io
import unicodedata
from googleapiclient.discovery import build
from google.oauth2 import service_account

# 1. Google Drive API 인증
def get_drive_service_from_secrets(secret_dict):
    creds = service_account.Credentials.from_service_account_info(secret_dict)
    return build("drive", "v3", credentials=creds)

# 2. 주차 계산
def get_current_week(start_date: datetime.date, today: datetime.date) -> int:
    return ((today - start_date).days // 7) + 1

# 3. 문자열 정규화
def normalize(text):
    return unicodedata.normalize('NFKC', text).replace(" ", "").lower()

# 4. 텍스트와 PDF 파일 바이너리 함께 반환
def get_weekly_files_with_binary(service, folder_id, week_num):
    def fetch_file_bytes(week_keyword):
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        files = results.get("files", [])

        print(f"🔍 주차 키워드: {week_keyword} (정규화: {normalize(week_keyword)})")
        print(f"📂 검색된 파일 수: {len(files)}")

        for file in files:
            if "pdf" in file["mimeType"] and normalize(week_keyword) in normalize(file["name"]):
                print(f"✅ 일치 파일 발견: {file['name']}")
                file_id = file["id"]
                request = service.files().get_media(fileId=file_id)
                file_bytes = io.BytesIO(request.execute())
                return file_bytes
        print("⚠️ 일치하는 파일을 찾지 못했습니다.")
        return None

    def extract_text(file_bytes):
        if file_bytes is None:
            return None
        file_bytes.seek(0)
        doc = fitz.open("pdf", file_bytes.read())
        return "\n".join([page.get_text() for page in doc])

    this_week_bytes = fetch_file_bytes(f"{week_num}주차")
    last_week_bytes = fetch_file_bytes(f"{week_num - 1}주차") if week_num > 1 else None

    this_text = extract_text(this_week_bytes)
    last_text = extract_text(last_week_bytes) if last_week_bytes else None

    return last_text, this_text, this_week_bytes
