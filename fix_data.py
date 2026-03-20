import json
import os

data_dir = 'data'
catalog_file = os.path.join(data_dir, 'catalog.json')
knowledge_file = os.path.join(data_dir, 'knowledge.json')

with open(catalog_file, 'r', encoding='utf-8') as f:
    catalog_data = json.load(f)

with open(knowledge_file, 'r', encoding='utf-8') as f:
    knowledge_data = json.load(f)

catalogs = {c['id']: c for c in catalog_data['catalogs']}

ai_keywords = ['AI', '机器学习', '深度学习', '神经网络', 'SFT', 'RLHF', 'LLM', 'NLP', 'RAG', 'GraphRAG', 'agent', '智能体', '人工智能', '监督微调']
ai_catalog_id = None

for c in catalog_data['catalogs']:
    if '机器学习' in c['name'] or '人工智能' in c['name']:
        ai_catalog_id = c['id']
        break

if not ai_catalog_id:
    print('未找到 AI 相关目录')
else:
    print(f'AI 目录 ID: {ai_catalog_id}')

fixed_count = 0
for item in knowledge_data['items']:
    if item['catalog_id'] is None:
        keywords = item.get('keywords', [])
        question = item.get('question', '')
        
        is_ai = any(any(ak.lower() in k.lower() for ak in ai_keywords) for k in keywords)
        is_ai = is_ai or any(ak.lower() in question.lower() for ak in ai_keywords)
        
        if is_ai and ai_catalog_id:
            item['catalog_id'] = ai_catalog_id
            if item['id'] not in catalogs[ai_catalog_id]['knowledge_items']:
                catalogs[ai_catalog_id]['knowledge_items'].append(item['id'])
            fixed_count += 1
            print(f"修复: {question[:30]}... -> 机器学习/人工智能")

with open(knowledge_file, 'w', encoding='utf-8') as f:
    json.dump(knowledge_data, f, ensure_ascii=False, indent=2)

with open(catalog_file, 'w', encoding='utf-8') as f:
    json.dump(catalog_data, f, ensure_ascii=False, indent=2)

print(f'\n修复完成! 共修复 {fixed_count} 条知识')
