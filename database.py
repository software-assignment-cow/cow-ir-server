import os
from typing import List
from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from dotenv import load_dotenv
from supabase import create_client, Client

# 환경 변수 로드 (.env 파일 사용)
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
COW_NOSEPRINT_BUCKET = "cow-noseprints"
COW_NOSEPRINT_SIGNED_URL_EXPIRES_IN_SECONDS = 60 * 60

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_cow_noseprint_file_path(path: str) -> str:
    if f"{COW_NOSEPRINT_BUCKET}/" in path:
        return path.split(f"{COW_NOSEPRINT_BUCKET}/")[-1]

    return path


def create_cow_noseprint_signed_url(path: str) -> str:
    file_path = get_cow_noseprint_file_path(path)
    response = supabase.storage.from_(COW_NOSEPRINT_BUCKET).create_signed_url(
        file_path,
        COW_NOSEPRINT_SIGNED_URL_EXPIRES_IN_SECONDS,
    )

    if isinstance(response, dict):
        return (
            response.get("signedURL")
            or response.get("signedUrl")
            or response.get("signed_url")
            or ""
        )

    return (
        getattr(response, "signedURL", None)
        or getattr(response, "signedUrl", None)
        or getattr(response, "signed_url", None)
        or ""
    )

# 1. Pydantic V2 모델 정의
class RegisteredCow(BaseModel):
    id: str  # 🛠️ UUID 문자열 형식을 지원하기 위해 str로 변경 (Validation Error 해결)
    name: str
    birth_date: date = Field(..., alias="birth_date")
    nose_image_path: str = Field(..., alias="nose_image_path")
    image_bytes: bytes  # Storage에서 다운로드한 파일의 이진 데이터

    model_config = ConfigDict(populate_by_name=True)

# 2. 핵심 기능 함수: 전체 소 목록 및 이미지 다운로드
async def get_registered_cows_with_images() -> List[RegisteredCow]:
    try:
        response = supabase.table("cows").select("id, name, birth_date, nose_image_path").execute()
        cow_records = response.data

        registered_cows: List[RegisteredCow] = []
        for record in cow_records:
            full_path = record.get("nose_image_path")
            if not full_path:
                continue
            
            # 🛠️ Storage 경로 불일치(Object not found) 해결 로직
            # DB에 어떤 형식으로 주소가 저장되어 있든, 버킷명 뒤의 순수 파일 경로만 잘라냅니다.
            file_path = get_cow_noseprint_file_path(full_path)

            try:
                # Storage에서 이미지 다운로드 (bytes 반환)
                image_data = supabase.storage.from_(COW_NOSEPRINT_BUCKET).download(file_path)
                
                # Pydantic 모델에 데이터 매핑
                cow_obj = RegisteredCow(
                    id=str(record["id"]), # UUID 객체일 경우를 대비해 안전하게 str 변환
                    name=record["name"],
                    birth_date=record["birth_date"],
                    nose_image_path=full_path,
                    image_bytes=image_data
                )
                registered_cows.append(cow_obj)
                
            except Exception as storage_err:
                print(f"❌ [ID: {record.get('id')}] 이미지 다운로드 실패: {storage_err}")
                continue

        return registered_cows

    except Exception as e:
        print(f"❌ Supabase 연동 중 오류 발생: {e}")
        return []
