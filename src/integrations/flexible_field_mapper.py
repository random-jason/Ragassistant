# -*- coding: utf-8 -*-
"""
灵活字段映射器
支持动态字段发现、智能映射和配置管理
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import difflib
from collections import defaultdict

logger = logging.getLogger(__name__)

class FlexibleFieldMapper:
    """灵活字段映射器"""
    
    def __init__(self, config_file: str = "config/field_mapping_config.json"):
        """
        初始化字段映射器
        
        Args:
            config_file: 字段映射配置文件路径
        """
        self.config_file = config_file
        self.field_mapping = {}
        self.field_aliases = {}  # 字段别名映射
        self.field_patterns = {}  # 字段模式匹配
        self.field_priorities = {}  # 字段优先级
        self.auto_mapping_enabled = True
        self.similarity_threshold = 0.6  # 相似度阈值
        
        # 加载配置
        self._load_config()
        
        # 初始化默认映射规则
        self._init_default_mappings()
    
    def _load_config(self):
        """加载字段映射配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.field_mapping = config.get('field_mapping', {})
                self.field_aliases = config.get('field_aliases', {})
                self.field_patterns = config.get('field_patterns', {})
                self.field_priorities = config.get('field_priorities', {})
                self.auto_mapping_enabled = config.get('auto_mapping_enabled', True)
                self.similarity_threshold = config.get('similarity_threshold', 0.6)
        except FileNotFoundError:
            logger.info(f"配置文件 {self.config_file} 不存在，将创建默认配置")
            self._create_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        default_config = {
            "field_mapping": {},
            "field_aliases": {},
            "field_patterns": {},
            "field_priorities": {},
            "auto_mapping_enabled": True,
            "similarity_threshold": 0.6
        }
        self._save_config(default_config)
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def _init_default_mappings(self):
        """初始化默认字段映射规则"""
        # 核心字段的别名和模式
        core_fields = {
            'order_id': {
                'aliases': ['TR Number', 'TR编号', '工单号', 'Order ID', 'Ticket ID'],
                'patterns': [r'.*number.*', r'.*id.*', r'.*编号.*'],
                'priority': 1
            },
            'description': {
                'aliases': ['TR Description', 'TR描述', '描述', 'Description', '问题描述'],
                'patterns': [r'.*description.*', r'.*描述.*', r'.*detail.*'],
                'priority': 1
            },
            'category': {
                'aliases': ['Type of problem', '问题类型', 'Category', '分类', 'Problem Type'],
                'patterns': [r'.*type.*', r'.*category.*', r'.*分类.*', r'.*类型.*'],
                'priority': 1
            },
            'priority': {
                'aliases': ['TR Level', '优先级', 'Priority', 'Level', '紧急程度'],
                'patterns': [r'.*level.*', r'.*priority.*', r'.*优先级.*'],
                'priority': 1
            },
            'status': {
                'aliases': ['TR Status', '状态', 'Status', '工单状态'],
                'patterns': [r'.*status.*', r'.*状态.*'],
                'priority': 1
            },
            'source': {
                'aliases': ['Source', '来源', 'Source Type', '来源类型'],
                'patterns': [r'.*source.*', r'.*来源.*'],
                'priority': 2
            },
            'created_at': {
                'aliases': ['Date creation', '创建日期', 'Created At', 'Creation Date'],
                'patterns': [r'.*creation.*', r'.*created.*', r'.*创建.*', r'.*date.*'],
                'priority': 1
            },
            'solution': {
                'aliases': ['处理过程', 'Solution', '解决方案', 'Process'],
                'patterns': [r'.*solution.*', r'.*处理.*', r'.*解决.*'],
                'priority': 2
            },
            'resolution': {
                'aliases': ['TR tracking', 'Resolution', '解决结果', '跟踪'],
                'patterns': [r'.*resolution.*', r'.*tracking.*', r'.*跟踪.*'],
                'priority': 2
            },
            'created_by': {
                'aliases': ['Created by', '创建人', 'Creator', 'Created By'],
                'patterns': [r'.*created.*by.*', r'.*creator.*', r'.*创建人.*'],
                'priority': 2
            },
        }
        
        # 更新配置
        for field, config in core_fields.items():
            if field not in self.field_aliases:
                self.field_aliases[field] = config['aliases']
            if field not in self.field_patterns:
                self.field_patterns[field] = config['patterns']
            if field not in self.field_priorities:
                self.field_priorities[field] = config['priority']
    
    def discover_fields(self, feishu_fields: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        发现飞书字段并尝试自动映射
        
        Args:
            feishu_fields: 飞书字段数据
            
        Returns:
            字段发现结果，包含已映射、未映射和建议映射的字段
        """
        logger.info(f"开始发现字段: {list(feishu_fields.keys())}")
        
        result = {
            'mapped_fields': {},      # 已映射字段
            'unmapped_fields': [],    # 未映射字段
            'suggested_mappings': {},  # 建议映射
            'field_analysis': {}       # 字段分析
        }
        
        # 分析每个飞书字段
        for feishu_field in feishu_fields.keys():
            analysis = self._analyze_field(feishu_field, feishu_fields[feishu_field])
            result['field_analysis'][feishu_field] = analysis
            
            # 尝试映射
            mapped_field = self.map_field(feishu_field)
            if mapped_field:
                result['mapped_fields'][feishu_field] = mapped_field
            else:
                result['unmapped_fields'].append(feishu_field)
                
                # 生成建议映射
                suggestions = self._suggest_mapping(feishu_field)
                if suggestions:
                    result['suggested_mappings'][feishu_field] = suggestions
        
        logger.info(f"字段发现完成: 已映射 {len(result['mapped_fields'])}, "
                   f"未映射 {len(result['unmapped_fields'])}, "
                   f"建议映射 {len(result['suggested_mappings'])}")
        
        return result
    
    def _analyze_field(self, field_name: str, field_value: Any) -> Dict[str, Any]:
        """
        分析字段特征
        
        Args:
            field_name: 字段名
            field_value: 字段值
            
        Returns:
            字段分析结果
        """
        analysis = {
            'name': field_name,
            'value_type': type(field_value).__name__,
            'value_length': len(str(field_value)) if field_value else 0,
            'is_empty': not field_value or str(field_value).strip() == '',
            'contains_chinese': any('\u4e00' <= char <= '\u9fff' for char in str(field_name)),
            'contains_numbers': any(char.isdigit() for char in str(field_name)),
            'contains_special_chars': any(char in '|()[]{}' for char in str(field_name)),
            'word_count': len(str(field_name).split()),
            'similarity_scores': {}
        }
        
        # 计算与已知字段的相似度
        for local_field, aliases in self.field_aliases.items():
            max_similarity = 0
            for alias in aliases:
                similarity = difflib.SequenceMatcher(None, field_name.lower(), alias.lower()).ratio()
                max_similarity = max(max_similarity, similarity)
            analysis['similarity_scores'][local_field] = max_similarity
        
        return analysis
    
    def _suggest_mapping(self, feishu_field: str) -> List[Dict[str, Any]]:
        """
        为未映射字段生成建议映射
        
        Args:
            feishu_field: 飞书字段名
            
        Returns:
            建议映射列表
        """
        suggestions = []
        
        # 基于相似度的建议
        for local_field, aliases in self.field_aliases.items():
            max_similarity = 0
            best_alias = ""
            
            for alias in aliases:
                similarity = difflib.SequenceMatcher(None, feishu_field.lower(), alias.lower()).ratio()
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_alias = alias
            
            if max_similarity >= self.similarity_threshold:
                suggestions.append({
                    'local_field': local_field,
                    'similarity': max_similarity,
                    'matched_alias': best_alias,
                    'confidence': 'high' if max_similarity >= 0.8 else 'medium',
                    'reason': f"与别名 '{best_alias}' 相似度 {max_similarity:.2f}"
                })
        
        # 基于模式匹配的建议
        for local_field, patterns in self.field_patterns.items():
            for pattern in patterns:
                import re
                if re.search(pattern, feishu_field.lower()):
                    suggestions.append({
                        'local_field': local_field,
                        'similarity': 0.7,  # 模式匹配给固定相似度
                        'matched_pattern': pattern,
                        'confidence': 'medium',
                        'reason': f"匹配模式 '{pattern}'"
                    })
                    break
        
        # 按相似度和优先级排序
        suggestions.sort(key=lambda x: (x['similarity'], self.field_priorities.get(x['local_field'], 999)), reverse=True)
        
        return suggestions[:3]  # 返回前3个建议
    
    def map_field(self, feishu_field: str) -> Optional[str]:
        """
        映射飞书字段到本地字段
        
        Args:
            feishu_field: 飞书字段名
            
        Returns:
            映射的本地字段名，如果没有映射则返回None
        """
        # 1. 直接映射
        if feishu_field in self.field_mapping:
            return self.field_mapping[feishu_field]
        
        # 2. 别名映射
        for local_field, aliases in self.field_aliases.items():
            if feishu_field in aliases:
                return local_field
        
        # 3. 自动映射（如果启用）
        if self.auto_mapping_enabled:
            suggestions = self._suggest_mapping(feishu_field)
            if suggestions and suggestions[0]['confidence'] == 'high':
                return suggestions[0]['local_field']
        
        return None
    
    def add_field_mapping(self, feishu_field: str, local_field: str, 
                         aliases: List[str] = None, patterns: List[str] = None,
                         priority: int = 3) -> bool:
        """
        添加字段映射
        
        Args:
            feishu_field: 飞书字段名
            local_field: 本地字段名
            aliases: 别名列表
            patterns: 模式列表
            priority: 优先级
            
        Returns:
            是否添加成功
        """
        try:
            # 添加到直接映射
            self.field_mapping[feishu_field] = local_field
            
            # 添加别名
            if aliases:
                if local_field not in self.field_aliases:
                    self.field_aliases[local_field] = []
                self.field_aliases[local_field].extend(aliases)
            
            # 添加模式
            if patterns:
                if local_field not in self.field_patterns:
                    self.field_patterns[local_field] = []
                self.field_patterns[local_field].extend(patterns)
            
            # 设置优先级
            self.field_priorities[local_field] = priority
            
            # 保存配置
            self._save_current_config()
            
            logger.info(f"添加字段映射: {feishu_field} -> {local_field}")
            return True
            
        except Exception as e:
            logger.error(f"添加字段映射失败: {e}")
            return False
    
    def remove_field_mapping(self, feishu_field: str) -> bool:
        """
        移除字段映射
        
        Args:
            feishu_field: 飞书字段名
            
        Returns:
            是否移除成功
        """
        try:
            if feishu_field in self.field_mapping:
                del self.field_mapping[feishu_field]
                self._save_current_config()
                logger.info(f"移除字段映射: {feishu_field}")
                return True
            return False
        except Exception as e:
            logger.error(f"移除字段映射失败: {e}")
            return False
    
    def get_mapping_status(self) -> Dict[str, Any]:
        """
        获取映射状态统计
        
        Returns:
            映射状态信息
        """
        return {
            'total_mappings': len(self.field_mapping),
            'total_aliases': sum(len(aliases) for aliases in self.field_aliases.values()),
            'total_patterns': sum(len(patterns) for patterns in self.field_patterns.values()),
            'auto_mapping_enabled': self.auto_mapping_enabled,
            'similarity_threshold': self.similarity_threshold,
            'field_mapping': self.field_mapping,
            'field_aliases': self.field_aliases,
            'field_patterns': self.field_patterns,
            'field_priorities': self.field_priorities
        }
    
    def _save_current_config(self):
        """保存当前配置"""
        config = {
            'field_mapping': self.field_mapping,
            'field_aliases': self.field_aliases,
            'field_patterns': self.field_patterns,
            'field_priorities': self.field_priorities,
            'auto_mapping_enabled': self.auto_mapping_enabled,
            'similarity_threshold': self.similarity_threshold
        }
        self._save_config(config)
    
    def convert_fields(self, feishu_fields: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        转换飞书字段到本地字段
        
        Args:
            feishu_fields: 飞书字段数据
            
        Returns:
            (转换后的本地字段, 转换统计信息)
        """
        local_data = {}
        conversion_stats = {
            'total_fields': len(feishu_fields),
            'mapped_fields': 0,
            'unmapped_fields': [],
            'mapping_details': {}
        }
        
        logger.info(f"开始转换字段: {list(feishu_fields.keys())}")
        
        for feishu_field, value in feishu_fields.items():
            local_field = self.map_field(feishu_field)
            
            if local_field:
                local_data[local_field] = value
                conversion_stats['mapped_fields'] += 1
                conversion_stats['mapping_details'][feishu_field] = {
                    'local_field': local_field,
                    'mapped': True,
                    'value': value
                }
                logger.info(f"映射字段 {feishu_field} -> {local_field}: {value}")
            else:
                conversion_stats['unmapped_fields'].append(feishu_field)
                conversion_stats['mapping_details'][feishu_field] = {
                    'mapped': False,
                    'value': value,
                    'suggestions': self._suggest_mapping(feishu_field)
                }
                logger.info(f"飞书字段 {feishu_field} 不存在于数据中")
        
        logger.info(f"字段转换完成: 已映射 {conversion_stats['mapped_fields']}, "
                   f"未映射 {len(conversion_stats['unmapped_fields'])}")
        
        return local_data, conversion_stats
