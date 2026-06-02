/**
 * TopicList Test Suite
 * DungeonMap yerine gelen sade konu listesi — kilit/ilerleme/soru sayısı +
 * tıklama davranışı. useDungeonMap mock'lanır.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { TopicList } from '../TopicList'
import { useDungeonMap, type LayoutNode } from '@/hooks/useDungeonMap'

vi.mock('@/hooks/useDungeonMap')
const mockedUseDungeonMap = vi.mocked(useDungeonMap)

const makeNode = (over: Partial<LayoutNode> = {}): LayoutNode => ({
  topic_id: 't1',
  code: 'C1',
  name_tr: 'Sayılar',
  parent_subject: 'MATEMATIK',
  prereqs_met: true,
  dag_depth: 0,
  progress: { attempt_count: 0, best_score: 0, last_score: 0, completed: false },
  question_count: 99,
  x: 0,
  y: 0,
  ...over,
})

const mockHook = (ret: Partial<ReturnType<typeof useDungeonMap>>) => {
  mockedUseDungeonMap.mockReturnValue({
    nodes: [],
    edges: [],
    theta: 0,
    loading: false,
    error: null,
    refetch: vi.fn(),
    ...ret,
  })
}

describe('TopicList', () => {
  beforeEach(() => vi.clearAllMocks())

  it('yükleniyor durumunda spinner gösterir', () => {
    mockHook({ loading: true })
    render(<TopicList subject="MATEMATIK" />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('konu yoksa boş mesaj gösterir', () => {
    mockHook({ nodes: [] })
    render(<TopicList subject="MATEMATIK" />)
    expect(screen.getByText(/henüz konu bulunamadı/i)).toBeInTheDocument()
  })

  it('açık konuya tıklayınca onNodeClick çağrılır + soru sayısı görünür', () => {
    const onNodeClick = vi.fn()
    mockHook({ nodes: [makeNode({ topic_id: 'open', name_tr: 'Sayılar', question_count: 99 })] })
    render(<TopicList subject="MATEMATIK" onNodeClick={onNodeClick} />)

    expect(screen.getByText('99 soru')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Sayılar'))
    expect(onNodeClick).toHaveBeenCalledTimes(1)
    expect(onNodeClick).toHaveBeenCalledWith(expect.objectContaining({ topic_id: 'open' }))
  })

  it('kilitli konu tıklanamaz (onNodeClick çağrılmaz) + Kilitli rozeti', () => {
    const onNodeClick = vi.fn()
    mockHook({ nodes: [makeNode({ topic_id: 'locked', name_tr: 'Türev', prereqs_met: false })] })
    render(<TopicList subject="MATEMATIK" onNodeClick={onNodeClick} />)

    expect(screen.getByText('Kilitli')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Türev'))
    expect(onNodeClick).not.toHaveBeenCalled()
  })

  it('tamamlanan konu "Tamamlandı" rozeti gösterir', () => {
    mockHook({
      nodes: [
        makeNode({
          name_tr: 'Polinomlar',
          progress: { attempt_count: 3, best_score: 90, last_score: 90, completed: true },
        }),
      ],
    })
    render(<TopicList subject="MATEMATIK" />)
    expect(screen.getByText('Tamamlandı')).toBeInTheDocument()
  })

  it('açık konular kilitli konulardan önce sıralanır', () => {
    mockHook({
      nodes: [
        makeNode({ topic_id: 'locked', name_tr: 'Türev', prereqs_met: false, dag_depth: 1 }),
        makeNode({ topic_id: 'open', name_tr: 'Sayılar', prereqs_met: true, dag_depth: 0 }),
      ],
    })
    render(<TopicList subject="MATEMATIK" />)
    const titles = screen.getAllByText(/Sayılar|Türev/).map((el) => el.textContent)
    expect(titles[0]).toBe('Sayılar') // açık olan üstte
  })
})
