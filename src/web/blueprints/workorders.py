# -*- coding: utf-8 -*-
"""
工单管理蓝图
处理工单相关的API路由
"""

import os
import pandas as pd
import logging
import uuid
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import text

logger = logging.getLogger(__name__)

# 简化的AI准确率配置类
class SimpleAIAccuracyConfig:
    """简化的AI准确率配置"""
    def __init__(self):
        self.auto_approve_threshold = 0.95
        self.use_human_resolution_threshold = 0.90
        self.manual_review_threshold = 0.80
        self.ai_suggestion_confidence = 0.95
        self.human_resolution_confidence = 0.90
    
    def should_auto_approve(self, similarity: float) -> bool:
        return similarity >= self.auto_approve_threshold
    
    def should_use_human_resolution(self, similarity: float) -> bool:
        return similarity < self.use_human_resolution_threshold
    
    def get_confidence_score(self, similarity: float, use_human: bool = False) -> float:
        if use_human:
            return self.human_resolution_confidence
        else:
            return max(similarity, self.ai_suggestion_confidence)

from src.main import Assistant
from src.core.database import db_manager
from src.core.models import WorkOrder, Conversation, WorkOrderSuggestion, KnowledgeEntry
from src.core.query_optimizer import query_optimizer
from src.web.service_manager import service_manager

workorders_bp = Blueprint('workorders', __name__, url_prefix='/api/workorders')

# 移除get_assistant函数，使用service_manager

def _ensure_workorder_template_file() -> str:
    """返回已有的模板xlsx路径；不做动态生成，避免运行时依赖问题"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    
    # 模板文件路径（项目根目录下的uploads）
    template_path = os.path.join(project_root, 'uploads', 'workorder_template.xlsx')
    
    # 确保目录存在
    uploads_dir = os.path.join(project_root, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    if not os.path.exists(template_path):
        # 尝试从其他可能的位置复制模板
        possible_locations = [
            os.path.join(project_root, 'uploads', 'workorder_template.xlsx'),
            os.path.join(current_dir, 'uploads', 'workorder_template.xlsx'),
            os.path.join(os.getcwd(), 'uploads', 'workorder_template.xlsx')
        ]
        
        source_found = False
        for source_path in possible_locations:
            if os.path.exists(source_path):
                try:
                    import shutil
                    shutil.copyfile(source_path, template_path)
                    source_found = True
                    break
                except Exception as e:
                    logger.warning(f"复制模板文件失败: {e}")
        
        if not source_found:
            # 自动生成一个最小可用模板
            try:
                import pandas as pd
                from pandas import DataFrame
                columns = ['标题', '描述', '分类', '优先级', '状态', '解决方案', '满意度']
                df: DataFrame = pd.DataFrame(columns=columns)
                df.to_excel(template_path, index=False)
                logger.info(f"自动生成模板文件: {template_path}")
            except Exception as gen_err:
                raise FileNotFoundError('模板文件缺失且自动生成失败，请检查依赖：openpyxl/pandas') from gen_err
    
    return template_path

@workorders_bp.route('')
def get_workorders():
    """获取工单列表（分页）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        
        # 从数据库获取分页数据
        from src.core.database import db_manager
        from src.core.models import WorkOrder
        
        with db_manager.get_session() as session:
            # 构建查询
            query = session.query(WorkOrder)
            
            # 应用过滤器
            if status_filter:
                query = query.filter(WorkOrder.status == status_filter)
            if priority_filter:
                query = query.filter(WorkOrder.priority == priority_filter)
            
            # 按创建时间倒序排列
            query = query.order_by(WorkOrder.created_at.desc())
            
            # 计算总数
            total = query.count()
            
            # 分页查询
            workorders = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # 转换为字典
            workorders_data = []
            for workorder in workorders:
                workorders_data.append({
                    'id': workorder.id,
                    'order_id': workorder.order_id,
                    'title': workorder.title,
                    'description': workorder.description,
                    'category': workorder.category,
                    'priority': workorder.priority,
                    'status': workorder.status,
                    'assignee': workorder.assignee,
                    'source': workorder.source,
                    'module': workorder.module,
                    'created_by': workorder.created_by,
                    'created_at': workorder.created_at.isoformat() if workorder.created_at else None,
                    'updated_at': workorder.updated_at.isoformat() if workorder.updated_at else None,
                    'date_of_close': workorder.date_of_close.isoformat() if workorder.date_of_close else None
                })
            
            # 计算分页信息
            total_pages = (total + per_page - 1) // per_page
            
            return jsonify({
                'workorders': workorders_data,
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('', methods=['POST'])
def create_workorder():
    """创建工单"""
    try:
        data = request.get_json()
        result = service_manager.get_assistant().create_work_order(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            priority=data['priority']
        )
        
        # 清除工单相关缓存
        from src.core.cache_manager import cache_manager
        cache_manager.clear()  # 清除所有缓存
        
        return jsonify({"success": True, "workorder": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/<int:workorder_id>')
def get_workorder_details(workorder_id):
    """获取工单详情（含数据库对话记录）"""
    try:
        with db_manager.get_session() as session:
            w = session.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
            if not w:
                return jsonify({"error": "工单不存在"}), 404
            convs = session.query(Conversation).filter(Conversation.work_order_id == w.id).order_by(Conversation.timestamp.asc()).all()
            conv_list = []
            for c in convs:
                conv_list.append({
                    "id": c.id,
                    "user_message": c.user_message,
                    "assistant_response": c.assistant_response,
                    "timestamp": c.timestamp.isoformat() if c.timestamp else None
                })
            # 在会话内构建工单数据
            workorder = {
                "id": w.id,
                "order_id": w.order_id,
                "title": w.title,
                "description": w.description,
                "category": w.category,
                "priority": w.priority,
                "status": w.status,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None,
                "resolution": w.resolution,
                "satisfaction_score": w.satisfaction_score,
                "conversations": conv_list
            }
            return jsonify(workorder)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/<int:workorder_id>', methods=['PUT'])
def update_workorder(workorder_id):
    """更新工单（写入数据库）"""
    try:
        data = request.get_json()
        if not data.get('title') or not data.get('description'):
            return jsonify({"error": "标题和描述不能为空"}), 400
        with db_manager.get_session() as session:
            w = session.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
            if not w:
                return jsonify({"error": "工单不存在"}), 404
            w.title = data.get('title', w.title)
            w.description = data.get('description', w.description)
            w.category = data.get('category', w.category)
            w.priority = data.get('priority', w.priority)
            w.status = data.get('status', w.status)
            w.resolution = data.get('resolution', w.resolution)
            w.satisfaction_score = data.get('satisfaction_score', w.satisfaction_score)
            w.updated_at = datetime.now()
            session.commit()
            
            # 清除工单相关缓存
            from src.core.cache_manager import cache_manager
            cache_manager.clear()  # 清除所有缓存
            
            updated = {
                "id": w.id,
                "title": w.title,
                "description": w.description,
                "category": w.category,
                "priority": w.priority,
                "status": w.status,
                "resolution": w.resolution,
                "satisfaction_score": w.satisfaction_score,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None
            }
            return jsonify({"success": True, "message": "工单更新成功", "workorder": updated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/<int:workorder_id>', methods=['DELETE'])
def delete_workorder(workorder_id):
    """删除工单"""
    try:
        with db_manager.get_session() as session:
            workorder = session.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
            if not workorder:
                return jsonify({"error": "工单不存在"}), 404
            
            # 先删除所有相关的子记录（按外键依赖顺序）
            # 1. 删除工单建议记录
            try:
                session.execute(text("DELETE FROM work_order_suggestions WHERE work_order_id = :id"), {"id": workorder_id})
            except Exception as e:
                print(f"删除工单建议记录失败: {e}")
            
            # 2. 删除对话记录
            session.query(Conversation).filter(Conversation.work_order_id == workorder_id).delete()
            
            # 3. 删除工单
            session.delete(workorder)
            session.commit()
            
            # 清除工单相关缓存
            from src.core.cache_manager import cache_manager
            cache_manager.clear()  # 清除所有缓存
            
            return jsonify({
                "success": True,
                "message": "工单删除成功"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/generate-ai-suggestion', methods=['POST'])
def generate_ai_suggestion():
    """通用AI建议生成API - 不需要先创建工单"""
    try:
        data = request.get_json()
        if not data or 'tr_description' not in data:
            return jsonify({"error": "缺少tr_description参数"}), 400

        tr_description = data['tr_description']
        vin = data.get('vin')
        process_history = data.get('process_history')

        # 使用AI建议服务生成建议
        from src.integrations.ai_suggestion_service import AISuggestionService
        ai_service = AISuggestionService()

        suggestion = ai_service.generate_suggestion(
            tr_description=tr_description,
            process_history=process_history,
            vin=vin
        )

        return jsonify({
            "success": True,
            "suggestion": suggestion,
            "message": "AI建议生成成功"
        })

    except Exception as e:
        logger.error(f"AI建议生成失败: {e}")
        return jsonify({"error": f"AI建议生成失败: {str(e)}"}), 500


@workorders_bp.route('/<int:workorder_id>/ai-suggestion', methods=['POST'])
def generate_workorder_ai_suggestion(workorder_id):
    """根据工单描述与知识库生成AI建议草稿"""
    try:
        with db_manager.get_session() as session:
            w = session.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
            if not w:
                return jsonify({"error": "工单不存在"}), 404
            # 调用知识库搜索与LLM生成
            # 使用问题描述（title）而不是处理过程（description）作为主要查询依据
            query = f"{w.title}"
            kb_results = service_manager.get_assistant().search_knowledge(query, top_k=3)
            kb_list = kb_results.get('results', []) if isinstance(kb_results, dict) else []
            # 组装提示词
            context = "\n".join([f"Q: {k.get('question','')}\nA: {k.get('answer','')}" for k in kb_list])
            from src.core.llm_client import QwenClient
            llm = QwenClient()
            prompt = f"请基于以下工单问题描述与知识库片段，给出简洁、可执行的处理建议。\n\n问题描述:\n{w.title}\n\n处理过程（仅供参考）:\n{w.description}\n\n知识库片段:\n{context}\n\n请直接输出建议文本："
            llm_resp = llm.chat_completion(messages=[{"role":"user","content":prompt}], temperature=0.3, max_tokens=800)
            suggestion = ""
            if llm_resp and 'choices' in llm_resp:
                suggestion = llm_resp['choices'][0]['message']['content']
            # 保存/更新草稿记录
            rec = session.query(WorkOrderSuggestion).filter(WorkOrderSuggestion.work_order_id == w.id).first()
            if not rec:
                rec = WorkOrderSuggestion(work_order_id=w.id, ai_suggestion=suggestion)
                session.add(rec)
            else:
                rec.ai_suggestion = suggestion
                rec.updated_at = datetime.now()
            session.commit()
            return jsonify({"success": True, "suggestion": suggestion})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/<int:workorder_id>/human-resolution', methods=['POST'])
def save_workorder_human_resolution(workorder_id):
    """保存人工描述，并计算与AI建议相似度；若≥95%可自动审批入库"""
    try:
        data = request.get_json() or {}
        human_text = data.get('human_resolution','').strip()
        if not human_text:
            return jsonify({"error":"人工描述不能为空"}), 400
        with db_manager.get_session() as session:
            w = session.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
            if not w:
                return jsonify({"error": "工单不存在"}), 404
            rec = session.query(WorkOrderSuggestion).filter(WorkOrderSuggestion.work_order_id == w.id).first()
            if not rec:
                rec = WorkOrderSuggestion(work_order_id=w.id)
                session.add(rec)
            rec.human_resolution = human_text
            # 计算语义相似度（使用sentence-transformers进行更准确的语义比较）
            try:
                from src.utils.semantic_similarity import calculate_semantic_similarity
                ai_text = rec.ai_suggestion or ""
                sim = calculate_semantic_similarity(ai_text, human_text)
                logger.info(f"AI建议与人工描述语义相似度: {sim:.4f}")
            except Exception as e:
                logger.error(f"计算语义相似度失败: {e}")
                # 回退到传统方法
                try:
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.metrics.pairwise import cosine_similarity
                    texts = [rec.ai_suggestion or "", human_text]
                    vec = TfidfVectorizer(max_features=1000)
                    mat = vec.fit_transform(texts)
                    sim = float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
                except Exception:
                    sim = 0.0
            rec.ai_similarity = sim
            
            # 使用简化的配置
            config = SimpleAIAccuracyConfig()
            
            # 自动审批条件
            approved = config.should_auto_approve(sim)
            rec.approved = approved
            
            # 记录使用人工描述入库的标记（当AI准确率低于阈值时）
            use_human_resolution = config.should_use_human_resolution(sim)
            rec.use_human_resolution = use_human_resolution
            
            session.commit()
            return jsonify({
                "success": True, 
                "similarity": sim, 
                "approved": approved,
                "use_human_resolution": use_human_resolution
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/<int:workorder_id>/approve-to-knowledge', methods=['POST'])
def approve_workorder_to_knowledge(workorder_id):
    """将已审批的AI建议或人工描述入库为知识条目"""
    try:
        with db_manager.get_session() as session:
            w = session.query(WorkOrder).filter(WorkOrder.id == workorder_id).first()
            if not w:
                return jsonify({"error": "工单不存在"}), 404
            
            rec = session.query(WorkOrderSuggestion).filter(WorkOrderSuggestion.work_order_id == w.id).first()
            if not rec:
                return jsonify({"error": "未找到工单建议记录"}), 400
            
            # 使用简化的配置
            config = SimpleAIAccuracyConfig()
            
            # 确定使用哪个内容入库
            if rec.use_human_resolution and rec.human_resolution:
                # AI准确率低于阈值，使用人工描述入库
                answer_content = rec.human_resolution
                confidence_score = config.get_confidence_score(rec.ai_similarity or 0, use_human=True)
                verified_by = 'human_resolution'
                logger.info(f"工单 {workorder_id} 使用人工描述入库，AI相似度: {rec.ai_similarity:.4f}")
            elif rec.approved and rec.ai_suggestion:
                # AI准确率≥阈值，使用AI建议入库
                answer_content = rec.ai_suggestion
                confidence_score = config.get_confidence_score(rec.ai_similarity or 0, use_human=False)
                verified_by = 'auto_approve'
                logger.info(f"工单 {workorder_id} 使用AI建议入库，相似度: {rec.ai_similarity:.4f}")
            else:
                return jsonify({"error": "未找到可入库的内容"}), 400
            
            # 入库为知识条目
            entry = KnowledgeEntry(
                question=w.title or (w.description[:20] if w.description else '工单问题'),
                answer=answer_content,
                category=w.category or '其他',
                confidence_score=confidence_score,
                is_active=True,
                is_verified=True,
                verified_by=verified_by,
                verified_at=datetime.now()
            )
            session.add(entry)
            session.commit()
            
            return jsonify({
                "success": True, 
                "knowledge_id": entry.id,
                "used_content": "human_resolution" if rec.use_human_resolution else "ai_suggestion",
                "confidence_score": confidence_score
            })
    except Exception as e:
        logger.error(f"入库知识库失败: {e}")
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/import', methods=['POST'])
def import_workorders():
    """导入Excel工单文件"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "没有选择文件"}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"error": "只支持Excel文件(.xlsx, .xls)"}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        upload_path = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(upload_path)
        
        # 解析Excel文件
        try:
            df = pd.read_excel(upload_path)
            imported_workorders = []
            
            # 处理每一行数据
            for index, row in df.iterrows():
                # 根据Excel列名映射到工单字段
                title = str(row.get('标题', row.get('title', f'导入工单 {index + 1}')))
                description = str(row.get('描述', row.get('description', '')))
                category = str(row.get('分类', row.get('category', '技术问题')))
                priority = str(row.get('优先级', row.get('priority', 'medium')))
                status = str(row.get('状态', row.get('status', 'open')))
                
                # 验证必填字段
                if not title or title.strip() == '':
                    continue
                
                # 生成唯一的工单ID
                timestamp = int(time.time())
                unique_id = str(uuid.uuid4())[:8]
                order_id = f"IMP_{timestamp}_{unique_id}"
                
                # 创建工单到数据库
                try:
                    with db_manager.get_session() as session:
                        workorder = WorkOrder(
                            order_id=order_id,
                            title=title,
                            description=description,
                            category=category,
                            priority=priority,
                            status=status,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        # 处理可选字段
                        if pd.notna(row.get('解决方案', row.get('resolution'))):
                            workorder.resolution = str(row.get('解决方案', row.get('resolution')))
                        
                        if pd.notna(row.get('满意度', row.get('satisfaction_score'))):
                            try:
                                workorder.satisfaction_score = int(row.get('满意度', row.get('satisfaction_score')))
                            except (ValueError, TypeError):
                                workorder.satisfaction_score = None
                        
                        session.add(workorder)
                        session.commit()
                        
                        logger.info(f"成功导入工单: {order_id} - {title}")
                        
                except Exception as db_error:
                    logger.error(f"导入工单到数据库失败: {db_error}")
                    continue
                
                # 添加到返回列表
                imported_workorders.append({
                    "id": workorder.id,
                    "order_id": workorder.order_id,
                    "title": workorder.title,
                    "description": workorder.description,
                    "category": workorder.category,
                    "priority": workorder.priority,
                    "status": workorder.status,
                    "created_at": workorder.created_at.isoformat() if workorder.created_at else None,
                    "updated_at": workorder.updated_at.isoformat() if workorder.updated_at else None,
                    "resolution": workorder.resolution,
                    "satisfaction_score": workorder.satisfaction_score
                })
            
            # 清理上传的文件
            os.remove(upload_path)
            
            return jsonify({
                "success": True,
                "message": f"成功导入 {len(imported_workorders)} 个工单",
                "imported_count": len(imported_workorders),
                "workorders": imported_workorders
            })
            
        except Exception as e:
            # 清理上传的文件
            if os.path.exists(upload_path):
                os.remove(upload_path)
            return jsonify({"error": f"解析Excel文件失败: {str(e)}"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/import/template')
def download_import_template():
    """下载工单导入模板"""
    try:
        template_path = _ensure_workorder_template_file()
        return jsonify({
            "success": True,
            "template_url": f"/uploads/workorder_template.xlsx"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workorders_bp.route('/import/template/file')
def download_import_template_file():
    """直接返回工单导入模板文件（下载）"""
    try:
        template_path = _ensure_workorder_template_file()
        
        # 检查文件是否存在
        if not os.path.exists(template_path):
            logger.error(f"模板文件不存在: {template_path}")
            return jsonify({"error": "模板文件不存在"}), 404
        
        # 检查文件大小
        file_size = os.path.getsize(template_path)
        if file_size == 0:
            logger.error(f"模板文件为空: {template_path}")
            return jsonify({"error": "模板文件为空"}), 500
        
        logger.info(f"准备下载模板文件: {template_path}, 大小: {file_size} bytes")
        
        try:
            # Flask>=2 使用 download_name
            return send_file(template_path, as_attachment=True, download_name='工单导入模板.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except TypeError:
            # 兼容 Flask<2 的 attachment_filename
            return send_file(template_path, as_attachment=True, attachment_filename='工单导入模板.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
    except Exception as e:
        logger.error(f"下载模板文件失败: {e}")
        return jsonify({"error": f"下载失败: {str(e)}"}), 500
