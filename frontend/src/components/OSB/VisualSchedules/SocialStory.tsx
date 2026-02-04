/**
 * Task 94.4: Social Story Component
 * Sosyal hikayeler - beklenen davranışlar, görsel anlatım
 */
import React, { useState } from 'react';
import './SocialStory.css';

export interface StoryPage {
  id: string;
  text: string;
  image?: string;
  emotion?: 'happy' | 'sad' | 'worried' | 'calm' | 'excited';
}

export interface SocialStoryProps {
  title: string;
  pages: StoryPage[];
  osbMode?: boolean;
  onComplete?: () => void;
}

export const SocialStory: React.FC<SocialStoryProps> = ({
  title,
  pages,
  osbMode = true,
  onComplete
}) => {
  const [currentPage, setCurrentPage] = useState(0);

  const emotionEmojis = {
    happy: '😊',
    sad: '😢',
    worried: '😟',
    calm: '😌',
    excited: '😃'
  };

  const page = pages[currentPage];

  return (
    <div className={`social-story ${osbMode ? 'osb-mode' : ''}`}>
      <div className="story-header">
        <h2 className="story-title">📖 {title}</h2>
        <div className="page-indicator">
          Sayfa {currentPage + 1} / {pages.length}
        </div>
      </div>

      <div className="story-page">
        {page.image && (
          <div className="page-image">
            <img src={page.image} alt={`Sayfa ${currentPage + 1}`} />
          </div>
        )}

        <div className="page-content">
          {page.emotion && (
            <div className="page-emotion">
              <span className="emotion-icon">{emotionEmojis[page.emotion]}</span>
            </div>
          )}
          <p className="page-text">{page.text}</p>
        </div>
      </div>

      <div className="story-navigation">
        <button
          onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
          disabled={currentPage === 0}
          className="nav-btn"
        >
          ← Önceki
        </button>

        <div className="page-dots">
          {pages.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentPage(index)}
              className={`dot ${index === currentPage ? 'active' : ''} ${index < currentPage ? 'completed' : ''}`}
              aria-label={`Sayfa ${index + 1}`}
            />
          ))}
        </div>

        {currentPage < pages.length - 1 ? (
          <button
            onClick={() => setCurrentPage(currentPage + 1)}
            className="nav-btn primary"
          >
            Sonraki →
          </button>
        ) : (
          <button onClick={onComplete} className="nav-btn primary">
            ✓ Bitir
          </button>
        )}
      </div>
    </div>
  );
};

export default SocialStory;
