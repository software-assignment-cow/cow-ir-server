import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# 1. 작성자님이 완벽하게 만들어 둔 Supabase 연동 부품 임포트
from test_supabase import get_registered_cows_with_images

app = FastAPI(title="소 비문 식별 MVP API")

# 프론트엔드(React) 연동을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. OpenCV ORB 기반 이미지 유사도 계산 함수 (기획서 반영)
def calculate_similarity(uploaded_bytes: bytes, registered_bytes: bytes) -> float:
    try:
        # 이미지 바이트 데이터를 OpenCV 이미지 객체로 디코딩 (그레이스케일 변환)
        nparr_up = np.frombuffer(uploaded_bytes, np.uint8)
        img_uploaded = cv2.imdecode(nparr_up, cv2.IMREAD_GRAYSCALE)

        nparr_reg = np.frombuffer(registered_bytes, np.uint8)
        img_registered = cv2.imdecode(nparr_reg, cv2.IMREAD_GRAYSCALE)

        if img_uploaded is None or img_registered is None:
            return 0.0

        # ORB 특징점 추출기 초기화
        orb = cv2.ORB_create(nfeatures=1000)
        kp1, des1 = orb.detectAndCompute(img_uploaded, None)
        kp2, des2 = orb.detectAndCompute(img_registered, None)

        if des1 is None or des2 is None:
            return 0.0

        # BFMatcher 매칭 도구 생성 (Hamming 거리 사용)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        if not matches:
            return 0.0

        # 유사도 매칭 점수 계산 (MVP 기준: 거리 50 미만의 좋은 특징점 비율)
        good_matches = [m for m in matches if m.distance < 50]
        total_features = min(len(kp1), len(kp2))
        
        if total_features == 0:
            return 0.0
            
        score = (len(good_matches) / total_features) * 100
        return round(score, 2)

    except Exception as e:
        print(f"⚠️ OpenCV 처리 중 오류 발생: {e}")
        return 0.0

# 3. 비문 매칭 API 엔드포인트 (기획서 및 리뷰 피드백 반영)
@app.post("/recognize")
async def recognize(image: UploadFile = File(...)):
    # 프론트엔드에서 업로드한 이미지 바이트 읽기
    file_bytes = await image.read()
    
    # [리뷰 반영 1] 작성자님의 Supabase 함수를 비동기(await)로 호출하여 등록된 소 목록 가져오기
    cows = await get_registered_cows_with_images()
    
    if not cows:
        return {"error": "등록된 소 데이터를 가져오지 못했습니다."}
        
    best_cow = None
    max_score = -1.0
    
    # [리뷰 반영 2] 가짜 데이터를 지우고, 1:N 전체 반복문을 돌며 실제 이미지 bytes로 유사도 계산
    for cow in cows:
        score = calculate_similarity(file_bytes, cow.image_bytes)
        if score > max_score:
            max_score = score
            best_cow = cow
            
    if best_cow is None:
        return {"error": "비교 대상을 찾을 수 없습니다."}
        
    # Supabase 스토리지의 Public 이미지 조회를 위한 Base URL 생성
    supabase_project_id = "lrxfzrbxobabevoyzuko"
    public_url = f"https://{supabase_project_id}.supabase.co/storage/v1/object/public/{best_cow.nose_image_path}"
    
    # [리뷰 반영 3] 딕셔너리 문법 대신 객체 속성(.속성명) 문법을 사용하여 최종 기획서 규격 JSON 반환
    return {
        "name": best_cow.name,
        "birthDate": str(best_cow.birth_date),
        "imageUrl": public_url,
        "score": int(max_score)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)