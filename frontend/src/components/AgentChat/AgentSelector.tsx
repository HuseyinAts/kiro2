import { motion } from 'framer-motion'
import { 
  School, 
  Psychology, 
  Quiz, 
  Timeline,
  AutoAwesome,
  TrendingUp
} from '@mui/icons-material'
import { Badge, Chip } from '@mui/material'
import clsx from 'clsx'

interface Agent {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  status: 'online' | 'offline' | 'busy'
  specialties: string[]
}

interface AgentSelectorProps {
  agents: Agent[]
  selectedAgent: string
  onSelectAgent: (agentId: string) => void
}

const defaultAgents: Agent[] = [
  {
    id: 'learning-path',
    name: 'Öğrenme Yolu Uzmanı',
    description: 'Kişiselleştirilmiş öğrenme rotaları oluşturur',
    icon: <Timeline />,
    status: 'online',
    specialties: ['Müfredat', 'Planlama', 'İlerleme']
  },
  {
    id: 'study-buddy',
    name: 'Çalışma Arkadaşı',
    description: 'Konuları anlamanıza yardımcı olur',
    icon: <School />,
    status: 'online',
    specialties: ['Açıklama', 'Örnekler', 'Pratik']
  },
  {
    id: 'quiz-master',
    name: 'Quiz Ustası',
    description: 'Test ve değerlendirmeler hazırlar',
    icon: <Quiz />,
    status: 'online',
    specialties: ['Test', 'Değerlendirme', 'Analiz']
  },
  {
    id: 'ai-tutor',
    name: 'AI Öğretmen',
    description: 'Derin öğrenme ve AI konularında uzman',
    icon: <Psychology />,
    status: 'online',
    specialties: ['AI', 'ML', 'Derin Öğrenme']
  },
  {
    id: 'motivation-coach',
    name: 'Motivasyon Koçu',
    description: 'Motivasyonunuzu yüksek tutar',
    icon: <AutoAwesome />,
    status: 'online',
    specialties: ['Motivasyon', 'Hedefler', 'Başarı']
  },
  {
    id: 'progress-analyst',
    name: 'İlerleme Analisti',
    description: 'İlerlemenizi analiz eder ve öneriler sunar',
    icon: <TrendingUp />,
    status: 'online',
    specialties: ['Analiz', 'Raporlama', 'Öneriler']
  }
]

export function AgentSelector({ 
  agents = defaultAgents, 
  selectedAgent, 
  onSelectAgent 
}: AgentSelectorProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500'
      case 'offline': return 'bg-gray-400'
      case 'busy': return 'bg-yellow-500'
      default: return 'bg-gray-400'
    }
  }

  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        AI Asistanlar
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {agents.map((agent) => (
          <motion.div
            key={agent.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <button
              onClick={() => onSelectAgent(agent.id)}
              className={clsx(
                'w-full p-4 rounded-xl border-2 transition-all duration-200',
                'hover:shadow-lg text-left relative overflow-hidden',
                selectedAgent === agent.id
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              )}
            >
              {/* Status Badge */}
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                variant="dot"
                sx={{
                  '& .MuiBadge-badge': {
                    backgroundColor: agent.status === 'online' ? '#10b981' : 
                                    agent.status === 'busy' ? '#f59e0b' : '#6b7280',
                    width: 12,
                    height: 12,
                    border: '2px solid white',
                    borderRadius: '50%',
                  }
                }}
              >
                <div className={clsx(
                  'w-12 h-12 rounded-lg flex items-center justify-center mb-3',
                  selectedAgent === agent.id
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600'
                )}>
                  {agent.icon}
                </div>
              </Badge>

              {/* Agent Info */}
              <h4 className="font-semibold text-gray-800 mb-1">
                {agent.name}
              </h4>
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                {agent.description}
              </p>

              {/* Specialties */}
              <div className="flex flex-wrap gap-1">
                {agent.specialties.slice(0, 3).map((specialty) => (
                  <Chip
                    key={specialty}
                    label={specialty}
                    size="small"
                    variant={selectedAgent === agent.id ? 'filled' : 'outlined'}
                    color={selectedAgent === agent.id ? 'primary' : 'default'}
                    className="text-xs"
                  />
                ))}
              </div>

              {/* Selection Indicator */}
              {selectedAgent === agent.id && (
                <motion.div
                  layoutId="selected-agent"
                  className="absolute inset-0 border-2 border-blue-500 rounded-xl pointer-events-none"
                  initial={false}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  )
}