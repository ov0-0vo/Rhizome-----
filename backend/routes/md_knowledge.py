from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from knowledge_agent.md_knowledge import md_knowledge_store
from knowledge_agent.md_knowledge.models import ProposalStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/md-knowledge", tags=["md-knowledge"])


class CreateDocumentRequest(BaseModel):
    title: str
    content: str
    path: str = ""
    tags: List[str] = []


class UpdateDocumentRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class CreateProposalRequest(BaseModel):
    document_id: str
    proposed_content: str
    description: str = ""


class ReviewProposalRequest(BaseModel):
    approve: bool
    comment: str = ""


@router.post("/documents")
async def create_document(request: CreateDocumentRequest):
    try:
        doc = md_knowledge_store.create_document(
            title=request.title,
            content=request.content,
            path=request.path,
            tags=request.tags
        )
        return {"success": True, "document": doc.to_dict()}
    except Exception as e:
        logger.error(f"创建文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/documents")
async def list_documents():
    try:
        docs = md_knowledge_store.get_all_documents()
        return {"documents": [doc.to_dict() for doc in docs]}
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    try:
        doc = md_knowledge_store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"document": doc.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.put("/documents/{doc_id}")
async def update_document(doc_id: str, request: UpdateDocumentRequest):
    try:
        doc = md_knowledge_store.update_document(
            doc_id=doc_id,
            title=request.title,
            content=request.content,
            tags=request.tags
        )
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"success": True, "document": doc.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        success = md_knowledge_store.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"success": True, "message": "文档已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/documents/search")
async def search_documents(query: str):
    try:
        docs = md_knowledge_store.search_documents(query)
        return {"documents": [doc.to_dict() for doc in docs]}
    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/proposals")
async def create_proposal(request: CreateProposalRequest):
    try:
        doc = md_knowledge_store.get_document(request.document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        proposal = md_knowledge_store.create_proposal(
            document_id=request.document_id,
            proposed_content=request.proposed_content,
            original_content=doc.content,
            description=request.description
        )
        return {"success": True, "proposal": proposal.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建修改提案失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/proposals")
async def list_proposals(status: Optional[str] = None):
    try:
        if status == "pending":
            proposals = md_knowledge_store.get_pending_proposals()
        else:
            proposals = md_knowledge_store.get_all_proposals()
        return {"proposals": [p.to_dict() for p in proposals]}
    except Exception as e:
        logger.error(f"获取提案列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    try:
        proposal = md_knowledge_store.get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="提案不存在")
        return {"proposal": proposal.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提案失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/proposals/{proposal_id}/review")
async def review_proposal(proposal_id: str, request: ReviewProposalRequest):
    try:
        proposal = md_knowledge_store.review_proposal(
            proposal_id=proposal_id,
            approve=request.approve,
            comment=request.comment
        )
        if not proposal:
            raise HTTPException(status_code=404, detail="提案不存在")
        return {
            "success": True,
            "proposal": proposal.to_dict(),
            "message": "已批准" if request.approve else "已拒绝"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"审核提案失败: {e}")
        raise HTTPException(status_code=500, detail=f"审核失败: {str(e)}")


@router.delete("/proposals/{proposal_id}")
async def delete_proposal(proposal_id: str):
    try:
        success = md_knowledge_store.delete_proposal(proposal_id)
        if not success:
            raise HTTPException(status_code=404, detail="提案不存在")
        return {"success": True, "message": "提案已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除提案失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/documents/{doc_id}/proposals")
async def get_document_proposals(doc_id: str):
    try:
        proposals = md_knowledge_store.get_proposals_by_document(doc_id)
        return {"proposals": [p.to_dict() for p in proposals]}
    except Exception as e:
        logger.error(f"获取文档提案失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/stats")
async def get_statistics():
    try:
        stats = md_knowledge_store.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
