from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import asyncio

from ..dependencies import get_state
from knowledge_agent.import_ import KnowledgeImporter

logger = logging.getLogger(__name__)

router = APIRouter()


class ImportResultResponse(BaseModel):
    success: bool
    total_sections: int
    imported_count: int
    skipped_count: int
    errors: List[str]
    imported_knowledge: List[Dict[str, Any]]


class TextImportRequest(BaseModel):
    content: str
    catalog_id: Optional[str] = None
    split_by: str = "paragraph"


@router.post("/file", response_model=ImportResultResponse)
async def import_file(
    file: UploadFile = File(...),
    catalog_id: Optional[str] = Form(None),
    auto_create_catalog: bool = Form(True),
    use_llm_analysis: bool = Form(False)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")
    
    if not file.filename.lower().endswith('.md'):
        raise HTTPException(status_code=400, detail="目前仅支持 .md 文件导入")
    
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text_content = content.decode('gbk')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="无法解析文件编码，请使用 UTF-8 编码")
    
    current_state = get_state()
    
    importer = KnowledgeImporter(
        knowledge_store=current_state.knowledge_store,
        catalog_manager=current_state.catalog_manager,
        qa_agent=current_state.qa_agent if use_llm_analysis else None
    )
    
    try:
        result = await asyncio.to_thread(
            importer.import_from_markdown,
            text_content,
            file.filename,
            catalog_id,
            auto_create_catalog,
            use_llm_analysis
        )
        
        if auto_create_catalog:
            current_state.catalog_manager.invalidate_cache()
        
        return ImportResultResponse(
            success=result.success,
            total_sections=result.total_sections,
            imported_count=result.imported_count,
            skipped_count=result.skipped_count,
            errors=result.errors,
            imported_knowledge=result.imported_knowledge
        )
    except Exception as e:
        logger.error(f"导入文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/text", response_model=ImportResultResponse)
async def import_text(request: TextImportRequest):
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    current_state = get_state()
    
    importer = KnowledgeImporter(
        knowledge_store=current_state.knowledge_store,
        catalog_manager=current_state.catalog_manager,
        qa_agent=None
    )
    
    try:
        result = await asyncio.to_thread(
            importer.import_from_text,
            request.content,
            request.catalog_id,
            request.split_by
        )
        
        return ImportResultResponse(
            success=result.success,
            total_sections=result.total_sections,
            imported_count=result.imported_count,
            skipped_count=result.skipped_count,
            errors=result.errors,
            imported_knowledge=result.imported_knowledge
        )
    except Exception as e:
        logger.error(f"导入文本失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/preview")
async def preview_file(
    file: UploadFile = File(...),
    max_sections: int = Query(10, ge=1, le=50)
):
    if not file.filename or not file.filename.lower().endswith('.md'):
        raise HTTPException(status_code=400, detail="仅支持 .md 文件预览")
    
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text_content = content.decode('gbk')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="无法解析文件编码")
    
    importer = KnowledgeImporter(
        knowledge_store=None,
        catalog_manager=None,
        qa_agent=None
    )
    
    try:
        sections = importer._parse_markdown_sections(text_content)
        
        preview_sections = []
        for section in sections[:max_sections]:
            preview_sections.append({
                "question": section.question,
                "answer": section.answer[:200] + "..." if len(section.answer) > 200 else section.answer,
                "section_path": section.section_path
            })
        
        return {
            "filename": file.filename,
            "total_sections": len(sections),
            "preview": preview_sections
        }
    except Exception as e:
        logger.error(f"预览文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
