import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ExamSession } from '../../features/exams/ExamSession';
import { ExamResultDashboard } from '../../features/exams/ExamResultDashboard';

// NOT: ExamSession bileşeni '../../services/mockExamService'i kullanıyor
// (examService DEĞİL -- ikisi ayrı router/response şekline sahip, bkz.
// mockExamService.ts başlık yorumu). Bu mock önceden yanlış modülü hedefliyordu,
// bu yüzden component gerçek mockExamService'i çağırıyor ve test 2 "Seçenek A"yı
// hiç bulamıyordu (component'in kendi 120 soruluk fallback'i "Örnek Seçenek A" döndürüyor).
// SS10.72: bilesen artik ADLANDIRILMIS ithal kullaniyor
// (`import { mockExamService } from ...`), bu yuzden mock HEM default HEM
// adlandirilmis disa aktarimi vermek ZORUNDA. Yalnizca `default` verilirse
// bilesen `undefined` bir servis gorur ve testler cakilir (olculdu).
//
// `vi.hoisted` sart: `vi.mock` dosyanin en ustune tasiniyor, dolayisiyla
// siradan bir `const`a erisemez ("Cannot access 'sahteServis' before
// initialization" -- bu da olculdu).
const sahteServis = vi.hoisted(() => ({
    generateMockExam: vi.fn().mockResolvedValue({ exam_session_id: 'test-session-123', total_questions: 120 }),
    getExamSession: vi.fn().mockResolvedValue({
      id: 'test-session-123',
      exam_name: 'TYT Deneme Sınavı',
      exam_type: 'TYT',
      total_questions: 120,
      duration_minutes: 165,
      status: 'in_progress',
      questions: [
        {
          id: 'q-1',
          order: 1,
          text: 'Bu ilk Türkçe sorusudur. Hangisi doğrudur?',
          options: [
            { letter: 'A', text: 'Seçenek A' },
            { letter: 'B', text: 'Seçenek B' },
            { letter: 'C', text: 'Seçenek C' },
            { letter: 'D', text: 'Seçenek D' },
            { letter: 'E', text: 'Seçenek E' },
          ],
          branch: 'TUR',
          selected_answer: null,
        },
      ],
    }),
    saveExamAnswer: vi.fn().mockResolvedValue({ status: 'success' }),
    submitExam: vi.fn().mockResolvedValue({
      status: 'success',
      session_id: 'test-session-123',
      total_correct: 1,
      total_wrong: 0,
      total_empty: 119,
      raw_score: 1.0,
      branch_breakdown: {
        TUR: { correct: 1, wrong: 0, empty: 39, net: 1.0 },
        SOS: { correct: 0, wrong: 0, empty: 20, net: 0.0 },
        MAT: { correct: 0, wrong: 0, empty: 40, net: 0.0 },
        FEN: { correct: 0, wrong: 0, empty: 20, net: 0.0 },
      },
    }),
}));

vi.mock('../../services/mockExamService', () => ({
  default: sahteServis,
  mockExamService: sahteServis,
}));

describe('ExamSession Component', () => {
  it('renders exam session sidebar and main question controls', async () => {
    render(<ExamSession studentId="test-student" />);

    // SS10.72: sorular artik SUNUCUDAN gelir; bilesenin uydurma 120 soruluk
    // baslangic durumu yok. Bu yuzden once yuklemenin bitmesi beklenir.
    expect(await screen.findByText(/KIRO2 MOCK/i)).toBeInTheDocument();
    expect(screen.getAllByText(/TÜRKÇE/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Sınavı Bitir/i)).toBeInTheDocument();
  });

  it('selects option when clicked', async () => {
    render(<ExamSession studentId="test-student" />);

    const optionA = await screen.findByText('Seçenek A');
    expect(optionA).toBeInTheDocument();

    fireEvent.click(optionA);
    const finishBtn = screen.getByText(/Sınavı Bitir/i);
    expect(finishBtn).toBeInTheDocument();
  });

  it('finishes exam and renders ExamResultDashboard', async () => {
    render(<ExamSession studentId="test-student" />);

    const finishBtn = await screen.findByText(/Sınavı Bitir/i);
    fireEvent.click(finishBtn);

    const resultHeader = await screen.findByText(/Sınav Sonucu/i);
    expect(resultHeader).toBeInTheDocument();
  });

  // --- SS10.72 CIVILERI: sahte sinav uretilmemeli -------------------------
  //
  // Bilesende 120 uydurma soruluk bir "fallback" havuzu vardi ve arka uc
  // duserse ogrenci hicbir uyari gormeden SAHTE bir deneme sinavi coziyordu.
  // Asagidaki iki test o davranisin geri gelmesini engelliyor.

  it('arka uc duserse SAHTE sinav gostermez, hata gosterir', async () => {
    vi.mocked(sahteServis.generateMockExam).mockRejectedValueOnce(new Error('ag hatasi'));

    render(<ExamSession studentId="test-student" />);

    expect(await screen.findByRole('alert')).toHaveTextContent(/yuklenemedi/i);
    // Uydurma havuzun imzasi: "Örnek Seçenek A" / "Bu örnek bir ... sorusudur"
    expect(screen.queryByText(/Örnek Seçenek/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Sınavı Bitir/i)).not.toBeInTheDocument();
  });

  it('gonderim duserse sessizce "bitti" demez, hatayi gosterir', async () => {
    vi.mocked(sahteServis.submitExam).mockRejectedValueOnce(new Error('gonderim hatasi'));

    render(<ExamSession studentId="test-student" />);

    fireEvent.click(await screen.findByText(/Sınavı Bitir/i));

    expect(await screen.findByRole('alert')).toHaveTextContent(/gonderilemedi/i);
    // Sonuc ekranina GECMEMELI -- eskiden bos `results` ile geciyordu.
    expect(screen.queryByText(/Sınav Sonucu/i)).not.toBeInTheDocument();
  });
});

describe('ExamResultDashboard Component', () => {
  it('renders score breakdown correctly', () => {
    render(
      <ExamResultDashboard
        results={{
          status: 'success',
          session_id: 'test-session-123',
          total_correct: 95,
          total_wrong: 15,
          total_empty: 10,
          raw_score: 87.5,
          branch_breakdown: {
            TUR: { correct: 30, wrong: 5, empty: 5, net: 28.75 },
            SOS: { correct: 15, wrong: 3, empty: 2, net: 14.25 },
            MAT: { correct: 32, wrong: 4, empty: 4, net: 31.0 },
            FEN: { correct: 18, wrong: 3, empty: 0, net: 17.25 },
          },
        }}
      />
    );

    expect(screen.getByText('Sınav Sonucu')).toBeInTheDocument();
    expect(screen.getByText('87.50')).toBeInTheDocument();
    expect(screen.getByText('95')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
  });
});
