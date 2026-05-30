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
    id: str  # 🛠️ [해결 1] int에서 str로 변경하여 UUID 문자열 형식 지원 (Validation Error 해결)
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
            
            # 🛠️ [해결 2] 경로 불일치(404 Object not found) 완벽 방어 로직
            # DB에 전체 URL(https://...)이나 버킷명이 포함된 경로가 들어있어도
            # 'cow-noseprints/' 뒷부분의 순수 파일명/경로만 깔끔하게 잘라냅니다.
            if f"{bucket_name}/" in full_path:
                file_path = full_path.split(f"{bucket_name}/")[-1]
            else:
                file_path = full_path

            try:
                # Storage에서 이미지 다운로드 (bytes 반환)
                image_data = supabase.storage.from_(bucket_name).download(file_path)
                
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