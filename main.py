from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_registered_cows_with_images
from image_processing import calculate_similarity

app = FastAPI(title="소 비문 개체 식별 MVP API")

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

    image_url = f"https://lrxfzrbxobabevoyzuko.supabase.co/storage/v1/object/public/{best_cow.nose_image_path}"

    return {
        "name": best_cow.name,
        "birthDate": str(best_cow.birth_date),
        "imageUrl": image_url,
        "score": int(best_score)
    }
