import { Upload, X, FileText, AlertCircle } from 'lucide-react';
import * as React from 'react';
import {  useState, useCallback  } from 'react';

import questionParserService, { ParsedQuestion } from '../../services/questionParser';

const QuestionParserUpload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [parsing, setParsing] = useState(false);
  const [results, setResults] = useState<ParsedQuestion[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
      setError(null);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setFiles(Array.from(e.dataTransfer.files));
      setError(null);
    }
  }, []);

  const handleParse = async () => {
    if (files.length === 0) {return;}

    setParsing(true);
    setError(null);

    try {
      if (files.length === 1) {
        const result = await questionParserService.parseTestPage(files[0]);
        setResults(result.questions);
      } else {
        const results = await questionParserService.parseBatch(files);
        const allQuestions = results.flatMap(r => r.questions);
        setResults(allQuestions);
      }
    } catch (err: any) {
      setError(err.message || 'Parse işlemi başarısız oldu');
    } finally {
      setParsing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">YKS Soru Ayrıştırıcı</h2>

      {/* Upload Area */}
      <div
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-gray-600 mb-4">
          Test sayfalarını sürükleyip bırakın veya seçin
        </p>
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="bg-blue-500 text-white px-4 py-2 rounded cursor-pointer hover:bg-blue-600 inline-block"
        >
          Dosya Seç
        </label>
      </div>

      {/* Selected Files */}
      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3">Seçilen Dosyalar:</h3>
          <div className="space-y-2">
            {files.map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-500 mr-2" />
                  <span className="text-sm">{file.name}</span>
                </div>
                <button
                  onClick={() => setFiles(files.filter((_, i) => i !== index))}
                  className="text-red-500 hover:text-red-700"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={handleParse}
            disabled={parsing}
            className={`mt-4 w-full py-2 rounded ${
              parsing
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-green-500 hover:bg-green-600 text-white'
            }`}
          >
            {parsing ? 'İşleniyor...' : 'Soruları Ayrıştır'}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded flex items-start">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3">
            Ayrıştırılan Sorular ({results.length} adet)
          </h3>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {results.map((question, index) => (
              <div key={index} className="bg-white border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <span className="font-semibold">Soru {question.question_number}</span>
                  <div className="flex items-center text-sm text-gray-500">
                    <span className="mr-2">{question.subject}</span>
                    <span>{question.topic}</span>
                  </div>
                </div>
                <p className="text-gray-700 mb-3">{question.question_text}</p>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  {Object.entries(question.options).map(([key, value]) => (
                    <div key={key} className="flex">
                      <span className="font-semibold mr-2">{key})</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default QuestionParserUpload;
