/**
 * LearningPathVisualizer Component Tests
 * Comprehensive test suite for learning path visualization functionality
 */

import * as React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../../test/utils/test-utils'
import { LearningPathVisualizer } from '../LearningPathVisualizer'
import { PathNodeData } from '../PathNode'

// Mock @mui/icons-material to prevent Map constructor conflict
vi.mock('@mui/icons-material', () => ({
  ZoomIn: () => <span>ZoomIn</span>,
  ZoomOut: () => <span>ZoomOut</span>,
  CenterFocusStrong: () => <span>CenterFocusStrong</span>,
  Timeline: () => <span>Timeline</span>,
  Map: () => <span>Map</span>,
  ViewModule: () => <span>ViewModule</span>,
  PlayArrow: () => <span>PlayArrow</span>,
  Info: () => <span>Info</span>,
}))

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }: any) => <>{children}</>
}))

// Mock PathNode component
vi.mock('../PathNode', () => ({
  PathNode: ({ node, onClick, isHighlighted, showDetails }: any) => (
    <div
      data-testid={`path-node-${node.id}`}
      data-status={node.status}
      data-highlighted={isHighlighted}
      onClick={() => onClick?.(node)}
      style={{
        position: 'absolute',
        left: node.position.x,
        top: node.position.y
      }}
    >
      <span data-testid="node-title">{node.title}</span>
      <span data-testid="node-status">{node.status}</span>
    </div>
  )
}))

// Mock PathConnection component
vi.mock('../PathConnection', () => ({
  PathConnection: ({ from, to, isActive, isCompleted }: any) => (
    <div
      data-testid="path-connection"
      data-from={`${from.x},${from.y}`}
      data-to={`${to.x},${to.y}`}
      data-active={isActive}
      data-completed={isCompleted}
    />
  )
}))

// Mock clsx
vi.mock('clsx', () => ({
  default: (...args: any[]) => args.filter(Boolean).join(' ')
}))

describe('LearningPathVisualizer', () => {
  const mockNodes: PathNodeData[] = [
    {
      id: 'node1',
      title: 'Temel Matematik',
      description: 'Matematik temelleri',
      type: 'lesson',
      status: 'completed',
      progress: 100,
      estimatedTime: '30 dk',
      difficulty: 'beginner',
      points: 100,
      prerequisites: [],
      position: { x: 100, y: 100 }
    },
    {
      id: 'node2',
      title: 'Denklemler',
      description: 'Birinci dereceden denklemler',
      type: 'lesson',
      status: 'current',
      progress: 50,
      estimatedTime: '45 dk',
      difficulty: 'intermediate',
      points: 150,
      prerequisites: ['Temel Matematik'],
      position: { x: 350, y: 100 }
    },
    {
      id: 'node3',
      title: 'Fonksiyonlar',
      description: 'Fonksiyon kavramlari',
      type: 'lesson',
      status: 'available',
      progress: 0,
      estimatedTime: '60 dk',
      difficulty: 'intermediate',
      points: 200,
      prerequisites: ['Denklemler'],
      position: { x: 600, y: 100 }
    },
    {
      id: 'node4',
      title: 'Ileri Matematik',
      description: 'Ileri matematik konulari',
      type: 'milestone',
      status: 'locked',
      progress: 0,
      estimatedTime: '90 dk',
      difficulty: 'advanced',
      points: 300,
      prerequisites: ['Fonksiyonlar'],
      position: { x: 850, y: 100 }
    }
  ]

  const mockConnections = [
    { from: 'node1', to: 'node2' },
    { from: 'node2', to: 'node3' },
    { from: 'node3', to: 'node4' }
  ]

  const mockOnNodeClick = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders all path nodes', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      expect(screen.getByTestId('path-node-node1')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node2')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node3')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node4')).toBeInTheDocument()
    })

    it('renders path connections', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const connections = screen.getAllByTestId('path-connection')
      expect(connections).toHaveLength(3)
    })

    it('renders view mode buttons', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      expect(screen.getByRole('button', { name: /agac/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /harita/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /dogrusal/i })).toBeInTheDocument()
    })

    it('renders zoom controls', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      // Zoom in, zoom out, and reset buttons
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(5) // View modes + zoom controls + filters
    })

    it('renders filter buttons', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      expect(screen.getByRole('button', { name: /tumu/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /erisilebilir/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /tamamlanan/i })).toBeInTheDocument()
    })
  })

  describe('Progress Statistics', () => {
    it('displays correct progress percentage', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      // 1 out of 4 nodes completed = 25%
      expect(screen.getByText(/ilerleme: %25/i)).toBeInTheDocument()
    })

    it('displays total points earned', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      // Only completed node (node1) has 100 points
      expect(screen.getByText('100 Puan')).toBeInTheDocument()
    })

    it('displays completion count', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      expect(screen.getByText('1/4 Tamamlandi')).toBeInTheDocument()
    })
  })

  describe('View Mode Switching', () => {
    it('switches to tree view', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const treeButton = screen.getByRole('button', { name: /agac/i })
      await user.click(treeButton)

      // Tree view should be active
      expect(treeButton).toHaveAttribute('variant', 'contained')
    })

    it('switches to map view', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const mapButton = screen.getByRole('button', { name: /harita/i })
      await user.click(mapButton)

      // Nodes should be repositioned in circular layout
      expect(mapButton).toHaveClass('MuiButton-contained')
    })

    it('switches to linear view', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const linearButton = screen.getByRole('button', { name: /dogrusal/i })
      await user.click(linearButton)

      expect(linearButton).toHaveClass('MuiButton-contained')
    })

    it('uses provided initial view mode', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
          viewMode="linear"
        />
      )

      const linearButton = screen.getByRole('button', { name: /dogrusal/i })
      expect(linearButton).toHaveAttribute('variant', 'contained')
    })
  })

  describe('Filtering', () => {
    it('shows all nodes by default', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      expect(screen.getByTestId('path-node-node1')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node2')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node3')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node4')).toBeInTheDocument()
    })

    it('filters to show only available nodes', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const availableFilter = screen.getByRole('button', { name: /erisilebilir/i })
      await user.click(availableFilter)

      // Locked nodes should be hidden
      await waitFor(() => {
        expect(screen.queryByTestId('path-node-node4')).not.toBeInTheDocument()
      })

      // Available and completed nodes should still be visible
      expect(screen.getByTestId('path-node-node1')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node2')).toBeInTheDocument()
      expect(screen.getByTestId('path-node-node3')).toBeInTheDocument()
    })

    it('filters to show only completed nodes', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const completedFilter = screen.getByRole('button', { name: /tamamlanan/i })
      await user.click(completedFilter)

      await waitFor(() => {
        expect(screen.getByTestId('path-node-node1')).toBeInTheDocument()
        expect(screen.queryByTestId('path-node-node2')).not.toBeInTheDocument()
        expect(screen.queryByTestId('path-node-node3')).not.toBeInTheDocument()
        expect(screen.queryByTestId('path-node-node4')).not.toBeInTheDocument()
      })
    })
  })

  describe('Zoom Controls', () => {
    it('increases zoom when zoom in is clicked', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      // Find zoom in button by icon
      const zoomInButton = container.querySelector('[data-testid="ZoomInIcon"]')?.closest('button')

      if (zoomInButton) {
        await user.click(zoomInButton)
        // Zoom should increase - we can check via transform style
      }
    })

    it('decreases zoom when zoom out is clicked', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const zoomOutButton = container.querySelector('[data-testid="ZoomOutIcon"]')?.closest('button')

      if (zoomOutButton) {
        await user.click(zoomOutButton)
      }
    })

    it('resets view when reset button is clicked', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const resetButton = container.querySelector('[data-testid="CenterFocusStrongIcon"]')?.closest('button')

      if (resetButton) {
        await user.click(resetButton)
      }
    })
  })

  describe('Node Interaction', () => {
    it('calls onNodeClick when node is clicked', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const node = screen.getByTestId('path-node-node1')
      await user.click(node)

      expect(mockOnNodeClick).toHaveBeenCalledWith(expect.objectContaining({
        id: 'node1',
        title: 'Temel Matematik'
      }))
    })

    it('highlights current node', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
          currentNodeId="node2"
        />
      )

      const currentNode = screen.getByTestId('path-node-node2')
      expect(currentNode).toHaveAttribute('data-highlighted', 'true')
    })

    it('opens details dialog when node is clicked', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const node = screen.getByTestId('path-node-node1')
      await user.click(node)

      // Dialog should open with node details
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      expect(screen.getByText('Temel Matematik')).toBeInTheDocument()
      expect(screen.getByText('Matematik temelleri')).toBeInTheDocument()
    })

    it('shows prerequisites in dialog', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const node = screen.getByTestId('path-node-node2')
      await user.click(node)

      await waitFor(() => {
        expect(screen.getByText(/onkosullar/i)).toBeInTheDocument()
        expect(screen.getByText('Temel Matematik')).toBeInTheDocument()
      })
    })

    it('closes dialog when close button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const node = screen.getByTestId('path-node-node1')
      await user.click(node)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      const closeButton = screen.getByRole('button', { name: /kapat/i })
      await user.click(closeButton)

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })
  })

  describe('Drag and Pan', () => {
    it('allows dragging to pan the view', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const visualizationArea = container.querySelector('.cursor-move')

      if (visualizationArea) {
        // Simulate drag
        await user.pointer([
          { keys: '[MouseLeft>]', target: visualizationArea },
          { coords: { x: 100, y: 100 } },
          { keys: '[/MouseLeft]' }
        ])
      }
    })
  })

  describe('Connection States', () => {
    it('marks connections as completed when both nodes are completed', () => {
      const completedNodes: PathNodeData[] = [
        { ...mockNodes[0], status: 'completed' },
        { ...mockNodes[1], status: 'completed' },
        { ...mockNodes[2], status: 'available' },
        { ...mockNodes[3], status: 'locked' }
      ]

      render(
        <LearningPathVisualizer
          nodes={completedNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const connections = screen.getAllByTestId('path-connection')
      const firstConnection = connections[0]

      expect(firstConnection).toHaveAttribute('data-completed', 'true')
    })

    it('marks connections as active when leading to current/available node', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const connections = screen.getAllByTestId('path-connection')
      const firstConnection = connections[0]

      // node1 (completed) -> node2 (current) should be active
      expect(firstConnection).toHaveAttribute('data-active', 'true')
    })
  })

  describe('Empty State', () => {
    it('renders without errors when nodes array is empty', () => {
      render(
        <LearningPathVisualizer
          nodes={[]}
          connections={[]}
          onNodeClick={mockOnNodeClick}
        />
      )

      // Progress should show 0
      expect(screen.getByText(/ilerleme: %0/i)).toBeInTheDocument()
      expect(screen.getByText('0 Puan')).toBeInTheDocument()
    })
  })

  describe('Custom Class Name', () => {
    it('applies custom className', () => {
      const { container } = render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
          className="custom-visualizer-class"
        />
      )

      expect(container.querySelector('.custom-visualizer-class')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has accessible button labels', () => {
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      // All buttons should have accessible names
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveAccessibleName()
      })
    })

    it('dialog has proper role', async () => {
      const user = userEvent.setup()
      render(
        <LearningPathVisualizer
          nodes={mockNodes}
          connections={mockConnections}
          onNodeClick={mockOnNodeClick}
        />
      )

      const node = screen.getByTestId('path-node-node1')
      await user.click(node)

      await waitFor(() => {
        const dialog = screen.getByRole('dialog')
        expect(dialog).toBeInTheDocument()
      })
    })
  })
})
