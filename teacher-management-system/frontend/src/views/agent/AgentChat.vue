<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const messages = ref([])
const inputText = ref('')
const sessionId = ref('')
const loading = ref(false)
const chatContainer = ref(null)
const activeModule = ref('')
const gameActive = ref(false)
const showNext24 = ref(false)

const modules = [
  { key: 'business', name: '业务处理', desc: '课表·请假·考勤', icon: 'Document', color: '#8B4513' },
  { key: 'knowledge', name: '知识问答', desc: '规章·FAQ', icon: 'Collection', color: '#2E8B57' },
  { key: 'chat', name: '闲聊', desc: '谈古论今', icon: 'ChatLineRound', color: '#5F9EA0' },
  { key: 'game_24', name: '二十四点', desc: '4数算24', icon: 'Timer', color: '#B22222' },
  { key: 'game_riddle', name: '猜灯谜', desc: '文字游戏', icon: 'Sunny', color: '#DAA520' },
]

const tokenPreview = ref((localStorage.getItem('token') || '').substring(0, 8) + '...' || '无')

function moduleStyle(m) {
  const active = activeModule.value === m.key
  return {
    background: active ? m.color : '#F5E6D3',
    color: active ? '#fff' : m.color,
    borderColor: m.color,
  }
}

function scrollBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function addMessage(role, content, isLoading) {
  messages.value.push({ role, content, loading: !!isLoading })
  scrollBottom()
}

function updateLastBot(content) {
  const last = messages.value[messages.value.length - 1]
  if (last && last.role === 'assistant') {
    last.content = content
    last.loading = false
  }
  scrollBottom()
}

function parseSSE(rawText) {
  let text = ''
  for (const line of rawText.split('\n')) {
    // Strip \r (Windows line endings) and trim
    const clean = line.replace(/\r$/, '')
    if (clean.startsWith('data: ')) {
      const d = clean.slice(6)
      if (d === '[DONE]') continue
      try {
        const chunk = JSON.parse(d)
        if (chunk.type === 'text') text += chunk.content
        if (chunk.type === 'meta') {
          try {
            const meta = JSON.parse(chunk.content)
            if (meta.game_active === null && activeModule.value === 'game_riddle') {
              gameActive.value = true
            }
            if (meta.show_next_24) {
              showNext24.value = true
            }
          } catch {}
        }
      } catch (e) {
        // Ignore parse errors on individual lines
      }
    }
  }
  return text
}

async function doSend(text, isAuto) {
  if (!text && !isAuto) { ElMessage.warning('请输入内容'); return }
  if (loading.value) return

  const displayText = text || (isAuto ? `[${modules.find(m=>m.key===activeModule.value)?.name || ''}]` : '')
  addMessage('user', displayText)
  if (!isAuto) inputText.value = ''
  loading.value = true
  gameActive.value = false
  showNext24.value = false
  addMessage('assistant', '', true)

  try {
    const body = { message: text }
    if (sessionId.value) body.session_id = sessionId.value
    if (activeModule.value) body.module = activeModule.value

    const t = localStorage.getItem('token') || auth.token || ''
    if (!t) {
      updateLastBot('请先登录')
      loading.value = false
      return
    }
    const resp = await fetch('/api/v1/agent/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`,
      },
      body: JSON.stringify(body),
    })

    const sid = resp.headers.get('X-Session-Id')
    if (sid) sessionId.value = sid

    const rawText = await resp.text()

    // Check if response is a JSON error (our middleware returns HTTP 200 with error code in body)
    if (rawText.startsWith('{') && rawText.includes('"code"')) {
      try {
        const j = JSON.parse(rawText)
        if (j.code && j.code !== 200) {
          if (j.code === 401) {
            throw new Error('令牌已过期，请退出后重新登录')
          }
          throw new Error(j.message || `错误 ${j.code}`)
        }
      } catch (e) {
        if (e.message.includes('令牌') || e.message.includes('登录')) throw e
      }
    }

    const result = parseSSE(rawText)
    const display = result || rawText || ''
    if (!display) throw new Error('空响应')
    updateLastBot(display)
  } catch (e) {
    updateLastBot('出错：' + (e.message || '未知错误'))
  }
  loading.value = false
}

function handleSend() {
  doSend(inputText.value.trim())
}

async function selectModule(key) {
  if (loading.value) return
  if (activeModule.value === key) return

  activeModule.value = key
  sessionId.value = ''
  messages.value = []
  gameActive.value = false
  showNext24.value = false
  loading.value = false

  if (key === 'game_24' || key === 'game_riddle') {
    await doSend('', true)
  } else {
    const hints = {
      business: '主公请吩咐，查询课表、请假审批、考勤记录等，亮皆可处理。',
      knowledge: '主公有何疑问？学校规章制度、报名条件、联系方式等，亮尽知于心。',
      chat: '主公今日安好？亮愿陪主公谈古论今，畅叙幽情。',
    }
    addMessage('assistant', hints[key] || '请吩咐。')
  }
}

async function newSession() {
  if (loading.value) return
  sessionId.value = ''
  activeModule.value = ''
  messages.value = []
  gameActive.value = false
  showNext24.value = false
  loading.value = false
  try {
    const t = localStorage.getItem('token') || ''
    const resp = await fetch('/api/v1/agent/abilities', {
      headers: t ? { Authorization: `Bearer ${t}` } : {},
    })
    const data = await resp.json()
    addMessage('assistant', (data.data?.greeting) || '主公在上，亮在此恭候差遣。')
  } catch {
    addMessage('assistant', '主公在上，亮在此恭候差遣。')
  }
}

async function nextRiddle() {
  gameActive.value = false
  activeModule.value = 'game_riddle'
  addMessage('user', '[下一题]')
  loading.value = true
  addMessage('assistant', '', true)

  try {
    const t = auth.token || localStorage.getItem('token') || ''
    const resp = await fetch(`/api/v1/agent/riddle/next`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`,
      },
      body: JSON.stringify({ action: 'next', session_id: sessionId.value }),
    })
    const data = await resp.json()
    if (data.code === 200 && data.data) {
      updateLastBot(data.data.message || '主公请听新谜...')
    } else {
      updateLastBot('获取灯谜失败')
    }
  } catch (e) {
    updateLastBot('获取灯谜失败: ' + (e.message || ''))
  }
  loading.value = false
  scrollBottom()
}

async function next24() {
  showNext24.value = false
  activeModule.value = 'game_24'
  addMessage('user', '[下一题]')
  loading.value = true
  addMessage('assistant', '', true)

  try {
    const t = auth.token || localStorage.getItem('token') || ''
    const resp = await fetch('/api/v1/agent/game24/next', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${t}`,
      },
      body: JSON.stringify({ action: 'next', session_id: sessionId.value }),
    })
    const data = await resp.json()
    if (data.code === 200 && data.data) {
      updateLastBot(data.data.message || '主公请听新题...')
    } else {
      updateLastBot('获取题目失败')
    }
  } catch (e) {
    updateLastBot('获取题目失败: ' + (e.message || ''))
  }
  loading.value = false
  scrollBottom()
}

async function loadAbilities() {
  try {
    const t = localStorage.getItem('token') || ''
    const resp = await fetch('/api/v1/agent/abilities', {
      headers: t ? { Authorization: `Bearer ${t}` } : {},
    })
    const data = await resp.json()
    if (data.code === 200) {
      addMessage('assistant', data.data?.greeting || '主公在上，亮在此恭候差遣。')
    } else {
      addMessage('assistant', '主公在上，亮在此恭候差遣。(' + (data.message || '') + ')')
    }
  } catch (e) {
    addMessage('assistant', '主公在上，亮在此恭候差遣。(err:' + (e.message || '') + ')')
  }
}

function fmt(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
}

onMounted(loadAbilities)
</script>

<template>
  <div class="page-container" style="height:calc(100vh - 80px);display:flex;flex-direction:column">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
      <h2 class="page-title" style="margin-bottom:0;border:none">诸葛亮 · 智能助手</h2>
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:11px;color:var(--text-light)">Token:{{ tokenPreview }}</span>
        <el-button text type="warning" @click="newSession" :disabled="loading">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
      </div>
    </div>

    <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap">
      <el-button
        v-for="m in modules" :key="m.key"
        :style="moduleStyle(m)"
        :class="{ 'mod-active': activeModule === m.key }"
        size="small"
        @click="selectModule(m.key)"
        :disabled="loading"
      >
        <el-icon><component :is="m.icon" /></el-icon>
        <span style="margin-left:4px">{{ m.name }}</span>
      </el-button>
    </div>

    <div ref="chatContainer" class="chat-area">
      <div v-for="(msg, i) in messages" :key="i" style="margin-bottom:16px">
        <div v-if="msg.role === 'user'" style="display:flex;justify-content:flex-end">
          <div class="bubble-user">{{ msg.content }}</div>
        </div>
        <div v-else style="display:flex;gap:10px">
          <div class="avatar">🐉</div>
          <div class="bubble-bot">
            <div class="bot-content" v-html="fmt(msg.content)"></div>
            <span v-if="msg.loading" class="typing">▌</span>
          </div>
        </div>
      </div>

      <div v-if="gameActive" style="text-align:center;margin:12px 0">
        <el-button type="warning" @click="nextRiddle" :loading="loading">
          <el-icon><ArrowRight /></el-icon> 下一题
        </el-button>
      </div>

      <div v-if="showNext24" style="text-align:center;margin:12px 0">
        <el-button type="warning" @click="next24" :loading="loading">
          <el-icon><ArrowRight /></el-icon> 下一题
        </el-button>
      </div>
    </div>

    <div style="display:flex;gap:10px;margin-top:8px">
      <el-input
        v-model="inputText"
        placeholder="主公请吩咐..."
        size="large"
        @keyup.enter="handleSend"
        :disabled="loading"
      />
      <el-button type="primary" size="large" @click="handleSend" :loading="loading">发送</el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-area {
  flex: 1; overflow-y: auto; padding: 16px;
  background: #FFFCF5; border: 1px solid var(--border); border-radius: 8px;
}
.bubble-user {
  max-width: 70%; background: var(--primary); color: #fff;
  padding: 10px 16px; border-radius: 12px 12px 0 12px; font-size: 14px;
}
.avatar {
  width: 36px; height: 36px; background: var(--gold); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 18px;
}
.bubble-bot {
  max-width: 75%; background: #F5E6D3;
  padding: 10px 16px; border-radius: 0 12px 12px 12px; font-size: 14px; line-height: 1.8;
}
.bot-content { white-space: pre-wrap; }
.mod-active { font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.typing { animation: blink 1s infinite; color: var(--primary); }
</style>
