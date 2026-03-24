<template>
  <div class="review-view">
    <div class="review-header">
      <h2>📚 知识复习</h2>
      <div class="review-stats" v-if="summary">
        <div class="stat-card">
          <div class="stat-value">{{ summary.total_knowledge }}</div>
          <div class="stat-label">总知识</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ summary.reviewed_knowledge }}</div>
          <div class="stat-label">已复习</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ Math.round(summary.review_progress * 100) }}%</div>
          <div class="stat-label">进度</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ summary.today_reviews }}</div>
          <div class="stat-label">今日复习</div>
        </div>
      </div>
    </div>

    <div class="mastery-chart" v-if="summary">
      <h3>掌握度分布</h3>
      <div class="mastery-bars">
        <div class="mastery-bar" v-for="(count, level) in masteryDistribution" :key="level">
          <div class="mastery-label">{{ getMasteryName(parseInt(level)) }}</div>
          <div class="mastery-progress">
            <div 
              class="mastery-fill" 
              :style="{ 
                width: `${(count / summary.total_knowledge) * 100}%`,
                backgroundColor: getMasteryColor(parseInt(level))
              }"
            ></div>
          </div>
          <div class="mastery-count">{{ count }}</div>
        </div>
      </div>
    </div>

    <div class="review-content">
      <div class="knowledge-list-section">
        <div class="section-header">
          <h3>待复习知识</h3>
          <div class="filter-controls">
            <select v-model="selectedCatalogId" @change="loadKnowledgeForReview">
              <option :value="null">全部目录</option>
              <option v-for="catalog in catalogs" :key="catalog.id" :value="catalog.id">
                {{ catalog.name }}
              </option>
            </select>
            <label class="checkbox-label">
              <input type="checkbox" v-model="includeReviewed" @change="loadKnowledgeForReview">
              显示已复习
            </label>
          </div>
        </div>

        <div class="knowledge-list" v-if="knowledgeList.length > 0">
          <div 
            class="knowledge-item" 
            v-for="item in knowledgeList" 
            :key="item.knowledge.id"
            :class="{ selected: selectedKnowledge?.knowledge.id === item.knowledge.id }"
            @click="selectKnowledge(item)"
          >
            <div class="knowledge-info">
              <div class="knowledge-question">{{ item.knowledge.question }}</div>
              <div class="knowledge-meta">
                <span class="mastery-badge" :style="{ backgroundColor: getMasteryColor(item.stats.mastery_level) }">
                  {{ getMasteryName(item.stats.mastery_level) }}
                </span>
                <span class="review-count" v-if="item.stats.total_reviews > 0">
                  复习 {{ item.stats.total_reviews }} 次
                </span>
                <span class="needs-review" v-if="item.stats.needs_review">需复习</span>
              </div>
            </div>
          </div>
        </div>
        <div class="empty-state" v-else>
          <p>暂无待复习的知识</p>
        </div>
      </div>

      <div class="review-panel" v-if="selectedKnowledge">
        <div class="panel-header">
          <h3>{{ selectedKnowledge.knowledge.question }}</h3>
          <button class="close-btn" @click="selectedKnowledge = null">×</button>
        </div>

        <div class="mode-tabs">
          <button 
            class="mode-tab" 
            :class="{ active: reviewMode === 'read' }"
            @click="reviewMode = 'read'"
          >📖 阅读</button>
          <div class="quiz-type-group">
            <button 
              class="mode-tab" 
              :class="{ active: reviewMode === 'quiz' && selectedQuizType === 'multiple_choice' }"
              @click="startQuiz('multiple_choice')"
            >📝 选择题</button>
            <button 
              class="mode-tab" 
              :class="{ active: reviewMode === 'quiz' && selectedQuizType === 'short_answer' }"
              @click="startQuiz('short_answer')"
            >✍️ 简答题</button>
          </div>
        </div>

        <div class="panel-content">
          <div class="read-mode" v-if="reviewMode === 'read'">
            <div class="answer-section">
              <h4>答案</h4>
              <div class="answer-content" v-html="formatMarkdown(selectedKnowledge.knowledge.answer)"></div>
            </div>
            <div class="keywords-section" v-if="selectedKnowledge.knowledge.keywords?.length">
              <h4>关键词</h4>
              <div class="keywords">
                <span class="keyword" v-for="kw in selectedKnowledge.knowledge.keywords" :key="kw">
                  {{ kw }}
                </span>
              </div>
            </div>
            <div class="review-actions">
              <button class="btn-primary" @click="markAsRead">
                ✓ 标记为已复习
              </button>
            </div>
          </div>

          <div class="quiz-mode" v-else>
            <div class="quiz-loading" v-if="quizLoading">
              <div class="spinner"></div>
              <p>正在生成习题...</p>
            </div>

            <div class="quiz-container" v-else-if="currentQuiz">
              <div class="quiz-progress">
                题目 {{ currentQuizIndex + 1 }} / {{ quizzes.length }}
              </div>
              <div class="quiz-question">{{ currentQuiz.question }}</div>
              
              <div class="quiz-options" v-if="currentQuiz.quiz_type === 'multiple_choice'">
                <button 
                  class="quiz-option" 
                  v-for="(option, index) in currentQuiz.options" 
                  :key="index"
                  :class="{ 
                    selected: selectedAnswer === String.fromCharCode(65 + index),
                    correct: quizSubmitted && String.fromCharCode(65 + index) === currentQuiz.correct_answer,
                    wrong: quizSubmitted && selectedAnswer === String.fromCharCode(65 + index) && selectedAnswer !== currentQuiz.correct_answer
                  }"
                  :disabled="quizSubmitted"
                  @click="selectAnswer(String.fromCharCode(65 + index))"
                >
                  {{ String.fromCharCode(65 + index) }}. {{ option }}
                </button>
              </div>

              <div class="quiz-input" v-else-if="currentQuiz.quiz_type === 'short_answer'">
                <textarea 
                  v-model="selectedAnswer" 
                  placeholder="请输入你的答案..."
                  :disabled="quizSubmitted"
                ></textarea>
              </div>

              <div class="quiz-input" v-else-if="currentQuiz.quiz_type === 'fill_blank'">
                <input 
                  type="text" 
                  v-model="selectedAnswer" 
                  placeholder="请填写答案..."
                  :disabled="quizSubmitted"
                >
              </div>

              <div class="quiz-true-false" v-else-if="currentQuiz.quiz_type === 'true_false'">
                <button 
                  class="quiz-option tf-option"
                  :class="{ 
                    selected: selectedAnswer === '正确',
                    correct: quizSubmitted && currentQuiz.correct_answer === '正确',
                    wrong: quizSubmitted && selectedAnswer === '正确' && currentQuiz.correct_answer !== '正确'
                  }"
                  :disabled="quizSubmitted"
                  @click="selectAnswer('正确')"
                >✓ 正确</button>
                <button 
                  class="quiz-option tf-option"
                  :class="{ 
                    selected: selectedAnswer === '错误',
                    correct: quizSubmitted && currentQuiz.correct_answer === '错误',
                    wrong: quizSubmitted && selectedAnswer === '错误' && currentQuiz.correct_answer !== '错误'
                  }"
                  :disabled="quizSubmitted"
                  @click="selectAnswer('错误')"
                >✗ 错误</button>
              </div>

              <div class="quiz-feedback" v-if="quizSubmitted && quizResult">
                <div class="feedback-header" :class="{ correct: quizResult.is_correct, wrong: !quizResult.is_correct }">
                  {{ quizResult.is_correct ? '✓ 回答正确！' : '✗ 回答错误' }}
                </div>
                <div class="feedback-score">得分: {{ Math.round(quizResult.score) }}分</div>
                <div class="feedback-text">{{ quizResult.feedback }}</div>
              </div>

              <div class="quiz-actions">
                <button 
                  class="btn-primary" 
                  v-if="!quizSubmitted"
                  @click="submitAnswer"
                  :disabled="!selectedAnswer"
                >提交答案</button>
                <button 
                  class="btn-secondary" 
                  v-else-if="currentQuizIndex < quizzes.length - 1"
                  @click="nextQuiz"
                >下一题</button>
                <button 
                  class="btn-primary" 
                  v-else-if="quizSubmitted"
                  @click="finishQuiz"
                >完成测试</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { reviewApi, catalogApi } from '../api'
import { marked } from 'marked'

const summary = ref(null)
const knowledgeList = ref([])
const catalogs = ref([])
const selectedCatalogId = ref(null)
const includeReviewed = ref(true)
const selectedKnowledge = ref(null)
const reviewMode = ref('read')
const reviewStartTime = ref(null)
const selectedQuizType = ref('multiple_choice')

const quizzes = ref([])
const currentQuizIndex = ref(0)
const quizLoading = ref(false)
const quizSubmitted = ref(false)
const selectedAnswer = ref('')
const quizResult = ref(null)
const quizResults = ref([])

const currentQuiz = computed(() => quizzes.value[currentQuizIndex.value] || null)

const masteryDistribution = computed(() => {
  if (!summary.value) return {}
  return summary.value.mastery_distribution
})

const getMasteryName = (level) => {
  const names = ['未学习', '初学', '理解', '熟悉', '掌握', '精通']
  return names[level] || '未知'
}

const getMasteryColor = (level) => {
  const colors = ['#9ca3af', '#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6']
  return colors[level] || '#9ca3af'
}

const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

const loadSummary = async () => {
  try {
    const res = await reviewApi.getSummary()
    summary.value = res.data
  } catch (e) {
    console.error('Failed to load summary:', e)
  }
}

const loadCatalogs = async () => {
  try {
    const res = await catalogApi.getAll()
    catalogs.value = res.data
  } catch (e) {
    console.error('Failed to load catalogs:', e)
  }
}

const loadKnowledgeForReview = async () => {
  try {
    const res = await reviewApi.getKnowledgeForReview(selectedCatalogId.value, includeReviewed.value)
    knowledgeList.value = res.data
  } catch (e) {
    console.error('Failed to load knowledge:', e)
  }
}

const selectKnowledge = (item) => {
  selectedKnowledge.value = item
  reviewMode.value = 'read'
  reviewStartTime.value = Date.now()
  quizzes.value = []
  currentQuizIndex.value = 0
  quizResults.value = []
}

const startQuiz = async (quizType = 'multiple_choice') => {
  if (!selectedKnowledge.value) return
  
  selectedQuizType.value = quizType
  quizLoading.value = true
  reviewMode.value = 'quiz'
  quizzes.value = []
  currentQuizIndex.value = 0
  quizResults.value = []
  quizSubmitted.value = false
  selectedAnswer.value = ''
  quizResult.value = null

  try {
    const res = await reviewApi.generateQuiz(
      selectedKnowledge.value.knowledge.id,
      quizType,
      'medium',
      3
    )
    quizzes.value = res.data.quizzes
  } catch (e) {
    console.error('Failed to generate quiz:', e)
    alert('生成习题失败，请稍后重试')
    reviewMode.value = 'read'
  } finally {
    quizLoading.value = false
  }
}

const selectAnswer = (answer) => {
  if (!quizSubmitted.value) {
    selectedAnswer.value = answer
  }
}

const submitAnswer = async () => {
  if (!selectedAnswer.value || !currentQuiz.value) return

  try {
    const res = await reviewApi.evaluateQuiz(
      currentQuiz.value,
      selectedAnswer.value,
      currentQuiz.value.correct_answer,
      currentQuiz.value.explanation
    )
    quizResult.value = res.data
    quizSubmitted.value = true

    quizResults.value.push({
      quiz_id: currentQuiz.value.id,
      user_answer: selectedAnswer.value,
      is_correct: res.data.is_correct,
      score: res.data.score,
      feedback: res.data.feedback
    })
  } catch (e) {
    console.error('Failed to evaluate quiz:', e)
    alert('评估答案失败')
  }
}

const nextQuiz = () => {
  currentQuizIndex.value++
  quizSubmitted.value = false
  selectedAnswer.value = ''
  quizResult.value = null
}

const finishQuiz = async () => {
  const duration = Math.round((Date.now() - reviewStartTime.value) / 1000)

  try {
    await reviewApi.recordReview(
      selectedKnowledge.value.knowledge.id,
      'quiz',
      quizResults.value,
      duration
    )
    alert('复习完成！')
    selectedKnowledge.value = null
    loadSummary()
    loadKnowledgeForReview()
  } catch (e) {
    console.error('Failed to record review:', e)
    alert('记录复习失败')
  }
}

const markAsRead = async () => {
  const duration = Math.round((Date.now() - reviewStartTime.value) / 1000)

  try {
    await reviewApi.recordReview(
      selectedKnowledge.value.knowledge.id,
      'read',
      [],
      duration
    )
    alert('已标记为已复习')
    selectedKnowledge.value = null
    loadSummary()
    loadKnowledgeForReview()
  } catch (e) {
    console.error('Failed to record review:', e)
    alert('记录复习失败')
  }
}

onMounted(() => {
  loadSummary()
  loadCatalogs()
  loadKnowledgeForReview()
})
</script>

<style scoped>
.review-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.review-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}

.review-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: var(--bg-card);
  padding: 12px 20px;
  border-radius: var(--radius-lg);
  text-align: center;
  min-width: 80px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.mastery-chart {
  background: var(--bg-card);
  padding: 16px;
  border-radius: var(--radius-lg);
}

.mastery-chart h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.mastery-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mastery-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mastery-label {
  width: 50px;
  font-size: 12px;
  color: var(--text-secondary);
}

.mastery-progress {
  flex: 1;
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.mastery-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.mastery-count {
  width: 30px;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
}

.review-content {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
  overflow: hidden;
}

.knowledge-list-section {
  width: 350px;
  min-width: 300px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
}

.section-header h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--text-primary);
}

.filter-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-controls select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}

.knowledge-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.knowledge-item {
  padding: 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.knowledge-item:hover {
  background: var(--bg-hover);
}

.knowledge-item.selected {
  background: var(--primary-light);
  border-color: var(--primary-color);
}

.knowledge-question {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 8px;
}

.knowledge-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.mastery-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  color: white;
}

.review-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.needs-review {
  font-size: 11px;
  color: var(--primary-color);
  background: var(--primary-light);
  padding: 2px 6px;
  border-radius: 4px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.review-panel {
  flex: 1;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
  line-height: 1.4;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.mode-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-light);
}

.quiz-type-group {
  display: flex;
  flex: 1;
}

.mode-tab {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;
}

.mode-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.mode-tab.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.read-mode {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.answer-section h4,
.keywords-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.answer-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.answer-content :deep(p) {
  margin: 0 0 12px 0;
}

.answer-content :deep(ul),
.answer-content :deep(ol) {
  margin: 0 0 12px 0;
  padding-left: 20px;
}

.keywords {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.keyword {
  padding: 4px 12px;
  background: var(--bg-secondary);
  border-radius: 16px;
  font-size: 13px;
  color: var(--text-secondary);
}

.review-actions {
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

.btn-primary {
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--primary-color);
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: var(--bg-hover);
}

.quiz-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-light);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.quiz-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.quiz-progress {
  font-size: 13px;
  color: var(--text-secondary);
}

.quiz-question {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.5;
}

.quiz-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quiz-option {
  padding: 12px 16px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quiz-option:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: var(--primary-light);
}

.quiz-option.selected {
  border-color: var(--primary-color);
  background: var(--primary-light);
}

.quiz-option.correct {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.quiz-option.wrong {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.quiz-option:disabled {
  cursor: default;
}

.quiz-input textarea,
.quiz-input input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  resize: vertical;
}

.quiz-input textarea {
  min-height: 100px;
}

.quiz-true-false {
  display: flex;
  gap: 12px;
}

.tf-option {
  flex: 1;
  text-align: center;
}

.quiz-feedback {
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.feedback-header {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.feedback-header.correct {
  color: #22c55e;
}

.feedback-header.wrong {
  color: #ef4444;
}

.feedback-score {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.feedback-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
}

.quiz-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 768px) {
  .review-content {
    flex-direction: column;
  }

  .knowledge-list-section {
    width: 100%;
    min-width: auto;
    max-height: 300px;
  }

  .review-stats {
    flex-wrap: wrap;
  }

  .stat-card {
    min-width: 60px;
    padding: 8px 12px;
  }

  .stat-value {
    font-size: 18px;
  }
}
</style>
