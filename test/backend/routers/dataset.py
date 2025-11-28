import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "mvtec_ad"

@router.get("/datasets")
def get_datasets():
    """사용 가능한 데이터셋 카테고리 목록 반환"""
    categories = [d.name for d in DATA_PATH.iterdir() if d.is_dir()]
    return sorted(categories)

@router.get("/dataset/{category}")
def get_dataset_info(category: str):
    """특정 카테고리의 데이터셋 정보 반환"""
    category_path = DATA_PATH / category
    if not category_path.exists():
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

    train_good_path = category_path / "train" / "good"
    test_path = category_path / "test"

    train_count = len(list(train_good_path.glob("*.png"))) if train_good_path.exists() else 0

    test_good_count = 0
    test_defect_count = 0
    defect_types = []

    if test_path.exists():
        for subdir in test_path.iterdir():
            if subdir.is_dir():
                count = len(list(subdir.glob("*.png")))
                if subdir.name == "good":
                    test_good_count = count
                else:
                    test_defect_count += count
                    defect_types.append({"name": subdir.name, "count": count})

    return {
        "category": category,
        "train_count": train_count,
        "test_good_count": test_good_count,
        "test_defect_count": test_defect_count,
        "defect_types": sorted(defect_types, key=lambda x: x["name"])
    }

@router.get("/images/{category}/{image_type:path}")
def get_images(category: str, image_type: str):
    """특정 카테고리/타입의 이미지 목록 반환"""
    images_path = DATA_PATH / category / image_type
    if not images_path.exists():
        raise HTTPException(status_code=404, detail=f"Path '{category}/{image_type}' not found")

    images = sorted([f.name for f in images_path.glob("*.png")])
    return {"images": images, "total": len(images)}

@router.get("/image/{category}/{image_type:path}/{filename}")
def get_image(category: str, image_type: str, filename: str):
    """이미지 파일 반환"""
    image_path = DATA_PATH / category / image_type / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    return FileResponse(image_path, media_type="image/png")

@router.get("/ground-truth/{category}/{defect_type}/{filename}")
def get_ground_truth(category: str, defect_type: str, filename: str):
    """Ground Truth 마스크 이미지 반환"""
    mask_filename = filename.replace(".png", "_mask.png")
    gt_path = DATA_PATH / category / "ground_truth" / defect_type / mask_filename

    if not gt_path.exists():
        raise HTTPException(status_code=404, detail=f"Ground truth not found: {mask_filename}")

    return FileResponse(gt_path, media_type="image/png")

@router.get("/test-images/{category}")
def get_all_test_images(category: str):
    """테스트 이미지 전체 목록 반환 (good + defects)"""
    test_path = DATA_PATH / category / "test"
    if not test_path.exists():
        raise HTTPException(status_code=404, detail=f"Test path not found for '{category}'")

    all_images = []
    for subdir in sorted(test_path.iterdir()):
        if subdir.is_dir():
            for img in sorted(subdir.glob("*.png")):
                all_images.append({
                    "filename": img.name,
                    "type": subdir.name,
                    "is_defect": subdir.name != "good"
                })

    return {"images": all_images, "total": len(all_images)}
