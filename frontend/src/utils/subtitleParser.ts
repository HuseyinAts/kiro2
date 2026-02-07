export interface Subtitle {
  index: number;
  startTime: number;
  endTime: number;
  text: string;
}

/**
 * Parses a WebVTT subtitle file
 * @param vttText - The raw VTT file content
 * @returns Array of subtitle objects
 */
export const parseVTT = (vttText: string): Subtitle[] => {
  const lines = vttText.split('\n');
  const subtitles: Subtitle[] = [];
  let i = 0;
  let index = 0;

  // Skip VTT header
  while (i < lines.length && !lines[i].includes('-->')) {
    i++;
  }

  while (i < lines.length) {
    const line = lines[i].trim();

    // Look for timestamp line (e.g., "00:00:01.000 --> 00:00:04.000")
    if (line.includes('-->')) {
      const [startStr, endStr] = line.split('-->').map(s => s.trim());
      const startTime = parseVTTTimestamp(startStr);
      const endTime = parseVTTTimestamp(endStr);

      i++;
      let text = '';

      // Collect subtitle text (until empty line)
      while (i < lines.length && lines[i].trim() !== '') {
        const textLine = lines[i].trim();
        // Remove VTT tags like <v Speaker>
        const cleanedText = textLine.replace(/<[^>]+>/g, '');
        text += cleanedText + ' ';
        i++;
      }

      if (text.trim()) {
        subtitles.push({
          index: index++,
          startTime,
          endTime,
          text: text.trim(),
        });
      }
    }
    i++;
  }

  return subtitles;
};

/**
 * Parses an SRT subtitle file
 * @param srtText - The raw SRT file content
 * @returns Array of subtitle objects
 */
export const parseSRT = (srtText: string): Subtitle[] => {
  const lines = srtText.split('\n');
  const subtitles: Subtitle[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();

    // Look for subtitle index (numeric line)
    if (/^\d+$/.test(line)) {
      const index = parseInt(line, 10);
      i++;

      // Next line should be timestamp
      if (i < lines.length && lines[i].includes('-->')) {
        const [startStr, endStr] = lines[i].split('-->').map(s => s.trim());
        const startTime = parseSRTTimestamp(startStr);
        const endTime = parseSRTTimestamp(endStr);

        i++;
        let text = '';

        // Collect subtitle text (until empty line)
        while (i < lines.length && lines[i].trim() !== '') {
          text += lines[i].trim() + ' ';
          i++;
        }

        if (text.trim()) {
          subtitles.push({
            index: index - 1,
            startTime,
            endTime,
            text: text.trim(),
          });
        }
      }
    }
    i++;
  }

  return subtitles;
};

/**
 * Parses VTT timestamp format: "00:00:01.000" or "00:01:00.000"
 */
export const parseVTTTimestamp = (timestamp: string): number => {
  const parts = timestamp.split(':');

  if (parts.length === 3) {
    // Format: HH:MM:SS.mmm
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    const seconds = parseFloat(parts[2].replace(',', '.'));
    return hours * 3600 + minutes * 60 + seconds;
  } else if (parts.length === 2) {
    // Format: MM:SS.mmm
    const minutes = parseInt(parts[0], 10);
    const seconds = parseFloat(parts[1].replace(',', '.'));
    return minutes * 60 + seconds;
  }

  return 0;
};

/**
 * Parses SRT timestamp format: "00:00:01,000"
 */
export const parseSRTTimestamp = (timestamp: string): number => {
  const parts = timestamp.split(':');

  if (parts.length === 3) {
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    const seconds = parseFloat(parts[2].replace(',', '.'));
    return hours * 3600 + minutes * 60 + seconds;
  }

  return 0;
};

/**
 * Formats seconds to HH:MM:SS or MM:SS format
 */
export const formatTime = (seconds: number, includeHours: boolean = false): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0 || includeHours) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

/**
 * Gets the current subtitle for a given time
 */
export const getCurrentSubtitle = (subtitles: Subtitle[], currentTime: number): Subtitle | null => {
  return subtitles.find(
    sub => currentTime >= sub.startTime && currentTime <= sub.endTime,
  ) || null;
};

/**
 * Converts SRT to VTT format
 */
export const srtToVtt = (srtText: string): string => {
  let vtt = 'WEBVTT\n\n';
  const subtitles = parseSRT(srtText);

  subtitles.forEach((sub, index) => {
    const startTime = formatVTTTimestamp(sub.startTime);
    const endTime = formatVTTTimestamp(sub.endTime);
    vtt += `${index + 1}\n${startTime} --> ${endTime}\n${sub.text}\n\n`;
  });

  return vtt;
};

/**
 * Formats a timestamp for VTT format: "HH:MM:SS.mmm"
 */
export const formatVTTTimestamp = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  const wholeSecs = Math.floor(secs);
  const milliseconds = Math.round((secs - wholeSecs) * 1000);

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${wholeSecs.toString().padStart(2, '0')}.${milliseconds.toString().padStart(3, '0')}`;
};

/**
 * Validates subtitle file format
 */
export const detectSubtitleFormat = (content: string): 'vtt' | 'srt' | 'unknown' => {
  if (content.trim().startsWith('WEBVTT')) {
    return 'vtt';
  } else if (/^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}/m.test(content)) {
    return 'srt';
  }
  return 'unknown';
};

/**
 * Parses subtitle file based on detected format
 */
export const parseSubtitleFile = (content: string): Subtitle[] => {
  const format = detectSubtitleFormat(content);

  switch (format) {
    case 'vtt':
      return parseVTT(content);
    case 'srt':
      return parseSRT(content);
    default:
      console.warn('Unknown subtitle format');
      return [];
  }
};

/**
 * Fetches and parses subtitles from URL
 */
export const fetchSubtitles = async (url: string): Promise<Subtitle[]> => {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const text = await response.text();
    return parseSubtitleFile(text);
  } catch (error) {
    console.error('Error fetching subtitles:', error);
    return [];
  }
};

/**
 * Generates a sample Turkish VTT subtitle file
 */
export const generateSampleTurkishVTT = (): string => {
  return `WEBVTT

1
00:00:00.000 --> 00:00:03.000
Merhaba, bu örnek bir Türkçe altyazı dosyasıdır.

2
00:00:03.500 --> 00:00:07.000
Bu altyazılar erişilebilirlik için önemlidir.

3
00:00:07.500 --> 00:00:11.000
Tüm öğrencilerin eğitim videolarına erişimi olmalıdır.

4
00:00:11.500 --> 00:00:15.000
WCAG 2.1 Level AA standardına uygunluk sağlanmıştır.
`;
};
