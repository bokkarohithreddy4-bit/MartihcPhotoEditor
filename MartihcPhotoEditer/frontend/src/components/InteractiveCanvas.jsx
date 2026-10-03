import { useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { useSpring, animated } from '@react-spring/web';
import { useGesture } from '@use-gesture/react';
import { Sparkles, Loader2 } from 'lucide-react';
import { useRefinePrompt } from '../hooks/useRefinePrompt';

const InteractiveCanvas = forwardRef(({ image, filters = {}, onRefine, onGenerate }, ref) => {
  const containerRef = useRef(null);
  const [prompt, setPrompt] = useState("");
  const { refinePrompt, isRefining, error } = useRefinePrompt();
  
  // Spring physics for smooth panning and zooming
  const [{ x, y, scale }, api] = useSpring(() => ({
    x: 0,
    y: 0,
    scale: 1,
    config: { mass: 1, tension: 250, friction: 30 }
  }));

  // Handle gestures
  useGesture(
    {
      onDrag: ({ offset: [dx, dy], pinching, cancel }) => {
        if (pinching) return cancel();
        api.start({ x: dx, y: dy });
      },
      onPinch: ({ offset: [d], origin: [ox, oy], memo }) => {
        // Simple scale implementation (origin handling requires more math, keeping it simple for now)
        api.start({ scale: Math.max(0.5, Math.min(d, 5)) });
      },
      onWheel: ({ delta: [, dy], ctrlKey }) => {
        if (ctrlKey) {
          // Zoom
          const currentScale = scale.get();
          const newScale = Math.max(0.5, Math.min(currentScale - dy * 0.01, 5));
          api.start({ scale: newScale });
        } else {
          // Pan
          api.start({ 
            x: x.get() - 0, // Ignoring x pan for simplicity 
            y: y.get() - dy 
          });
        }
      }
    },
    {
      target: containerRef,
      drag: { from: () => [x.get(), y.get()] },
      pinch: { scaleBounds: { min: 0.5, max: 5 }, rubberband: true },
      eventOptions: { passive: false }
    }
  );

  // Reset zoom on double click
  const handleDoubleClick = () => {
    api.start({ x: 0, y: 0, scale: 1 });
  };

  // Convert filter values (-50 to 50, etc) to CSS filter strings
  // exposure -> brightness, contrast -> contrast, saturation -> saturate, temperature -> sepia/hue-rotate
  const cssFilters = `
    brightness(${100 + (filters.exposure || 0)}%)
    contrast(${100 + (filters.contrast || 0)}%)
    saturate(${100 + (filters.saturation || 0)}%)
    sepia(${Math.max(0, filters.temperature || 0)}%)
    hue-rotate(${(filters.tint || 0)}deg)
  `.trim();

  // Highlight and shadow hacks via mix-blend-mode or complex SVG filters are hard in pure CSS.
  // We apply the basic ones via the `filter` property.

  const handleRefine = async () => {
    if (!prompt.trim()) return;
    const refined = await refinePrompt(prompt);
    if (refined) {
      setPrompt(refined);
    }
    if (onRefine) onRefine(refined || prompt);
  };

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    if (onGenerate) onGenerate(prompt);
  };

  useImperativeHandle(ref, () => ({
    exportImage: () => {
      if (!image) return;
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        
        // Apply basic filters
        ctx.filter = cssFilters;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Apply vignette if needed
        if (filters.vignette > 0) {
          const gradient = ctx.createRadialGradient(
            canvas.width / 2, canvas.height / 2, 0,
            canvas.width / 2, canvas.height / 2, Math.max(canvas.width, canvas.height) / 2
          );
          gradient.addColorStop(0.4, 'transparent');
          gradient.addColorStop(1, `rgba(0,0,0,${filters.vignette / 100})`);
          ctx.fillStyle = gradient;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
        const link = document.createElement('a');
        link.download = 'artstyle-export.jpg';
        link.href = dataUrl;
        link.click();
      };
      img.src = image;
    }
  }));

  return (
    <div 
      ref={containerRef} 
      className="canvas-container glass-panel"
      style={{ touchAction: 'none', cursor: 'grab' }}
      onDoubleClick={handleDoubleClick}
    >
      <animated.div
        style={{
          x,
          y,
          scale,
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transformOrigin: 'center center'
        }}
      >
        <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <img 
            src={image} 
            alt="Workspace" 
            className="workspace-image" 
            draggable="false"
            style={{ filter: cssFilters, transition: 'filter 0.1s ease-out' }}
          />
          {/* Vignette Overlay */}
          {filters.vignette > 0 && (
            <div style={{
              position: 'absolute',
              inset: 0,
              pointerEvents: 'none',
              background: `radial-gradient(circle, transparent 40%, rgba(0,0,0,${filters.vignette / 100}) 100%)`
            }} />
          )}
        </div>
      </animated.div>
      
      {/* Floating Toolbar inside canvas container */}
      <div className="floating-toolbar glass-panel flex-center">
        <div className="prompt-bar" style={{ position: 'relative' }}>
          <Sparkles size={16} color="var(--accent-primary)" />
          <input 
            type="text" 
            placeholder="What do you want to change? (e.g., Make it cinematic)" 
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRefine()}
            style={{ paddingRight: '140px' }}
          />
          <div style={{ position: 'absolute', right: '4px', display: 'flex', gap: '4px' }}>
            <button 
              className="glass-button ghost-refine-btn"
              onClick={handleRefine}
              disabled={isRefining}
              style={{ padding: '6px 12px' }}
            >
              {isRefining ? <Loader2 size={14} className="animate-spin" /> : "Refine"}
            </button>
            <button 
              className="glass-button primary ghost-refine-btn"
              onClick={handleGenerate}
              style={{ padding: '6px 12px' }}
            >
              Generate
            </button>
          </div>
          {error && <div style={{position: 'absolute', top: '-30px', left: 0, color: '#ef4444', fontSize: '12px'}}>{error}</div>}
        </div>
      </div>
    </div>
  );
});

export default InteractiveCanvas;
