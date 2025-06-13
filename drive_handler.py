import datetime
import fitz  # PyMuPDF
from pptx import Presentation
import io

# ------------------ 주차 계산 ------------------ #
def get_current_week(start_date: datetime.date, today: datetime.date) -> int:
    return ((today - start_date).days // 7) + 1

# ------------------ Google Drive 탐색 ------------------ #
def get_week_folder_file(service, parent_folder_id, today):
    # 예: 학기 시작일
    semester_start = datetime.date(2025, 3, 4)
    week_num = get_current_week(semester_start, today.date())
    week_name = f"{week_num}주차"

    # 주차 폴더 검색
    folder_query = f"'{parent_folder_id}' in parents and title = '{week_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    folder_list = service.files().list(q=folder_query).execute().get('items', [])

    if not folder_list:
        return None

    week_folder_id = folder_list[0]['id']

    # 강의자료 파일 검색 (PDF 또는 PPTX 우선)
    file_query = f"'{week_folder_id}' in parents and (mimeType contains 'pdf' or mimeType contains 'presentation') and trashed = false"
    file_list = service.files().list(q=file_query).execute().get('items', [])

    return file_list[0] if file_list else None


# ------------------ 파일 내용 텍스트 추출 ------------------ #
def extract_text_from_file(service, file_metadata):
    file_id = file_metadata['id']
    file_name = file_metadata['title']
    mime_type = file_metadata['mimeType']

    file = service.files().get_media(fileId=file_id).execute()
    file_stream = io.BytesIO(file)

    if 'pdf' in mime_type:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        return text

    elif 'presentation' in mime_type:
        prs = Presentation(file_stream)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text

    return None
