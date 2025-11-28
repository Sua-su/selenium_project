#!/usr/bin/env python3
"""
데이터셋 폴더 구조와 데이터셋 갯수를 표시하는 스크립트
"""

import os
from pathlib import Path
from collections import defaultdict


def count_files(directory: Path, extensions: tuple = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')) -> int:
    """지정된 확장자를 가진 파일 갯수를 계산"""
    count = 0
    for ext in extensions:
        count += len(list(directory.glob(f'*{ext}')))
        count += len(list(directory.glob(f'*{ext.upper()}')))
    return count


def display_tree(directory: Path, prefix: str = "", is_last: bool = True, depth: int = 0, max_depth: int = 5):
    """폴더 구조를 트리 형태로 출력"""
    if depth > max_depth:
        return

    connector = "└── " if is_last else "├── "

    if depth == 0:
        print(f"📁 {directory.name}/")
    else:
        # 파일 갯수 계산
        file_count = count_files(directory)
        count_str = f" ({file_count} images)" if file_count > 0 else ""
        print(f"{prefix}{connector}📁 {directory.name}/{count_str}")

    # 하위 디렉토리 목록
    subdirs = sorted([d for d in directory.iterdir() if d.is_dir() and not d.name.startswith('.')])

    for i, subdir in enumerate(subdirs):
        is_last_item = (i == len(subdirs) - 1)
        new_prefix = prefix + ("    " if is_last else "│   ")
        display_tree(subdir, new_prefix, is_last_item, depth + 1, max_depth)


def summarize_datasets(data_dir: Path):
    """데이터셋 요약 정보 출력"""
    print("\n" + "=" * 60)
    print("📊 데이터셋 요약")
    print("=" * 60)

    total_images = 0
    dataset_stats = defaultdict(lambda: defaultdict(int))

    # MVTec AD 데이터셋 분석
    mvtec_dir = data_dir / "mvtec_ad"
    if mvtec_dir.exists():
        print(f"\n🔍 MVTec AD 데이터셋")
        print("-" * 40)

        categories = sorted([d for d in mvtec_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])

        for category in categories:
            train_dir = category / "train"
            test_dir = category / "test"
            gt_dir = category / "ground_truth"

            train_count = 0
            test_count = 0

            if train_dir.exists():
                for subdir in train_dir.iterdir():
                    if subdir.is_dir():
                        train_count += count_files(subdir)

            if test_dir.exists():
                for subdir in test_dir.iterdir():
                    if subdir.is_dir():
                        test_count += count_files(subdir)

            total = train_count + test_count
            total_images += total

            print(f"  📦 {category.name}:")
            print(f"      - Train: {train_count} images")
            print(f"      - Test:  {test_count} images")
            print(f"      - Total: {total} images")

            # 테스트 세트 상세 (결함 유형별)
            if test_dir.exists():
                defect_types = sorted([d for d in test_dir.iterdir() if d.is_dir()])
                if defect_types:
                    print(f"      - Test 결함 유형:")
                    for defect in defect_types:
                        defect_count = count_files(defect)
                        print(f"          • {defect.name}: {defect_count} images")

    print("\n" + "=" * 60)
    print(f"📈 총 이미지 수: {total_images}")
    print("=" * 60)


def main():
    # 현재 스크립트가 위치한 디렉토리를 data 디렉토리로 사용
    data_dir = Path(__file__).parent.resolve()

    print("=" * 60)
    print("📂 데이터 폴더 구조")
    print("=" * 60)
    print()

    # 트리 구조 출력
    display_tree(data_dir)

    # 요약 정보 출력
    summarize_datasets(data_dir)


if __name__ == "__main__":
    main()
