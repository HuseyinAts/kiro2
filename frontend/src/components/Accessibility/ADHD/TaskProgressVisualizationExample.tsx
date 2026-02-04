/**
 * Task Progress Visualization Example
 * 
 * TaskProgressVisualization bileşeninin kullanım örnekleri
 */

import React, { useState } from 'react';
import TaskProgressVisualization from './TaskProgressVisualization';

export const TaskProgressVisualizationExample: React.FC = () => {
  const [selectedTaskId, setSelectedTaskId] = useState<string>('task-1');

  const exampleTasks = [
    { id: 'task-1', name: 'Matematik Sınavına Hazırlan', progress: 60 },
    { id: 'task-2', name: 'Türkçe Ödevini Tamamla', progress: 25 },
    { id: 'task-3', name: 'Fizik Konularını Tekrarla', progress: 100 },
    { id: 'task-4', name: 'İngilizce Kelime Çalış', progress: 0 }
  ];

  const handleTaskChange = (taskId: string) => {
    setSelectedTaskId(taskId);
  };

  const handleViewTask = () => {
    alert(`Görev detayları: ${selectedTaskId}`);
    // Gerçek uygulamada görev detay sayfasına yönlendir
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '24px', color: '#212121' }}>
        Görev İlerleme Görselleştirme Örnekleri
      </h1>

      {/* Task Selector */}
      <div style={{ marginBottom: '32px' }}>
        <label 
          htmlFor="task-selector"
          style={{ 
            display: 'block', 
            marginBottom: '8px',
            fontSize: '16px',
            fontWeight: 500,
            color: '#424242'
          }}
        >
          Görev Seç:
        </label>
        <select
          id="task-selector"
          value={selectedTaskId}
          onChange={(e) => handleTaskChange(e.target.value)}
          style={{
            width: '100%',
            padding: '12px',
            fontSize: '16px',
            borderRadius: '8px',
            border: '2px solid #E0E0E0',
            backgroundColor: '#FFFFFF',
            cursor: 'pointer'
          }}
        >
          {exampleTasks.map((task) => (
            <option key={task.id} value={task.id}>
              {task.name} ({task.progress}% tamamlandı)
            </option>
          ))}
        </select>
      </div>

      {/* Progress Visualization */}
      <div style={{ marginBottom: '32px' }}>
        <TaskProgressVisualization 
          taskId={selectedTaskId}
          onRefresh={handleViewTask}
        />
      </div>

      {/* Usage Examples */}
      <div style={{ 
        backgroundColor: '#F5F5F5', 
        padding: '24px', 
        borderRadius: '8px',
        marginTop: '32px'
      }}>
        <h2 style={{ marginTop: 0, color: '#212121' }}>Kullanım Örnekleri</h2>
        
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ color: '#424242' }}>1. Temel Kullanım</h3>
          <pre style={{ 
            backgroundColor: '#FFFFFF', 
            padding: '16px', 
            borderRadius: '4px',
            overflow: 'auto'
          }}>
{`<TaskProgressVisualization 
  taskId="task-123"
/>`}
          </pre>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ color: '#424242' }}>2. Callback ile Kullanım</h3>
          <pre style={{ 
            backgroundColor: '#FFFFFF', 
            padding: '16px', 
            borderRadius: '4px',
            overflow: 'auto'
          }}>
{`<TaskProgressVisualization 
  taskId="task-123"
  onRefresh={() => {
    // Görev detayına git
    navigate('/tasks/task-123');
  }}
/>`}
          </pre>
        </div>

        <div>
          <h3 style={{ color: '#424242' }}>3. Özellikler</h3>
          <ul style={{ color: '#616161' }}>
            <li>✅ Animasyonlu progress bar</li>
            <li>✅ Renk kodlu durum gösterimi</li>
            <li>✅ Kilometre taşları (milestones)</li>
            <li>✅ Zaman takibi</li>
            <li>✅ Alt görev sayacı</li>
            <li>✅ WCAG 2.1 Level AA uyumlu</li>
            <li>✅ Responsive tasarım</li>
            <li>✅ Klavye navigasyonu</li>
          </ul>
        </div>
      </div>

      {/* Accessibility Features */}
      <div style={{ 
        backgroundColor: '#E3F2FD', 
        padding: '24px', 
        borderRadius: '8px',
        marginTop: '24px'
      }}>
        <h2 style={{ marginTop: 0, color: '#1976D2' }}>
          ♿ Erişilebilirlik Özellikleri
        </h2>
        <ul style={{ color: '#424242' }}>
          <li>
            <strong>ARIA Etiketleri:</strong> Progress bar için role="progressbar" ve aria-* attributes
          </li>
          <li>
            <strong>Klavye Navigasyonu:</strong> Tab ile butonlar arasında gezinme
          </li>
          <li>
            <strong>Yüksek Kontrast:</strong> prefers-contrast: high desteği
          </li>
          <li>
            <strong>Azaltılmış Hareket:</strong> prefers-reduced-motion desteği
          </li>
          <li>
            <strong>Ekran Okuyucu:</strong> Tüm öğeler için anlamlı etiketler
          </li>
        </ul>
      </div>

      {/* DEHB Support Info */}
      <div style={{ 
        backgroundColor: '#FFF3E0', 
        padding: '24px', 
        borderRadius: '8px',
        marginTop: '24px'
      }}>
        <h2 style={{ marginTop: 0, color: '#E65100' }}>
          🧠 DEHB Desteği
        </h2>
        <p style={{ color: '#424242', lineHeight: 1.6 }}>
          Bu bileşen, DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) tanılı 
          öğrenciler için özel olarak optimize edilmiştir:
        </p>
        <ul style={{ color: '#616161' }}>
          <li>
            <strong>Görsel Geri Bildirim:</strong> Renkli ve animasyonlu göstergeler
          </li>
          <li>
            <strong>Küçük Adımlar:</strong> Alt görevlere bölünmüş ilerleme
          </li>
          <li>
            <strong>Kilometre Taşları:</strong> Motivasyon artırıcı başarı noktaları
          </li>
          <li>
            <strong>Zaman Yönetimi:</strong> Tahmini ve gerçek süre takibi
          </li>
          <li>
            <strong>Anında Geri Bildirim:</strong> Her adımda görsel onay
          </li>
        </ul>
      </div>
    </div>
  );
};

export default TaskProgressVisualizationExample;
