import axios from 'axios';

export interface ParsedQuestion {
  question_number: number;
  question_text: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
    E: string;
  };
  subject: string;
  topic: string;
  test_id: string;
  page_number: number;
  bbox: [number, number, number, number];
  confidence: number;
}

export interface ParseResult {
  file: string;
  processed_at: string;
  questions: ParsedQuestion[];
  metadata: {
    subject?: string;
    topic?: string;
    test_identifier?: string;
    page_number?: string;
  };
}

class QuestionParserService {
  private baseURL = '/api/v1/question-parser';

  async parseTestPage(file: File): Promise<ParseResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(
      `${this.baseURL}/parse-test`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    );

    if (!response.data.success) {
      throw new Error(response.data.error);
    }

    return response.data.data;
  }

  async parseBatch(files: File[]): Promise<ParseResult[]> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await axios.post(
      `${this.baseURL}/parse-batch`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    );

    if (!response.data.success) {
      throw new Error(response.data.error);
    }

    return response.data.data.results;
  }
}

export default new QuestionParserService();
