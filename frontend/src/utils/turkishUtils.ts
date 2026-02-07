/**
 * Turkish Character Utilities
 * Handles proper Turkish I/i/I/ı character transformations
 *
 * IMPORTANT: JavaScript's toUpperCase/toLowerCase does NOT handle
 * Turkish characters correctly. Always use these utilities for Turkish text.
 *
 * Turkish character mappings:
 * - 'i' (dotted i) → 'İ' (dotted I)
 * - 'I' (dotless I) → 'ı' (dotless i)
 * - 'ı' (dotless i) → 'I' (dotless I)
 * - 'İ' (dotted I) → 'i' (dotted i)
 */

/**
 * Turkish lowercase character map
 */
const TURKISH_LOWERCASE_MAP: Record<string, string> = {
  'I': 'ı',   // Dotless I → dotless i
  'İ': 'i',   // Dotted I → dotted i
  'Ş': 'ş',
  'Ğ': 'ğ',
  'Ü': 'ü',
  'Ö': 'ö',
  'Ç': 'ç',
};

/**
 * Turkish uppercase character map
 */
const TURKISH_UPPERCASE_MAP: Record<string, string> = {
  'i': 'İ',   // Dotted i → Dotted I
  'ı': 'I',   // Dotless i → Dotless I
  'ş': 'Ş',
  'ğ': 'Ğ',
  'ü': 'Ü',
  'ö': 'Ö',
  'ç': 'Ç',
};

/**
 * Converts a string to uppercase using Turkish locale rules
 * @param str - Input string
 * @returns Uppercase string with proper Turkish character handling
 *
 * @example
 * turkishUpperCase('istanbul') // 'İSTANBUL'
 * turkishUpperCase('diyarbakır') // 'DİYARBAKIR'
 */
export function turkishUpperCase(str: string): string {
  if (!str) {return str;}

  let result = '';
  for (const char of str) {
    result += TURKISH_UPPERCASE_MAP[char] ?? char.toUpperCase();
  }
  return result;
}

/**
 * Converts a string to lowercase using Turkish locale rules
 * @param str - Input string
 * @returns Lowercase string with proper Turkish character handling
 *
 * @example
 * turkishLowerCase('İSTANBUL') // 'istanbul'
 * turkishLowerCase('DIYARBAKIR') // 'dıyarbakır'
 */
export function turkishLowerCase(str: string): string {
  if (!str) {return str;}

  let result = '';
  for (const char of str) {
    result += TURKISH_LOWERCASE_MAP[char] ?? char.toLowerCase();
  }
  return result;
}

/**
 * Capitalizes the first letter using Turkish locale rules
 * @param str - Input string
 * @returns Capitalized string
 *
 * @example
 * turkishCapitalize('istanbul') // 'İstanbul'
 * turkishCapitalize('ığdır') // 'Iğdır'
 */
export function turkishCapitalize(str: string): string {
  if (!str) {return str;}

  const firstChar = str.charAt(0);
  const rest = str.slice(1);
  return (TURKISH_UPPERCASE_MAP[firstChar] ?? firstChar.toUpperCase()) + turkishLowerCase(rest);
}

/**
 * Title case conversion using Turkish locale rules
 * @param str - Input string
 * @returns Title cased string
 *
 * @example
 * turkishTitleCase('türkiye cumhuriyeti') // 'Türkiye Cumhuriyeti'
 */
export function turkishTitleCase(str: string): string {
  if (!str) {return str;}

  return str.split(' ')
    .map(word => turkishCapitalize(word))
    .join(' ');
}

/**
 * Case-insensitive comparison using Turkish locale rules
 * @param a - First string
 * @param b - Second string
 * @returns true if strings are equal (case-insensitive)
 *
 * @example
 * turkishEquals('İstanbul', 'istanbul') // true
 * turkishEquals('DIYARBAKIR', 'dıyarbakır') // true
 */
export function turkishEquals(a: string, b: string): boolean {
  return turkishLowerCase(a) === turkishLowerCase(b);
}

/**
 * Case-insensitive includes using Turkish locale rules
 * @param str - String to search in
 * @param search - String to search for
 * @returns true if str includes search (case-insensitive)
 *
 * @example
 * turkishIncludes('İstanbul', 'istan') // true
 * turkishIncludes('DIYARBAKIR', 'bakır') // true
 */
export function turkishIncludes(str: string, search: string): boolean {
  return turkishLowerCase(str).includes(turkishLowerCase(search));
}

/**
 * Turkish locale sort comparison function
 * Use with Array.sort() for proper Turkish alphabetical order
 *
 * @example
 * ['ı', 'i', 'a', 'z'].sort(turkishCompare) // ['a', 'ı', 'i', 'z']
 */
export function turkishCompare(a: string, b: string): number {
  return a.localeCompare(b, 'tr-TR');
}

/**
 * Turkish alphabet order
 */
export const TURKISH_ALPHABET = [
  'a', 'b', 'c', 'ç', 'd', 'e', 'f', 'g', 'ğ', 'h',
  'ı', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'ö', 'p',
  'r', 's', 'ş', 't', 'u', 'ü', 'v', 'y', 'z',
] as const;

/**
 * Check if a character is a Turkish special character
 */
export function isTurkishChar(char: string): boolean {
  return 'ıİşŞğĞüÜöÖçÇ'.includes(char);
}

/**
 * Normalize Turkish text for search/comparison
 * Converts to lowercase and removes diacritics
 * @param str - Input string
 * @returns Normalized string
 */
export function normalizeTurkish(str: string): string {
  return turkishLowerCase(str)
    .replace(/ı/g, 'i')
    .replace(/ö/g, 'o')
    .replace(/ü/g, 'u')
    .replace(/ş/g, 's')
    .replace(/ğ/g, 'g')
    .replace(/ç/g, 'c');
}

export default {
  turkishUpperCase,
  turkishLowerCase,
  turkishCapitalize,
  turkishTitleCase,
  turkishEquals,
  turkishIncludes,
  turkishCompare,
  normalizeTurkish,
  isTurkishChar,
  TURKISH_ALPHABET,
};
