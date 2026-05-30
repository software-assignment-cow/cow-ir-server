import os
from typing import List
from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from dotenv import load_dotenv
from supabase import create_client, Client

# 환경 변수 로드 (.env 파일 사용)
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Pydantic V2 모델 정의
class RegisteredCow(BaseModel):
    id: int
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
        bucket_name = "cow-noseprints"

        for record in cow_records:
            full_path = record.get("nose_image_path")
            if not full_path:
                continue
                
            file_path = full_path.replace(f"{bucket_name}/", "") if full_path.startswith(bucket_name) else full_path

            try:
                # Storage에서 이미지 다운로드 (bytes 반환)
                image_data = supabase.storage.from_(bucket_name).download(file_path)
                
                # Pydantic 모델에 데이터 매핑
                cow_obj = RegisteredCow(
                    id=record["id"],
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