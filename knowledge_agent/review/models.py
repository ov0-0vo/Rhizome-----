from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class ReviewMode(Enum):
    READ = "read"
    QUIZ = "quiz"


class QuizType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"


class QuizDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Quiz:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = ""
    question: str = ""
    quiz_type: QuizType = QuizType.MULTIPLE_CHOICE
    difficulty: QuizDifficulty = QuizDifficulty.MEDIUM
    options: List[str] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuizResult:
    quiz_id: str = ""
    user_answer: str = ""
    is_correct: bool = False
    score: float = 0.0
    feedback: str = ""
    answered_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReviewRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_id: str = ""
    catalog_id: Optional[str] = None
    review_mode: ReviewMode = ReviewMode.READ
    review_duration: int = 0
    quiz_results: List[QuizResult] = field(default_factory=list)
    total_score: float = 0.0
    mastery_level: int = 0
    reviewed_at: datetime = field(default_factory=datetime.now)
    next_review_date: Optional[datetime] = None


@dataclass
class KnowledgeReviewStats:
    knowledge_id: str = ""
    total_reviews: int = 0
    total_quiz_count: int = 0
    correct_count: int = 0
    average_score: float = 0.0
    mastery_level: int = 0
    last_reviewed_at: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    review_history: List[ReviewRecord] = field(default_factory=list)


@dataclass
class CatalogReviewStats:
    catalog_id: str = ""
    catalog_name: str = ""
    total_knowledge: int = 0
    reviewed_knowledge: int = 0
    average_mastery: float = 0.0
    knowledge_stats: List[KnowledgeReviewStats] = field(default_factory=list)


EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30, 60, 120]

MASTERY_LEVELS = {
    0: {"name": "未学习", "color": "#gray"},
    1: {"name": "初学", "color": "#red"},
    2: {"name": "理解", "color": "#orange"},
    3: {"name": "熟悉", "color": "#yellow"},
    4: {"name": "掌握", "color": "#green"},
    5: {"name": "精通", "color": "#blue"},
}
