# image_processing.py

import cv2
import numpy as np


def calculate_similarity(uploaded_image_bytes, registered_image_bytes):
    """
    [B, C 담당 영역]
    업로드된 소 비문 이미지와 등록된 소 비문 이미지를
    OpenCV ORB + BFMatcher 방식으로 비교하여
    0~100 사이의 유사도 점수를 반환한다.
    """

    print("OpenCV 이미지 비교 엔진 가동 중...")

    # 1. 입력 이미지 bytes 검증
    if uploaded_image_bytes is None or len(uploaded_image_bytes) == 0:
        raise ValueError("업로드 이미지 데이터가 비어 있습니다.")

    if registered_image_bytes is None or len(registered_image_bytes) == 0:
        raise ValueError("등록 이미지 데이터가 비어 있습니다.")

    # 2. bytes 데이터를 numpy 배열로 변환
    uploaded_np = np.frombuffer(uploaded_image_bytes, np.uint8)
    registered_np = np.frombuffer(registered_image_bytes, np.uint8)

    # 3. numpy 배열을 OpenCV 이미지로 변환
    uploaded_image = cv2.imdecode(uploaded_np, cv2.IMREAD_COLOR)
    registered_image = cv2.imdecode(registered_np, cv2.IMREAD_COLOR)

    if uploaded_image is None:
        raise ValueError("업로드 이미지를 읽을 수 없습니다.")

    if registered_image is None:
        raise ValueError("등록 이미지를 읽을 수 없습니다.")

    # 4. grayscale 변환
    uploaded_gray = cv2.cvtColor(uploaded_image, cv2.COLOR_BGR2GRAY)
    registered_gray = cv2.cvtColor(registered_image, cv2.COLOR_BGR2GRAY)

    # 5. resize 처리
    target_size = (512, 512)
    uploaded_resized = cv2.resize(uploaded_gray, target_size)
    registered_resized = cv2.resize(registered_gray, target_size)

    # 6. 대비 보정
    uploaded_equalized = cv2.equalizeHist(uploaded_resized)
    registered_equalized = cv2.equalizeHist(registered_resized)

    # 7. ORB 특징점 추출
    orb = cv2.ORB_create(
        nfeatures=1000,
        scaleFactor=1.2,
        nlevels=8
    )

    uploaded_keypoints, uploaded_descriptors = orb.detectAndCompute(
        uploaded_equalized,
        None
    )

    registered_keypoints, registered_descriptors = orb.detectAndCompute(
        registered_equalized,
        None
    )

    # 특징점이 없으면 비교 불가
    if uploaded_descriptors is None or registered_descriptors is None:
        return 0.0

    if len(uploaded_keypoints) == 0 or len(registered_keypoints) == 0:
        return 0.0

    # 8. BFMatcher로 descriptor 매칭
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(uploaded_descriptors, registered_descriptors)

    if len(matches) == 0:
        return 0.0

    # distance가 낮을수록 더 좋은 매칭
    good_matches = [match for match in matches if match.distance < 60]

    # 9. similarity score 계산
    base_count = min(len(uploaded_keypoints), len(registered_keypoints))

    if base_count == 0:
        return 0.0

    score = len(good_matches) / base_count
    score = max(0.0, min(score, 1.0))

    # 0~1 점수를 0~100 점수로 변환
    score_percent = score * 100

    return round(score_percent, 2)