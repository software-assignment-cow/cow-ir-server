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


def calculate_similarity(desc1, desc2, kp1_count, kp2_count):
    """
    ORB descriptor를 BFMatcher로 비교하여 0.0 ~ 1.0 사이 점수를 계산한다.
    """
    if desc1 is None or desc2 is None:
        return 0.0

    if kp1_count == 0 or kp2_count == 0:
        return 0.0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(desc1, desc2)

    if len(matches) == 0:
        return 0.0

    good_matches = [m for m in matches if m.distance < 60]

    base_count = min(kp1_count, kp2_count)

    if base_count == 0:
        return 0.0

    score = len(good_matches) / base_count
    score = max(0.0, min(score, 1.0))

    score_percent = score * 100

    return round(score_percent, 2)


def compare_cow_nose_similarity(image_bytes_1: bytes, image_bytes_2: bytes) -> float:
    """
    소 비문 이미지 2장을 비교해서 유사도 점수를 반환한다.

    반환값:
        0.0 ~ 1.0
        1.0에 가까울수록 유사함
    """
    image1 = read_image_from_bytes(image_bytes_1)
    image2 = read_image_from_bytes(image_bytes_2)

    processed1 = preprocess_image(image1)
    processed2 = preprocess_image(image2)

    kp1, desc1 = extract_orb_features(processed1)
    kp2, desc2 = extract_orb_features(processed2)

    score = calculate_similarity(
        desc1,
        desc2,
        len(kp1),
        len(kp2)
    )

    return score