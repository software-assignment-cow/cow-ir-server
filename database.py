# database.py

def get_registered_cows():
    """
    [Supabase 연동 영역]
    나중에 cows 테이블을 조회해서 id, name, birth_date, nose_image_path를 
    가져오는 진짜 코드가 들어올 예정입니다!
    """
    print("Supabase DB에서 등록된 소 목록 가져오는 중...")

    # 지금은 임시로 가짜 리스트를 반환해 둡니다.
    return [
        {"id": 1, "name": "진짜소1", "birth_date": "2023-01-01", "image_path": "path1.webp"},
        {"id": 2, "name": "진짜소2", "birth_date": "2022-05-10", "image_path": "path2.webp"}
    ]
