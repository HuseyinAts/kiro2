/**
 * Expert Dashboard - HITL (Human-in-the-Loop) Workflow
 * Gamified expert review system for question quality control
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ReviewTask {
  task_id: string;
  question_id: string;
  priority: string;
  konu: string;
  incentive_points: number;
  ai_validation_result: {
    confidence: number;
    weaknesses: string[];
  };
}

interface ExpertStats {
  total_reviews: number;
  approval_rate: string;
  quality_score: number;
  points: number;
  leaderboard_rank: number;
  badges: string[];
}

export const ExpertDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<ExpertStats | null>(null);
  const [assignedTasks, setAssignedTasks] = useState<ReviewTask[]>([]);
  const [currentTask, setCurrentTask] = useState<ReviewTask | null>(null);
  const [decision, setDecision] = useState<string>('');
  const [score, setScore] = useState<number>(75);
  const [comments, setComments] = useState<string>('');

  const expertId = localStorage.getItem('expertId') || 'demo-expert';

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await axios.get(`/api/v2/hitl/dashboard/${expertId}`);
      setStats(response.data.statistics);
      setAssignedTasks(response.data.assigned_tasks_preview || []);
    } catch (error) {
      console.error('Dashboard load failed:', error);
    }
  };

  const submitReview = async () => {
    if (!currentTask || !decision) return;

    try {
      await axios.post(`/api/v2/hitl/tasks/${currentTask.task_id}/review`, {
        task_id: currentTask.task_id,
        expert_id: expertId,
        decision,
        pedagogy_score: score,
        comments,
        review_time_seconds: 180
      });

      alert('İnceleme gönderildi!');
      setCurrentTask(null);
      setDecision('');
      setComments('');
      loadDashboard();
    } catch (error) {
      console.error('Review submission failed:', error);
    }
  };

  return (
    <div className="expert-dashboard">
      <h1>Uzman İnceleme Paneli</h1>

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_reviews}</div>
            <div className="stat-label">Toplam İnceleme</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.approval_rate}</div>
            <div className="stat-label">Onay Oranı</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.points}</div>
            <div className="stat-label">Puan</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">#{stats.leaderboard_rank}</div>
            <div className="stat-label">Sıralama</div>
          </div>
        </div>
      )}

      {/* Task Queue */}
      <div className="task-queue">
        <h2>Bekleyen Görevler ({assignedTasks.length})</h2>
        {assignedTasks.map(task => (
          <div key={task.task_id} className="task-item" onClick={() => setCurrentTask(task)}>
            <span className={`priority-badge ${task.priority}`}>{task.priority}</span>
            <span>{task.konu}</span>
            <span>+{task.incentive_points} puan</span>
          </div>
        ))}
      </div>

      {/* Review Panel */}
      {currentTask && (
        <div className="review-panel">
          <h2>Soru İncelemesi</h2>
          <div className="ai-analysis">
            <p>AI Güven: {(currentTask.ai_validation_result.confidence * 100).toFixed(0)}%</p>
            <p>Zayıf Noktalar: {currentTask.ai_validation_result.weaknesses.join(', ')}</p>
          </div>

          <div className="decision-buttons">
            <button onClick={() => setDecision('approve')}>Onayla</button>
            <button onClick={() => setDecision('needs_revision')}>Revizyon</button>
            <button onClick={() => setDecision('reject')}>Reddet</button>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            value={score}
            onChange={(e) => setScore(Number(e.target.value))}
          />
          <p>Pedagojik Skor: {score}/100</p>

          <textarea
            placeholder="Yorumlar..."
            value={comments}
            onChange={(e) => setComments(e.target.value)}
          />

          <button onClick={submitReview}>Gönder</button>
        </div>
      )}
    </div>
  );
};

export default ExpertDashboardPage;
