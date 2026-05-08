# -*- coding: utf-8 -*-
"""
工单权限管理模块
实现基于角色的访问控制（RBAC）和工单分发流程
"""

import logging
from typing import List, Dict, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """用户角色枚举"""
    # 属地运维（海外/国内）
    OVERSEAS_OPS = "overseas_ops"  # 海外属地运维
    DOMESTIC_OPS = "domestic_ops"  # 国内属地运维

    # 业务方接口人（各模块负责人）
    MODULE_OWNER_A = "module_owner_a"  # 模块A负责人
    MODULE_OWNER_B = "module_owner_b"  # 模块B负责人
    MODULE_OWNER_C = "module_owner_c"  # 模块C负责人

    # 系统角色
    ADMIN = "admin"  # 系统管理员
    VIEWER = "viewer"  # 只读用户

class WorkOrderModule(Enum):
    """工单模块枚举（可根据业务需求自定义）"""
    MODULE_A = "module_a"
    MODULE_B = "module_b"
    MODULE_C = "module_c"
    LOCAL_OPS = "local_ops"  # 属地运维处理
    UNASSIGNED = "unassigned"  # 未分配

class WorkOrderStatus:
    """工单状态常量"""
    PENDING = "pending"  # 待处理
    ASSIGNED = "assigned"  # 已分配
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭

class WorkOrderPermissionManager:
    """工单权限管理器"""
    
    # 所有模块集合（供属地运维和管理员使用）
    ALL_MODULES = {
        WorkOrderModule.MODULE_A, WorkOrderModule.MODULE_B,
        WorkOrderModule.MODULE_C, WorkOrderModule.LOCAL_OPS
    }

    # 角色到模块的映射
    ROLE_MODULE_MAP = {
        UserRole.MODULE_OWNER_A: {WorkOrderModule.MODULE_A},
        UserRole.MODULE_OWNER_B: {WorkOrderModule.MODULE_B},
        UserRole.MODULE_OWNER_C: {WorkOrderModule.MODULE_C},
        UserRole.OVERSEAS_OPS: ALL_MODULES,  # 可访问所有模块
        UserRole.DOMESTIC_OPS: ALL_MODULES,  # 可访问所有模块
        UserRole.ADMIN: ALL_MODULES,  # 管理员可访问所有
        UserRole.VIEWER: set(),  # 只读，由其他逻辑控制
    }
    
    @staticmethod
    def can_view_all_workorders(role: UserRole) -> bool:
        """判断角色是否可以查看所有工单（属地运维和管理员）"""
        return role in [UserRole.OVERSEAS_OPS, UserRole.DOMESTIC_OPS, UserRole.ADMIN]
    
    @staticmethod
    def get_accessible_modules(role: UserRole) -> Set[WorkOrderModule]:
        """获取角色可访问的模块列表"""
        return WorkOrderPermissionManager.ROLE_MODULE_MAP.get(role, set())
    
    @staticmethod
    def can_access_module(role: UserRole, module: WorkOrderModule) -> bool:
        """判断角色是否可以访问指定模块"""
        accessible_modules = WorkOrderPermissionManager.get_accessible_modules(role)
        
        # 属地运维和管理员可以访问所有模块
        if WorkOrderPermissionManager.can_view_all_workorders(role):
            return True
        
        # 业务方只能访问自己的模块
        return module in accessible_modules
    
    @staticmethod
    def can_dispatch_workorder(role: UserRole) -> bool:
        """判断角色是否可以进行工单分发（属地运维和管理员）"""
        return role in [UserRole.OVERSEAS_OPS, UserRole.DOMESTIC_OPS, UserRole.ADMIN]
    
    @staticmethod
    def can_update_workorder(role: UserRole, workorder_module: Optional[WorkOrderModule], 
                            assigned_to_module: Optional[WorkOrderModule]) -> bool:
        """判断角色是否可以更新工单"""
        # 管理员和属地运维可以更新所有工单
        if WorkOrderPermissionManager.can_view_all_workorders(role):
            return True
        
        # 业务方只能更新分配给自己的模块的工单
        if workorder_module and assigned_to_module:
            accessible_modules = WorkOrderPermissionManager.get_accessible_modules(role)
            return workorder_module in accessible_modules and workorder_module == assigned_to_module
        
        return False
    
    @staticmethod
    def filter_workorders_by_permission(role: UserRole, workorders: List[Dict]) -> List[Dict]:
        """根据权限过滤工单列表"""
        if WorkOrderPermissionManager.can_view_all_workorders(role):
            # 属地运维和管理员可以看到所有工单
            return workorders
        
        # 业务方只能看到自己模块的工单
        accessible_modules = WorkOrderPermissionManager.get_accessible_modules(role)
        filtered = []
        
        for wo in workorders:
            module_str = wo.get("module") or wo.get("assigned_module")
            if module_str:
                try:
                    module = WorkOrderModule(module_str)
                    if module in accessible_modules:
                        filtered.append(wo)
                except ValueError:
                    # 如果模块值不在枚举中，跳过
                    continue
            else:
                # 未分配的工单，业务方看不到
                pass
        
        return filtered

class WorkOrderDispatchManager:
    """工单分发管理器"""
    
    # 模块到业务接口人的映射（可以动态配置）
    MODULE_OWNER_MAP = {
        WorkOrderModule.MODULE_A: "模块A负责人",
        WorkOrderModule.MODULE_B: "模块B负责人",
        WorkOrderModule.MODULE_C: "模块C负责人",
    }
    
    @staticmethod
    def get_module_owner(module: WorkOrderModule) -> str:
        """获取模块的业务接口人"""
        return WorkOrderDispatchManager.MODULE_OWNER_MAP.get(module, "未指定")
    
    @staticmethod
    def dispatch_workorder(workorder_id: int, target_module: WorkOrderModule, 
                           dispatcher_role: UserRole, dispatcher_name: str) -> Dict:
        """
        分发工单到指定模块
        
        Args:
            workorder_id: 工单ID
            target_module: 目标模块
            dispatcher_role: 分发者角色（必须是运维或管理员）
            dispatcher_name: 分发者姓名
            
        Returns:
            分发结果
        """
        # 检查分发权限
        if not WorkOrderPermissionManager.can_dispatch_workorder(dispatcher_role):
            return {
                "success": False,
                "error": "无权进行工单分发，只有属地运维和管理员可以分发工单"
            }
        
        # 获取模块负责人
        module_owner = WorkOrderDispatchManager.get_module_owner(target_module)
        
        # 这里应该更新数据库中的工单信息
        # 实际实现时需要调用数据库更新逻辑
        return {
            "success": True,
            "message": f"工单已分发到{target_module.value}模块",
            "assigned_module": target_module.value,
            "module_owner": module_owner,
            "dispatcher": dispatcher_name,
            "dispatcher_role": dispatcher_role.value
        }
    
    @staticmethod
    def suggest_module(description: str, title: str = "") -> Optional[WorkOrderModule]:
        """
        根据工单描述建议分配模块（可以使用AI分析）
        
        Args:
            description: 工单描述
            title: 工单标题
            
        Returns:
            建议的模块
        """
        # 简单的关键词匹配（实际可以使用AI分析）
        text = (title + " " + description).lower()

        keyword_module_map = {
            WorkOrderModule.MODULE_A: ["模块a", "module a"],
            WorkOrderModule.MODULE_B: ["模块b", "module b"],
            WorkOrderModule.MODULE_C: ["模块c", "module c"],
        }
        
        for module, keywords in keyword_module_map.items():
            for keyword in keywords:
                if keyword in text:
                    return module
        
        return WorkOrderModule.UNASSIGNED
