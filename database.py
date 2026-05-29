import os
import asyncio
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

# 1. Pydantic 최신(V2) 문법으로 수정된 모델 정의 
class RegisteredCow(BaseModel):
    id: int
    name: str
    birth_date: date = Field(..., alias="birth_date")
    nose_image_path: str = Field(..., alias="nose_image_path")
    image_bytes: bytes  # Storage에서 다운로드한 파일의 이진 데이터

    model_config = ConfigDict(populate_by_name=True)

# 2. 핵심 기능 함수: 전체 소 목록 및 이미지 다운로드 (부품)
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
                
                # Pydantic 모델에 데이터 예쁘게 담기
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

# 3. 부품이 잘 작동하는지 확인하는 테스트 시동 모터
async def main():
    print("🚀 실전용 코드(부품) 테스트 가동을 시작합니다...")
    result_data = await get_registered_cows_with_images()
    
    print("\n==========================================")
    if result_data:
        print(f"✅ 총 {len(result_data)}마리의 소 비문(코 무늬) 데이터를 성공적으로 로드했습니다!")
        # 첫 번째 소의 데이터 구조가 잘 잡혔는지 확인
        first_cow = result_data[0]
        print(f"  👉 1번 소 이름: {first_cow.name}")
        print(f"  👉 1번 소 비문 이미지 용량: {len(first_cow.image_bytes)} bytes")
    else:
        print("💡 데이터를 가져오지 못했습니다.")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(main())


    
    
    