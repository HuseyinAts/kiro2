import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const screenshotDir = path.resolve('../docs/screenshots');
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir, { recursive: true });
}

(async () => {
  console.log('🚀 Starting Playwright Click Rehearsal (JSON Cookie Auth via Port 3000)...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`[Browser Console Error] ${msg.text()}`);
      errors.push(msg.text());
    }
  });

  page.on('requestfailed', request => {
    if (!request.url().includes('web-vitals') && !request.url().includes('favicon')) {
      console.log(`[Request Failed] ${request.url()} - ${request.failure()?.errorText}`);
    }
  });

  try {
    // Step 1: Landing Page
    console.log('\n--- Step 1: Landing Page (http://localhost:3000) ---');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(screenshotDir, 'step1_landing.png') });
    console.log('✅ Step 1 Captured: step1_landing.png');

    // Step 2: Student Login via JSON API
    console.log('\n--- Step 2: Student Login (test@kiro2.com) ---');
    const loginRes = await context.request.post('http://localhost:3000/api/v1/auth/login/secure', {
      data: {
        email: 'test@kiro2.com',
        password: 'Kiro2Beta2026@x'
      }
    });
    console.log(`Student Login Status: ${loginRes.status()}`);

    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });
    await page.screenshot({ path: path.join(screenshotDir, 'step2_student_login.png') });
    console.log('✅ Step 2 Captured: step2_student_login.png');

    // Step 3: Student Dashboard
    console.log('\n--- Step 3: Student Dashboard ---');
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(screenshotDir, 'step3_student_dashboard.png') });
    console.log('✅ Step 3 Captured: step3_student_dashboard.png');

    // Step 4: Learning Path
    console.log('\n--- Step 4: Learning Path ---');
    await page.goto('http://localhost:3000/learning-path', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(screenshotDir, 'step4_learning_path.png') });
    console.log('✅ Step 4 Captured: step4_learning_path.png');

    // Step 5: Practice Flow
    console.log('\n--- Step 5: Practice Flow ---');
    await page.goto('http://localhost:3000/exam', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(screenshotDir, 'step5_practice_exam.png') });
    console.log('✅ Step 5 Captured: step5_practice_exam.png');

    // Step 6: FSRS Review
    console.log('\n--- Step 6: FSRS Review ---');
    await page.goto('http://localhost:3000/review', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(screenshotDir, 'step6_fsrs_review.png') });
    console.log('✅ Step 6 Captured: step6_fsrs_review.png');

    // Step 7: Teacher Dashboard
    console.log('\n--- Step 7: Teacher Dashboard ---');
    const teacherContext = await browser.newContext();
    const teacherPage = await teacherContext.newPage();
    const tLoginRes = await teacherContext.request.post('http://localhost:3000/api/v1/auth/login/secure', {
      data: {
        email: 'ogretmen@kiro2.com',
        password: 'Kiro2Beta2026@x'
      }
    });
    console.log(`Teacher Login Status: ${tLoginRes.status()}`);

    await teacherPage.goto('http://localhost:3000/teacher', { waitUntil: 'networkidle' });
    await teacherPage.waitForTimeout(2000);
    await teacherPage.screenshot({ path: path.join(screenshotDir, 'step7_teacher_dashboard.png') });
    console.log('✅ Step 7 Captured: step7_teacher_dashboard.png');

    // Step 8: Exam History
    console.log('\n--- Step 8: Exam History ---');
    await page.goto('http://localhost:3000/exam-history', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(screenshotDir, 'step8_exam_history.png') });
    console.log('✅ Step 8 Captured: step8_exam_history.png');

    console.log('\n==================================================');
    console.log('🎉 PLAYWRIGHT REHEARSAL COMPLETED SUCCESSFULLY!');
    console.log(`📸 Screenshots saved to: ${screenshotDir}`);
    console.log(`⚠️ Relevant console errors count: ${errors.length}`);
    console.log('==================================================');

  } catch (err) {
    console.error('❌ Rehearsal encountered an error:', err);
  } finally {
    await browser.close();
  }
})();
