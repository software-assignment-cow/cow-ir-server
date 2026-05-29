from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

#  1, 2단계에서 새로 만든 분리된 방(파일)들로부터 함수 불러오기!
from image_processing import calculate_similarity
from database import get_registered_cows

app = FastAPI()

# 프론트엔드 배포 주소 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cow-ir-client.netlify.app","http://localhost:5173"], # 프론트 주소 생기면 여기에 적어주기
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/recognize")
async def recognize_cow(image: UploadFile = File(...)):
    file_bytes = await image.read()
    print(f"🎯 프론트로부터 수신된 비문 파일명: {image.filename}")
    
    # 2. Supabase 방(database.py)에서 소 목록 가져오기
    cows = get_registered_cows()
    
    # [피드백 반영] 빈 배열(데이터가 없을 때) 케이스 방어하기!
    if not cows:  # 소 목록이 텅 비어있다면(빈 리스트라면)
        return {
            "name": "등록된 소 없음",
            "birthDate": "",
            "imageUrl": "",
            "score": 0.0,
            "message": "데이터베이스에 등록된 소 정보가 존재하지 않습니다."
        }
    
    # 3. OpenCV 방(image_processing.py)에서 비교 연산 돌리기
    mock_registered_bytes = b"sample_bytes"
    final_score = calculate_similarity(file_bytes, mock_registered_bytes)
    
    # 4. 최종 조립된 결과를 프론트엔드로 반환!
    return {
        "name": cows[0]["name"],         
        "birthDate": cows[0]["birth_date"],
        "imageUrl": "https://example.com/test.webp",
        "score": final_score             
    }
