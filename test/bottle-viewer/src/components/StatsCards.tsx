import type { DatasetInfo } from '../types/dataset';
import './StatsCards.css';

interface StatsCardsProps {
  info: DatasetInfo | null;
}

export default function StatsCards({ info }: StatsCardsProps) {
  if (!info) return null;

  return (
    <div className="stats-cards">
      <div className="stat-card training">
        <span className="stat-icon">📦</span>
        <span className="stat-label">Training</span>
        <span className="stat-value">{info.train_count} images</span>
      </div>
      <div className="stat-card test-good">
        <span className="stat-icon">✅</span>
        <span className="stat-label">Test Good</span>
        <span className="stat-value">{info.test_good_count} images</span>
      </div>
      <div className="stat-card test-defect">
        <span className="stat-icon">❌</span>
        <span className="stat-label">Test Defects</span>
        <span className="stat-value">{info.test_defect_count} images</span>
      </div>
    </div>
  );
}
