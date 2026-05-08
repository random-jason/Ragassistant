
# -*- coding: utf-8 -*-
"""
推理引擎
负责逻辑推理和决策制定
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..core.llm_client import QwenClient

logger = logging.getLogger(__name__)

class ReasoningEngine:
    """推理引擎"""
    
    def __init__(self):
        self.llm_client = QwenClient()
        self.reasoning_patterns = {
            "causal": self._causal_reasoning,
            "deductive": self._deductive_reasoning,
            "inductive": self._inductive_reasoning,
            "abductive": self._abductive_reasoning,
            "analogical": self._analogical_reasoning
        }
        self.reasoning_history = []
    
    async def analyze_intent(
        self,
        message: str,
        context: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析用户意图"""
        try:
            prompt = f"""
            请分析以下用户消息的意图：
            
            用户消息: {message}
            上下文: {json.dumps(context, ensure_ascii=False)}
            历史记录: {json.dumps(history, ensure_ascii=False)}
            
            请从以下维度分析：
            1. 主要意图（问题咨询、工单创建、系统查询等）
            2. 情感倾向（积极、消极、中性）
            3. 紧急程度（高、中、低）
            4. 所需工具类型
            5. 预期响应类型
            6. 关键信息提取
            
            请以JSON格式返回分析结果。
            """
            
            messages = [
                {"role": "system", "content": "你是一个意图分析专家，擅长理解用户需求和意图。"},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm_client.chat_completion(messages, temperature=0.3)
            
            if "error" in result:
                return self._create_fallback_intent(message)
            
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            
            if json_match:
                intent_analysis = json.loads(json_match.group())
                intent_analysis["timestamp"] = datetime.now().isoformat()
                return intent_analysis
            else:
                return self._create_fallback_intent(message)
                
        except Exception as e:
            logger.error(f"意图分析失败: {e}")
            return self._create_fallback_intent(message)
    
    async def make_decision(
        self,
        situation: Dict[str, Any],
        options: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """制定决策"""
        try:
            prompt = f"""
            请根据以下情况制定决策：
            
            当前情况: {json.dumps(situation, ensure_ascii=False)}
            可选方案: {json.dumps(options, ensure_ascii=False)}
            决策标准: {json.dumps(criteria, ensure_ascii=False)}
            
            请分析每个方案的优缺点，并选择最佳方案。
            返回格式：
            {{
                "selected_option": "方案ID",
                "reasoning": "选择理由",
                "confidence": 0.8,
                "risks": ["风险1", "风险2"],
                "mitigation": "风险缓解措施"
            }}
            """
            
            messages = [
                {"role": "system", "content": "你是一个决策制定专家，擅长分析情况并做出最优决策。"},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm_client.chat_completion(messages, temperature=0.3)
            
            if "error" in result:
                return self._create_fallback_decision(options)
            
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            
            if json_match:
                decision = json.loads(json_match.group())
                decision["timestamp"] = datetime.now().isoformat()
                return decision
            else:
                return self._create_fallback_decision(options)
                
        except Exception as e:
            logger.error(f"决策制定失败: {e}")
            return self._create_fallback_decision(options)
    
    async def reason_about_problem(
        self,
        problem: str,
        available_information: Dict[str, Any],
        reasoning_type: str = "causal"
    ) -> Dict[str, Any]:
        """对问题进行推理"""
        try:
            if reasoning_type not in self.reasoning_patterns:
                reasoning_type = "causal"
            
            reasoning_func = self.reasoning_patterns[reasoning_type]
            result = await reasoning_func(problem, available_information)
            
            # 记录推理历史
            self.reasoning_history.append({
                "timestamp": datetime.now().isoformat(),
                "problem": problem,
                "reasoning_type": reasoning_type,
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"问题推理失败: {e}")
            return {"error": str(e)}
    
    async def _causal_reasoning(self, problem: str, information: Dict[str, Any]) -> Dict[str, Any]:
        """因果推理"""
        prompt = f"""
        请使用因果推理分析以下问题：
        
        问题: {problem}
        可用信息: {json.dumps(information, ensure_ascii=False)}
        
        请分析：
        1. 问题的根本原因
        2. 可能的因果关系链
        3. 影响因素分析
        4. 解决方案的预期效果
        
        请以JSON格式返回分析结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个因果推理专家，擅长分析问题的因果关系。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return {"reasoning_type": "causal", "error": "推理失败"}
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"reasoning_type": "causal", "analysis": response_content}
    
    async def _deductive_reasoning(self, problem: str, information: Dict[str, Any]) -> Dict[str, Any]:
        """演绎推理"""
        prompt = f"""
        请使用演绎推理分析以下问题：
        
        问题: {problem}
        可用信息: {json.dumps(information, ensure_ascii=False)}
        
        请分析：
        1. 一般性规则或原理
        2. 具体事实或条件
        3. 逻辑推导过程
        4. 必然结论
        
        请以JSON格式返回分析结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个演绎推理专家，擅长从一般原理推导具体结论。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return {"reasoning_type": "deductive", "error": "推理失败"}
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"reasoning_type": "deductive", "analysis": response_content}
    
    async def _inductive_reasoning(self, problem: str, information: Dict[str, Any]) -> Dict[str, Any]:
        """归纳推理"""
        prompt = f"""
        请使用归纳推理分析以下问题：
        
        问题: {problem}
        可用信息: {json.dumps(information, ensure_ascii=False)}
        
        请分析：
        1. 观察到的具体现象
        2. 寻找共同模式
        3. 形成一般性假设
        4. 验证假设的合理性
        
        请以JSON格式返回分析结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个归纳推理专家，擅长从具体现象归纳一般规律。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return {"reasoning_type": "inductive", "error": "推理失败"}
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"reasoning_type": "inductive", "analysis": response_content}
    
    async def _abductive_reasoning(self, problem: str, information: Dict[str, Any]) -> Dict[str, Any]:
        """溯因推理"""
        prompt = f"""
        请使用溯因推理分析以下问题：
        
        问题: {problem}
        可用信息: {json.dumps(information, ensure_ascii=False)}
        
        请分析：
        1. 观察到的现象
        2. 可能的最佳解释
        3. 解释的合理性评估
        4. 需要进一步验证的假设
        
        请以JSON格式返回分析结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个溯因推理专家，擅长寻找现象的最佳解释。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return {"reasoning_type": "abductive", "error": "推理失败"}
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"reasoning_type": "abductive", "analysis": response_content}
    
    async def _analogical_reasoning(self, problem: str, information: Dict[str, Any]) -> Dict[str, Any]:
        """类比推理"""
        prompt = f"""
        请使用类比推理分析以下问题：
        
        问题: {problem}
        可用信息: {json.dumps(information, ensure_ascii=False)}
        
        请分析：
        1. 寻找相似的问题或情况
        2. 识别相似性和差异性
        3. 应用类比关系
        4. 调整解决方案以适应当前情况
        
        请以JSON格式返回分析结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个类比推理专家，擅长通过类比解决问题。"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.llm_client.chat_completion(messages, temperature=0.3)
        
        if "error" in result:
            return {"reasoning_type": "analogical", "error": "推理失败"}
        
        response_content = result["choices"][0]["message"]["content"]
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"reasoning_type": "analogical", "analysis": response_content}
    
    async def extract_insights(
        self,
        execution_result: Dict[str, Any],
        goal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从执行结果中提取洞察"""
        try:
            prompt = f"""
            请从以下执行结果中提取洞察：
            
            执行结果: {json.dumps(execution_result, ensure_ascii=False)}
            目标: {json.dumps(goal, ensure_ascii=False)}
            
            请分析：
            1. 成功模式（什么导致了成功）
            2. 失败模式（什么导致了失败）
            3. 性能指标（效率、准确性等）
            4. 改进建议
            5. 新发现的知识
            
            请以JSON格式返回分析结果。
            """
            
            messages = [
                {"role": "system", "content": "你是一个洞察提取专家，擅长从执行结果中提取有价值的洞察。"},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm_client.chat_completion(messages, temperature=0.3)
            
            if "error" in result:
                return {"error": "洞察提取失败"}
            
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            
            if json_match:
                insights = json.loads(json_match.group())
                insights["timestamp"] = datetime.now().isoformat()
                return insights
            else:
                return {"analysis": response_content, "timestamp": datetime.now().isoformat()}
                
        except Exception as e:
            logger.error(f"洞察提取失败: {e}")
            return {"error": str(e)}
    
    async def evaluate_solution(
        self,
        problem: str,
        solution: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估解决方案"""
        try:
            prompt = f"""
            请评估以下解决方案：
            
            问题: {problem}
            解决方案: {json.dumps(solution, ensure_ascii=False)}
            评估标准: {json.dumps(criteria, ensure_ascii=False)}
            
            请从以下维度评估：
            1. 有效性（是否能解决问题）
            2. 效率（资源消耗和时间成本）
            3. 可行性（实施难度）
            4. 风险（潜在问题）
            5. 创新性（新颖程度）
            
            请以JSON格式返回评估结果。
            """
            
            messages = [
                {"role": "system", "content": "你是一个解决方案评估专家，擅长全面评估解决方案的质量。"},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm_client.chat_completion(messages, temperature=0.3)
            
            if "error" in result:
                return {"error": "解决方案评估失败"}
            
            response_content = result["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            
            if json_match:
                evaluation = json.loads(json_match.group())
                evaluation["timestamp"] = datetime.now().isoformat()
                return evaluation
            else:
                return {"evaluation": response_content, "timestamp": datetime.now().isoformat()}
                
        except Exception as e:
            logger.error(f"解决方案评估失败: {e}")
            return {"error": str(e)}
    
    def _create_fallback_intent(self, message: str) -> Dict[str, Any]:
        """创建备用意图分析"""
        return {
            "main_intent": "general_query",
            "emotion": "neutral",
            "urgency": "medium",
            "required_tools": ["generate_response"],
            "expected_response": "text",
            "key_information": {"message": message},
            "confidence": 0.5,
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_fallback_decision(self, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建备用决策"""
        if not options:
            return {
                "selected_option": None,
                "reasoning": "无可用选项",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        # 选择第一个选项作为默认选择
        return {
            "selected_option": options[0].get("id", "option_1"),
            "reasoning": "默认选择",
            "confidence": 0.3,
            "risks": ["决策质量未知"],
            "mitigation": "需要进一步验证",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_reasoning_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取推理历史"""
        return self.reasoning_history[-limit:] if self.reasoning_history else []
    
    def clear_reasoning_history(self):
        """清空推理历史"""
        self.reasoning_history = []
        logger.info("推理历史已清空")
