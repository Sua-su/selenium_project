import { useState, useEffect } from 'react';
import type { DatasetInfo, ImageListResponse, TestImagesResponse } from '../types/dataset';

const API_BASE = 'http://localhost:8000/api';

export function useDatasets() {
  const [datasets, setDatasets] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/datasets`)
      .then(res => res.json())
      .then(data => {
        setDatasets(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { datasets, loading, error };
}

export function useDatasetInfo(category: string) {
  const [info, setInfo] = useState<DatasetInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!category) return;
    setLoading(true);
    fetch(`${API_BASE}/dataset/${category}`)
      .then(res => res.json())
      .then(data => {
        setInfo(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [category]);

  return { info, loading, error };
}

export function useTrainImages(category: string) {
  const [images, setImages] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!category) return;
    setLoading(true);
    fetch(`${API_BASE}/images/${category}/train/good`)
      .then(res => res.json())
      .then((data: ImageListResponse) => {
        setImages(data.images);
        setTotal(data.total);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [category]);

  return { images, total, loading };
}

export function useTestImages(category: string) {
  const [images, setImages] = useState<TestImagesResponse['images']>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!category) return;
    setLoading(true);
    fetch(`${API_BASE}/test-images/${category}`)
      .then(res => res.json())
      .then((data: TestImagesResponse) => {
        setImages(data.images);
        setTotal(data.total);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [category]);

  return { images, total, loading };
}

export function getImageUrl(category: string, imageType: string, filename: string): string {
  return `${API_BASE}/image/${category}/${imageType}/${filename}`;
}

export function getGroundTruthUrl(category: string, defectType: string, filename: string): string {
  return `${API_BASE}/ground-truth/${category}/${defectType}/${filename}`;
}
