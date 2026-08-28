/**
 * Centralized Error Messages
 * Turkish user-friendly error messages for KIRO2 platform
 */

/**
 * HTTP Status Code Error Messages
 */
export const HTTP_ERROR_MESSAGES: Record<number, string> = {
  // 400 series - Client errors
  400: 'Geçersiz istek. Lütfen girdiğiniz bilgileri kontrol edin.',
  401: 'Oturum süreniz doldu. Lütfen tekrar giriş yapın.',
  403: 'Bu işlem için yetkiniz bulunmuyor.',
  404: 'Aradığınız sayfa veya kaynak bulunamadı.',
  405: 'Bu işlem desteklenmiyor.',
  408: 'İstek zaman aşımına uğradı. Lütfen tekrar deneyin.',
  409: 'Bu işlem bir çakışmaya neden oldu. Lütfen sayfayı yenileyin.',
  422: 'Girdiğiniz bilgiler işlenemedi. Lütfen kontrol edin.',
  429: 'Çok fazla istek gönderildi. Lütfen biraz bekleyin.',

  // 500 series - Server errors
  500: 'Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.',
  502: 'Sunucu geçici olarak kullanılamıyor.',
  503: 'Servis şu anda bakımda. Lütfen daha sonra tekrar deneyin.',
  504: 'Sunucu yanıt vermiyor. Lütfen daha sonra tekrar deneyin.',
};

/**
 * API Error Codes and Messages
 */
export const API_ERROR_MESSAGES: Record<string, string> = {
  // Authentication errors
  INVALID_CREDENTIALS: 'E-posta veya şifre hatalı.',
  EMAIL_NOT_VERIFIED: 'E-posta adresinizi doğrulamanız gerekiyor.',
  ACCOUNT_LOCKED: 'Hesabınız kilitlendi. Destek ekibi ile iletişime geçin.',
  TOKEN_EXPIRED: 'Oturum süreniz doldu. Lütfen tekrar giriş yapın.',
  INVALID_TOKEN: 'Geçersiz oturum. Lütfen tekrar giriş yapın.',
  SESSION_EXPIRED: 'Oturumunuz sona erdi. Lütfen tekrar giriş yapın.',

  // User errors
  USER_NOT_FOUND: 'Kullanıcı bulunamadı.',
  EMAIL_ALREADY_EXISTS: 'Bu e-posta adresi zaten kayıtlı.',
  USERNAME_ALREADY_EXISTS: 'Bu kullanıcı adı zaten kullanılıyor.',
  WEAK_PASSWORD: 'Şifreniz en az 8 karakter olmalı ve büyük harf, küçük harf, rakam içermelidir.',

  // Exam errors
  EXAM_NOT_FOUND: 'Sınav bulunamadı.',
  EXAM_ALREADY_STARTED: 'Bu sınavı zaten başlattınız.',
  EXAM_ALREADY_COMPLETED: 'Bu sınavı zaten tamamladınız.',
  EXAM_TIME_EXPIRED: 'Sınav süresi doldu.',
  INVALID_ANSWER: 'Geçersiz cevap formatı.',

  // Question errors
  QUESTION_NOT_FOUND: 'Soru bulunamadı.',
  NO_QUESTIONS_AVAILABLE: 'Uygun soru bulunamadı. Lütfen filtrelerinizi kontrol edin.',
  // Kalite kapısı boş havuz (27 Tem 2026). NO_QUESTIONS_AVAILABLE'dan AYRI:
  // orada sorun kullanıcının filtresi, burada içeriğin kendisi — "filtrelerinizi
  // kontrol edin" demek kullanıcıyı düzeltemeyeceği bir şeye yönlendirir.
  // Ürün kararı: kapı gevşetilmez, komşu konudan doldurulmaz, durum söylenir.
  NO_VERIFIED_QUESTIONS:
    'Bu konuda henüz doğrulanmış soru yok. İçerik ekibimiz üzerinde çalışıyor.',

  // Learning path errors
  LEARNING_PATH_NOT_FOUND: 'Öğrenme yolu bulunamadı.',
  TOPIC_NOT_COMPLETED: 'Önceki konuyu tamamlamanız gerekiyor.',

  // Upload errors
  FILE_TOO_LARGE: 'Dosya boyutu çok büyük. Maksimum 10MB yükleyebilirsiniz.',
  INVALID_FILE_TYPE: 'Geçersiz dosya tipi. Sadece PDF, JPG, PNG dosyaları yüklenebilir.',

  // Network errors
  NETWORK_ERROR: 'İnternet bağlantınızı kontrol edin.',
  TIMEOUT_ERROR: 'İstek zaman aşımına uğradı. Lütfen tekrar deneyin.',

  // Database errors
  DATABASE_ERROR: 'Veritabanı hatası. Lütfen daha sonra tekrar deneyin.',
  CONNECTION_ERROR: 'Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin.',

  // Validation errors
  REQUIRED_FIELD: 'Bu alan zorunludur.',
  INVALID_EMAIL: 'Geçersiz e-posta adresi.',
  INVALID_PHONE: 'Geçersiz telefon numarası.',
  INVALID_DATE: 'Geçersiz tarih formatı.',

  // Permission errors
  INSUFFICIENT_PERMISSIONS: 'Bu işlem için yetkiniz bulunmuyor.',
  ADMIN_ONLY: 'Sadece yöneticiler bu işlemi yapabilir.',
  TEACHER_ONLY: 'Sadece öğretmenler bu işlemi yapabilir.',

  // Rate limiting
  RATE_LIMIT_EXCEEDED: 'Çok fazla istek gönderildi. Lütfen biraz bekleyip tekrar deneyin.',
  TOO_MANY_ATTEMPTS: 'Çok fazla deneme yaptınız. Lütfen 15 dakika sonra tekrar deneyin.',
};

/**
 * Fallback error messages
 */
export const FALLBACK_ERROR_MESSAGES = {
  GENERIC: 'Bir hata oluştu. Lütfen tekrar deneyin.',
  UNKNOWN: 'Bilinmeyen bir hata oluştu. Lütfen destek ekibi ile iletişime geçin.',
  NETWORK: 'Bağlantı hatası. İnternet bağlantınızı kontrol edin.',
  SERVER: 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.',
};

/**
 * Success messages
 */
export const SUCCESS_MESSAGES = {
  LOGIN: 'Başarıyla giriş yaptınız.',
  LOGOUT: 'Başarıyla çıkış yaptınız.',
  REGISTER: 'Hesabınız oluşturuldu. E-posta adresinizi doğrulayın.',
  UPDATE_PROFILE: 'Profiliniz güncellendi.',
  CHANGE_PASSWORD: 'Şifreniz değiştirildi.',
  EXAM_STARTED: 'Sınav başlatıldı. Başarılar!',
  EXAM_SUBMITTED: 'Sınavınız gönderildi. Sonuçları görüntüleyebilirsiniz.',
  ANSWER_SAVED: 'Cevabınız kaydedildi.',
  FILE_UPLOADED: 'Dosya başarıyla yüklendi.',
  SETTINGS_SAVED: 'Ayarlarınız kaydedildi.',
};

/**
 * Warning messages
 */
export const WARNING_MESSAGES = {
  UNSAVED_CHANGES: 'Kaydedilmemiş değişiklikleriniz var. Çıkmak istediğinize emin misiniz?',
  EXAM_TIME_WARNING: 'Sınav süreniz dolmak üzere!',
  LOW_BATTERY: 'Pil seviyeniz düşük. Şarj cihazınızı bağlayın.',
  POOR_CONNECTION: 'İnternet bağlantınız zayıf. Verileriniz kaydedilmeyebilir.',
};

/**
 * Info messages
 */
export const INFO_MESSAGES = {
  LOADING: 'Yükleniyor...',
  PROCESSING: 'İşleniyor...',
  SAVING: 'Kaydediliyor...',
  UPLOADING: 'Yükleniyor...',
  SYNCING: 'Senkronize ediliyor...',
};

/**
 * Get user-friendly error message from error code or HTTP status
 */
export const getErrorMessage = (
  errorCode?: string | number,
  defaultMessage?: string,
): string => {
  // If errorCode is a number (HTTP status code)
  if (typeof errorCode === 'number') {
    return HTTP_ERROR_MESSAGES[errorCode] || defaultMessage || FALLBACK_ERROR_MESSAGES.GENERIC;
  }

  // If errorCode is a string (API error code)
  if (typeof errorCode === 'string') {
    return API_ERROR_MESSAGES[errorCode] || defaultMessage || FALLBACK_ERROR_MESSAGES.GENERIC;
  }

  // No error code provided
  return defaultMessage || FALLBACK_ERROR_MESSAGES.GENERIC;
};

/**
 * Validation error messages (for forms)
 */
export const VALIDATION_MESSAGES = {
  required: (fieldName: string) => `${fieldName} zorunludur.`,
  minLength: (fieldName: string, minLength: number) =>
    `${fieldName} en az ${minLength} karakter olmalıdır.`,
  maxLength: (fieldName: string, maxLength: number) =>
    `${fieldName} en fazla ${maxLength} karakter olabilir.`,
  email: 'Geçerli bir e-posta adresi girin.',
  phone: 'Geçerli bir telefon numarası girin (örn: 05551234567).',
  password: 'Şifreniz en az 8 karakter olmalı ve büyük harf, küçük harf, rakam içermelidir.',
  passwordMatch: 'Şifreler eşleşmiyor.',
  min: (fieldName: string, min: number) => `${fieldName} en az ${min} olmalıdır.`,
  max: (fieldName: string, max: number) => `${fieldName} en fazla ${max} olabilir.`,
  pattern: (fieldName: string) => `${fieldName} geçersiz format.`,
};
