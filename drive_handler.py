# drive_handler.py (디버깅 포함)

import datetime
import fitz  # PyMuPDF
import io
import unicodedata
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
# 3. 문자열 정규화 (공백 제거 + 소문자 + 유니코드 통일)
# ─────────────────────────────────────────────
def normalize(text):
    return unicodedata.normalize('NFKC', text).replace(" ", "").lower()

# ─────────────────────────────────────────────
# 4. 해당 주차/지난주차 PDF 텍스트 추출 + 디버깅 출력 포함
# ─────────────────────────────────────────────
def get_weekly_files(service, folder_id, week_num):
    def get_text_from_week(week_keyword):
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        files = results.get("files", [])

        print(f"🔍 주차 키워드: {week_keyword} (정규화: {normalize(week_keyword)})")
        print(f"📂 검색된 파일 수: {len(files)}")

        for file in files:
            filename = file["name"]
            print(f"📝 검사 중: {filename} → 정규화: {normalize(filename)}")
            if "pdf" in file["mimeType"]:
                if normalize(week_keyword) in normalize(filename):
                    print(f"✅ 일치 파일 발견: {filename}")
                    file_id = file["id"]
                    request = service.files().get_media(fileId=file_id)
                    file_bytes = io.BytesIO(request.execute())
                    doc = fitz.open("pdf", file_bytes.read())
                    text = "\n".join([page.get_text() for page in doc])
                    print(f"📄 추출된 텍스트 길이: {len(text)}")
                    print(f"📄 미리보기: {text[:200].strip()}")
                    return text  # 빈 텍스트라도 반환 (디버깅용)
        print("⚠️ 일치하는 파일을 찾지 못했습니다.")
        return None

    this_week_text = get_text_from_week(f"{week_num}주차")
    last_week_text = get_text_from_week(f"{week_num - 1}주차") if week_num > 1 else None
    return last_week_text, this_week_text
