import { useState } from 'react';
import { X, Wand2, Image as ImageIcon, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { artStyleBaseUrl } from '../endPoints';

const STYLES = [
  { id: 1, name: 'Impression Sunrise', artworkName: 'impression_sunshine', artistName: 'monet', preview: 'https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=150&q=80' },
  { id: 2, name: 'The Scream', artworkName: 'the_scream', artistName: 'edward_munch', preview: 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=150&q=80' },
  { id: 3, name: 'Cafe Terrace', artworkName: 'cafe_terrace_at_night', artistName: 'gough', preview: 'https://images.unsplash.com/photo-1578301978693-85fa9c026f43?w=150&q=80' },
  {
    id: 4,
    name: 'The Great Wave',
    artworkName: 'the_great_wave_off_kanagawa',
    artistName: 'hokusai',
    preview: 'https://images.unsplash.com/photo-1552642986-ccb41e7059e7?w=150&q=80' // A sample thumbnail URL for the sidebar
  },
  {
    id: 5,
    name: 'Ghibli',
    artworkName: 'ghibli',
    artistName: 'ghibli',
    preview: 'https://images.unsplash.com/photo-1552642986-ccb41e7059e7?w=150&q=80' // A sample thumbnail URL for the sidebar
  },
  {
    id: 6,
    name: 'Doraemon',
    artworkName: 'doraemon',
    artistName: 'doraemon',
    preview: 'https://images.unsplash.com/photo-1552642986-ccb41e7059e7?w=150&q=80' // A sample thumbnail URL for the sidebar
  },
  {
    id: 7,
    name: 'Cyberpunk',
    artworkName: 'cyberpunk neon lit city streets',
    artistName: 'cyberpunk art',
    preview: 'https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?w=150&q=80'
  },
];

export default function ArtStyleSidebar({ isOpen, onClose, onApplyStyle, image }) {
  const [selectedStyle, setSelectedStyle] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApply = async () => {
    if (!selectedStyle || !image) return;

    setIsProcessing(true);
    try {
      // Get blob from current image
      const imageResponse = await fetch(image);
      const blob = await imageResponse.blob();

      const formData = new FormData();
      formData.append("file", blob, "canvas_image.jpg");
      formData.append("artwork_name", selectedStyle.artworkName);
      formData.append("artist_name", selectedStyle.artistName);
      formData.append("prompt", "");
      formData.append("negative_prompt", "");
      formData.append("num_inference_steps", "50");
      formData.append("guidance_scale", "7");

      const response = await fetch(`${artStyleBaseUrl}/generate_with_image`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Art Style transfer failed');
      }

      const data = await response.json();
      if (data.status === "success" && data.image_url_refined) {
        const fullImageUrl = `${artStyleBaseUrl}${data.image_url_refined.startsWith("/")
          ? data.image_url_refined
          : "/" + data.image_url_refined
          }`;
        onApplyStyle(fullImageUrl);
      } else {
        throw new Error("Invalid response");
      }
    } catch (error) {
      console.error(error);
      alert('Failed to apply art style. Please ensure the backend is running.');
    } finally {
      setIsProcessing(false);
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '-100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '-100%', opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="sidebar-panel glass-panel"
          style={{ left: 16, right: 'auto' }}
        >
          <div className="sidebar-header flex-between">
            <div className="flex-center" style={{ gap: '8px' }}>
              <Wand2 size={20} color="var(--accent-secondary)" />
              <h2>Art Style</h2>
            </div>
            <button className="icon-button" onClick={onClose}>
              <X size={24} />
            </button>
          </div>

          <div className="sidebar-content">
            <p className="text-muted" style={{ marginBottom: '20px' }}>
              Choose an art style to transform your image.
            </p>

            <div className="style-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {STYLES.map(style => (
                <div
                  key={style.id}
                  className={`style-card ${selectedStyle?.id === style.id ? 'selected' : ''}`}
                  onClick={() => setSelectedStyle(style)}
                  style={{
                    position: 'relative',
                    cursor: 'pointer',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    border: `2px solid ${selectedStyle?.id === style.id ? 'var(--accent-secondary)' : 'transparent'}`,
                    transition: 'all 0.2s'
                  }}
                >
                  <img src={style.preview} alt={style.name} style={{ width: '100%', height: '100px', objectFit: 'cover' }} />
                  <div style={{
                    position: 'absolute', bottom: 0, left: 0, right: 0,
                    background: 'rgba(0,0,0,0.6)', padding: '4px', textAlign: 'center',
                    fontSize: '12px', backdropFilter: 'blur(4px)'
                  }}>
                    {style.name}
                  </div>
                  {selectedStyle?.id === style.id && (
                    <div style={{ position: 'absolute', top: 4, right: 4, background: 'var(--accent-secondary)', borderRadius: '50%' }}>
                      <CheckCircle2 size={16} color="#fff" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div style={{ padding: '20px', borderTop: '1px solid var(--border-light)' }}>
            <button
              className="glass-button primary"
              style={{ width: '100%', padding: '12px', background: 'linear-gradient(135deg, var(--accent-secondary), var(--accent-primary))' }}
              disabled={!selectedStyle || isProcessing}
              onClick={handleApply}
            >
              {isProcessing ? 'Processing...' : 'Apply Style'}
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
