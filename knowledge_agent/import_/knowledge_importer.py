import re
import logging
import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "data" / "imported_documents"
DOCUMENTS_META_FILE = DOCUMENTS_DIR / "documents_meta.json"


@dataclass
class ParsedKnowledge:
    question: str
    answer: str
    keywords: List[str] = field(default_factory=list)
    section_path: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    success: bool
    total_sections: int = 0
    imported_count: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)
    imported_knowledge: List[Dict[str, Any]] = field(default_factory=list)
    document_id: Optional[str] = None


class DocumentManager:
    def __init__(self):
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.meta_file = DOCUMENTS_META_FILE
        self._ensure_meta_file()
    
    def _ensure_meta_file(self):
        if not self.meta_file.exists():
            with open(self.meta_file, 'w', encoding='utf-8') as f:
                json.dump({"documents": []}, f, ensure_ascii=False, indent=2)
    
    def _read_meta(self) -> Dict:
        with open(self.meta_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_meta(self, data: Dict):
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_document(self, filename: str, content: str, import_result: ImportResult) -> str:
        doc_id = str(uuid.uuid4())
        doc_file = DOCUMENTS_DIR / f"{doc_id}.md"
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        meta = self._read_meta()
        doc_meta = {
            "id": doc_id,
            "filename": filename,
            "original_filename": filename,
            "file_size": len(content),
            "imported_at": datetime.now().isoformat(),
            "imported_count": import_result.imported_count,
            "skipped_count": import_result.skipped_count,
            "total_sections": import_result.total_sections,
            "knowledge_ids": [k["id"] for k in import_result.imported_knowledge],
            "errors": import_result.errors[:5]
        }
        meta["documents"].append(doc_meta)
        self._write_meta(meta)
        
        return doc_id
    
    def get_all_documents(self) -> List[Dict]:
        meta = self._read_meta()
        return sorted(meta["documents"], key=lambda x: x["imported_at"], reverse=True)
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        meta = self._read_meta()
        for doc in meta["documents"]:
            if doc["id"] == doc_id:
                doc_file = DOCUMENTS_DIR / f"{doc_id}.md"
                if doc_file.exists():
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        doc["content"] = f.read()
                return doc
        return None
    
    def delete_document(self, doc_id: str) -> bool:
        meta = self._read_meta()
        for i, doc in enumerate(meta["documents"]):
            if doc["id"] == doc_id:
                doc_file = DOCUMENTS_DIR / f"{doc_id}.md"
                if doc_file.exists():
                    doc_file.unlink()
                meta["documents"].pop(i)
                self._write_meta(meta)
                return True
        return False
    
    def get_document_stats(self) -> Dict:
        meta = self._read_meta()
        docs = meta["documents"]
        return {
            "total_documents": len(docs),
            "total_knowledge": sum(d["imported_count"] for d in docs),
            "total_size": sum(d["file_size"] for d in docs)
        }


document_manager = DocumentManager()


class KnowledgeImporter:
    def __init__(self, knowledge_store, catalog_manager=None, qa_agent=None):
        self.knowledge_store = knowledge_store
        self.catalog_manager = catalog_manager
        self.qa_agent = qa_agent

    def import_from_markdown(
        self,
        content: str,
        filename: str = "",
        catalog_id: Optional[str] = None,
        auto_create_catalog: bool = True,
        use_llm_analysis: bool = True,
        save_document: bool = True
    ) -> ImportResult:
        result = ImportResult(success=True)
        
        try:
            sections = self._parse_markdown_sections(content)
            result.total_sections = len(sections)
            
            if not sections:
                result.errors.append("未找到有效的知识内容")
                result.success = False
                return result
            
            root_catalog_name = self._extract_root_name(filename, content)
            root_catalog_id = catalog_id
            
            if auto_create_catalog and not catalog_id and root_catalog_name:
                root_catalog_id = self._get_or_create_catalog(root_catalog_name)
            
            for section in sections:
                try:
                    knowledge_data = self._process_section(
                        section,
                        root_catalog_id,
                        root_catalog_name,
                        auto_create_catalog,
                        use_llm_analysis
                    )
                    
                    if knowledge_data:
                        item = self.knowledge_store.add_knowledge(
                            question=knowledge_data["question"],
                            answer=knowledge_data["answer"],
                            catalog_id=knowledge_data.get("catalog_id"),
                            keywords=knowledge_data.get("keywords", [])
                        )
                        result.imported_count += 1
                        result.imported_knowledge.append({
                            "id": item.id,
                            "question": item.question,
                            "catalog_id": item.catalog_id
                        })
                    else:
                        result.skipped_count += 1
                        logger.debug(f"跳过空内容章节: {section.question}")
                        
                except Exception as e:
                    logger.error(f"导入知识失败: {e}")
                    result.errors.append(str(e))
                    result.skipped_count += 1
            
            if save_document and result.imported_count > 0:
                result.document_id = document_manager.save_document(filename, content, result)
                    
        except Exception as e:
            logger.error(f"解析Markdown失败: {e}")
            result.errors.append(f"解析失败: {str(e)}")
            result.success = False
            
        return result

    def _parse_markdown_sections(self, content: str) -> List[ParsedKnowledge]:
        sections = []
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        current_path = []
        code_block = False
        code_lang = ""
        
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        code_start_pattern = re.compile(r'^```(\w*)$')
        code_end_pattern = re.compile(r'^```$')
        
        for line in lines:
            code_start_match = code_start_pattern.match(line)
            if code_start_match and not code_block:
                code_block = True
                code_lang = code_start_match.group(1)
                current_content.append(line)
                continue
                
            if code_end_pattern.match(line) and code_block:
                code_block = False
                code_lang = ""
                current_content.append(line)
                continue
                
            if code_block:
                current_content.append(line)
                continue
            
            heading_match = heading_pattern.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                if current_section and current_content:
                    answer = '\n'.join(current_content).strip()
                    if answer:
                        current_section.answer = answer
                        sections.append(current_section)
                    current_content = []
                
                current_path = current_path[:level-1]
                current_path.append(title)
                
                current_section = ParsedKnowledge(
                    question=title,
                    answer="",
                    section_path=current_path.copy()
                )
            else:
                if current_section:
                    current_content.append(line)
                elif line.strip():
                    if not current_section:
                        current_section = ParsedKnowledge(
                            question="概述",
                            answer="",
                            section_path=["概述"]
                        )
                    current_content.append(line)
        
        if current_section and current_content:
            answer = '\n'.join(current_content).strip()
            if answer:
                current_section.answer = answer
                sections.append(current_section)
        
        if not sections:
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            for i, para in enumerate(paragraphs):
                if len(para) > 20:
                    first_line = para.split('\n')[0][:50]
                    sections.append(ParsedKnowledge(
                        question=first_line if first_line else f"知识点 {i+1}",
                        answer=para,
                        section_path=["导入内容"]
                    ))
        
        return sections

    def _extract_root_name(self, filename: str, content: str) -> str:
        if filename:
            name = filename.rsplit('.', 1)[0]
            return name.replace('_', ' ').replace('-', ' ')
        
        first_heading = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if first_heading:
            return first_heading.group(1).strip()
        
        return "导入的知识"

    def _get_or_create_catalog(self, name: str, parent_id: str = None) -> str:
        if not self.catalog_manager:
            return None
            
        existing = self.catalog_manager.find_catalog_by_name(name, parent_id)
        if existing:
            return existing.id
        
        catalog = self.catalog_manager.create_catalog(
            name=name,
            keywords=[],
            parent_id=parent_id
        )
        return catalog.id

    def _process_section(
        self,
        section: ParsedKnowledge,
        root_catalog_id: Optional[str],
        root_catalog_name: str,
        auto_create_catalog: bool,
        use_llm_analysis: bool
    ) -> Optional[Dict[str, Any]]:
        if not section.answer or not section.answer.strip():
            return None
        
        question = section.question
        answer = section.answer.strip()
        keywords = section.keywords.copy() if section.keywords else []
        catalog_id = root_catalog_id
        
        if len(section.section_path) > 1 and auto_create_catalog and self.catalog_manager:
            parent_id = root_catalog_id
            for path_item in section.section_path[:-1]:
                catalog_id = self._get_or_create_catalog(path_item, parent_id)
                parent_id = catalog_id
        
        if use_llm_analysis and self.qa_agent:
            try:
                analysis = self._analyze_with_llm(question, answer)
                if analysis:
                    if analysis.get("improved_question"):
                        question = analysis["improved_question"]
                    if analysis.get("keywords"):
                        keywords = list(set(keywords + analysis["keywords"]))
                    if analysis.get("catalog_suggestion") and auto_create_catalog:
                        suggested_catalog = analysis["catalog_suggestion"]
                        if suggested_catalog != root_catalog_name:
                            catalog_id = self._get_or_create_catalog(suggested_catalog, root_catalog_id)
            except Exception as e:
                logger.warning(f"LLM分析失败: {e}")
        
        if not keywords:
            keywords = self._extract_keywords_from_text(question + " " + answer)
        
        return {
            "question": question,
            "answer": answer,
            "keywords": keywords[:10],
            "catalog_id": catalog_id
        }

    def _analyze_with_llm(self, question: str, answer: str) -> Optional[Dict[str, Any]]:
        if not self.qa_agent:
            return None
        
        try:
            prompt = f"""分析以下知识内容，提取关键信息：

标题：{question}
内容：{answer[:500]}

请以JSON格式返回：
{{
    "improved_question": "更清晰的问题表述（可选）",
    "keywords": ["关键词1", "关键词2"],
    "catalog_suggestion": "建议的分类目录名称"
}}

只返回JSON，不要其他内容。"""

            response = self.qa_agent.llm_non_streaming.invoke(prompt)
            content = response.content
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                import json
                return json.loads(json_match.group())
        except Exception as e:
            logger.debug(f"LLM分析异常: {e}")
        
        return None

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        keywords = []
        
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5]{2,4}')
        chinese_words = chinese_pattern.findall(text)
        keywords.extend(chinese_words[:5])
        
        english_pattern = re.compile(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b|\b[A-Z]{2,}\b')
        english_words = english_pattern.findall(text)
        keywords.extend(english_words[:3])
        
        tech_pattern = re.compile(r'\b(?:Python|JavaScript|Java|React|Vue|FastAPI|API|LLM|AI|ML|NLP|RAG)\b', re.IGNORECASE)
        tech_words = tech_pattern.findall(text)
        keywords.extend(tech_words[:3])
        
        return list(set(keywords))[:8]

    def import_from_text(
        self,
        content: str,
        catalog_id: Optional[str] = None,
        split_by: str = "paragraph"
    ) -> ImportResult:
        result = ImportResult(success=True)
        
        try:
            if split_by == "paragraph":
                chunks = [p.strip() for p in content.split('\n\n') if p.strip()]
            elif split_by == "line":
                chunks = [l.strip() for l in content.split('\n') if l.strip()]
            else:
                chunks = [content.strip()]
            
            result.total_sections = len(chunks)
            
            for i, chunk in enumerate(chunks):
                try:
                    question = f"知识点 {i+1}"
                    
                    first_line = chunk.split('\n')[0][:50]
                    if first_line and not first_line.startswith('#'):
                        question = first_line
                    
                    keywords = self._extract_keywords_from_text(chunk)
                    
                    item = self.knowledge_store.add_knowledge(
                        question=question,
                        answer=chunk,
                        catalog_id=catalog_id,
                        keywords=keywords
                    )
                    result.imported_count += 1
                    result.imported_knowledge.append({
                        "id": item.id,
                        "question": item.question
                    })
                except Exception as e:
                    result.errors.append(str(e))
                    result.skipped_count += 1
                    
        except Exception as e:
            result.errors.append(str(e))
            result.success = False
            
        return result
