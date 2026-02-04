import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { AgentSelector } from './AgentSelector'
import { Paper, Divider } from '@mui/material'
import { Clear, ExpandMore } from '@mui/icons-material'
import clsx from 'clsx'

export interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: string
  agentName?: string
  agentIcon?: string
}

interface AgentChatProps {
  className?: string
  showAgentSelector?: boolean
  defaultAgent?: string
}

export function AgentChat({ 
  className, 
  showAgentSelector = true,
  defaultAgent = 'study-buddy'
}: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedAgent, setSelectedAgent] = useState(defaultAgent)
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setIsTyping(true)

    try {
      // Simulate API call
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: selectedAgent,
          message: content,
          session_id: `session-${Date.now()}`
        })
      })

      const data = await response.json()

      // Add agent response
      setIsTyping(false)
      const agentMessage: Message = {
        id: `msg-${Date.now()}-agent`,
        role: 'agent',
        content: data.response || 'Merhaba! Size nasıl yardımcı olabilirim?',
        timestamp: new Date().toISOString(),
        agentName: data.agentName || 'AI Asistan',
        agentIcon: data.agentIcon || '🤖'
      }
      setMessages(prev => [...prev, agentMessage])
    } catch (error) {
      setIsTyping(false)
      console.error('Chat error:', error)
      
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        role: 'agent',
        content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.',
        timestamp: new Date().toISOString(),
        agentName: 'Sistem',
        agentIcon: '⚠️'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      {/* Agent Selector */}
      {showAgentSelector && (
        <>
          <AgentSelector
            agents={[]}
            selectedAgent={selectedAgent}
            onSelectAgent={setSelectedAgent}
          />
          <Divider className="my-4" />
        </>
      )}

      {/* Chat Container */}
      <Paper 
        elevation={0} 
        className="flex-1 flex flex-col bg-gray-50 rounded-lg overflow-hidden"
      >
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-800">AI Sohbet</h3>
            <p className="text-sm text-gray-500">
              {messages.length} mesaj
            </p>
          </div>
          
          <button
            onClick={clearChat}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Sohbeti Temizle"
          >
            <Clear className="text-gray-600" />
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <AnimatePresence initial={false}>
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center h-full text-gray-400"
              >
                <div className="text-6xl mb-4">💬</div>
                <p className="text-lg font-medium">Henüz mesaj yok</p>
                <p className="text-sm mt-2">
                  Bir soru sorarak başlayın!
                </p>
              </motion.div>
            ) : (
              <>
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    timestamp={message.timestamp}
                    agentName={message.agentName}
                    agentIcon={message.agentIcon}
                  />
                ))}
                
                {isTyping && (
                  <ChatMessage
                    role="agent"
                    content=""
                    timestamp={new Date().toISOString()}
                    agentName="AI Asistan"
                    agentIcon="🤖"
                    isTyping
                  />
                )}
              </>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          placeholder="Sorunuzu yazın..."
        />
      </Paper>
    </div>
  )
}

export default AgentChat