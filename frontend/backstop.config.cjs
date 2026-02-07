/**
 * BackstopJS Visual Regression Testing Configuration
 *
 * KIRO2 Visual Testing Setup
 * - Tests critical user flows across desktop, tablet, and mobile viewports
 * - Uses Playwright engine for modern browser support
 * - Self-hosted, no external dependencies
 */

module.exports = {
  id: "kiro2-visual-regression",
  viewports: [
    {
      label: "desktop",
      width: 1920,
      height: 1080,
    },
    {
      label: "tablet",
      width: 768,
      height: 1024,
    },
    {
      label: "mobile",
      width: 375,
      height: 812,
    },
  ],
  scenarios: [
    {
      label: "Login Page",
      url: "http://localhost:3002/login",
      delay: 1000,
      misMatchThreshold: 0.1,
    },
    {
      label: "Dashboard",
      url: "http://localhost:3002/dashboard",
      delay: 2000,
      misMatchThreshold: 0.1,
    },
    {
      label: "Exam Start",
      url: "http://localhost:3002/sinav",
      delay: 1000,
      misMatchThreshold: 0.1,
    },
    {
      label: "Learning Path",
      url: "http://localhost:3002/learning-path",
      delay: 1500,
      misMatchThreshold: 0.1,
    },
    {
      label: "Question Bank",
      url: "http://localhost:3002/soru-bankasi",
      delay: 1000,
      misMatchThreshold: 0.1,
    },
    {
      label: "Student Profile",
      url: "http://localhost:3002/profil",
      delay: 1000,
      misMatchThreshold: 0.1,
    },
  ],
  paths: {
    bitmaps_reference: "backstop_data/bitmaps_reference",
    bitmaps_test: "backstop_data/bitmaps_test",
    engine_scripts: "backstop_data/engine_scripts",
    html_report: "backstop_data/html_report",
  },
  engine: "playwright",
  engineOptions: {
    browser: "chromium",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
    ],
  },
  asyncCaptureLimit: 3,
  asyncCompareLimit: 10,
  debug: false,
  debugWindow: false,
  report: ["browser", "json"],
  resembleOutputOptions: {
    errorColor: {
      red: 255,
      green: 0,
      blue: 255,
    },
    errorType: "movement",
    transparency: 0.3,
    ignoreAntialiasing: true,
  },
};
