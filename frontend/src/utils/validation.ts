/**
 * Form Validation Utilities
 * Turkish-specific validations for KIRO2 platform
 *
 * Includes:
 * - Email validation
 * - Phone number validation (Turkish format)
 * - TC Kimlik No validation (Turkish ID)
 * - Password strength validation
 * - YKS-specific validations
 */

import { z } from 'zod';

// ============================================================================
// Turkish TC Kimlik No Validation
// ============================================================================

/**
 * Validates Turkish TC Kimlik No (11 digits with checksum)
 * Algorithm: https://tr.wikipedia.org/wiki/T%C3%BCrkiye_Cumhuriyeti_Kimlik_Numaras%C4%B1
 */
export function validateTCKN(tcno: string): boolean {
  if (!tcno || !/^\d{11}$/.test(tcno)) {return false;}
  if (tcno[0] === '0') {return false;} // Cannot start with 0

  const digits = tcno.split('').map(Number);

  // 10th digit check: ((d1+d3+d5+d7+d9)*7 - (d2+d4+d6+d8)) mod 10 = d10
  const oddSum = digits[0] + digits[2] + digits[4] + digits[6] + digits[8];
  const evenSum = digits[1] + digits[3] + digits[5] + digits[7];
  const check10 = (oddSum * 7 - evenSum) % 10;
  if (check10 < 0 ? check10 + 10 : check10 !== digits[9]) {return false;}

  // 11th digit check: (d1+d2+d3+d4+d5+d6+d7+d8+d9+d10) mod 10 = d11
  const total = digits.slice(0, 10).reduce((a, b) => a + b, 0);
  if (total % 10 !== digits[10]) {return false;}

  return true;
}

// ============================================================================
// Turkish Phone Number Validation
// ============================================================================

/**
 * Validates Turkish phone number
 * Formats: 05XXXXXXXXX, 5XXXXXXXXX, +905XXXXXXXXX
 */
export function validateTurkishPhone(phone: string): boolean {
  // Remove spaces and dashes
  const cleaned = phone.replace(/[\s-]/g, '');

  // Check various formats
  const patterns = [
    /^05\d{9}$/,        // 05XXXXXXXXX (11 digits)
    /^5\d{9}$/,         // 5XXXXXXXXX (10 digits)
    /^\+905\d{9}$/,     // +905XXXXXXXXX (13 chars)
    /^905\d{9}$/,        // 905XXXXXXXXX (12 digits)
  ];

  return patterns.some(p => p.test(cleaned));
}

/**
 * Formats phone number to standard format
 */
export function formatTurkishPhone(phone: string): string {
  const cleaned = phone.replace(/[\s-+]/g, '');

  if (cleaned.startsWith('90') && cleaned.length === 12) {
    return `0${cleaned.slice(2)}`;
  }
  if (cleaned.startsWith('5') && cleaned.length === 10) {
    return `0${cleaned}`;
  }
  return cleaned;
}

// ============================================================================
// Password Validation
// ============================================================================

export interface PasswordStrength {
  score: number // 0-4
  label: 'Zayif' | 'Orta' | 'Iyi' | 'Guclu' | 'Cok Guclu'
  suggestions: string[]
}

/**
 * Calculates password strength
 */
export function checkPasswordStrength(password: string): PasswordStrength {
  const suggestions: string[] = [];
  let score = 0;

  if (password.length >= 8) {score++;}
  else {suggestions.push('En az 8 karakter olmali');}

  if (password.length >= 12) {score++;}

  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {score++;}
  else {suggestions.push('Kucuk ve buyuk harf kullanin');}

  if (/\d/.test(password)) {score++;}
  else {suggestions.push('En az bir rakam ekleyin');}

  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {score++;}
  else {suggestions.push('Ozel karakter ekleyin (!@#$%^&*)');}

  // Common patterns to avoid
  if (/(.)\1{2,}/.test(password)) {
    score = Math.max(0, score - 1);
    suggestions.push('Tekrarlayan karakterlerden kacinin');
  }

  const labels: PasswordStrength['label'][] = ['Zayif', 'Orta', 'Iyi', 'Guclu', 'Cok Guclu'];

  return {
    score: Math.min(score, 4),
    label: labels[Math.min(score, 4)],
    suggestions,
  };
}

// ============================================================================
// Zod Schemas for Common Forms
// ============================================================================

export const emailSchema = z
  .string()
  .min(1, 'Email gerekli')
  .email('Gecerli bir email adresi girin');

export const passwordSchema = z
  .string()
  .min(8, 'Sifre en az 8 karakter olmali')
  .regex(/[a-z]/, 'Kucuk harf icermeli')
  .regex(/[A-Z]/, 'Buyuk harf icermeli')
  .regex(/\d/, 'Rakam icermeli');

export const tcknSchema = z
  .string()
  .length(11, 'TC Kimlik No 11 haneli olmali')
  .regex(/^\d+$/, 'Sadece rakam icermeli')
  .refine(validateTCKN, 'Gecersiz TC Kimlik No');

export const phoneSchema = z
  .string()
  .min(10, 'Telefon numarasi cok kisa')
  .refine(validateTurkishPhone, 'Gecersiz telefon numarasi (05XXXXXXXXX)');

// ============================================================================
// Form Schemas
// ============================================================================

export const loginFormSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Sifre gerekli'),
  rememberMe: z.boolean().optional(),
});

export const registerFormSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  confirmPassword: z.string(),
  firstName: z.string().min(2, 'Isim en az 2 karakter olmali'),
  lastName: z.string().min(2, 'Soyisim en az 2 karakter olmali'),
  phone: phoneSchema.optional(),
  tcKimlikNo: tcknSchema.optional(),
  acceptTerms: z.literal(true, {
    error: 'Kullanim sartlarini kabul etmelisiniz',
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Sifreler eslesmiyor',
  path: ['confirmPassword'],
});

export const passwordResetSchema = z.object({
  email: emailSchema,
});

export const passwordChangeSchema = z.object({
  currentPassword: z.string().min(1, 'Mevcut sifre gerekli'),
  newPassword: passwordSchema,
  confirmPassword: z.string(),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: 'Sifreler eslesmiyor',
  path: ['confirmPassword'],
}).refine((data) => data.currentPassword !== data.newPassword, {
  message: 'Yeni sifre eskisiyle ayni olamaz',
  path: ['newPassword'],
});

export const profileUpdateSchema = z.object({
  firstName: z.string().min(2, 'Isim en az 2 karakter olmali'),
  lastName: z.string().min(2, 'Soyisim en az 2 karakter olmali'),
  phone: phoneSchema.optional().or(z.literal('')),
  birthDate: z.string().optional(),
});

// ============================================================================
// YKS Specific Validations
// ============================================================================

export const examPreferenceSchema = z.object({
  examType: z.enum(['TYT', 'AYT-SAY', 'AYT-EA', 'AYT-SOZ', 'YDT'], {
    error: 'Sinav turu secin',
  }),
  targetUniversity: z.string().optional(),
  targetDepartment: z.string().optional(),
  dailyStudyHours: z.number().min(0).max(24).optional(),
  examDate: z.string().optional(),
});

// ============================================================================
// Validation Helpers
// ============================================================================

export type ValidationResult<T> =
  | { success: true; data: T }
  | { success: false; errors: Record<string, string> }

/**
 * Validates form data and returns errors in a format suitable for form libraries
 */
export function validateForm<T>(
  schema: z.ZodSchema<T>,
  data: unknown,
): ValidationResult<T> {
  const result = schema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  const errors: Record<string, string> = {};
  result.error.issues.forEach((issue) => {
    const path = issue.path.join('.');
    if (!errors[path]) {
      errors[path] = issue.message;
    }
  });

  return { success: false, errors };
}

/**
 * Pre-built validators for quick access
 */
export const validators = {
  email: (v: string) => emailSchema.safeParse(v).success,
  phone: (v: string) => validateTurkishPhone(v),
  tcno: (v: string) => validateTCKN(v),
  password: (v: string) => passwordSchema.safeParse(v).success,
};

export default {
  validateTCKN,
  validateTurkishPhone,
  formatTurkishPhone,
  checkPasswordStrength,
  validateForm,
  validators,
  schemas: {
    email: emailSchema,
    password: passwordSchema,
    tckn: tcknSchema,
    phone: phoneSchema,
    loginForm: loginFormSchema,
    registerForm: registerFormSchema,
    passwordReset: passwordResetSchema,
    passwordChange: passwordChangeSchema,
    profileUpdate: profileUpdateSchema,
    examPreference: examPreferenceSchema,
  },
};
