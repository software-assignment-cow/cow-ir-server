from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import (
    COW_NOSEPRINT_BUCKET,
    SUPABASE_URL,
    get_cow_noseprint_file_path,
    get_registered_cows_with_images,
)
from image_processing import calculate_similarity

app = FastAPI(title="소 비문 개체 식별 MVP API")
MIN_RECOGNITION_SCORE = 20

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CowRecognitionResponse(BaseModel):
    name: str
    birthDate: str
    imageUrl: str
    score: int


def create_cow_noseprint_public_url(path: str) -> str:
    file_path = get_cow_noseprint_file_path(path)
    return f"{SUPABASE_URL}/storage/v1/object/public/{COW_NOSEPRINT_BUCKET}/{file_path}"


@app.post("/recognize", response_model=CowRecognitionResponse)
async def recognize_cow(image: UploadFile = File(...)):
    uploaded_bytes = await image.read()

    cows = await get_registered_cows_with_images()

    if not cows:
        return {
            "name": "등록된 소 없음",
            "birthDate": "",
            "imageUrl": "",
            "score": 0
        }

    best_cow = None
    best_score = -1

    for cow in cows:
        score = calculate_similarity(uploaded_bytes, cow.image_bytes)

        if score > best_score:
            best_score = score
            best_cow = cow

    if best_score < MIN_RECOGNITION_SCORE:
        return {
            "name": "일치하는 소 없음",
            "birthDate": "",
            "imageUrl": "",
            "score": int(best_score)
        }

    image_url = create_cow_noseprint_public_url(best_cow.nose_image_path)

    return {
        "name": best_cow.name,
        "birthDate": str(best_cow.birth_date),
        "imageUrl": image_url,
        "score": int(best_score)
    }
