from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="소 비문 개체 식별 MVP API")

# 프론트엔드 통신 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 최종 Response 구조 정의 (명세서 규격 일치)
class CowRecognitionResponse(BaseModel):
    name: str
    birthDate: str
    imageUrl: str
    score: int

@app.post("/recognize", response_model=CowRecognitionResponse)
async def recognize_cow(image: UploadFile = File(...)):
    # 프론트엔드에서 보낸 파일 이름 확인 로그
    print(f"수신된 파일명: {image.filename}")
    
    # 이미지 데이터를 bytes 형태로 변환 (이후 B,C 담당자 함수로 전달할 데이터)
    image_bytes = await image.read()
    
    # 임시 가짜 데이터 (1단계 테스트용)
    mock_response = {
        "name": "소돌이",
        "birthDate": "2021-03-12",
        "imageUrl": "https://supabase-storage-url.../cow-noseprints/cow1.webp",
        "score": 57
    }
    return mock_response
