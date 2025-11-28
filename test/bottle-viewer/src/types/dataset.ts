export interface DefectType {
  name: string;
  count: number;
}

export interface DatasetInfo {
  category: string;
  train_count: number;
  test_good_count: number;
  test_defect_count: number;
  defect_types: DefectType[];
}

export interface ImageListResponse {
  images: string[];
  total: number;
}

export interface TestImage {
  filename: string;
  type: string;
  is_defect: boolean;
}

export interface TestImagesResponse {
  images: TestImage[];
  total: number;
}
