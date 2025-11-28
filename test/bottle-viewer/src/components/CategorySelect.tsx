import './CategorySelect.css';

interface CategorySelectProps {
  categories: string[];
  selected: string;
  onChange: (category: string) => void;
}

export default function CategorySelect({ categories, selected, onChange }: CategorySelectProps) {
  return (
    <div className="category-select">
      <label htmlFor="category">카테고리:</label>
      <select
        id="category"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
      >
        {categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
      </select>
    </div>
  );
}
