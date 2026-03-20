"""
修复已有知识的目录关联
将 catalog_id 为 null 的知识重新匹配到合适的目录
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_agent.knowledge.catalog_manager import CatalogManager
from knowledge_agent.knowledge.knowledge_store import KnowledgeStore
from knowledge_agent.config import config


def fix_knowledge_catalogs():
    catalog_manager = CatalogManager()
    knowledge_store = KnowledgeStore()
    
    all_knowledge = knowledge_store.get_all_knowledge()
    catalogs = catalog_manager.get_all_catalogs()
    
    print(f"总知识数: {len(all_knowledge)}")
    print(f"总目录数: {len(catalogs)}")
    
    fixed_count = 0
    
    for item in all_knowledge:
        if item.catalog_id is None:
            print(f"\n处理知识: {item.question[:50]}...")
            
            keywords = item.keywords or []
            matched_catalog = None
            
            for catalog in catalogs:
                score = 0
                for kw in keywords:
                    if kw.lower() in [k.lower() for k in catalog.keywords]:
                        score += 1
                    if kw.lower() in catalog.name.lower():
                        score += 2
                
                if score > 0:
                    if matched_catalog is None or score > matched_catalog[1]:
                        matched_catalog = (catalog, score)
            
            if matched_catalog:
                catalog, score = matched_catalog
                print(f"  -> 匹配到目录: {catalog.name} (得分: {score})")
                
                item.catalog_id = catalog.id
                knowledge_store.json_storage.update_item(item)
                catalog_manager.add_knowledge_to_catalog(catalog.id, item.id)
                fixed_count += 1
            else:
                domain_keywords = {
                    "人工智能": ["AI", "机器学习", "深度学习", "神经网络", "SFT", "RLHF", "LLM", "NLP", "RAG", "GraphRAG", "agent", "智能体"],
                    "编程": ["Python", "代码", "编程", "函数", "变量", "语法", "算法"],
                }
                
                matched_domain = None
                for domain, d_keywords in domain_keywords.items():
                    for kw in keywords:
                        if any(dk.lower() in kw.lower() or kw.lower() in dk.lower() for dk in d_keywords):
                            matched_domain = domain
                            break
                    if matched_domain:
                        break
                
                if matched_domain:
                    for catalog in catalogs:
                        if matched_domain in catalog.name:
                            print(f"  -> 根据领域匹配到目录: {catalog.name}")
                            item.catalog_id = catalog.id
                            knowledge_store.json_storage.update_item(item)
                            catalog_manager.add_knowledge_to_catalog(catalog.id, item.id)
                            fixed_count += 1
                            break
                    else:
                        print(f"  -> 创建新目录: {matched_domain}")
                        new_catalog = catalog_manager.create_catalog(
                            name=matched_domain,
                            keywords=keywords
                        )
                        item.catalog_id = new_catalog.id
                        knowledge_store.json_storage.update_item(item)
                        catalog_manager.add_knowledge_to_catalog(new_catalog.id, item.id)
                        fixed_count += 1
                else:
                    print(f"  -> 未找到匹配目录，跳过")
    
    print(f"\n修复完成! 共修复 {fixed_count} 条知识")


if __name__ == "__main__":
    fix_knowledge_catalogs()
