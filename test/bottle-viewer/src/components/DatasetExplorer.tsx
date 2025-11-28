import { useState, useMemo } from 'react';
import { useDatasets, useDatasetInfo, useTrainImages, useTestImages, getImageUrl, getGroundTruthUrl } from '../hooks/useDataset';
import CategorySelect from './CategorySelect';
import StatsCards from './StatsCards';
import ImageGrid from './ImageGrid';
import ImageModal from './ImageModal';
import DefectTypeFilter from './DefectTypeFilter';
import './DatasetExplorer.css';

export default function DatasetExplorer() {
  const { datasets } = useDatasets();
  const [selectedCategory, setSelectedCategory] = useState('bottle');
  const { info } = useDatasetInfo(selectedCategory);
  const { images: trainImages, total: trainTotal } = useTrainImages(selectedCategory);
  const { images: testImages } = useTestImages(selectedCategory);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalImage, setModalImage] = useState({ src: '', path: '' });
  const [selectedDefectType, setSelectedDefectType] = useState('all');

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    setSelectedDefectType('all');
  };

  const handleImageClick = (src: string, path: string) => {
    setModalImage({ src, path });
    setModalOpen(true);
  };

  const trainImageData = useMemo(() => {
    return trainImages.map((filename) => ({
      src: getImageUrl(selectedCategory, 'train/good', filename),
      filename,
      label: filename.replace('.png', ''),
    }));
  }, [trainImages, selectedCategory]);

  const filteredTestImages = useMemo(() => {
    if (selectedDefectType === 'all') {
      return testImages;
    }
    return testImages.filter((img) => img.type === selectedDefectType);
  }, [testImages, selectedDefectType]);

  const testImageData = useMemo(() => {
    return filteredTestImages.map((img) => ({
      src: getImageUrl(selectedCategory, `test/${img.type}`, img.filename),
      filename: img.filename,
      label: `${img.type}/${img.filename.replace('.png', '')}`,
      isDefect: img.is_defect,
      type: img.type,
    }));
  }, [filteredTestImages, selectedCategory]);

  const groundTruthData = useMemo(() => {
    return filteredTestImages.map((img) => {
      if (!img.is_defect) {
        return { src: null, filename: '-' };
      }
      return {
        src: getGroundTruthUrl(selectedCategory, img.type, img.filename),
        filename: img.filename.replace('.png', '_mask'),
      };
    });
  }, [filteredTestImages, selectedCategory]);

  const defectTypes = useMemo(() => {
    const types = new Set(testImages.map((img) => img.type));
    return Array.from(types).sort();
  }, [testImages]);

  return (
    <div className="dataset-explorer">
      <div className="explorer-header">
        <h1>📊 Dataset Explorer</h1>
        <CategorySelect
          categories={datasets.length > 0 ? datasets : ['bottle']}
          selected={selectedCategory}
          onChange={handleCategoryChange}
        />
      </div>

      <StatsCards info={info} />

      <ImageGrid
        key={`train-${selectedCategory}`}
        title="📷 Training Images"
        images={trainImageData}
        total={trainTotal}
        onImageClick={handleImageClick}
      />

      <div className="test-section">
        <div className="test-section-header">
          <h3>📷 Test Images</h3>
          <DefectTypeFilter
            types={defectTypes}
            selected={selectedDefectType}
            onChange={setSelectedDefectType}
          />
        </div>
        <ImageGrid
          key={`test-${selectedCategory}-${selectedDefectType}`}
          title=""
          images={testImageData}
          groundTruths={groundTruthData}
          total={filteredTestImages.length}
          onImageClick={handleImageClick}
        />
      </div>

      <div className="explorer-help">
        💡 Click any image for detailed view with zoom
      </div>

      <ImageModal
        isOpen={modalOpen}
        imageSrc={modalImage.src}
        imagePath={modalImage.path}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
}
