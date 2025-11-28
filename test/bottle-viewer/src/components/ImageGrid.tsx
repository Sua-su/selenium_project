import { useState } from 'react';
import './ImageGrid.css';

interface ImageGridProps {
  title: string;
  images: Array<{ src: string; filename: string; label?: string; isDefect?: boolean }>;
  groundTruths?: Array<{ src: string | null; filename: string }>;
  total: number;
  onImageClick: (src: string, path: string) => void;
}

export default function ImageGrid({ title, images, groundTruths, total, onImageClick }: ImageGridProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const displayCount = 5;

  const handlePrev = () => {
    setCurrentIndex(Math.max(0, currentIndex - 4));
  };

  const handleNext = () => {
    setCurrentIndex(Math.min(images.length - displayCount, currentIndex + 4));
  };

  const displayedImages = images.slice(currentIndex, currentIndex + displayCount);
  const displayedGTs = groundTruths?.slice(currentIndex, currentIndex + displayCount);

  const leftDisabled = currentIndex === 0;
  const rightDisabled = currentIndex + displayCount >= images.length;

  const showingStart = currentIndex + 1;
  const showingEnd = Math.min(currentIndex + displayCount, total);

  return (
    <div className="image-grid-section">
      {title && <h3>{title}</h3>}
      <div className="image-grid-container">
        <button
          className="nav-button prev"
          onClick={handlePrev}
          disabled={leftDisabled}
        >
          ◀
        </button>

        <div className="image-grid-wrapper">
          <div className="image-grid">
            {displayedImages.map((img, idx) => (
              <div
                key={`${currentIndex}-${idx}`}
                className="image-card"
                onClick={() => onImageClick(img.src, img.filename)}
              >
                <div className="image-wrapper">
                  {img.isDefect !== undefined && (
                    <span className={`status-badge ${img.isDefect ? 'defect' : 'good'}`}>
                      {img.isDefect ? '❌' : '✅'}
                    </span>
                  )}
                  <img src={img.src} alt={img.filename} />
                </div>
                <p className="filename">{img.label || img.filename}</p>
              </div>
            ))}
          </div>

          {displayedGTs && (
            <div className="ground-truth-grid">
              <p className="gt-label">🎯 Ground Truth</p>
              <div className="image-grid">
                {displayedGTs.map((gt, idx) => (
                  <div
                    key={`gt-${currentIndex}-${idx}`}
                    className={`image-card gt-card ${!gt.src ? 'na' : ''}`}
                    onClick={() => gt.src && onImageClick(gt.src, gt.filename)}
                  >
                    <div className="image-wrapper">
                      {gt.src ? (
                        <img src={gt.src} alt={gt.filename} />
                      ) : (
                        <div className="na-placeholder">N/A</div>
                      )}
                    </div>
                    <p className="filename">{gt.src ? gt.filename : '-'}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <button
          className="nav-button next"
          onClick={handleNext}
          disabled={rightDisabled}
        >
          ▶
        </button>
      </div>

      <p className="showing-info">Showing {showingStart}-{showingEnd} of {total}</p>
    </div>
  );
}
