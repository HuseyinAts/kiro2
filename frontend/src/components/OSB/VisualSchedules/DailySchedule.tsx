/**
 * Task 94.1: Daily Schedule Visualization
 * OSB desteği için günlük program görselleştirmesi
 *
 * Özellikler:
 * - Görsel timeline
 * - Her aktivite için ikon
 * - Renk kodlu zaman blokları
 * - Mevcut aktivite vurgusu
 * - Tamamlanan aktiviteler işaretli
 */

import React, { useState, useEffect } from 'react';
import './DailySchedule.css';

export interface ScheduleActivity {
  id: string;
  title: string;
  startTime: string; // "09:00"
  endTime: string;   // "10:00"
  icon: string;      // Emoji veya ikon
  color: string;     // Renk kodu (#hex)
  description?: string;
  location?: string;
  completed?: boolean;
}

export interface DailyScheduleProps {
  /** Günün aktiviteleri */
  activities: ScheduleActivity[];

  /** Bugünün tarihi */
  date?: Date;

  /** Görünüm modu */
  viewMode?: 'timeline' | 'list' | 'cards';

  /** OSB modu - ekstra görsel destek */
  osbMode?: boolean;

  /** Aktivite tıklama */
  onActivityClick?: (activity: ScheduleActivity) => void;

  /** Aktivite tamamlama */
  onActivityComplete?: (activityId: string) => void;
}

/**
 * Günlük program bileşeni
 * OSB öğrenciler için görsel ve öngörülebilir
 */
export const DailySchedule: React.FC<DailyScheduleProps> = ({
  activities,
  date = new Date(),
  viewMode = 'timeline',
  osbMode = true,
  onActivityClick,
  onActivityComplete
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [currentActivity, setCurrentActivity] = useState<string | null>(null);

  // Şu anki zamanı güncelle
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Her dakika

    return () => clearInterval(timer);
  }, []);

  // Mevcut aktiviteyi bul
  useEffect(() => {
    const now = currentTime;
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentTimeInMinutes = currentHour * 60 + currentMinute;

    const active = activities.find(activity => {
      const [startHour, startMin] = activity.startTime.split(':').map(Number);
      const [endHour, endMin] = activity.endTime.split(':').map(Number);

      const startInMinutes = startHour * 60 + startMin;
      const endInMinutes = endHour * 60 + endMin;

      return currentTimeInMinutes >= startInMinutes && currentTimeInMinutes < endInMinutes;
    });

    setCurrentActivity(active?.id || null);
  }, [currentTime, activities]);

  // Zaman string'i parse et
  const parseTime = (time: string): number => {
    const [hour, min] = time.split(':').map(Number);
    return hour * 60 + min;
  };

  // Timeline view
  const renderTimeline = () => {
    const startOfDay = 0; // 00:00
    const endOfDay = 24 * 60; // 24:00
    const totalMinutes = endOfDay - startOfDay;

    return (
      <div className="daily-schedule__timeline">
        {/* Zaman çizgisi */}
        <div className="timeline-track">
          {/* Saat işaretleri */}
          {Array.from({ length: 25 }, (_, i) => (
            <div
              key={i}
              className="timeline-hour-mark"
              style={{ left: `${(i / 24) * 100}%` }}
            >
              <span className="hour-label">{i.toString().padStart(2, '0')}:00</span>
            </div>
          ))}

          {/* Şu anki zaman göstergesi */}
          {(() => {
            const now = currentTime;
            const currentMinutes = now.getHours() * 60 + now.getMinutes();
            const position = (currentMinutes / totalMinutes) * 100;

            return (
              <div
                className="timeline-current-time"
                style={{ left: `${position}%` }}
              >
                <div className="current-time-line" />
                <div className="current-time-label">
                  Şimdi: {now.getHours().toString().padStart(2, '0')}:{now.getMinutes().toString().padStart(2, '0')}
                </div>
              </div>
            );
          })()}

          {/* Aktiviteler */}
          {activities.map((activity) => {
            const startMinutes = parseTime(activity.startTime);
            const endMinutes = parseTime(activity.endTime);
            const duration = endMinutes - startMinutes;

            const left = (startMinutes / totalMinutes) * 100;
            const width = (duration / totalMinutes) * 100;

            const isCurrent = currentActivity === activity.id;
            const isPast = endMinutes < (currentTime.getHours() * 60 + currentTime.getMinutes());

            return (
              <div
                key={activity.id}
                className={`timeline-activity ${isCurrent ? 'current' : ''} ${isPast || activity.completed ? 'completed' : ''}`}
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  backgroundColor: activity.color,
                  borderColor: activity.color
                }}
                onClick={() => onActivityClick?.(activity)}
                role="button"
                tabIndex={0}
                aria-label={`${activity.title}, ${activity.startTime} - ${activity.endTime}`}
              >
                <span className="activity-icon" aria-hidden="true">{activity.icon}</span>
                <span className="activity-title">{activity.title}</span>
                <span className="activity-time">{activity.startTime} - {activity.endTime}</span>

                {(isPast || activity.completed) && (
                  <span className="activity-check" aria-label="Tamamlandı">✓</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // List view
  const renderList = () => {
    return (
      <div className="daily-schedule__list">
        {activities.map((activity, index) => {
          const isCurrent = currentActivity === activity.id;
          const startMinutes = parseTime(activity.startTime);
          const currentMinutes = currentTime.getHours() * 60 + currentTime.getMinutes();
          const isPast = startMinutes < currentMinutes;

          return (
            <div
              key={activity.id}
              className={`list-activity ${isCurrent ? 'current' : ''} ${isPast || activity.completed ? 'completed' : ''}`}
              onClick={() => onActivityClick?.(activity)}
              role="button"
              tabIndex={0}
            >
              {/* Sıra numarası */}
              <div className="activity-number">{index + 1}</div>

              {/* İkon */}
              <div
                className="activity-icon-box"
                style={{ backgroundColor: activity.color }}
                aria-hidden="true"
              >
                <span className="activity-icon">{activity.icon}</span>
              </div>

              {/* Bilgiler */}
              <div className="activity-info">
                <h3 className="activity-title">{activity.title}</h3>
                <p className="activity-time">
                  <span className="time-icon" aria-hidden="true">🕐</span>
                  {activity.startTime} - {activity.endTime}
                </p>
                {activity.location && (
                  <p className="activity-location">
                    <span className="location-icon" aria-hidden="true">📍</span>
                    {activity.location}
                  </p>
                )}
                {activity.description && (
                  <p className="activity-description">{activity.description}</p>
                )}
              </div>

              {/* Tamamlama checkbox */}
              <div className="activity-complete">
                <button
                  className={`complete-button ${isPast || activity.completed ? 'checked' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onActivityComplete?.(activity.id);
                  }}
                  aria-label={activity.completed ? 'Tamamlandı' : 'Tamamla'}
                  type="button"
                >
                  {(isPast || activity.completed) && <span className="check-icon">✓</span>}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // Cards view
  const renderCards = () => {
    return (
      <div className="daily-schedule__cards">
        {activities.map((activity, index) => {
          const isCurrent = currentActivity === activity.id;
          const startMinutes = parseTime(activity.startTime);
          const currentMinutes = currentTime.getHours() * 60 + currentTime.getMinutes();
          const isPast = startMinutes < currentMinutes;

          return (
            <div
              key={activity.id}
              className={`card-activity ${isCurrent ? 'current' : ''} ${isPast || activity.completed ? 'completed' : ''}`}
              onClick={() => onActivityClick?.(activity)}
              role="button"
              tabIndex={0}
            >
              {/* Başlık bölümü */}
              <div
                className="card-header"
                style={{ backgroundColor: activity.color }}
              >
                <span className="card-number">{index + 1}</span>
                <span className="card-icon">{activity.icon}</span>
                <h3 className="card-title">{activity.title}</h3>
              </div>

              {/* İçerik bölümü */}
              <div className="card-body">
                <div className="card-time">
                  <span className="time-icon" aria-hidden="true">🕐</span>
                  <strong>{activity.startTime} - {activity.endTime}</strong>
                </div>

                {activity.location && (
                  <div className="card-location">
                    <span className="location-icon" aria-hidden="true">📍</span>
                    {activity.location}
                  </div>
                )}

                {activity.description && (
                  <p className="card-description">{activity.description}</p>
                )}

                {/* Durum */}
                <div className="card-status">
                  {isCurrent && (
                    <span className="status-badge status-current">
                      ⏰ Şimdi
                    </span>
                  )}
                  {(isPast || activity.completed) && !isCurrent && (
                    <span className="status-badge status-completed">
                      ✓ Tamamlandı
                    </span>
                  )}
                  {!isCurrent && !isPast && !activity.completed && (
                    <span className="status-badge status-upcoming">
                      ⏳ Bekliyor
                    </span>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="card-footer">
                <button
                  className="card-complete-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onActivityComplete?.(activity.id);
                  }}
                  disabled={isPast || activity.completed}
                  type="button"
                >
                  {(isPast || activity.completed) ? '✓ Tamamlandı' : 'Tamamla'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`daily-schedule ${osbMode ? 'osb-mode' : ''}`}>
      {/* Header */}
      <div className="daily-schedule__header">
        <h2 className="schedule-title">
          <span className="title-icon" aria-hidden="true">📅</span>
          Günlük Program
        </h2>
        <p className="schedule-date">
          {date.toLocaleDateString('tr-TR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </p>

        {/* View mode selector */}
        <div className="view-mode-selector" role="group" aria-label="Görünüm modu">
          <button
            className={`view-mode-button ${viewMode === 'timeline' ? 'active' : ''}`}
            onClick={() => {}}
            aria-label="Zaman çizgisi görünümü"
            type="button"
          >
            📊 Zaman Çizgisi
          </button>
          <button
            className={`view-mode-button ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => {}}
            aria-label="Liste görünümü"
            type="button"
          >
            📝 Liste
          </button>
          <button
            className={`view-mode-button ${viewMode === 'cards' ? 'active' : ''}`}
            onClick={() => {}}
            aria-label="Kart görünümü"
            type="button"
          >
            🃏 Kartlar
          </button>
        </div>
      </div>

      {/* İçerik */}
      <div className="daily-schedule__content">
        {viewMode === 'timeline' && renderTimeline()}
        {viewMode === 'list' && renderList()}
        {viewMode === 'cards' && renderCards()}
      </div>

      {/* Özet */}
      <div className="daily-schedule__summary">
        <div className="summary-stat">
          <span className="stat-icon" aria-hidden="true">📊</span>
          <span className="stat-label">Toplam</span>
          <span className="stat-value">{activities.length} aktivite</span>
        </div>
        <div className="summary-stat">
          <span className="stat-icon" aria-hidden="true">✓</span>
          <span className="stat-label">Tamamlanan</span>
          <span className="stat-value">
            {activities.filter(a => a.completed).length} aktivite
          </span>
        </div>
        <div className="summary-stat">
          <span className="stat-icon" aria-hidden="true">⏰</span>
          <span className="stat-label">Şu an</span>
          <span className="stat-value">
            {currentActivity
              ? activities.find(a => a.id === currentActivity)?.title
              : 'Boş zaman'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default DailySchedule;
