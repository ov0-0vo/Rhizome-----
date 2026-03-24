import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import (
    Quiz, QuizResult, ReviewRecord, ReviewMode, QuizType, QuizDifficulty,
    KnowledgeReviewStats, CatalogReviewStats, EBBINGHAUS_INTERVALS, MASTERY_LEVELS
)
from ..knowledge.knowledge_store import KnowledgeStore
from ..knowledge.catalog_manager import CatalogManager
from ..knowledge.models import KnowledgeItem
from ..agent.qa_agent import QAAgent, create_llm

logger = logging.getLogger(__name__)


class ReviewStorage:
    def __init__(self, file_path: str = "data/review_records.json"):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save([])

    def _load(self) -> List[Dict]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, records: List[Dict]) -> None:
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def get_records_by_knowledge(self, knowledge_id: str) -> List[Dict]:
        records = self._load()
        return [r for r in records if r.get("knowledge_id") == knowledge_id]

    def get_all_records(self) -> List[Dict]:
        return self._load()

    def add_record(self, record: Dict) -> None:
        records = self._load()
        records.append(record)
        self._save(records)

    def get_records_by_catalog(self, catalog_id: str) -> List[Dict]:
        records = self._load()
        return [r for r in records if r.get("catalog_id") == catalog_id]


class ReviewManager:
    def __init__(
        self,
        knowledge_store: KnowledgeStore = None,
        catalog_manager: CatalogManager = None,
        qa_agent: QAAgent = None
    ):
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.catalog_manager = catalog_manager or CatalogManager()
        self.qa_agent = qa_agent or QAAgent(
            catalog_manager=self.catalog_manager,
            knowledge_store=self.knowledge_store
        )
        self.storage = ReviewStorage()

    def get_knowledge_for_review(
        self,
        catalog_id: Optional[str] = None,
        include_reviewed: bool = True
    ) -> List[Dict[str, Any]]:
        if catalog_id:
            all_ids = self.catalog_manager.get_all_descendant_ids(catalog_id)
            knowledge_list = []
            for cid in all_ids:
                knowledge_list.extend(self.knowledge_store.get_knowledge_by_catalog(cid))
        else:
            knowledge_list = self.knowledge_store.get_all_knowledge()

        result = []
        for k in knowledge_list:
            stats = self.get_knowledge_review_stats(k.id)
            needs_review = self._needs_review(stats)

            if not include_reviewed and stats.total_reviews > 0:
                continue

            result.append({
                "knowledge": k.to_dict() if hasattr(k, 'to_dict') else {
                    "id": k.id,
                    "question": k.question,
                    "answer": k.answer,
                    "keywords": k.keywords,
                    "catalog_id": k.catalog_id
                },
                "stats": {
                    "total_reviews": stats.total_reviews,
                    "mastery_level": stats.mastery_level,
                    "mastery_name": MASTERY_LEVELS.get(stats.mastery_level, {}).get("name", "未知"),
                    "last_reviewed": stats.last_reviewed_at.isoformat() if stats.last_reviewed_at else None,
                    "needs_review": needs_review
                }
            })

        result.sort(key=lambda x: (
            not x["stats"]["needs_review"],
            -(x["stats"]["mastery_level"] or 0)
        ))

        return result

    def _needs_review(self, stats: KnowledgeReviewStats) -> bool:
        if stats.total_reviews == 0:
            return True

        if stats.next_review_date:
            return datetime.now() >= stats.next_review_date

        return False

    def get_knowledge_review_stats(self, knowledge_id: str) -> KnowledgeReviewStats:
        records = self.storage.get_records_by_knowledge(knowledge_id)

        stats = KnowledgeReviewStats(knowledge_id=knowledge_id)
        stats.total_reviews = len(records)

        if records:
            total_score = 0
            total_quiz = 0
            correct = 0

            for r in records:
                quiz_results = r.get("quiz_results", [])
                for qr in quiz_results:
                    total_quiz += 1
                    if qr.get("is_correct"):
                        correct += 1
                    total_score += qr.get("score", 0)

                reviewed_at = r.get("reviewed_at")
                if reviewed_at:
                    reviewed_time = datetime.fromisoformat(reviewed_at)
                    if stats.last_reviewed_at is None or reviewed_time > stats.last_reviewed_at:
                        stats.last_reviewed_at = reviewed_time

                next_review = r.get("next_review_date")
                if next_review:
                    next_review_time = datetime.fromisoformat(next_review)
                    if stats.next_review_date is None or next_review_time < stats.next_review_date:
                        stats.next_review_date = next_review_time

            stats.total_quiz_count = total_quiz
            stats.correct_count = correct
            stats.average_score = total_score / total_quiz if total_quiz > 0 else 0
            stats.mastery_level = self._calculate_mastery_level(stats)

        return stats

    def _calculate_mastery_level(self, stats: KnowledgeReviewStats) -> int:
        if stats.total_reviews == 0:
            return 0

        score_factor = stats.average_score / 100 if stats.average_score > 0 else 0
        review_factor = min(stats.total_reviews / 5, 1.0)
        accuracy_factor = stats.correct_count / stats.total_quiz_count if stats.total_quiz_count > 0 else 0

        combined = (score_factor * 0.4 + review_factor * 0.3 + accuracy_factor * 0.3)
        level = int(combined * 5)

        return min(max(level, 1), 5)

    def generate_quiz(
        self,
        knowledge_id: str,
        quiz_type: QuizType = QuizType.MULTIPLE_CHOICE,
        difficulty: QuizDifficulty = QuizDifficulty.MEDIUM,
        count: int = 3
    ) -> List[Quiz]:
        knowledge = self.knowledge_store.get_knowledge(knowledge_id)
        if not knowledge:
            logger.warning(f"Knowledge not found: {knowledge_id}")
            return []

        quizzes = []
        for i in range(count):
            quiz = self._generate_single_quiz(knowledge, quiz_type, difficulty)
            if quiz:
                quizzes.append(quiz)

        return quizzes

    def _generate_single_quiz(
        self,
        knowledge: KnowledgeItem,
        quiz_type: QuizType,
        difficulty: QuizDifficulty
    ) -> Optional[Quiz]:
        prompt = self._build_quiz_prompt(knowledge, quiz_type, difficulty)

        try:
            llm = create_llm(streaming=False)
            response = llm.invoke(prompt)
            content = response.content

            quiz = self._parse_quiz_response(content, knowledge.id, quiz_type, difficulty)
            return quiz
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return None

    def _build_quiz_prompt(
        self,
        knowledge: KnowledgeItem,
        quiz_type: QuizType,
        difficulty: QuizDifficulty
    ) -> str:
        difficulty_desc = {
            QuizDifficulty.EASY: "简单（考查基本概念理解）",
            QuizDifficulty.MEDIUM: "中等（考查应用和理解）",
            QuizDifficulty.HARD: "困难（考查深入分析和综合应用）"
        }

        type_desc = {
            QuizType.MULTIPLE_CHOICE: "选择题（提供4个选项，标注正确答案）",
            QuizType.TRUE_FALSE: "判断题（判断对错，提供解释）",
            QuizType.SHORT_ANSWER: "简答题（需要简短回答）",
            QuizType.FILL_BLANK: "填空题（挖空关键概念）"
        }

        return f"""基于以下知识内容，生成一道{difficulty_desc[difficulty]}的{type_desc[quiz_type]}。

知识问题：{knowledge.question}
知识答案：{knowledge.answer}
关键词：{', '.join(knowledge.keywords) if knowledge.keywords else '无'}

请按以下JSON格式返回（不要包含其他内容）：
{{
    "question": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "正确答案（选择题填选项字母如'A'，判断题填'正确'或'错误'，简答题填参考答案，填空题填正确答案）",
    "explanation": "答案解析"
}}

注意：
1. 题目应该考查对知识点的理解，而不是死记硬背
2. 干扰选项应该有一定迷惑性
3. 解析要清晰说明为什么这个答案是对的
"""

    def _parse_quiz_response(
        self,
        content: str,
        knowledge_id: str,
        quiz_type: QuizType,
        difficulty: QuizDifficulty
    ) -> Optional[Quiz]:
        import json
        import re

        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return Quiz(
                    knowledge_id=knowledge_id,
                    question=data.get("question", ""),
                    quiz_type=quiz_type,
                    difficulty=difficulty,
                    options=data.get("options", []),
                    correct_answer=data.get("correct_answer", ""),
                    explanation=data.get("explanation", "")
                )
        except Exception as e:
            logger.error(f"Error parsing quiz response: {e}")

        return None

    def evaluate_answer(
        self,
        quiz: Quiz,
        user_answer: str
    ) -> QuizResult:
        is_correct = False
        score = 0.0
        feedback = ""

        if quiz.quiz_type == QuizType.MULTIPLE_CHOICE:
            is_correct = user_answer.upper() == quiz.correct_answer.upper()
            score = 100.0 if is_correct else 0.0
            feedback = f"正确答案是 {quiz.correct_answer}。\n{quiz.explanation}"

        elif quiz.quiz_type == QuizType.TRUE_FALSE:
            is_correct = user_answer == quiz.correct_answer
            score = 100.0 if is_correct else 0.0
            feedback = f"正确答案是「{quiz.correct_answer}」。\n{quiz.explanation}"

        elif quiz.quiz_type == QuizType.SHORT_ANSWER:
            result = self._evaluate_short_answer_with_llm(
                quiz.question, 
                user_answer, 
                quiz.correct_answer
            )
            is_correct = result["is_correct"]
            score = result["score"]
            feedback = result["feedback"]

        elif quiz.quiz_type == QuizType.FILL_BLANK:
            is_correct = user_answer.strip().lower() == quiz.correct_answer.strip().lower()
            score = 100.0 if is_correct else 0.0
            feedback = f"正确答案是「{quiz.correct_answer}」。\n{quiz.explanation}"

        return QuizResult(
            quiz_id=quiz.id,
            user_answer=user_answer,
            is_correct=is_correct,
            score=score,
            feedback=feedback
        )

    def _evaluate_short_answer_with_llm(
        self,
        question: str,
        user_answer: str,
        reference_answer: str
    ) -> Dict[str, Any]:
        prompt = f"""你是一位专业的知识评估老师。请评估学生的简答题答案。

题目：{question}

参考答案：{reference_answer}

学生答案：{user_answer}

请从以下几个方面评估：
1. 语义正确性：答案是否表达了正确的含义
2. 完整性：是否涵盖了关键知识点
3. 准确性：表述是否准确无误

请按以下JSON格式返回评估结果（不要包含其他内容）：
{{
    "score": <0-100的分数>,
    "is_correct": <true或false，60分以上为true>,
    "feedback": "<针对性的反馈，指出答案的优点和不足，以及如何改进>"
}}

注意：
- 同义词、近义词应视为正确
- 部分正确应给予部分分数
- 反馈要具体、有建设性
"""

        try:
            llm = create_llm(streaming=False)
            response = llm.invoke(prompt)
            content = response.content

            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "score": float(data.get("score", 0)),
                    "is_correct": bool(data.get("is_correct", False)),
                    "feedback": data.get("feedback", "")
                }
        except Exception as e:
            logger.error(f"Error evaluating short answer with LLM: {e}")

        similarity = self._calculate_similarity(user_answer, reference_answer)
        return {
            "score": similarity * 100,
            "is_correct": similarity >= 0.6,
            "feedback": f"参考答案：{reference_answer}\n（LLM评估失败，使用相似度计算）"
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def record_review(
        self,
        knowledge_id: str,
        review_mode: ReviewMode,
        quiz_results: List[QuizResult] = None,
        review_duration: int = 0
    ) -> ReviewRecord:
        knowledge = self.knowledge_store.get_knowledge(knowledge_id)

        record = ReviewRecord(
            knowledge_id=knowledge_id,
            catalog_id=knowledge.catalog_id if knowledge else None,
            review_mode=review_mode,
            review_duration=review_duration,
            quiz_results=quiz_results or []
        )

        if quiz_results:
            total_score = sum(qr.score for qr in quiz_results)
            record.total_score = total_score / len(quiz_results)
            record.mastery_level = self._calculate_mastery_from_score(record.total_score)

        record.next_review_date = self._calculate_next_review_date(record.mastery_level)

        record_dict = {
            "id": record.id,
            "knowledge_id": record.knowledge_id,
            "catalog_id": record.catalog_id,
            "review_mode": record.review_mode.value,
            "review_duration": record.review_duration,
            "quiz_results": [
                {
                    "quiz_id": qr.quiz_id,
                    "user_answer": qr.user_answer,
                    "is_correct": qr.is_correct,
                    "score": qr.score,
                    "feedback": qr.feedback,
                    "answered_at": qr.answered_at.isoformat()
                }
                for qr in record.quiz_results
            ],
            "total_score": record.total_score,
            "mastery_level": record.mastery_level,
            "reviewed_at": record.reviewed_at.isoformat(),
            "next_review_date": record.next_review_date.isoformat() if record.next_review_date else None
        }

        self.storage.add_record(record_dict)

        return record

    def _calculate_mastery_from_score(self, score: float) -> int:
        if score >= 90:
            return 5
        elif score >= 75:
            return 4
        elif score >= 60:
            return 3
        elif score >= 40:
            return 2
        else:
            return 1

    def _calculate_next_review_date(self, mastery_level: int) -> datetime:
        interval_index = min(mastery_level, len(EBBINGHAUS_INTERVALS) - 1)
        days = EBBINGHAUS_INTERVALS[interval_index]
        return datetime.now() + timedelta(days=days)

    def get_catalog_review_stats(self, catalog_id: str) -> CatalogReviewStats:
        catalog = self.catalog_manager.get_catalog(catalog_id)
        all_catalog_ids = self.catalog_manager.get_all_descendant_ids(catalog_id)

        all_knowledge = []
        for cid in all_catalog_ids:
            all_knowledge.extend(self.knowledge_store.get_knowledge_by_catalog(cid))

        stats = CatalogReviewStats(
            catalog_id=catalog_id,
            catalog_name=catalog.name if catalog else "未知目录",
            total_knowledge=len(all_knowledge)
        )

        reviewed_count = 0
        total_mastery = 0

        for k in all_knowledge:
            k_stats = self.get_knowledge_review_stats(k.id)
            stats.knowledge_stats.append(k_stats)

            if k_stats.total_reviews > 0:
                reviewed_count += 1
                total_mastery += k_stats.mastery_level

        stats.reviewed_knowledge = reviewed_count
        stats.average_mastery = total_mastery / reviewed_count if reviewed_count > 0 else 0

        return stats

    def get_review_schedule(self, days: int = 7) -> Dict[str, List[Dict]]:
        all_knowledge = self.knowledge_store.get_all_knowledge()
        schedule = {}

        for i in range(days):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            schedule[date] = []

        for k in all_knowledge:
            stats = self.get_knowledge_review_stats(k.id)

            if stats.next_review_date:
                date_str = stats.next_review_date.strftime("%Y-%m-%d")
                if date_str in schedule:
                    schedule[date_str].append({
                        "knowledge_id": k.id,
                        "question": k.question,
                        "mastery_level": stats.mastery_level,
                        "mastery_name": MASTERY_LEVELS.get(stats.mastery_level, {}).get("name", "未知")
                    })

        return schedule

    def get_review_summary(self) -> Dict[str, Any]:
        all_knowledge = self.knowledge_store.get_all_knowledge()
        all_records = self.storage.get_all_records()

        total_knowledge = len(all_knowledge)
        reviewed_knowledge = len(set(r.get("knowledge_id") for r in all_records))

        mastery_distribution = {i: 0 for i in range(6)}
        for k in all_knowledge:
            stats = self.get_knowledge_review_stats(k.id)
            mastery_distribution[stats.mastery_level] += 1

        today = datetime.now().strftime("%Y-%m-%d")
        today_reviews = len([r for r in all_records if r.get("reviewed_at", "").startswith(today)])

        return {
            "total_knowledge": total_knowledge,
            "reviewed_knowledge": reviewed_knowledge,
            "review_progress": reviewed_knowledge / total_knowledge if total_knowledge > 0 else 0,
            "mastery_distribution": mastery_distribution,
            "today_reviews": today_reviews,
            "total_reviews": len(all_records)
        }
