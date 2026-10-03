import { X, SlidersHorizontal, RotateCcw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const filterDefinitions = [
  { id: 'exposure', label: 'Exposure', min: -50, max: 50, default: 0 },
  { id: 'contrast', label: 'Contrast', min: -50, max: 50, default: 0 },
  { id: 'saturation', label: 'Saturation', min: -100, max: 100, default: 0 },
  { id: 'temperature', label: 'Temperature', min: -50, max: 50, default: 0 },
  { id: 'tint', label: 'Tint', min: -50, max: 50, default: 0 },
  { id: 'highlights', label: 'Highlights', min: -50, max: 50, default: 0 },
  { id: 'shadows', label: 'Shadows', min: -50, max: 50, default: 0 },
  { id: 'vignette', label: 'Vignette', min: 0, max: 100, default: 0 },
];

export default function FilterSidebar({ isOpen, onClose, filters, setFilters }) {
  const handleChange = (id, value) => {
    setFilters(prev => ({ ...prev, [id]: parseFloat(value) }));
  };

  const handleReset = () => {
    const defaultFilters = {};
    filterDefinitions.forEach(f => { defaultFilters[f.id] = f.default; });
    setFilters(defaultFilters);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="sidebar-panel glass-panel"
        >
          <div className="sidebar-header flex-between">
            <div className="flex-center" style={{ gap: '8px' }}>
              <SlidersHorizontal size={20} color="var(--accent-primary)" />
              <h2>Adjustments</h2>
            </div>
            <button className="icon-button" onClick={onClose}>
              <X size={24} />
            </button>
          </div>

          <div className="sidebar-content">
            <div className="flex-between" style={{ marginBottom: '24px' }}>
              <span className="text-muted">Fine-tune your image</span>
              <button className="glass-button" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={handleReset}>
                <RotateCcw size={12} /> Reset All
              </button>
            </div>

            <div className="sliders-container">
              {filterDefinitions.map(filter => (
                <div key={filter.id} className="slider-group">
                  <div className="slider-header flex-between">
                    <label>{filter.label}</label>
                    <span className="slider-value">{filters[filter.id] > 0 ? `+${filters[filter.id]}` : filters[filter.id]}</span>
                  </div>
                  <input
                    type="range"
                    min={filter.min}
                    max={filter.max}
                    value={filters[filter.id] || 0}
                    onChange={(e) => handleChange(filter.id, e.target.value)}
                    className="custom-slider"
                  />
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
