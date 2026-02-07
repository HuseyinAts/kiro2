/**
 * Çevrimdışı Veri Depolama Servisi
 * Offline soru çözme ve yerel veri senkronizasyonu için
 */

export interface OfflineQuestion {
  id: string;
  text: string;
  options: string[];
  correct: number;
  subject: string;
  difficulty: 'easy' | 'medium' | 'hard';
  explanation?: string;
  downloadedAt: string;
}

export interface OfflineExamSession {
  id: string;
  questions: OfflineQuestion[];
  answers: Record<string, number>;
  startTime: string;
  endTime?: string;
  score?: number;
  completed: boolean;
  synced: boolean;
}

export interface OfflineStudyNote {
  id: string;
  title: string;
  content: string;
  subject: string;
  createdAt: string;
  updatedAt: string;
  synced: boolean;
}

export interface OfflineProgress {
  userId: string;
  subject: string;
  totalQuestions: number;
  correctAnswers: number;
  studyTime: number; // dakika cinsinden
  lastActivity: string;
  synced: boolean;
}

export interface OfflineUserData {
  questions: OfflineQuestion[];
  examSessions: OfflineExamSession[];
  studyNotes: OfflineStudyNote[];
  progress: OfflineProgress[];
  settings: {
    autoSync: boolean;
    offlineMode: boolean;
    downloadLimit: number;
  };
}

class OfflineStorageService {
  private readonly STORAGE_KEY = 'kiro2-offline-data';
  private readonly CACHE_NAME = 'kiro2-offline-cache';

  /**
   * Çevrimdışı verileri yükle
   */
  async loadOfflineData(): Promise<OfflineUserData> {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        return JSON.parse(data);
      }
    } catch (error) {
      console.error('Çevrimdışı veri yükleme hatası:', error);
    }

    // Varsayılan veri yapısı
    return {
      questions: [],
      examSessions: [],
      studyNotes: [],
      progress: [],
      settings: {
        autoSync: true,
        offlineMode: false,
        downloadLimit: 1000,
      },
    };
  }

  /**
   * Çevrimdışı verileri kaydet
   */
  async saveOfflineData(data: OfflineUserData): Promise<void> {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('Çevrimdışı veri kaydetme hatası:', error);
      throw new Error('Veri kaydetme başarısız. Depolama alanı dolu olabilir.');
    }
  }

  /**
   * Soruları çevrimdışı kullanım için indir
   */
  async downloadQuestionsForOffline(
    subject: string,
    count: number = 50,
  ): Promise<OfflineQuestion[]> {
    try {
      // API'den soruları çek
      const response = await fetch('/api/v1/questions/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject,
          count,
          difficulty: ['easy', 'medium', 'hard'],
        }),
      });

      if (!response.ok) {
        throw new Error('Soru indirme başarısız');
      }

      const questions: OfflineQuestion[] = await response.json();

      // Mevcut verileri yükle
      const offlineData = await this.loadOfflineData();

      // Yeni soruları ekle (duplikasyon kontrolü)
      const existingIds = new Set(offlineData.questions.map(q => q.id));
      const newQuestions = questions.filter(q => !existingIds.has(q.id));

      offlineData.questions.push(...newQuestions);

      // Limit kontrolü
      if (offlineData.questions.length > offlineData.settings.downloadLimit) {
        // Eski soruları sil (FIFO)
        offlineData.questions = offlineData.questions
          .sort((a, b) => new Date(b.downloadedAt).getTime() - new Date(a.downloadedAt).getTime())
          .slice(0, offlineData.settings.downloadLimit);
      }

      await this.saveOfflineData(offlineData);

      return newQuestions;
    } catch (error) {
      console.error('Soru indirme hatası:', error);
      throw error;
    }
  }

  /**
   * Çevrimdışı sınav oturumu başlat
   */
  async startOfflineExam(
    subject: string,
    questionCount: number = 20,
  ): Promise<OfflineExamSession> {
    const offlineData = await this.loadOfflineData();

    // Konuya göre soruları filtrele
    const availableQuestions = offlineData.questions.filter(q =>
      q.subject === subject || subject === 'all',
    );

    if (availableQuestions.length < questionCount) {
      throw new Error(`Yeterli çevrimdışı soru yok. Mevcut: ${availableQuestions.length}, Gerekli: ${questionCount}`);
    }

    // Rastgele soru seç
    const shuffled = [...availableQuestions].sort(() => Math.random() - 0.5);
    const selectedQuestions = shuffled.slice(0, questionCount);

    // Sınav oturumu oluştur
    const examSession: OfflineExamSession = {
      id: `offline-exam-${Date.now()}`,
      questions: selectedQuestions,
      answers: {},
      startTime: new Date().toISOString(),
      completed: false,
      synced: false,
    };

    // Oturumu kaydet
    offlineData.examSessions.push(examSession);
    await this.saveOfflineData(offlineData);

    return examSession;
  }

  /**
   * Sınav cevabını kaydet
   */
  async saveExamAnswer(
    examId: string,
    questionId: string,
    answer: number,
  ): Promise<void> {
    const offlineData = await this.loadOfflineData();
    const exam = offlineData.examSessions.find(e => e.id === examId);

    if (!exam) {
      throw new Error('Sınav oturumu bulunamadı');
    }

    exam.answers[questionId] = answer;
    await this.saveOfflineData(offlineData);
  }

  /**
   * Sınavı tamamla
   */
  async completeOfflineExam(examId: string): Promise<OfflineExamSession> {
    const offlineData = await this.loadOfflineData();
    const exam = offlineData.examSessions.find(e => e.id === examId);

    if (!exam) {
      throw new Error('Sınav oturumu bulunamadı');
    }

    // Skoru hesapla
    let correctCount = 0;
    exam.questions.forEach(question => {
      if (exam.answers[question.id] === question.correct) {
        correctCount++;
      }
    });

    exam.score = Math.round((correctCount / exam.questions.length) * 100);
    exam.completed = true;
    exam.endTime = new Date().toISOString();

    // İlerleme verilerini güncelle
    await this.updateProgress(exam);

    await this.saveOfflineData(offlineData);

    return exam;
  }

  /**
   * İlerleme verilerini güncelle
   */
  private async updateProgress(exam: OfflineExamSession): Promise<void> {
    const offlineData = await this.loadOfflineData();

    // Her konu için ayrı ilerleme
    const subjectProgress = new Map<string, OfflineProgress>();

    exam.questions.forEach(question => {
      const subject = question.subject;
      const isCorrect = exam.answers[question.id] === question.correct;

      if (!subjectProgress.has(subject)) {
        const existing = offlineData.progress.find(p => p.subject === subject);
        subjectProgress.set(subject, existing || {
          userId: 'offline-user',
          subject,
          totalQuestions: 0,
          correctAnswers: 0,
          studyTime: 0,
          lastActivity: new Date().toISOString(),
          synced: false,
        });
      }

      const progress = subjectProgress.get(subject)!;
      progress.totalQuestions++;
      if (isCorrect) {
        progress.correctAnswers++;
      }
      progress.lastActivity = new Date().toISOString();
      progress.synced = false;
    });

    // Çalışma süresini hesapla
    if (exam.startTime && exam.endTime) {
      const studyDuration = Math.round(
        (new Date(exam.endTime).getTime() - new Date(exam.startTime).getTime()) / (1000 * 60),
      );

      subjectProgress.forEach(progress => {
        progress.studyTime += Math.round(studyDuration / subjectProgress.size);
      });
    }

    // İlerleme verilerini güncelle
    subjectProgress.forEach((progress, subject) => {
      const existingIndex = offlineData.progress.findIndex(p => p.subject === subject);
      if (existingIndex >= 0) {
        offlineData.progress[existingIndex] = progress;
      } else {
        offlineData.progress.push(progress);
      }
    });
  }

  /**
   * Çalışma notu kaydet
   */
  async saveStudyNote(note: Omit<OfflineStudyNote, 'id' | 'createdAt' | 'updatedAt' | 'synced'>): Promise<OfflineStudyNote> {
    const offlineData = await this.loadOfflineData();

    const studyNote: OfflineStudyNote = {
      ...note,
      id: `note-${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      synced: false,
    };

    offlineData.studyNotes.push(studyNote);
    await this.saveOfflineData(offlineData);

    return studyNote;
  }

  /**
   * Çalışma notunu güncelle
   */
  async updateStudyNote(noteId: string, updates: Partial<OfflineStudyNote>): Promise<void> {
    const offlineData = await this.loadOfflineData();
    const noteIndex = offlineData.studyNotes.findIndex(n => n.id === noteId);

    if (noteIndex === -1) {
      throw new Error('Not bulunamadı');
    }

    offlineData.studyNotes[noteIndex] = {
      ...offlineData.studyNotes[noteIndex],
      ...updates,
      updatedAt: new Date().toISOString(),
      synced: false,
    };

    await this.saveOfflineData(offlineData);
  }

  /**
   * Senkronize edilmemiş verileri al
   */
  async getUnsyncedData(): Promise<{
    examSessions: OfflineExamSession[];
    studyNotes: OfflineStudyNote[];
    progress: OfflineProgress[];
  }> {
    const offlineData = await this.loadOfflineData();

    return {
      examSessions: offlineData.examSessions.filter(e => !e.synced),
      studyNotes: offlineData.studyNotes.filter(n => !n.synced),
      progress: offlineData.progress.filter(p => !p.synced),
    };
  }

  /**
   * Verileri senkronize edildi olarak işaretle
   */
  async markAsSynced(type: 'examSessions' | 'studyNotes' | 'progress', ids: string[]): Promise<void> {
    const offlineData = await this.loadOfflineData();

    switch (type) {
      case 'examSessions':
        offlineData.examSessions.forEach(session => {
          if (ids.includes(session.id)) {
            session.synced = true;
          }
        });
        break;
      case 'studyNotes':
        offlineData.studyNotes.forEach(note => {
          if (ids.includes(note.id)) {
            note.synced = true;
          }
        });
        break;
      case 'progress':
        offlineData.progress.forEach(progress => {
          if (ids.includes(`${progress.userId}-${progress.subject}`)) {
            progress.synced = true;
          }
        });
        break;
    }

    await this.saveOfflineData(offlineData);
  }

  /**
   * Çevrimdışı veri istatistikleri
   */
  async getOfflineStats(): Promise<{
    totalQuestions: number;
    totalExams: number;
    totalNotes: number;
    unsyncedItems: number;
    storageUsed: number; // KB cinsinden
  }> {
    const offlineData = await this.loadOfflineData();
    const dataString = JSON.stringify(offlineData);

    return {
      totalQuestions: offlineData.questions.length,
      totalExams: offlineData.examSessions.length,
      totalNotes: offlineData.studyNotes.length,
      unsyncedItems:
        offlineData.examSessions.filter(e => !e.synced).length +
        offlineData.studyNotes.filter(n => !n.synced).length +
        offlineData.progress.filter(p => !p.synced).length,
      storageUsed: Math.round(new Blob([dataString]).size / 1024),
    };
  }

  /**
   * Çevrimdışı verileri temizle
   */
  async clearOfflineData(keepSettings: boolean = true): Promise<void> {
    const offlineData = await this.loadOfflineData();

    const clearedData: OfflineUserData = {
      questions: [],
      examSessions: [],
      studyNotes: [],
      progress: [],
      settings: keepSettings ? offlineData.settings : {
        autoSync: true,
        offlineMode: false,
        downloadLimit: 1000,
      },
    };

    await this.saveOfflineData(clearedData);
  }

  /**
   * Cache'den icerik al
   */
  async getCachedContent(url: string): Promise<Response | null> {
    try {
      const cache = await caches.open(this.CACHE_NAME);
      const response = await cache.match(url);
      return response ?? null;
    } catch (error) {
      console.error('Cache erisim hatasi:', error);
      return null;
    }
  }

  /**
   * İçeriği cache'e ekle
   */
  async addToCache(url: string, response: Response): Promise<void> {
    try {
      const cache = await caches.open(this.CACHE_NAME);
      await cache.put(url, response.clone());
    } catch (error) {
      console.error('Cache ekleme hatası:', error);
    }
  }
}

// Singleton instance
export const offlineStorageService = new OfflineStorageService();

// Note: Types are already exported via 'export interface' above