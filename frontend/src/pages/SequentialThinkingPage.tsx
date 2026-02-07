/**
 * Sequential Thinking Page
 * Problem solving with step-by-step reasoning
 *
 * Multi-LLM support: Gemini, OpenAI, Claude, Qwen
 */

import * as React from 'react';

import { SequentialThinkingViewer } from '../components/SequentialThinking';

const SequentialThinkingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Adim Adim Problem Cozumu
          </h1>
          <p className="text-gray-600">
            Yapay zeka destekli mantiksal dusunme ve problem cozme
          </p>
        </header>

        <SequentialThinkingViewer
          enableEnsemble={true}
          onSolutionComplete={(_answer) => {
            // Solution completed
          }}
        />
      </div>
    </div>
  );
};

export default SequentialThinkingPage;
