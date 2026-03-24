from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from ..dependencies import get_review_manager
from knowledge_agent.review import (
    ReviewManager, QuizType, QuizDifficulty, ReviewMode
)


router = APIRouter(prefix="/api/review", tags=["review"])


class KnowledgeForReviewResponse(BaseModel):
    knowledge: Dict[str, Any]
    stats: Dict[str, Any]


class QuizGenerateRequest(BaseModel):
    knowledge_id: str
    quiz_type: str = "multiple_choice"
    difficulty: str = "medium"
    count: int = 3


class QuizData(BaseModel):
    id: str
    knowledge_id: str
    question: str
    quiz_type: str
    difficulty: str
    options: List[str] = []


class QuizAnswerRequest(BaseModel):
    quiz: QuizData
    user_answer: str
    correct_answer: str
    explanation: str = ""


class QuizResultResponse(BaseModel):
    is_correct: bool
    score: float
    feedback: str
    correct_answer: Optional[str] = None


class QuizResultData(BaseModel):
    quiz_id: str
    user_answer: str
    is_correct: bool
    score: float
    feedback: str


class ReviewRecordRequest(BaseModel):
    knowledge_id: str
    review_mode: str = "read"
    quiz_results: List[QuizResultData] = []
    review_duration: int = 0


class ReviewRecordResponse(BaseModel):
    id: str
    knowledge_id: str
    review_mode: str
    total_score: float
    mastery_level: int
    next_review_date: Optional[str]


class KnowledgeStatsResponse(BaseModel):
    knowledge_id: str
    total_reviews: int
    total_quiz_count: int
    correct_count: int
    average_score: float
    mastery_level: int
    last_reviewed_at: Optional[str]
    next_review_date: Optional[str]


class CatalogStatsResponse(BaseModel):
    catalog_id: str
    catalog_name: str
    total_knowledge: int
    reviewed_knowledge: int
    average_mastery: float


class ReviewSummaryResponse(BaseModel):
    total_knowledge: int
    reviewed_knowledge: int
    review_progress: float
    mastery_distribution: Dict[str, int]
    today_reviews: int
    total_reviews: int


@router.get("/knowledge", response_model=List[KnowledgeForReviewResponse])
async def get_knowledge_for_review(
    catalog_id: Optional[str] = Query(None, description="目录ID，不传则获取所有"),
    include_reviewed: bool = Query(True, description="是否包含已复习的知识"),
    manager: ReviewManager = Depends(get_review_manager)
):
    """获取待复习的知识列表"""
    knowledge_list = manager.get_knowledge_for_review(catalog_id, include_reviewed)
    return knowledge_list


@router.post("/quiz/generate")
async def generate_quiz(
    request: QuizGenerateRequest,
    manager: ReviewManager = Depends(get_review_manager)
):
    """生成习题"""
    try:
        quiz_type = QuizType(request.quiz_type)
    except ValueError:
        quiz_type = QuizType.MULTIPLE_CHOICE

    try:
        difficulty = QuizDifficulty(request.difficulty)
    except ValueError:
        difficulty = QuizDifficulty.MEDIUM

    quizzes = manager.generate_quiz(
        knowledge_id=request.knowledge_id,
        quiz_type=quiz_type,
        difficulty=difficulty,
        count=request.count
    )

    return {
        "quizzes": [
            {
                "id": q.id,
                "knowledge_id": q.knowledge_id,
                "question": q.question,
                "quiz_type": q.quiz_type.value,
                "difficulty": q.difficulty.value,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation
            }
            for q in quizzes
        ]
    }


@router.post("/quiz/generate/stream")
async def generate_quiz_stream(
    request: QuizGenerateRequest,
    manager: ReviewManager = Depends(get_review_manager)
):
    """流式生成习题"""
    try:
        quiz_type = QuizType(request.quiz_type)
    except ValueError:
        quiz_type = QuizType.MULTIPLE_CHOICE

    try:
        difficulty = QuizDifficulty(request.difficulty)
    except ValueError:
        difficulty = QuizDifficulty.MEDIUM

    def event_generator():
        for event in manager.generate_quiz_stream(
            knowledge_id=request.knowledge_id,
            quiz_type=quiz_type,
            difficulty=difficulty,
            count=request.count
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/quiz/evaluate", response_model=QuizResultResponse)
async def evaluate_quiz_answer(
    request: QuizAnswerRequest,
    manager: ReviewManager = Depends(get_review_manager)
):
    """评估习题答案"""
    from knowledge_agent.review.models import Quiz

    quiz = Quiz(
        id=request.quiz.id,
        knowledge_id=request.quiz.knowledge_id,
        question=request.quiz.question,
        quiz_type=QuizType(request.quiz.quiz_type),
        difficulty=QuizDifficulty(request.quiz.difficulty),
        options=request.quiz.options,
        correct_answer=request.correct_answer,
        explanation=request.explanation
    )

    result = manager.evaluate_answer(quiz, request.user_answer)

    response = QuizResultResponse(
        is_correct=result.is_correct,
        score=result.score,
        feedback=result.feedback
    )

    if not result.is_correct:
        response.correct_answer = request.correct_answer

    return response


@router.post("/record", response_model=ReviewRecordResponse)
async def record_review(
    request: ReviewRecordRequest,
    manager: ReviewManager = Depends(get_review_manager)
):
    """记录复习"""
    from knowledge_agent.review.models import QuizResult

    try:
        review_mode = ReviewMode(request.review_mode)
    except ValueError:
        review_mode = ReviewMode.READ

    quiz_results = [
        QuizResult(
            quiz_id=qr.quiz_id,
            user_answer=qr.user_answer,
            is_correct=qr.is_correct,
            score=qr.score,
            feedback=qr.feedback
        )
        for qr in request.quiz_results
    ]

    record = manager.record_review(
        knowledge_id=request.knowledge_id,
        review_mode=review_mode,
        quiz_results=quiz_results,
        review_duration=request.review_duration
    )

    return ReviewRecordResponse(
        id=record.id,
        knowledge_id=record.knowledge_id,
        review_mode=record.review_mode.value,
        total_score=record.total_score,
        mastery_level=record.mastery_level,
        next_review_date=record.next_review_date.isoformat() if record.next_review_date else None
    )


@router.get("/knowledge/{knowledge_id}/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats(
    knowledge_id: str,
    manager: ReviewManager = Depends(get_review_manager)
):
    """获取知识的复习统计"""
    stats = manager.get_knowledge_review_stats(knowledge_id)

    return KnowledgeStatsResponse(
        knowledge_id=stats.knowledge_id,
        total_reviews=stats.total_reviews,
        total_quiz_count=stats.total_quiz_count,
        correct_count=stats.correct_count,
        average_score=stats.average_score,
        mastery_level=stats.mastery_level,
        last_reviewed_at=stats.last_reviewed_at.isoformat() if stats.last_reviewed_at else None,
        next_review_date=stats.next_review_date.isoformat() if stats.next_review_date else None
    )


@router.get("/catalog/{catalog_id}/stats", response_model=CatalogStatsResponse)
async def get_catalog_stats(
    catalog_id: str,
    manager: ReviewManager = Depends(get_review_manager)
):
    """获取目录的复习统计"""
    stats = manager.get_catalog_review_stats(catalog_id)

    return CatalogStatsResponse(
        catalog_id=stats.catalog_id,
        catalog_name=stats.catalog_name,
        total_knowledge=stats.total_knowledge,
        reviewed_knowledge=stats.reviewed_knowledge,
        average_mastery=stats.average_mastery
    )


@router.get("/schedule")
async def get_review_schedule(
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    manager: ReviewManager = Depends(get_review_manager)
):
    """获取复习计划"""
    schedule = manager.get_review_schedule(days)
    return {"schedule": schedule}


@router.get("/summary", response_model=ReviewSummaryResponse)
async def get_review_summary(
    manager: ReviewManager = Depends(get_review_manager)
):
    """获取复习概览"""
    summary = manager.get_review_summary()

    return ReviewSummaryResponse(
        total_knowledge=summary["total_knowledge"],
        reviewed_knowledge=summary["reviewed_knowledge"],
        review_progress=summary["review_progress"],
        mastery_distribution={str(k): v for k, v in summary["mastery_distribution"].items()},
        today_reviews=summary["today_reviews"],
        total_reviews=summary["total_reviews"]
    )
