// KIRO2 ui-starter — P0 yapı taşları (BILESEN_ENVANTER.md §B ile birebir)
// [DIKKAT] Test edilmemiş başlangıç kodu — hedef repoda derleyip ince ayar yapın.
export { KiroThemeProvider, useKiroTheme, surf, baseText, numText, serifText } from './theme';
export type { KiroTheme } from './theme';
export { Button } from './Button';
export type { ButtonProps } from './Button';
export { Chip } from './Chip';
export type { ChipProps } from './Chip';
export { Card } from './Card';
export type { CardProps } from './Card';
export { StatBlock } from './StatBlock';
export type { StatBlockProps } from './StatBlock';
export { ProgressBar } from './ProgressBar';
export type { ProgressBarProps } from './ProgressBar';
export { ProgressRing } from './ProgressRing';
export type { ProgressRingProps } from './ProgressRing';
export { SegmentedControl } from './SegmentedControl';
export type { SegmentedControlProps, SegmentedOption } from './SegmentedControl';
export { Input } from './Input';
export type { InputProps } from './Input';
export { Avatar, AVATAR_PAL } from './Avatar';
export type { AvatarProps } from './Avatar';
export { IconBadge } from './IconBadge';
export type { IconBadgeProps, IconBadgeTone } from './IconBadge';
export { Callout } from './Callout';
export type { CalloutProps, CalloutTone } from './Callout';
export { Skeleton } from './Skeleton';
export type { SkeletonProps } from './Skeleton';
export { EmptyState } from './EmptyState';
export type { EmptyStateProps } from './EmptyState';
export { ErrorState } from './ErrorState';
export type { ErrorStateProps } from './ErrorState';
export { ZoneHeader } from './ZoneHeader';
export type { ZoneHeaderProps, ZoneTone } from './ZoneHeader';
// --- Prototip DC'lerinden çıkarılan ek P0 bileşenler (Faz 2) ---
export { SideNav, NAV_ICONS, STUDENT_NAV, PARENT_NAV, TEACHER_NAV } from './SideNav';
export type { SideNavProps, SideNavRole, SideNavItem, SideNavSection } from './SideNav';
export { MasteryBadge, tierFromPct } from './MasteryBadge';
export type { MasteryBadgeProps, MasteryTier, MasteryTrend } from './MasteryBadge';
export { StatusChip } from './StatusChip';
export type { StatusChipProps, OdevDurum } from './StatusChip';
export { ChatBubble } from './ChatBubble';
export type { ChatBubbleProps } from './ChatBubble';
export { ConfettiDawn, useReducedMotion } from './ConfettiDawn';
export type { ConfettiDawnProps } from './ConfettiDawn';
export { QuestionCard } from './QuestionCard';
export type { QuestionCardProps } from './QuestionCard';
// --- SPRINT9 · Grup 7-A paylaşılan çubuk (Veli · Öğretmen · Öğrenci-Özeti) ---
export { WeeklyActivityBars } from './WeeklyActivityBars';
export type { WeeklyActivityBarsProps } from './WeeklyActivityBars';
// --- SPRINT10-C · Ayarlar aç/kapa anahtarı ---
export { Switch } from './Switch';
export type { SwitchProps } from './Switch';
