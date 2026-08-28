// Ödev Atama ↔ Ödevlerim — TAM DÖNGÜ E2E (ortak mock-store)
// Öğretmen atama yapar (postAtama) → ortak mock-store'daki `odevler`'e yazılır →
// öğrenci Ödevlerim (getAssignments) listesinde görünür. configureKiroApi klonlaması
// sayesinde her config taze/izole bir oturum-store verir (testler arası sızıntı yok).
import { describe, it, expect, beforeEach } from 'vitest';
import kiroData from './kiro-data.json';
import {
  configureKiroApi,
  getAssignments,
  getAtamaKonular,
  postAtama,
  type MockData,
} from './api-client';
import type { AtamaForm } from '../types';

const md = (): MockData => kiroData as unknown as MockData;

describe('Ödev Atama ↔ Ödevlerim — tam döngü (ortak mock-store)', () => {
  beforeEach(() => {
    configureKiroApi({ mode: 'mock', mockData: md() });
  });

  it('öğretmen atama yapınca öğrencinin Ödevlerim listesinde görünür', async () => {
    const oncesi = await getAssignments();
    const konular = await getAtamaKonular('sinif-1');
    expect(konular.length).toBeGreaterThan(0);
    const hedef = konular[0];

    const form: AtamaForm = {
      konuId: hedef.id,
      adet: 8,
      teslimTarihi: '2026-08-01',
      kisisel: true,
      ogrenciIds: ['o1', 'o2', 'o3'],
    };
    const res = await postAtama(form);
    expect(res.atananSayi).toBe(3);

    const sonrasi = await getAssignments();
    expect(sonrasi.length).toBe(oncesi.length + 1);

    const yeni = sonrasi[0];
    expect(yeni.konu).toBe(hedef.ad);
    expect(yeni.teslim).toBe('2026-08-01');
    expect(yeni.durum).toBe('acik'); // 'bekliyor' değil — geciken teslim yok
    expect(yeni.kisisel).toBe(true);
    expect(yeni.yapilan).toBe(0);
    expect(yeni.adet).toBe(8);
  });

  it('izolasyon: yeni configureKiroApi klonu önceki atamayı taşımaz', async () => {
    const konular = await getAtamaKonular('s');
    await postAtama({
      konuId: konular[0].id, adet: 5, teslimTarihi: '2026-08-02', kisisel: false, ogrenciIds: ['o1'],
    });
    const kirli = await getAssignments();

    // taze config → yeni klon → atama sıfırlanır
    configureKiroApi({ mode: 'mock', mockData: md() });
    const temiz = await getAssignments();
    expect(temiz.length).toBe(kirli.length - 1);
  });
});
