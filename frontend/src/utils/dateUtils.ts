/**
 * Date Utilities
 * Centralized date formatting using dayjs
 * Migration from date-fns to reduce bundle size by ~50KB
 */

import dayjs, { Dayjs, ConfigType } from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import duration from 'dayjs/plugin/duration';
import isBetween from 'dayjs/plugin/isBetween';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/tr';

// Initialize plugins
dayjs.extend(relativeTime);
dayjs.extend(customParseFormat);
dayjs.extend(isBetween);
dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);
dayjs.extend(duration);

// Set Turkish locale as default
dayjs.locale('tr');

/**
 * Date formatting utility
 */
export const dateUtils = {
  /**
   * Format date with given pattern
   * @example format(new Date(), 'DD MMMM YYYY HH:mm') // "14 Kasım 2025 18:30"
   */
  format: (date: ConfigType, formatStr = 'DD MMMM YYYY HH:mm'): string => {
    return dayjs(date).format(formatStr);
  },

  /**
   * Get relative time from now
   * @example fromNow(new Date('2025-11-14')) // "2 saat önce"
   */
  fromNow: (date: ConfigType): string => {
    return dayjs(date).fromNow();
  },

  /**
   * Get relative time to now
   * @example toNow(new Date('2025-12-01')) // "17 gün içinde"
   */
  toNow: (date: ConfigType): string => {
    return dayjs(date).toNow();
  },

  /**
   * Get distance between two dates in words
   * @example formatDistance(date1, date2) // "2 saat"
   */
  formatDistance: (date1: ConfigType, date2: ConfigType, options?: { addSuffix?: boolean }): string => {
    const d1 = dayjs(date1);
    const d2 = dayjs(date2);
    const diff = Math.abs(d1.diff(d2, 'second'));

    if (diff < 60) {return options?.addSuffix ? 'şimdi' : '1 dakikadan az';}
    if (diff < 3600) {
      const minutes = Math.floor(diff / 60);
      return options?.addSuffix ? `${minutes} dakika önce` : `${minutes} dakika`;
    }
    if (diff < 86400) {
      const hours = Math.floor(diff / 3600);
      return options?.addSuffix ? `${hours} saat önce` : `${hours} saat`;
    }
    const days = Math.floor(diff / 86400);
    return options?.addSuffix ? `${days} gün önce` : `${days} gün`;
  },

  /**
   * Format date as ISO string
   */
  formatISO: (date: ConfigType): string => {
    return dayjs(date).toISOString();
  },

  /**
   * Parse ISO date string
   */
  parseISO: (dateString: string): Dayjs => {
    return dayjs(dateString);
  },

  /**
   * Check if date1 is before date2
   */
  isBefore: (date1: ConfigType, date2: ConfigType): boolean => {
    return dayjs(date1).isBefore(dayjs(date2));
  },

  /**
   * Check if date1 is after date2
   */
  isAfter: (date1: ConfigType, date2: ConfigType): boolean => {
    return dayjs(date1).isAfter(dayjs(date2));
  },

  /**
   * Check if dates are same
   */
  isSame: (date1: ConfigType, date2: ConfigType, unit?: any): boolean => {
    return dayjs(date1).isSame(dayjs(date2), unit);
  },

  /**
   * Check if date is between two dates
   */
  isBetween: (date: ConfigType, startDate: ConfigType, endDate: ConfigType): boolean => {
    return dayjs(date).isBetween(startDate, endDate, null, '[]');
  },

  /**
   * Get difference between dates
   */
  diff: (date1: ConfigType, date2: ConfigType, unit: any = 'millisecond'): number => {
    return dayjs(date1).diff(dayjs(date2), unit);
  },

  /**
   * Add time to date
   * @example add(new Date(), 1, 'day') // tomorrow
   */
  add: (date: ConfigType, amount: number, unit: any): Dayjs => {
    return dayjs(date).add(amount, unit);
  },

  /**
   * Subtract time from date
   */
  subtract: (date: ConfigType, amount: number, unit: any): Dayjs => {
    return dayjs(date).subtract(amount, unit);
  },

  /**
   * Start of time unit
   * @example startOf(new Date(), 'day') // today at 00:00:00
   */
  startOf: (date: ConfigType, unit: any): Dayjs => {
    return dayjs(date).startOf(unit);
  },

  /**
   * End of time unit
   * @example endOf(new Date(), 'day') // today at 23:59:59
   */
  endOf: (date: ConfigType, unit: any): Dayjs => {
    return dayjs(date).endOf(unit);
  },

  /**
   * Check if date is valid
   */
  isValid: (date: ConfigType): boolean => {
    return dayjs(date).isValid();
  },

  /**
   * Get current date/time
   */
  now: (): Dayjs => {
    return dayjs();
  },

  /**
   * Format duration (milliseconds to human readable)
   * @example formatDuration(125000) // "2 dakika 5 saniye"
   */
  formatDuration: (milliseconds: number): string => {
    const dur = dayjs.duration(milliseconds);
    const hours = Math.floor(dur.asHours());
    const minutes = dur.minutes();
    const seconds = dur.seconds();

    const parts: string[] = [];
    if (hours > 0) {parts.push(`${hours} saat`);}
    if (minutes > 0) {parts.push(`${minutes} dakika`);}
    if (seconds > 0 || parts.length === 0) {parts.push(`${seconds} saniye`);}

    return parts.join(' ');
  },

  /**
   * Format time (HH:mm:ss)
   */
  formatTime: (date: ConfigType): string => {
    return dayjs(date).format('HH:mm:ss');
  },

  /**
   * Format date only (DD/MM/YYYY)
   */
  formatDate: (date: ConfigType): string => {
    return dayjs(date).format('DD/MM/YYYY');
  },

  /**
   * Format date with day name
   * @example formatDateWithDay(new Date()) // "14 Kasım 2025, Perşembe"
   */
  formatDateWithDay: (date: ConfigType): string => {
    return dayjs(date).format('DD MMMM YYYY, dddd');
  },

  /**
   * Get timestamp (Unix)
   */
  toTimestamp: (date: ConfigType): number => {
    return dayjs(date).unix();
  },

  /**
   * From timestamp (Unix)
   */
  fromTimestamp: (timestamp: number): Dayjs => {
    return dayjs.unix(timestamp);
  },

  /**
   * Calendar time (today, yesterday, etc.)
   */
  calendar: (date: ConfigType): string => {
    const d = dayjs(date);
    const now = dayjs();
    const diffDays = now.diff(d, 'day');

    if (diffDays === 0) {return `Bugün ${d.format('HH:mm')}`;}
    if (diffDays === 1) {return `Dün ${d.format('HH:mm')}`;}
    if (diffDays === -1) {return `Yarın ${d.format('HH:mm')}`;}
    if (diffDays > 1 && diffDays <= 7) {return d.format('dddd HH:mm');}
    return d.format('DD MMMM YYYY HH:mm');
  },

  /**
   * Add days to date (returns Date object for compatibility)
   * @example addDays(new Date(), 7) // date 7 days from now
   */
  addDays: (date: ConfigType, days: number): Date => {
    return dayjs(date).add(days, 'day').toDate();
  },

  /**
   * Add weeks to date (returns Date object for compatibility)
   * @example addWeeks(new Date(), 2) // date 2 weeks from now
   */
  addWeeks: (date: ConfigType, weeks: number): Date => {
    return dayjs(date).add(weeks, 'week').toDate();
  },

  /**
   * Add months to date (returns Date object for compatibility)
   * @example addMonths(new Date(), 3) // date 3 months from now
   */
  addMonths: (date: ConfigType, months: number): Date => {
    return dayjs(date).add(months, 'month').toDate();
  },
};

/**
 * Export dayjs instance for advanced usage
 */
export { dayjs };

/**
 * Export default
 */
export default dateUtils;
