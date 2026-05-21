/**
 * ADHD Task Management Component
 *
 * Görev yönetimi bileşeni - DEHB desteği için öncelik sıralaması ve renk kodlama
 *
 * Features:
 * - Öncelik seviyeleri (Critical, High, Medium, Low, None)
 * - Eisenhower Matrix (Urgent/Important)
 * - Otomatik önceliklendirme
 * - Renk kodlama (öncelik, durum, kategori)
 * - Alt görev yönetimi
 *
 * Requirements: REQ-52.41 - REQ-52.60
 * Tasks: 90.3, 90.4
 */

import * as React from 'react';
import {  useState, useEffect  } from 'react';
import './TaskManagement.css';

// ============================================================================
// Types
// ============================================================================

type TaskPriority = 'critical' | 'high' | 'medium' | 'low' | 'none';
type TaskStatus = 'todo' | 'in_progress' | 'completed' | 'cancelled' | 'on_hold';
type TaskCategory = 'study' | 'exam' | 'homework' | 'review' | 'practice' | 'other';
type EisenhowerQuadrant = 'q1_urgent_important' | 'q2_not_urgent_important' | 'q3_urgent_not_important' | 'q4_not_urgent_not_important';

interface Task {
  task_id: string;
  user_id: number;
  title: string;
  description?: string;
  category: TaskCategory;
  status: TaskStatus;
  priority: TaskPriority;
  eisenhower_quadrant: EisenhowerQuadrant;
  due_date?: string;
  estimated_duration_minutes?: number;
  is_urgent: boolean;
  is_important: boolean;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  parent_task_id?: string;
  subtasks_count: number;
  priority_color: string;
  status_color: string;
  category_color: string;
  quadrant_color: string;
}

interface ColorScheme {
  priority_colors: Record<TaskPriority, string>;
  status_colors: Record<TaskStatus, string>;
  category_colors: Record<TaskCategory, string>;
  quadrant_colors: Record<EisenhowerQuadrant, string>;
}

interface TaskStats {
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  completion_rate: number;
  by_priority: Record<string, { count: number; color: string }>;
  by_quadrant: Record<string, { count: number; color: string }>;
}

// ============================================================================
// Priority Labels (Turkish)
// ============================================================================

const PRIORITY_LABELS: Record<TaskPriority, string> = {
  critical: 'Kritik',
  high: 'Yüksek',
  medium: 'Orta',
  low: 'Düşük',
  none: 'Önceliksiz',
};

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'Yapılacak',
  in_progress: 'Devam Ediyor',
  completed: 'Tamamlandı',
  cancelled: 'İptal Edildi',
  on_hold: 'Beklemede',
};

const CATEGORY_LABELS: Record<TaskCategory, string> = {
  study: 'Ders Çalışma',
  exam: 'Sınav',
  homework: 'Ödev',
  review: 'Tekrar',
  practice: 'Pratik',
  other: 'Diğer',
};

const QUADRANT_LABELS: Record<EisenhowerQuadrant, string> = {
  q1_urgent_important: 'Acil ve Önemli',
  q2_not_urgent_important: 'Önemli ama Acil Değil',
  q3_urgent_not_important: 'Acil ama Önemli Değil',
  q4_not_urgent_not_important: 'Ne Acil Ne Önemli',
};

// ============================================================================
// Component
// ============================================================================

export const TaskManagement: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [colorScheme, setColorScheme] = useState<ColorScheme | null>(null);
  const [stats, setStats] = useState<TaskStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [categoryFilter, setCategoryFilter] = useState<TaskCategory | 'all'>('all');
  const [quadrantFilter, _setQuadrantFilter] = useState<EisenhowerQuadrant | 'all'>('all');

  // New task form
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    category: 'other' as TaskCategory,
    is_urgent: false,
    is_important: false,
    due_date: '',
    estimated_duration_minutes: 30,
  });

  // ============================================================================
  // API Calls
  // ============================================================================

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (priorityFilter !== 'all') {params.append('priority_filter', priorityFilter);}
      if (statusFilter !== 'all') {params.append('status_filter', statusFilter);}
      if (categoryFilter !== 'all') {params.append('category_filter', categoryFilter);}
      if (quadrantFilter !== 'all') {params.append('quadrant_filter', quadrantFilter);}

      const response = await fetch(`/api/v1/adhd-support/tasks/list?${params}`, {
        credentials: 'include',
      });

      if (!response.ok) {throw new Error('Görevler yüklenemedi');}

      const data = await response.json();
      setTasks(data.tasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const fetchColorScheme = async () => {
    try {
      const response = await fetch('/api/v1/adhd-support/tasks/colors/scheme', { credentials: 'include' });
      if (!response.ok) {throw new Error('Renk şeması yüklenemedi');}
      const data = await response.json();
      setColorScheme(data);
    } catch (err) {
      console.error('Renk şeması yüklenemedi:', err);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/adhd-support/tasks/stats/summary', {
        credentials: 'include',
      });
      if (!response.ok) {throw new Error('İstatistikler yüklenemedi');}
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('İstatistikler yüklenemedi:', err);
    }
  };

  const createTask = async () => {
    try {
      const response = await fetch('/api/v1/adhd-support/tasks/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(newTask),
      });

      if (!response.ok) {throw new Error('Görev oluşturulamadı');}

      // Reset form
      setNewTask({
        title: '',
        description: '',
        category: 'other',
        is_urgent: false,
        is_important: false,
        due_date: '',
        estimated_duration_minutes: 30,
      });
      setShowNewTaskForm(false);

      // Refresh tasks
      fetchTasks();
      fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Görev oluşturulamadı');
    }
  };

  const updateTaskStatus = async (taskId: string, newStatus: TaskStatus) => {
    try {
      const response = await fetch(`/api/v1/adhd-support/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {throw new Error('Görev güncellenemedi');}

      fetchTasks();
      fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Görev güncellenemedi');
    }
  };

  const deleteTask = async (taskId: string) => {
    if (!confirm('Bu görevi silmek istediğinizden emin misiniz?')) {return;}

    try {
      const response = await fetch(`/api/v1/adhd-support/tasks/${taskId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {throw new Error('Görev silinemedi');}

      fetchTasks();
      fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Görev silinemedi');
    }
  };

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    fetchColorScheme();
  }, []);

  useEffect(() => {
    fetchTasks();
    fetchStats();
  }, [priorityFilter, statusFilter, categoryFilter, quadrantFilter]);

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const renderPriorityBadge = (task: Task) => (
    <span
      className="priority-badge"
      style={{ backgroundColor: task.priority_color }}
      title={`Öncelik: ${PRIORITY_LABELS[task.priority]}`}
    >
      {PRIORITY_LABELS[task.priority]}
    </span>
  );

  const renderStatusBadge = (task: Task) => (
    <span
      className="status-badge"
      style={{ backgroundColor: task.status_color }}
      title={`Durum: ${STATUS_LABELS[task.status]}`}
    >
      {STATUS_LABELS[task.status]}
    </span>
  );

  const renderCategoryBadge = (task: Task) => (
    <span
      className="category-badge"
      style={{ backgroundColor: task.category_color }}
      title={`Kategori: ${CATEGORY_LABELS[task.category]}`}
    >
      {CATEGORY_LABELS[task.category]}
    </span>
  );

  const renderQuadrantIndicator = (task: Task) => (
    <div
      className="quadrant-indicator"
      style={{ borderLeftColor: task.quadrant_color }}
      title={QUADRANT_LABELS[task.eisenhower_quadrant]}
    />
  );

  const renderTaskCard = (task: Task) => (
    <div key={task.task_id} className="task-card" data-priority={task.priority}>
      {renderQuadrantIndicator(task)}

      <div className="task-header">
        <h3 className="task-title">{task.title}</h3>
        <div className="task-badges">
          {renderPriorityBadge(task)}
          {renderStatusBadge(task)}
          {renderCategoryBadge(task)}
        </div>
      </div>

      {task.description && (
        <p className="task-description">{task.description}</p>
      )}

      <div className="task-meta">
        {task.due_date && (
          <span className="task-due-date">
            📅 {new Date(task.due_date).toLocaleDateString('tr-TR')}
          </span>
        )}
        {task.estimated_duration_minutes && (
          <span className="task-duration">
            ⏱️ {task.estimated_duration_minutes} dk
          </span>
        )}
        {task.subtasks_count > 0 && (
          <span className="task-subtasks">
            📋 {task.subtasks_count} alt görev
          </span>
        )}
      </div>

      <div className="task-actions">
        {task.status !== 'completed' && (
          <button
            className="btn-complete"
            onClick={() => updateTaskStatus(task.task_id, 'completed')}
          >
            ✓ Tamamla
          </button>
        )}
        {task.status === 'todo' && (
          <button
            className="btn-start"
            onClick={() => updateTaskStatus(task.task_id, 'in_progress')}
          >
            ▶ Başla
          </button>
        )}
        <button
          className="btn-delete"
          onClick={() => deleteTask(task.task_id)}
        >
          🗑️ Sil
        </button>
      </div>
    </div>
  );

  const renderStats = () => {
    if (!stats) {return null;}

    return (
      <div className="task-stats">
        <div className="stat-card">
          <h4>Toplam Görev</h4>
          <p className="stat-value">{stats.total_tasks}</p>
        </div>
        <div className="stat-card">
          <h4>Tamamlanan</h4>
          <p className="stat-value">{stats.completed_tasks}</p>
        </div>
        <div className="stat-card">
          <h4>Devam Eden</h4>
          <p className="stat-value">{stats.in_progress_tasks}</p>
        </div>
        <div className="stat-card">
          <h4>Tamamlanma Oranı</h4>
          <p className="stat-value">{stats.completion_rate.toFixed(1)}%</p>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${stats.completion_rate}%` }}
            />
          </div>
        </div>
      </div>
    );
  };

  const renderFilters = () => (
    <div className="task-filters">
      <div className="filter-group">
        <label htmlFor="task-priority-filter">Öncelik:</label>
        <select
          id="task-priority-filter"
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as TaskPriority | 'all')}
        >
          <option value="all">Tümü</option>
          <option value="critical">Kritik</option>
          <option value="high">Yüksek</option>
          <option value="medium">Orta</option>
          <option value="low">Düşük</option>
          <option value="none">Önceliksiz</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="task-status-filter">Durum:</label>
        <select
          id="task-status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TaskStatus | 'all')}
        >
          <option value="all">Tümü</option>
          <option value="todo">Yapılacak</option>
          <option value="in_progress">Devam Ediyor</option>
          <option value="completed">Tamamlandı</option>
          <option value="on_hold">Beklemede</option>
          <option value="cancelled">İptal Edildi</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="task-category-filter">Kategori:</label>
        <select
          id="task-category-filter"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value as TaskCategory | 'all')}
        >
          <option value="all">Tümü</option>
          <option value="study">Ders Çalışma</option>
          <option value="exam">Sınav</option>
          <option value="homework">Ödev</option>
          <option value="review">Tekrar</option>
          <option value="practice">Pratik</option>
          <option value="other">Diğer</option>
        </select>
      </div>
    </div>
  );

  const renderNewTaskForm = () => {
    if (!showNewTaskForm) {return null;}

    return (
      <div className="new-task-form">
        <h3>Yeni Görev Oluştur</h3>

        <div className="form-group">
          <label htmlFor="new-task-title">Başlık *</label>
          <input
            id="new-task-title"
            type="text"
            value={newTask.title}
            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            placeholder="Görev başlığı"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="new-task-description">Açıklama</label>
          <textarea
            id="new-task-description"
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            placeholder="Görev açıklaması (opsiyonel)"
            rows={3}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="new-task-category">Kategori</label>
            <select
              id="new-task-category"
              value={newTask.category}
              onChange={(e) => setNewTask({ ...newTask, category: e.target.value as TaskCategory })}
            >
              <option value="study">Ders Çalışma</option>
              <option value="exam">Sınav</option>
              <option value="homework">Ödev</option>
              <option value="review">Tekrar</option>
              <option value="practice">Pratik</option>
              <option value="other">Diğer</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="new-task-duration">Tahmini Süre (dk)</label>
            <input
              id="new-task-duration"
              type="number"
              value={newTask.estimated_duration_minutes}
              onChange={(e) => setNewTask({ ...newTask, estimated_duration_minutes: parseInt(e.target.value) })}
              min="1"
              max="480"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="new-task-due-date">Bitiş Tarihi</label>
          <input
            id="new-task-due-date"
            type="datetime-local"
            value={newTask.due_date}
            onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
          />
        </div>

        <div className="form-checkboxes">
          <label>
            <input
              type="checkbox"
              checked={newTask.is_urgent}
              onChange={(e) => setNewTask({ ...newTask, is_urgent: e.target.checked })}
            />
            Acil
          </label>

          <label>
            <input
              type="checkbox"
              checked={newTask.is_important}
              onChange={(e) => setNewTask({ ...newTask, is_important: e.target.checked })}
            />
            Önemli
          </label>
        </div>

        <div className="form-actions">
          <button className="btn-primary" onClick={createTask} disabled={!newTask.title}>
            Oluştur
          </button>
          <button className="btn-secondary" onClick={() => setShowNewTaskForm(false)}>
            İptal
          </button>
        </div>
      </div>
    );
  };

  // ============================================================================
  // Main Render
  // ============================================================================

  if (loading && tasks.length === 0) {
    return <div className="task-management loading">Yükleniyor...</div>;
  }

  if (error) {
    return (
      <div className="task-management error">
        <p>❌ {error}</p>
        <button onClick={fetchTasks}>Tekrar Dene</button>
      </div>
    );
  }

  return (
    <div className="task-management">
      <div className="task-management-header">
        <h2>📋 Görev Yönetimi</h2>
        <p className="subtitle">DEHB Desteği - Öncelik Sıralaması ve Renk Kodlama</p>
        <button
          className="btn-new-task"
          onClick={() => setShowNewTaskForm(!showNewTaskForm)}
        >
          {showNewTaskForm ? '✕ İptal' : '+ Yeni Görev'}
        </button>
      </div>

      {renderStats()}
      {renderNewTaskForm()}
      {renderFilters()}

      <div className="task-list">
        {tasks.length === 0 ? (
          <div className="empty-state">
            <p>Henüz görev yok. Yeni bir görev oluşturun!</p>
          </div>
        ) : (
          tasks.map(renderTaskCard)
        )}
      </div>

      {colorScheme && (
        <div className="color-legend">
          <h4>Renk Açıklaması</h4>
          <div className="legend-section">
            <h5>Öncelik:</h5>
            {Object.entries(colorScheme.priority_colors).map(([priority, color]) => (
              <span key={priority} className="legend-item">
                <span className="legend-color" style={{ backgroundColor: color }} />
                {PRIORITY_LABELS[priority as TaskPriority]}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskManagement;
