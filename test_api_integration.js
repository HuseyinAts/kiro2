/**
 * Test script for API integrations
 * Run this with: node test_api_integration.js
 */

const API_BASE_URL = 'http://localhost:8000';

// Helper function for making requests
async function makeRequest(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    const data = await response.json();
    return { success: response.ok, status: response.status, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// Test cases
async function runTests() {
  console.log('🚀 Testing API Integrations');
  console.log('=' .repeat(50));

  // Test 1: Health Check
  console.log('\n✅ Test 1: Health Check');
  const health = await makeRequest('/health');
  console.log('Response:', health.success ? '✓' : '✗', health.data || health.error);

  // Test 2: Get Agents
  console.log('\n✅ Test 2: Get Agents');
  const agents = await makeRequest('/api/agents');
  console.log('Response:', agents.success ? '✓' : '✗');
  if (agents.success) {
    console.log('Available agents:', agents.data.agents.map(a => a.id).join(', '));
  }

  // Test 3: Chat API
  console.log('\n✅ Test 3: Chat API');
  const chatResponse = await makeRequest('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      agent: 'learning',
      message: 'Merhaba, matematik öğrenmek istiyorum',
      session_id: 'test-session-123',
    }),
  });
  console.log('Response:', chatResponse.success ? '✓' : '✗');
  if (chatResponse.success) {
    console.log('Agent response:', chatResponse.data.response.substring(0, 100) + '...');
  }

  // Test 4: Student Profile Creation
  console.log('\n✅ Test 4: Student Profile Creation');
  const profileResponse = await makeRequest('/api/learning-path/create-profile', {
    method: 'POST',
    body: JSON.stringify({
      name: 'Test Öğrenci',
      grade: 11,
      subjects: ['Matematik', 'Fizik'],
      goals: ['YKS hazırlık'],
      learning_style: 'visual',
      available_time: 120,
    }),
  });
  console.log('Response:', profileResponse.success ? '✓' : '✗');
  let studentId = null;
  if (profileResponse.success && profileResponse.data.success) {
    studentId = profileResponse.data.profile.student_id;
    console.log('Student ID:', studentId);
    console.log('Learning Style:', profileResponse.data.profile.learning_style);
  }

  // Test 5: Knowledge Assessment
  if (studentId) {
    console.log('\n✅ Test 5: Knowledge Assessment');
    const assessmentResponse = await makeRequest('/api/learning-path/assess-knowledge', {
      method: 'POST',
      body: JSON.stringify({
        student_id: studentId,
        subject: 'Matematik',
        questions: ['Türev nedir?', 'İntegral nasıl alınır?'],
      }),
    });
    console.log('Response:', assessmentResponse.success ? '✓' : '✗');
    if (assessmentResponse.success && assessmentResponse.data.success) {
      console.log('Knowledge Level:', assessmentResponse.data.assessment);
    }
  }

  // Test 6: Create Learning Path
  if (studentId) {
    console.log('\n✅ Test 6: Create Learning Path');
    const pathResponse = await makeRequest('/api/learning-path/create-path', {
      method: 'POST',
      body: JSON.stringify({
        student_profile: { student_id: studentId },
        topic: 'Türev ve İntegral',
        duration_weeks: 4,
      }),
    });
    console.log('Response:', pathResponse.success ? '✓' : '✗');
    if (pathResponse.success && pathResponse.data.success) {
      console.log('Path ID:', pathResponse.data.learning_path.path_id);
      console.log('Total Resources:', pathResponse.data.learning_path.resources.length);
    }
  }

  // Test 7: Search Resources
  console.log('\n✅ Test 7: Search Resources');
  const searchResponse = await makeRequest('/api/learning-path/search-resources', {
    method: 'POST',
    body: JSON.stringify({
      topic: 'Matematik',
      learning_style: 'visual',
      level: 'beginner',
      language: 'tr',
      limit: 5,
    }),
  });
  console.log('Response:', searchResponse.success ? '✓' : '✗');
  if (searchResponse.success && searchResponse.data.success) {
    console.log('Found Resources:', searchResponse.data.resources.length);
  }

  // Test 8: RAG - Add Document
  console.log('\n✅ Test 8: RAG - Add Document');
  const ragAddResponse = await makeRequest('/api/rag/add_document', {
    method: 'POST',
    body: JSON.stringify({
      content: 'Türev, bir fonksiyonun değişim hızını gösteren matematiksel bir kavramdır.',
      metadata: {
        subject: 'Matematik',
        topic: 'Türev',
        grade: 11,
      },
    }),
  });
  console.log('Response:', ragAddResponse.success ? '✓' : '✗');

  // Test 9: RAG - Search
  console.log('\n✅ Test 9: RAG - Search');
  const ragSearchResponse = await makeRequest('/api/rag/search', {
    method: 'POST',
    body: JSON.stringify({
      query: 'türev nedir',
      k: 3,
    }),
  });
  console.log('Response:', ragSearchResponse.success ? '✓' : '✗');
  if (ragSearchResponse.success && ragSearchResponse.data.success) {
    console.log('Search Results:', ragSearchResponse.data.results.length);
  }

  // Test 10: RAG - Query with Context
  console.log('\n✅ Test 10: RAG - Query with Context');
  const ragQueryResponse = await makeRequest('/api/rag/query', {
    method: 'POST',
    body: JSON.stringify({
      query: 'Türev nasıl hesaplanır?',
      context_size: 3,
    }),
  });
  console.log('Response:', ragQueryResponse.success ? '✓' : '✗');
  if (ragQueryResponse.success && ragQueryResponse.data.success) {
    console.log('Answer:', ragQueryResponse.data.response?.substring(0, 100) + '...');
  }

  // Test 11: WebSocket Connection
  console.log('\n✅ Test 11: WebSocket Connection');
  try {
    const WebSocket = require('ws');
    const ws = new WebSocket(`ws://localhost:8000/ws`);
    
    await new Promise((resolve, reject) => {
      ws.on('open', () => {
        console.log('WebSocket: Connected ✓');
        
        // Send test message
        ws.send(JSON.stringify({
          agent: 'study',
          message: 'WebSocket test mesajı',
        }));
      });

      ws.on('message', (data) => {
        const message = JSON.parse(data);
        console.log('WebSocket Response:', message.type === 'response' ? '✓' : '✗');
        ws.close();
        resolve();
      });

      ws.on('error', (error) => {
        console.log('WebSocket Error:', error.message);
        reject(error);
      });

      setTimeout(() => {
        ws.close();
        resolve();
      }, 5000);
    });
  } catch (error) {
    console.log('WebSocket test requires ws package. Install with: npm install ws');
  }

  // Test 12: Metrics Endpoint
  console.log('\n✅ Test 12: Metrics Endpoint');
  const metricsResponse = await fetch(`${API_BASE_URL}/metrics`);
  console.log('Response:', metricsResponse.ok ? '✓' : '✗');
  if (metricsResponse.ok) {
    const metricsText = await metricsResponse.text();
    console.log('Metrics Available:', metricsText.includes('http_requests_total') ? '✓' : '✗');
  }

  console.log('\n' + '=' .repeat(50));
  console.log('✅ API Integration Tests Complete!');
}

// Run tests
runTests().catch(console.error);