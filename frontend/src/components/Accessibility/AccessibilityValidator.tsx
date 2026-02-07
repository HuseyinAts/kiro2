import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { validateWCAG, generateAccessibilityReport, type ValidationResult } from '../../utils/wcagValidator';

interface AccessibilityValidatorProps {
  autoRun?: boolean;
  showReport?: boolean;
}

/**
 * Accessibility Validator Component
 * Runs WCAG 2.1 Level AA validation and displays results
 * For development and testing purposes only
 */
export const AccessibilityValidator: React.FC<AccessibilityValidatorProps> = ({
  autoRun = false,
  showReport = true,
}) => {
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [report, setReport] = useState<string>('');

  useEffect(() => {
    if (autoRun) {
      runValidation();
    }
  }, [autoRun]);

  const runValidation = () => {
    setIsRunning(true);

    // Run validation after a short delay to ensure DOM is ready
    setTimeout(() => {
      const validationResult = validateWCAG(document.body);
      setResult(validationResult);
      setReport(generateAccessibilityReport(validationResult));
      setIsRunning(false);

      // Log to console
      console.group('🔍 WCAG 2.1 Validation Results');
      console.log('Score:', validationResult.score);
      console.log('Passed:', validationResult.passed);
      console.log('Errors:', validationResult.errors);
      console.log('Warnings:', validationResult.warnings);
      console.groupEnd();
    }, 500);
  };

  const downloadReport = () => {
    if (!report) {return;}

    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `accessibility-report-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!showReport && !result) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        maxWidth: '400px',
        backgroundColor: '#fff',
        border: '2px solid #ccc',
        borderRadius: '8px',
        padding: '16px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        zIndex: 9999,
        fontFamily: 'system-ui, sans-serif',
      }}
      role="region"
      aria-label="Erişilebilirlik doğrulama paneli"
    >
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 }}>
        🔍 WCAG 2.1 Doğrulama
      </h3>

      <button
        onClick={runValidation}
        disabled={isRunning}
        style={{
          width: '100%',
          padding: '10px',
          backgroundColor: '#1976d2',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          fontSize: '14px',
          fontWeight: 500,
          cursor: isRunning ? 'not-allowed' : 'pointer',
          marginBottom: '12px',
        }}
        aria-busy={isRunning}
      >
        {isRunning ? 'Doğrulanıyor...' : 'Doğrulamayı Çalıştır'}
      </button>

      {result && (
        <>
          <div
            style={{
              padding: '12px',
              backgroundColor: result.passed ? '#e8f5e9' : '#ffebee',
              borderRadius: '4px',
              marginBottom: '12px',
            }}
            role="status"
            aria-live="polite"
          >
            <div style={{ fontSize: '14px', marginBottom: '8px' }}>
              <strong>Skor:</strong> {result.score}/100
            </div>
            <div style={{ fontSize: '14px', marginBottom: '8px' }}>
              <strong>Durum:</strong>{' '}
              {result.passed ? '✅ Geçti' : '❌ Başarısız'}
            </div>
            <div style={{ fontSize: '14px', marginBottom: '4px' }}>
              <strong>Hatalar:</strong> {result.errors.length}
            </div>
            <div style={{ fontSize: '14px' }}>
              <strong>Uyarılar:</strong> {result.warnings.length}
            </div>
          </div>

          {result.errors.length > 0 && (
            <div
              style={{
                maxHeight: '300px',
                overflowY: 'auto',
                fontSize: '12px',
                marginBottom: '12px',
              }}
            >
              <strong style={{ display: 'block', marginBottom: '8px' }}>
                Bulunan Hatalar:
              </strong>
              <ul style={{ margin: 0, paddingLeft: '20px' }}>
                {result.errors.slice(0, 10).map((error, index) => (
                  <li key={index} style={{ marginBottom: '8px' }}>
                    <strong>{error.rule}</strong> ({error.wcagRef})
                    <div style={{ color: '#666', marginTop: '4px' }}>
                      {error.description}
                    </div>
                  </li>
                ))}
              </ul>
              {result.errors.length > 10 && (
                <div style={{ marginTop: '8px', color: '#666' }}>
                  ... ve {result.errors.length - 10} hata daha
                </div>
              )}
            </div>
          )}

          <button
            onClick={downloadReport}
            style={{
              width: '100%',
              padding: '8px',
              backgroundColor: '#4caf50',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              fontSize: '13px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            📥 Raporu İndir
          </button>
        </>
      )}

      {/* Development only notice */}
      <div
        style={{
          marginTop: '12px',
          padding: '8px',
          backgroundColor: '#fff3cd',
          borderRadius: '4px',
          fontSize: '11px',
          color: '#856404',
        }}
      >
        ⚠️ Bu bileşen sadece geliştirme aşamasında kullanılmalıdır
      </div>
    </div>
  );
};

export default AccessibilityValidator;
