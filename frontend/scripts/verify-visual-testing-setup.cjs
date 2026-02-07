#!/usr/bin/env node

/**
 * Visual Regression Testing Setup Verification Script
 *
 * Verifies BackstopJS installation and configuration
 */

const fs = require('fs');
const path = require('path');

const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';

function log(message, color = RESET) {
  console.log(`${color}${message}${RESET}`);
}

function checkFile(filePath, description) {
  const exists = fs.existsSync(filePath);
  if (exists) {
    log(`✓ ${description}`, GREEN);
    return true;
  } else {
    log(`✗ ${description} (Missing: ${filePath})`, RED);
    return false;
  }
}

function checkPackageJson() {
  const packagePath = path.join(process.cwd(), 'package.json');
  if (!fs.existsSync(packagePath)) {
    log('✗ package.json not found', RED);
    return false;
  }

  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));

  // Check devDependency
  const hasBackstop = packageJson.devDependencies?.backstopjs;
  if (hasBackstop) {
    log(`✓ backstopjs in devDependencies (${hasBackstop})`, GREEN);
  } else {
    log('✗ backstopjs not in devDependencies', RED);
    return false;
  }

  // Check scripts
  const requiredScripts = [
    'test:visual',
    'test:visual:approve',
    'test:visual:reference'
  ];

  let allScriptsPresent = true;
  requiredScripts.forEach(script => {
    if (packageJson.scripts?.[script]) {
      log(`✓ Script "${script}" defined`, GREEN);
    } else {
      log(`✗ Script "${script}" missing`, RED);
      allScriptsPresent = false;
    }
  });

  return allScriptsPresent;
}

function checkGitignore() {
  const gitignorePath = path.join(process.cwd(), '..', '.gitignore');
  if (!fs.existsSync(gitignorePath)) {
    log('⚠ .gitignore not found (optional)', YELLOW);
    return true;
  }

  const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');
  const requiredPatterns = [
    'backstop_data/bitmaps_test/',
    'backstop_data/html_report/'
  ];

  let allPatternsPresent = true;
  requiredPatterns.forEach(pattern => {
    if (gitignoreContent.includes(pattern)) {
      log(`✓ .gitignore includes "${pattern}"`, GREEN);
    } else {
      log(`⚠ .gitignore missing "${pattern}"`, YELLOW);
      allPatternsPresent = false;
    }
  });

  return allPatternsPresent;
}

function checkBackstopConfig() {
  const configPath = path.join(process.cwd(), 'backstop.config.cjs');
  if (!fs.existsSync(configPath)) {
    log('✗ backstop.config.cjs not found', RED);
    return false;
  }

  try {
    const config = require(configPath);

    // Check required properties
    const hasId = !!config.id;
    const hasViewports = Array.isArray(config.viewports) && config.viewports.length > 0;
    const hasScenarios = Array.isArray(config.scenarios) && config.scenarios.length > 0;
    const hasEngine = !!config.engine;

    if (hasId && hasViewports && hasScenarios && hasEngine) {
      log('✓ backstop.config.cjs is valid', GREEN);
      log(`  - ${config.scenarios.length} scenarios`, GREEN);
      log(`  - ${config.viewports.length} viewports`, GREEN);
      log(`  - Engine: ${config.engine}`, GREEN);
      return true;
    } else {
      log('✗ backstop.config.cjs is incomplete', RED);
      return false;
    }
  } catch (error) {
    log(`✗ Error loading backstop.config.cjs: ${error.message}`, RED);
    return false;
  }
}

// Main verification
console.log('\n=== Visual Regression Testing Setup Verification ===\n');

const checks = [
  checkFile(
    path.join(process.cwd(), 'backstop.config.cjs'),
    'backstop.config.cjs exists'
  ),
  checkFile(
    path.join(process.cwd(), 'VISUAL_TESTING.md'),
    'VISUAL_TESTING.md documentation exists'
  ),
  checkPackageJson(),
  checkBackstopConfig(),
  checkGitignore(),
];

console.log('\n=== Summary ===\n');

const passed = checks.filter(Boolean).length;
const total = checks.length;

if (passed === total) {
  log(`All ${total} checks passed! ✓`, GREEN);
  log('\nYou can now run:', GREEN);
  log('  npm install (if not already done)');
  log('  npm run dev (start dev server)');
  log('  npm run test:visual:reference (create baseline)');
  log('  npm run test:visual (run tests)');
  process.exit(0);
} else {
  log(`${passed}/${total} checks passed`, YELLOW);
  log('\nPlease fix the issues above before running visual tests.', RED);
  process.exit(1);
}
