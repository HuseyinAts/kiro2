/**
 * Task 94.2: Weekly Calendar Component
 * Haftalık takvim görünümü - renk kodlu, tekrarlayan aktiviteler
 */
import React from 'react';
import './WeeklyCalendar.css';

export interface WeeklyEvent {
  id: string;
  title: string;
  dayOfWeek: number; // 0=Pazar, 1=Pazartesi, ...
  startTime: string;
  endTime: string;
  color: string;
  icon?: string;
  recurring?: boolean;
}

export interface WeeklyCalendarProps {
  events: WeeklyEvent[];
  currentDay?: number;
  osbMode?: boolean;
  onEventClick?: (event: WeeklyEvent) => void;
}

export const WeeklyCalendar: React.FC<WeeklyCalendarProps> = ({
  events,
  currentDay = new Date().getDay(),
  osbMode = true,
  onEventClick
}) => {
  const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];

  return (
    <div className={`weekly-calendar ${osbMode ? 'osb-mode' : ''}`}>
      <h2 className="calendar-title">📅 Haftalık Program</h2>
      <div className="calendar-grid">
        {days.map((day, index) => (
          <div
            key={index}
            className={`calendar-day ${index === currentDay ? 'current' : ''}`}
          >
            <div className="day-header">{day}</div>
            <div className="day-events">
              {events
                .filter(e => e.dayOfWeek === index)
                .sort((a, b) => a.startTime.localeCompare(b.startTime))
                .map(event => (
                  <div
                    key={event.id}
                    className="calendar-event"
                    style={{ backgroundColor: event.color }}
                    onClick={() => onEventClick?.(event)}
                    role="button"
                    tabIndex={0}
                  >
                    {event.icon && <span className="event-icon">{event.icon}</span>}
                    <span className="event-title">{event.title}</span>
                    <span className="event-time">{event.startTime} - {event.endTime}</span>
                    {event.recurring && <span className="recurring-icon" title="Tekrarlayan">🔄</span>}
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WeeklyCalendar;
