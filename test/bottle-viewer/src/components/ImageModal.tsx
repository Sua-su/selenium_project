import { useState, useRef, useEffect, useCallback } from 'react';
import './ImageModal.css';

interface ImageModalProps {
  isOpen: boolean;
  imageSrc: string;
  imagePath: string;
  onClose: () => void;
}

export default function ImageModal({ isOpen, imageSrc, imagePath, onClose }: ImageModalProps) {
  const [zoom, setZoom] = useState(100);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  const resetView = useCallback(() => {
    setZoom(100);
    setPosition({ x: 0, y: 0 });
  }, []);

  useEffect(() => {
    if (isOpen) {
      resetView();
    }
  }, [isOpen, imageSrc, resetView]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -10 : 10;
    setZoom((prev) => Math.min(300, Math.max(25, prev + delta)));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleDoubleClick = () => {
    resetView();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">🔍 {imagePath}</span>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div
          ref={containerRef}
          className="image-container"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onDoubleClick={handleDoubleClick}
        >
          <img
            src={imageSrc}
            alt={imagePath}
            style={{
              transform: `translate(${position.x}px, ${position.y}px) scale(${zoom / 100})`,
              cursor: isDragging ? 'grabbing' : 'grab',
            }}
            draggable={false}
          />
        </div>

        <div className="zoom-control">
          <span>Zoom: 25%</span>
          <input
            type="range"
            min="25"
            max="300"
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
          />
          <span>300%</span>
          <span className="current-zoom">[{zoom}%]</span>
        </div>

        <div className="modal-help">
          💡 Drag to move • Scroll to zoom • Double-click: reset
        </div>
      </div>
    </div>
  );
}
