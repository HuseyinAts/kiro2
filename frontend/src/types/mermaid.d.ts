/**
 * Type declarations for mermaid.js
 * Used by MermaidThoughtTree component
 */

declare module 'mermaid' {
  interface MermaidConfig {
    startOnLoad?: boolean
    theme?: 'default' | 'dark' | 'forest' | 'neutral' | 'base'
    securityLevel?: 'strict' | 'loose' | 'antiscript' | 'sandbox'
    flowchart?: {
      useMaxWidth?: boolean
      htmlLabels?: boolean
      curve?: 'basis' | 'linear' | 'cardinal'
      padding?: number
      nodeSpacing?: number
      rankSpacing?: number
      diagramPadding?: number
    }
    themeVariables?: Record<string, string>
  }

  interface RenderResult {
    svg: string
    bindFunctions?: (element: HTMLElement) => void
  }

  const mermaid: {
    initialize: (config: MermaidConfig) => void
    render: (id: string, text: string, callback?: (svg: string) => void) => Promise<RenderResult>
    parse: (text: string) => boolean
  };

  export default mermaid;
}
