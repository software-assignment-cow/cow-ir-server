import cv2
import numpy as np


def read_image_from_bytes(image_bytes: bytes):
    """
    이미지 bytes를 OpenCV 이미지로 변환한다.
    webp, png, jpg, jpeg 등을 처리할 수 있다.
    """
    if image_bytes is None or len(image_bytes) == 0:
        raise ValueError("이미지 데이터가 비어 있습니다.")

    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("이미지를 읽을 수 없습니다. 지원하지 않는 형식이거나 손상된 파일입니다.")

    return image


def preprocess_image(image, size=(512, 512)):
    """
    ORB 비교를 위한 이미지 전처리 함수.
    grayscale 변환, resize, 대비 보정을 수행한다.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, size)

    # 대비 보정
    equalized = cv2.equalizeHist(resized)

    return equalized


def extract_orb_features(image):
    """
    ORB 특징점과 descriptor를 추출한다.
    """
    orb = cv2.ORB_create(
        nfeatures=1000,
        scaleFactor=1.2,
        nlevels=8
    )

    keypoints, descriptors = orb.detectAndCompute(image, None)

    return keypoints, descriptors


def calculate_similarity(uploaded_image_bytes: bytes, registered_image_bytes: bytes) -> float:
    """
    업로드 이미지와 등록된 소 비문 이미지를 비교해서 0~100 사이 유사도 점수를 반환한다.

    Args:
        uploaded_image_bytes: 프론트엔드에서 업로드된 소 비문 이미지 bytes
        registered_image_bytes: Supabase Storage에서 가져온 등록 소 비문 이미지 bytes

    Returns:
        float: 0.0 ~ 100.0 사이 유사도 점수.
               100에 가까울수록 더 유사하다.
    """
    uploaded_image = read_image_from_bytes(uploaded_image_bytes)
    registered_image = read_image_from_bytes(registered_image_bytes)

    processed_uploaded = preprocess_image(uploaded_image)
    processed_registered = preprocess_image(registered_image)

    uploaded_keypoints, uploaded_descriptors = extract_orb_features(processed_uploaded)
    registered_keypoints, registered_descriptors = extract_orb_features(processed_registered)

    if uploaded_descriptors is None or registered_descriptors is None:
        return 0.0

    if len(uploaded_keypoints) == 0 or len(registered_keypoints) == 0:
        return 0.0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(uploaded_descriptors, registered_descriptors)

    if len(matches) == 0:
        return 0.0

    # distance가 낮을수록 더 좋은 매칭
    good_matches = [match for match in matches if match.distance < 60]

    base_count = min(len(uploaded_keypoints), len(registered_keypoints))

    if base_count == 0:
        return 0.0

    score = len(good_matches) / base_count
    score = max(0.0, min(score, 1.0))

    score_percent = score * 100

    return round(score_percent, 2)