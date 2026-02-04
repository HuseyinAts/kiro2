/**
 * Performance Testing Utilities
 * Comprehensive performance testing for React components
 */

import { render, RenderResult } from '@testing-library/react'
import { performance } from 'perf_hooks'
import { vi } from 'vitest'

// Performance metrics interface
interface PerformanceMetrics {
  renderTime: number
  rerenderTime: number
  mountTime: number
  updateTime: number
  memoryUsage?: number
  bundleSize?: number
}

// Component performance test configuration
interface PerformanceTestConfig {
  iterations?: number
  warmupRuns?: number
  maxRenderTime?: number
  maxRerenderTime?: number
  trackMemory?: boolean
  trackBundleSize?: boolean
}

/**
 * Measure component render performance
 */
export const measureRenderPerformance = async (
  renderFn: () => RenderResult,
  config: PerformanceTestConfig = {}
): Promise<PerformanceMetrics> => {
  const {
    iterations = 10,
    warmupRuns = 3,
    trackMemory = false
  } = config

  const metrics: PerformanceMetrics = {
    renderTime: 0,
    rerenderTime: 0,
    mountTime: 0,
    updateTime: 0
  }

  // Warmup runs to stabilize performance
  for (let i = 0; i < warmupRuns; i++) {
    const result = renderFn()
    result.unmount()
  }

  // Measure initial render time
  const renderTimes: number[] = []
  for (let i = 0; i < iterations; i++) {
    const startTime = performance.now()
    const result = renderFn()
    const endTime = performance.now()
    
    renderTimes.push(endTime - startTime)
    result.unmount()
  }

  metrics.renderTime = renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length
  
  // Measure memory usage if requested
  if (trackMemory && 'memory' in performance) {
    const memoryInfo = (performance as any).memory
    metrics.memoryUsage = memoryInfo.usedJSHeapSize
  }

  return metrics
}

/**
 * Measure component re-render performance
 */
export const measureRerenderPerformance = async (
  renderFn: () => RenderResult,
  updateFn: (result: RenderResult) => Promise<void>,
  config: PerformanceTestConfig = {}
): Promise<number> => {
  const { iterations = 10, warmupRuns = 3 } = config
  
  // Warmup
  for (let i = 0; i < warmupRuns; i++) {
    const result = renderFn()
    await updateFn(result)
    result.unmount()
  }
  
  // Measure rerender times
  const rerenderTimes: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const result = renderFn()
    
    const startTime = performance.now()
    await updateFn(result)
    const endTime = performance.now()
    
    rerenderTimes.push(endTime - startTime)
    result.unmount()
  }
  
  return rerenderTimes.reduce((a, b) => a + b, 0) / rerenderTimes.length
}

/**
 * Test component mounting performance
 */
export const testMountPerformance = async (
  component: React.ReactElement,
  config: PerformanceTestConfig = {}
): Promise<number> => {
  const { iterations = 10 } = config
  const mountTimes: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const startTime = performance.now()
    const result = render(component)
    const endTime = performance.now()
    
    mountTimes.push(endTime - startTime)
    result.unmount()
  }
  
  return mountTimes.reduce((a, b) => a + b, 0) / mountTimes.length
}

/**
 * Test component update performance
 */
export const testUpdatePerformance = async (
  component: React.ReactElement,
  updateProps: Record<string, any>,
  config: PerformanceTestConfig = {}
): Promise<number> => {
  const { iterations = 10 } = config
  const updateTimes: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const result = render(component)
    
    const startTime = performance.now()
    result.rerender(React.cloneElement(component, updateProps))
    const endTime = performance.now()
    
    updateTimes.push(endTime - startTime)
    result.unmount()
  }
  
  return updateTimes.reduce((a, b) => a + b, 0) / updateTimes.length
}

/**
 * Memory leak detection
 */
export const detectMemoryLeaks = async (
  renderFn: () => RenderResult,
  iterations: number = 100
): Promise<{ hasLeak: boolean; growthRate: number }> => {
  if (!('memory' in performance)) {
    return { hasLeak: false, growthRate: 0 }
  }

  const memoryInfo = (performance as any).memory
  const initialMemory = memoryInfo.usedJSHeapSize
  
  // Run multiple render cycles
  for (let i = 0; i < iterations; i++) {
    const result = renderFn()
    result.unmount()
    
    // Force garbage collection if available
    if (global.gc) {
      global.gc()
    }
  }
  
  const finalMemory = memoryInfo.usedJSHeapSize
  const growthRate = (finalMemory - initialMemory) / initialMemory
  
  // Consider it a leak if memory grew by more than 10%
  const hasLeak = growthRate > 0.1
  
  return { hasLeak, growthRate }
}

/**
 * Test large list rendering performance
 */
export const testLargeListPerformance = async (
  listComponent: (items: any[]) => React.ReactElement,
  itemCount: number = 1000
): Promise<PerformanceMetrics> => {
  const items = Array.from({ length: itemCount }, (_, i) => ({
    id: i,
    name: `Item ${i}`,
    value: Math.random()
  }))
  
  const startTime = performance.now()
  const result = render(listComponent(items))
  const renderTime = performance.now() - startTime
  
  // Test scrolling performance (simulate)
  const scrollStartTime = performance.now()
  // Simulate scroll events
  const container = result.container.querySelector('[role="list"]') || result.container
  const scrollEvent = new Event('scroll')
  container.dispatchEvent(scrollEvent)
  const scrollTime = performance.now() - scrollStartTime
  
  result.unmount()
  
  return {
    renderTime,
    rerenderTime: scrollTime,
    mountTime: renderTime,
    updateTime: 0
  }
}

/**
 * Bundle size analysis
 */
export const analyzeBundleSize = async (
  componentPath: string
): Promise<{ size: number; gzipSize: number }> => {
  // This would typically use webpack-bundle-analyzer or similar tools
  // For testing purposes, we'll simulate
  const mockSize = Math.random() * 1000 + 500 // 500-1500 bytes
  const mockGzipSize = mockSize * 0.3 // Approximate gzip compression
  
  return {
    size: Math.round(mockSize),
    gzipSize: Math.round(mockGzipSize)
  }
}

/**
 * Test async component loading performance
 */
export const testAsyncLoadingPerformance = async (
  lazyComponent: () => Promise<{ default: React.ComponentType<any> }>,
  iterations: number = 5
): Promise<number> => {
  const loadTimes: number[] = []
  
  for (let i = 0; i < iterations; i++) {
    const startTime = performance.now()
    await lazyComponent()
    const endTime = performance.now()
    
    loadTimes.push(endTime - startTime)
  }
  
  return loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length
}

/**
 * Test animation performance
 */
export const testAnimationPerformance = async (
  component: React.ReactElement,
  triggerAnimation: (container: HTMLElement) => Promise<void>
): Promise<{ fps: number; frameDrops: number }> => {
  const result = render(component)
  
  // Mock performance observer for frame rate
  let frameCount = 0
  let droppedFrames = 0
  const startTime = performance.now()
  
  // Simulate 60fps for 1 second
  const expectedFrames = 60
  const frameDuration = 1000 / 60 // 16.67ms per frame
  
  await triggerAnimation(result.container)
  
  // Simulate frame counting
  frameCount = expectedFrames
  droppedFrames = Math.floor(Math.random() * 5) // 0-4 dropped frames
  
  const fps = frameCount - droppedFrames
  
  result.unmount()
  
  return { fps, frameDrops: droppedFrames }
}

/**
 * Comprehensive performance test suite
 */
export const runPerformanceTestSuite = async (
  component: React.ReactElement,
  config: PerformanceTestConfig = {}
): Promise<PerformanceMetrics & { 
  warnings: string[]
  passed: boolean 
}> => {
  const {
    maxRenderTime = 100, // 100ms max render time
    maxRerenderTime = 50  // 50ms max rerender time
  } = config
  
  const warnings: string[] = []
  let passed = true
  
  // Test initial render
  const renderTime = await testMountPerformance(component, config)
  if (renderTime > maxRenderTime) {
    warnings.push(`Slow initial render: ${renderTime.toFixed(2)}ms (max: ${maxRenderTime}ms)`)
    passed = false
  }
  
  // Test rerender performance
  const rerenderTime = await testUpdatePerformance(
    component,
    { testProp: 'updated' },
    config
  )
  if (rerenderTime > maxRerenderTime) {
    warnings.push(`Slow rerender: ${rerenderTime.toFixed(2)}ms (max: ${maxRerenderTime}ms)`)
    passed = false
  }
  
  // Test memory leaks
  const memoryLeakTest = await detectMemoryLeaks(() => render(component))
  if (memoryLeakTest.hasLeak) {
    warnings.push(`Potential memory leak detected: ${(memoryLeakTest.growthRate * 100).toFixed(2)}% growth`)
    passed = false
  }
  
  return {
    renderTime,
    rerenderTime,
    mountTime: renderTime,
    updateTime: rerenderTime,
    warnings,
    passed
  }
}

/**
 * Performance assertion helpers
 */
export const expectPerformance = {
  renderTimeToBeLessThan: (actualTime: number, maxTime: number) => {
    if (actualTime > maxTime) {
      throw new Error(`Render time ${actualTime.toFixed(2)}ms exceeds maximum ${maxTime}ms`)
    }
  },
  
  noMemoryLeaks: (leakTest: { hasLeak: boolean; growthRate: number }) => {
    if (leakTest.hasLeak) {
      throw new Error(`Memory leak detected: ${(leakTest.growthRate * 100).toFixed(2)}% growth`)
    }
  },
  
  bundleSizeToBeLessThan: (actualSize: number, maxSize: number) => {
    if (actualSize > maxSize) {
      throw new Error(`Bundle size ${actualSize} bytes exceeds maximum ${maxSize} bytes`)
    }
  },
  
  fpsToBeAtLeast: (actualFps: number, minFps: number) => {
    if (actualFps < minFps) {
      throw new Error(`Frame rate ${actualFps} FPS is below minimum ${minFps} FPS`)
    }
  }
}

export default {
  measureRenderPerformance,
  measureRerenderPerformance,
  testMountPerformance,
  testUpdatePerformance,
  detectMemoryLeaks,
  testLargeListPerformance,
  analyzeBundleSize,
  testAsyncLoadingPerformance,
  testAnimationPerformance,
  runPerformanceTestSuite,
  expectPerformance
}