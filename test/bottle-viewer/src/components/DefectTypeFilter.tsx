import './DefectTypeFilter.css';

interface DefectTypeFilterProps {
  types: string[];
  selected: string;
  onChange: (type: string) => void;
}

export default function DefectTypeFilter({ types, selected, onChange }: DefectTypeFilterProps) {
  return (
    <div className="defect-type-filter">
      <label>필터:</label>
      <select value={selected} onChange={(e) => onChange(e.target.value)}>
        <option value="all">All Types</option>
        {types.map((type) => (
          <option key={type} value={type}>
            {type === 'good' ? '✅ good' : `❌ ${type}`}
          </option>
        ))}
      </select>
    </div>
  );
}
