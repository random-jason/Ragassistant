# -*- coding: utf-8 -*-
"""
知识库管理蓝图
处理知识库相关的API路由
"""

import os
import tempfile
import uuid
from flask import Blueprint, request, jsonify
from src.web.service_manager import service_manager
from src.web.error_handlers import handle_api_errors, create_error_response, create_success_response
from src.agent_assistant import AgentAssistant

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

def get_agent_assistant():
    """获取Agent助手实例（懒加载）"""
    global _agent_assistant
    if '_agent_assistant' not in globals():
        _agent_assistant = AgentAssistant()
    return _agent_assistant

@knowledge_bp.route('')
def get_knowledge():
    """获取知识库列表（分页）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category_filter = request.args.get('category', '')
        verified_filter = request.args.get('verified', '')
        
        # 从数据库获取知识库数据
        from src.core.database import db_manager
        from src.core.models import KnowledgeEntry
        
        with db_manager.get_session() as session:
            # 构建查询
            query = session.query(KnowledgeEntry).filter(KnowledgeEntry.is_active == True)
            
            # 应用过滤器
            if category_filter:
                query = query.filter(KnowledgeEntry.category == category_filter)
            if verified_filter:
                if verified_filter == 'true':
                    query = query.filter(KnowledgeEntry.is_verified == True)
                elif verified_filter == 'false':
                    query = query.filter(KnowledgeEntry.is_verified == False)
            
            # 按创建时间倒序排列
            query = query.order_by(KnowledgeEntry.created_at.desc())
            
            # 计算总数
            total = query.count()
            
            # 分页查询
            knowledge_entries = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典
            knowledge_data = []
            for entry in knowledge_entries:
                knowledge_data.append({
                    'id': entry.id,
                    'question': entry.question,
                    'answer': entry.answer,
                    'category': entry.category,
                    'confidence_score': entry.confidence_score,
                    'usage_count': entry.usage_count,
                    'is_verified': entry.is_verified,
                    'is_active': entry.is_active,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None,
                    'updated_at': entry.updated_at.isoformat() if entry.updated_at else None
                })
            
            # 计算分页信息
            total_pages = (total + per_page - 1) // per_page
            
            return jsonify({
                'knowledge': knowledge_data,
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/search')
def search_knowledge():
    """搜索知识库"""
    try:
        query = request.args.get('q', '')
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"搜索查询: '{query}'")
        
        if not query.strip():
            logger.info("查询为空，返回空结果")
            return jsonify([])
        
        # 直接调用知识库管理器的搜索方法
        assistant = service_manager.get_assistant()
        results = assistant.knowledge_manager.search_knowledge(query, top_k=5)
        logger.info(f"搜索结果数量: {len(results)}")
        return jsonify(results)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"搜索知识库失败: {e}")
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('', methods=['POST'])
def add_knowledge():
    """添加知识库条目"""
    try:
        data = request.get_json()
        success = service_manager.get_assistant().knowledge_manager.add_knowledge_entry(
            question=data['question'],
            answer=data['answer'],
            category=data['category'],
            confidence_score=data['confidence_score']
        )
        return jsonify({"success": success, "message": "知识添加成功" if success else "添加失败"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/stats')
def get_knowledge_stats():
    """获取知识库统计"""
    try:
        stats = service_manager.get_assistant().knowledge_manager.get_knowledge_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/upload', methods=['POST'])
def upload_knowledge_file():
    """上传文件并生成知识库"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "没有选择文件"}), 400
        
        # 保存文件到临时目录
        import tempfile
        import os
        import uuid
        
        # 创建唯一的临时文件名
        temp_filename = f"upload_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        try:
            # 保存文件
            file.save(temp_path)
            
            # 使用Agent助手处理文件
            result = get_agent_assistant().process_file_to_knowledge(temp_path, file.filename)
            
            return jsonify(result)
            
        finally:
            # 确保删除临时文件
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as cleanup_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"清理临时文件失败: {cleanup_error}")
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"文件上传处理失败: {e}")
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/delete/<int:knowledge_id>', methods=['DELETE'])
def delete_knowledge(knowledge_id):
    """删除知识库条目"""
    try:
        success = service_manager.get_assistant().knowledge_manager.delete_knowledge_entry(knowledge_id)
        return jsonify({"success": success, "message": "删除成功" if success else "删除失败"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/verify/<int:knowledge_id>', methods=['POST'])
def verify_knowledge(knowledge_id):
    """验证知识库条目"""
    try:
        data = request.get_json() or {}
        verified_by = data.get('verified_by', 'admin')
        success = service_manager.get_assistant().knowledge_manager.verify_knowledge_entry(knowledge_id, verified_by)
        return jsonify({"success": success, "message": "验证成功" if success else "验证失败"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/unverify/<int:knowledge_id>', methods=['POST'])
def unverify_knowledge(knowledge_id):
    """取消验证知识库条目"""
    try:
        success = service_manager.get_assistant().knowledge_manager.unverify_knowledge_entry(knowledge_id)
        return jsonify({"success": success, "message": "取消验证成功" if success else "取消验证失败"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
