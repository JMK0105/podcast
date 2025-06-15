# drive_handler.py (multi-PDF 병합 지원 버전)

import datetime
import fitz  # PyMuPDF
import io
import unicodedata
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

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

# 4. 주차별 PDF 텍스트 병합 + 마지막 PDF 바이너리 반환
def get_weekly_files_with_binary(service, folder_id, week_num):
    def fetch_all_files(week_keyword):
        query = f"'{folder_id}' in parents and trashed = false and mimeType = 'application/pdf'"
        results = service.files().list(q=query, fields="files(id, name, createdTime)").execute()
        files = results.get("files", [])

        matched_files = [f for f in files if normalize(week_keyword) in normalize(f["name"])]
        matched_files.sort(key=lambda f: f["createdTime"])  # 오래된 순서 → 마지막 파일은 최신

        print(f"📂 {week_keyword} 관련 PDF 수: {len(matched_files)}")
        return matched_files

    def download_and_extract_text(file_id):
        try:
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            doc = fitz.open("pdf", fh.read())
            return "\n".join([page.get_text() for page in doc]), fh
        except Exception as e:
            print(f"❌ PDF 처리 실패 (ID: {file_id}) - {e}")
            return "", None

    # 이번 주차
    this_week_keyword = f"{week_num}주차"
    this_files = fetch_all_files(this_week_keyword)

    this_text_merged = ""
    this_week_bytes = None

    for idx, file in enumerate(this_files):
        text, file_bytes = download_and_extract_text(file["id"])
        this_text_merged += text + "\n"
        if idx == len(this_files) - 1:  # 가장 마지막 파일은 binary로 저장
            this_week_bytes = file_bytes

    # 지난 주차 (단일 PDF만 처리)
    last_text = None
    if week_num > 1:
        last_week_keyword = f"{week_num - 1}주차"
        last_files = fetch_all_files(last_week_keyword)
        if last_files:
            last_text, _ = download_and_extract_text(last_files[-1]["id"])

    return last_text, this_text_merged.strip(), this_week_bytes
