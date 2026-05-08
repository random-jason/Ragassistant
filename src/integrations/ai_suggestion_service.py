# -*- coding: utf-8 -*-
"""
AI建议服务
基于工单描述和知识库生成AI建议
"""

import logging
from typing import Dict, List, Optional, Any
from src.knowledge_base.knowledge_manager import KnowledgeManager
from src.config.unified_config import get_config  # 使用统一配置管理器

logger = logging.getLogger(__name__)

class AISuggestionService:
    """AI建议服务"""
    
    def __init__(self):
        self.knowledge_manager = KnowledgeManager()

        # 从统一配置管理器获取LLM配置
        self.llm_config = get_config().llm
        logger.info(f"使用LLM配置: {self.llm_config.provider} - {self.llm_config.model}")
    
    def generate_suggestion(self, tr_description: str, process_history: Optional[str] = None, existing_ai_suggestion: Optional[str] = None, context: str = "realtime_chat") -> str:
        """
        生成AI建议 - 根据不同上下文使用不同的提示词

        Args:
            tr_description: 工单描述
            process_history: 处理过程记录（可选，用于了解当前问题状态）
            existing_ai_suggestion: 现有的AI建议（可选，用于判断是否是首次建议）
            context: 调用上下文，"realtime_chat" 或 "feishu_sync"

        Returns:
            AI建议文本
        """
        try:
            # 调用实时对话接口生成建议
            from ..dialogue.realtime_chat import RealtimeChatManager
            
            chat_manager = RealtimeChatManager()
            
            # 判断是否是首次建议（通过检查现有AI建议）
            is_first_suggestion = True
            if existing_ai_suggestion and existing_ai_suggestion.strip():
                is_first_suggestion = False
            
            # 构建上下文信息
            context_info = ""
            if process_history and process_history.strip():
                context_info = f"""
                
已处理的步骤：
{process_history}"""
            
            # 根据是否为首次建议，设置不同的提示词
            if is_first_suggestion:
                # 首次建议：只给出一般性的排查步骤，不要提进站抓取日志
                suggestion_instruction = """要求：
1. 首次给客户建议，只提供远程可操作的一般性排查步骤
2. 如检查网络、重启系统、确认配置等常见操作
3. 绝对不要提到"进站"、"抓取日志"等需要线下操作的内容
4. 语言简洁精炼，用逗号连接，不要用序号或分行"""
            else:
                # 后续建议：如果已有处理记录但未解决，可以考虑更深入的方案
                suggestion_instruction = """要求：
1. 基于已有处理步骤，给出下一步的排查建议
2. 如果远程操作都无法解决，可以考虑更深入的诊断方案
3. 语言简洁精炼，用逗号连接，不要用序号或分行"""
            
            # 根据上下文选择不同的提示词构建方法
            if context == "feishu_sync":
                user_message = self._build_feishu_sync_prompt(tr_description, process_history, vin, existing_ai_suggestion, is_first_suggestion)
            else:
                user_message = self._build_realtime_chat_prompt(tr_description, process_history, is_first_suggestion)
            
            # 创建会话
            session_id = chat_manager.create_session("ai_suggestion_service")
            
            # 调用实时对话接口
            response = chat_manager.process_message(session_id, user_message)
            
            if response and "content" in response:
                content = response["content"]
                
                # 记录原始内容用于调试
                logger.info(f"AI生成原始内容: {content[:100]}...")
                
                # 二次处理：替换默认建议（在清理前先替换）
                content = self._post_process_suggestion(content, is_first_suggestion)
                
                # 清理并限制长度
                cleaned = self._clean_response(content)
                
                # 再次检查，确保替换生效
                cleaned = self._post_process_suggestion(cleaned, is_first_suggestion)
                
                # 记录清理后的内容
                logger.info(f"AI建议清理后: {cleaned[:100]}...")
                
                return cleaned
            else:
                logger.error(f"AI建议生成失败，response内容: {response}")
                return "AI建议生成失败，无法获取有效响应。"
                
        except Exception as e:
            logger.error(f"生成AI建议失败: {e}")
            return f"AI建议生成失败：{str(e)}"
    
    def _clean_response(self, content: str) -> str:
        """
        清理AI建议内容，使其简洁
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的简洁内容（只做基本清理，保留原意）
        """
        if not content or not content.strip():
            return ""
        
        # 移除多余的格式和提示词
        cleaned = content.strip()
        
        # 如果内容很短，直接返回
        if len(cleaned) < 10:
            return cleaned
        
        # 移除常见的提示词开头（只移除一个）
        prefixes = ["建议您", "您可以", "请尝试", "建议先", "建议"]
        
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                # 移除前缀，保留后面的内容
                cleaned = cleaned[len(prefix):].strip()
                if cleaned.startswith(('，', '。', '：', ':')):
                    cleaned = cleaned[1:].strip()
                break  # 只处理第一个匹配的前缀
        
        # 处理多行内容：只取第一段有效内容
        lines = cleaned.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            # 跳过空行
            if not line:
                continue
            
            # 跳过明显的提示词行
            if any(p in line for p in ["请按照", "要求", "示例", "问题描述", "相关背景"]):
                continue
            
            # 检查是否以序号开头（如"1.", "一、", "1017:"等）
            if len(line) > 2 and line[0].isdigit() and line[1] in ['.', '、', '：', ':']:
                # 提取序号后的内容
                for sep in ['. ', '、', '：', ':']:
                    if sep in line:
                        content_part = line.split(sep, 1)[1].strip()
                        if content_part and len(content_part) > 5:  # 确保内容有意义
                            filtered_lines.append(content_part)
                        break
            else:
                filtered_lines.append(line)
            
            # 如果已经有有效内容，停止处理
            if filtered_lines:
                break
        
        # 合并内容
        if filtered_lines:
            cleaned = filtered_lines[0]  #移除逗号分隔，只取第一段
        else:
            # 如果没有找到有效行，使用原来的第一行
            cleaned = lines[0].strip() if lines and lines[0].strip() else cleaned
        
        # 限制长度在150字以内，确保精炼
        if len(cleaned) > 150:
            # 尝试在标点符号处截断
            truncated = cleaned[:150]
            for punct in ['。', '；', '，', '.', ';', ',']:
                pos = truncated.rfind(punct)
                if pos > 100:  # 在100字之后找到标点，保留更多内容
                    cleaned = truncated[:pos + 1]
                    break
            else:
                cleaned = truncated
        
        return cleaned
    
    def _post_process_suggestion(self, content: str, is_first_suggestion: bool = True) -> str:
        """
        二次处理建议内容：替换默认建议文案
        
        Args:
            content: 清理后的内容
            is_first_suggestion: 是否是首次建议
            
        Returns:
            处理后的内容
        """
        if not content or not content.strip():
            return content
        
        result = content
        
        # 如果是首次建议，移除所有"进站"、"抓取日志"相关的内容
        if is_first_suggestion:
            # 移除进站相关的文案
            station_keywords = [
                "进站", "抓取日志", "邀请用户进站", "建议邀请用户进站",
                "建议进站", "需要进站", "前往服务站", "联系售后", "售后技术支持"
            ]
            for keyword in station_keywords:
                if keyword in result:
                    # 找到包含关键词的句子并移除
                    lines = result.split('，')
                    new_lines = [line for line in lines if keyword not in line]
                    result = '，'.join(new_lines)
                    logger.info(f"首次建议，移除包含'{keyword}'的内容")
        else:
            # 非首次建议：替换"联系售后技术支持"为"邀请用户进站抓取日志分析"
            replacements = [
                ("建议联系售后技术支持进一步排查", "建议邀请用户进站抓取日志分析"),
                ("联系售后技术支持进行进一步排查", "邀请用户进站抓取日志分析"),
                ("建议联系售后技术支持", "建议邀请用户进站抓取日志分析"),
                ("联系售后技术支持", "邀请用户进站抓取日志分析"),
                ("如问题仍未解决，建议联系售后技术支持进行进一步排查", "如问题仍未解决，建议邀请用户进站抓取日志分析"),
                ("若仍无效，建议联系售后技术支持进一步排查", "若仍无效，建议邀请用户进站抓取日志分析"),
                ("仍无效，建议联系售后技术支持", "仍无效，建议邀请用户进站抓取日志分析"),
            ]
            
            for old_text, new_text in replacements:
                if old_text in result:
                    result = result.replace(old_text, new_text)
                    logger.info(f"✓ 替换建议文案: '{old_text}' -> '{new_text}'")
        
        # 如果没有任何替换，记录一下
        if result == content:
            logger.info(f"未找到需要替换的内容: {content[:100] if len(content) > 100 else content}")
        
        return result

    def _build_feishu_sync_prompt(self, tr_description: str, process_history: str = None, vin: str = None, existing_ai_suggestion: str = None, is_first_suggestion: bool = True) -> str:
        """
        构建飞书同步专用的AI建议提示词

        Args:
            tr_description: TR描述
            process_history: 处理过程记录
            vin: 车架号
            existing_ai_suggestion: 现有的AI建议
            is_first_suggestion: 是否是首次建议

        Returns:
            构建的提示词
        """
        prompt = f"""请作为专业的技术支持工程师，为以下工单问题提供详细的技术分析和处理建议。

问题描述：
{tr_description}

"""

        # 添加处理过程记录
        if process_history and process_history.strip():
            prompt += f"""
当前处理进度：
{process_history}

"""

        # 添加现有AI建议历史
        if existing_ai_suggestion and existing_ai_suggestion.strip():
            prompt += f"""
历史AI建议记录：
{existing_ai_suggestion}

"""

        # 根据是否首次建议设置不同的要求
        if is_first_suggestion:
            prompt += """
要求：
1. 详细分析问题描述，识别可能的根本原因
2. 基于当前处理进度，判断问题处于哪个阶段
3. 提供具体的排查步骤和技术指导
4. 建议需要收集哪些技术信息（如日志、配置、版本等）
5. 如果需要，可以建议进站处理的具体项目
6. 语言专业，包含技术细节，方便技术人员理解
7. 建议格式要清晰，便于执行和跟踪

请提供完整的分析和建议："""
        else:
            prompt += """
要求：
1. 基于已有处理记录和当前进度，分析问题进展情况
2. 判断之前的处理步骤是否有效，找出可能的遗漏点
3. 根据问题发展阶段提供更深入的技术解决方案
4. 如果远程处理无效，明确说明需要哪些线下技术支持
5. 详细说明进站后需要执行的具体诊断和修复步骤
6. 包含技术参数、工具要求和注意事项
7. 便于技术人员快速理解问题状态和下一步行动

请提供针对性的深入分析和处理建议："""

        return prompt

    def _build_realtime_chat_prompt(self, tr_description: str, process_history: str = None, is_first_suggestion: bool = True) -> str:
        """
        构建实时对话专用的AI建议提示词（保持原有风格）

        Args:
            tr_description: TR描述
            process_history: 处理过程记录
            is_first_suggestion: 是否是首次建议

        Returns:
            构建的提示词
        """
        # 构建上下文信息
        context_info = ""
        if process_history and process_history.strip():
            context_info = f"""

已处理的步骤：
{process_history}"""

        # 根据是否为首次建议，设置不同的提示词
        if is_first_suggestion:
            # 首次建议：只给出一般性的排查步骤，不要提进站抓取日志
            suggestion_instruction = """要求：
1. 首次给客户建议，只提供远程可操作的一般性排查步骤
2. 如检查网络、重启系统、确认配置等常见操作
3. 绝对不要提到"进站"、"抓取日志"等需要线下操作的内容
4. 语言简洁精炼，用逗号连接，不要用序号或分行"""
        else:
            # 后续建议：如果已有处理记录但未解决，可以考虑更深入的方案
            suggestion_instruction = """要求：
1. 基于已有处理步骤，给出下一步的排查建议
2. 如果远程操作都无法解决，可以考虑更深入的诊断方案
3. 语言简洁精炼，用逗号连接，不要用序号或分行"""

        # 构建用户消息 - 要求生成简洁的简短建议
        user_message = f"""请为以下问题提供精炼的技术支持操作建议：

格式要求：
1. 现状+步骤，语言精炼
2. 总长度控制在150字以内

{suggestion_instruction}

问题描述：{tr_description}{context_info}"""

        return user_message

    def _clean_and_validate_response(self, content: str) -> str:
        """
        清理和校验响应内容
        
        Args:
            content: 原始响应内容
            
        Returns:
            清理后的内容
        """
        try:
            # 移除常见的提示词和格式标记
            cleaned = content.strip()
            
            # 移除提示词模式
            prompt_patterns = [
                "作为技术支持专家",
                "请基于以下问题描述",
                "为工单提供专业的处理建议",
                "请提供：",
                "1. 问题分析",
                "2. 建议的解决步骤", 
                "3. 注意事项",
                "4. 如果问题无法解决",
                "请用中文回答，简洁明了",
                "模拟LLM响应:",
                "问题描述：",
                "相关背景信息：",
                "无相关背景信息",
                "您好",
                "感谢您反馈问题",
                "关于您反馈的",
                "建议您先尝试以下操作：",
                "建议您",
                "您可以",
                "请尝试",
                "建议先",
                "建议",
                "操作：",
                "步骤：",
                "1.",
                "2.",
                "3.",
                "4.",
                "5.",
                "关于",
                "情况",
                "问题",
                "无法正常使用",
                "的",
                "，",
                "。。。。。。"
            ]
            
            for pattern in prompt_patterns:
                cleaned = cleaned.replace(pattern, "").strip()
            
            # 移除多余的标点符号
            cleaned = cleaned.replace("，，", "，").replace("。。", "。").strip()
            
            # 进一步清理：移除编号和列表格式，提取核心建议
            lines = cleaned.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                # 跳过空行
                if not line:
                    continue
                
                # 移除行首的编号
                line = line.replace('1.', '').replace('2.', '').replace('3.', '').replace('4.', '').replace('5.', '').replace('6.', '').replace('7.', '').replace('8.', '').replace('9.', '').strip()
                
                # 只保留包含具体操作的行，跳过客套话
                if line and len(line) > 10 and not any(courtesy in line for courtesy in ['您好', '感谢', '关于', '情况', '问题', '无法正常使用']):
                    if any(keyword in line for keyword in ['检查', '确保', '重启', '尝试', '联系', '升级', '恢复', '设置', '配置', '确认', '观察', '重装']):
                        cleaned_lines.append(line)
            
            # 重新组合内容
            if cleaned_lines:
                cleaned = '，'.join(cleaned_lines)
            else:
                cleaned = cleaned.strip()
            
            # 最终清理：移除多余的标点符号和空格
            cleaned = cleaned.replace("，，", "，").replace("。。", "。").replace("  ", " ").strip()
            
            # 如果内容太短，返回默认建议
            if len(cleaned) < 10:
                return "建议邀请用户进站抓取日志分析"
            
            return cleaned
            
        except Exception as e:
            logger.error(f"清理响应内容失败: {e}")
            return content
    
    def batch_generate_suggestions(self, records: List[Dict[str, Any]], limit: int = 10, context: str = "feishu_sync") -> List[Dict[str, Any]]:
        """
        批量生成AI建议

        Args:
            records: 记录列表
            limit: 处理数量限制
            context: 调用上下文，"realtime_chat" 或 "feishu_sync"

        Returns:
            处理后的记录列表
        """
        from datetime import datetime
        
        processed_records = []
        now = datetime.now()
        time_str = now.strftime("%m%d")  # MMDD格式
        
        for i, record in enumerate(records[:limit]):
            try:
                fields = record.get("fields", {})
                tr_description = fields.get("TR Description", "")
                process_history = fields.get("处理过程", "")  # 获取处理过程记录
                existing_ai_suggestion = fields.get("AI建议", "")  # 获取现有AI建议
                vin = self._extract_vin_from_description(tr_description)
                
                # 调试日志
                logger.info(f"记录 {record.get('record_id', i)} - 现有AI建议长度: {len(existing_ai_suggestion) if existing_ai_suggestion else 0}")
                if existing_ai_suggestion:
                    logger.info(f"记录 {record.get('record_id', i)} - 现有AI建议前100字符: {existing_ai_suggestion[:100]}")
                
                if tr_description:
                    ai_suggestion = self.generate_suggestion(tr_description, process_history, vin, existing_ai_suggestion, context)
                    # 处理同一天多次更新的情况
                    new_suggestion = self._format_ai_suggestion_with_numbering(
                        time_str, ai_suggestion, existing_ai_suggestion
                    )
                    record["ai_suggestion"] = new_suggestion
                    logger.info(f"为记录 {record.get('record_id', i)} 生成AI建议，新建议长度: {len(new_suggestion)}")
                else:
                    record["ai_suggestion"] = f"{time_str}：无TR描述，无法生成建议"
                
                processed_records.append(record)
                
            except Exception as e:
                logger.error(f"处理记录 {record.get('record_id', i)} 失败: {e}")
                record["ai_suggestion"] = f"{time_str}：处理失败：{str(e)}"
                processed_records.append(record)
        
        return processed_records
    
    def _format_ai_suggestion_with_numbering(self, time_str: str, new_suggestion: str, existing_ai_suggestion: str) -> str:
        """
        格式化AI建议，支持同一天多次更新的编号
        
        Args:
            time_str: 时间字符串（MMDD格式）
            new_suggestion: 新的建议内容
            existing_ai_suggestion: 现有的AI建议
            
        Returns:
            格式化后的AI建议
        """
        logger.info(f"_format_ai_suggestion_with_numbering 调用 - time_str={time_str}, existing长度={len(existing_ai_suggestion) if existing_ai_suggestion else 0}")
        
        if not existing_ai_suggestion or not existing_ai_suggestion.strip():
            # 如果没有现有建议，直接返回带时间戳的第一条
            logger.info(f"没有现有建议，返回: {time_str}：{new_suggestion[:50]}...")
            return f"{time_str}：{new_suggestion}"
        
        # 检查是否已经有今天的时间戳
        if time_str not in existing_ai_suggestion:
            # 如果是新的一天，将新建议放在最前面
            return f"{time_str}：{new_suggestion}\n{existing_ai_suggestion}"
        
        # 如果是同一天，需要找到最大的编号
        lines = existing_ai_suggestion.split('\n')
        max_number = 0
        today_lines = []
        other_lines = []
        
        # 分离今天的记录和其他天的记录
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是今天的记录
            if line.startswith(time_str):
                today_lines.append(line)
                # 查找当前日期后的编号格式：1017-1, 1017-2等
                if f"{time_str}-" in line:
                    try:
                        # 提取编号：1017-1：... -> 1
                        number_part = line.split(f"{time_str}-", 1)[1].split('：', 1)[0]
                        number = int(number_part)
                        if number > max_number:
                            max_number = number
                    except (ValueError, IndexError):
                        pass
            else:
                other_lines.append(line)
        
        # 生成带编号的新建议
        new_number = max_number + 1
        new_line = f"{time_str}-{new_number}：{new_suggestion}"
        
        # 将新建议放在同一天记录的最前面，与其他天的记录组合
        today_lines.insert(0, new_line)
        today_text = '\n'.join(today_lines)
        
        # 组合：今天的记录（最新在前） + 其他天的记录
        if other_lines:
            other_text = '\n'.join(other_lines)
            return f"{today_text}\n{other_text}"
        else:
            return today_text
    
