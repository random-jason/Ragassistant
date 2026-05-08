# -*- coding: utf-8 -*-
"""
飞书权限检查工具
用于诊断和解决飞书API权限问题
"""

import logging
from typing import Dict, Any, List
from src.integrations.feishu_client import FeishuClient
from src.integrations.config_manager import config_manager

logger = logging.getLogger(__name__)

class FeishuPermissionChecker:
    """飞书权限检查器"""
    
    def __init__(self):
        self.feishu_config = config_manager.get_feishu_config()
        self.client = None
        
        if self.feishu_config.get("app_id") and self.feishu_config.get("app_secret"):
            self.client = FeishuClient(
                self.feishu_config["app_id"], 
                self.feishu_config["app_secret"]
            )
    
    def check_permissions(self) -> Dict[str, Any]:
        """
        检查飞书应用权限
        
        Returns:
            权限检查结果
        """
        result = {
            "success": False,
            "checks": {},
            "recommendations": [],
            "errors": []
        }
        
        if not self.client:
            result["errors"].append("飞书客户端未初始化，请检查配置")
            return result
        
        # 1. 检查访问令牌
        try:
            token = self.client._get_access_token()
            if token:
                result["checks"]["access_token"] = {
                    "status": "success",
                    "message": "访问令牌获取成功"
                }
            else:
                result["checks"]["access_token"] = {
                    "status": "failed",
                    "message": "无法获取访问令牌"
                }
                result["errors"].append("无法获取访问令牌")
        except Exception as e:
            result["checks"]["access_token"] = {
                "status": "failed",
                "message": f"访问令牌获取失败: {e}"
            }
            result["errors"].append(f"访问令牌获取失败: {e}")
        
        # 2. 检查应用权限
        try:
            app_token = self.feishu_config.get("app_token")
            table_id = self.feishu_config.get("table_id")
            
            if not app_token or not table_id:
                result["errors"].append("缺少app_token或table_id配置")
                return result
            
            # 尝试获取表格信息
            table_info = self._get_table_info(app_token, table_id)
            if table_info:
                result["checks"]["table_access"] = {
                    "status": "success",
                    "message": "可以访问表格"
                }
            else:
                result["checks"]["table_access"] = {
                    "status": "failed",
                    "message": "无法访问表格"
                }
                result["errors"].append("无法访问表格")
                
        except Exception as e:
            result["checks"]["table_access"] = {
                "status": "failed",
                "message": f"表格访问失败: {e}"
            }
            result["errors"].append(f"表格访问失败: {e}")
        
        # 3. 检查记录读取权限
        try:
            records = self.client.get_table_records(app_token, table_id, page_size=1)
            if records.get("code") == 0:
                result["checks"]["read_records"] = {
                    "status": "success",
                    "message": "可以读取记录"
                }
            else:
                result["checks"]["read_records"] = {
                    "status": "failed",
                    "message": f"读取记录失败: {records.get('msg', '未知错误')}"
                }
                result["errors"].append(f"读取记录失败: {records.get('msg', '未知错误')}")
        except Exception as e:
            result["checks"]["read_records"] = {
                "status": "failed",
                "message": f"读取记录失败: {e}"
            }
            result["errors"].append(f"读取记录失败: {e}")
        
        # 4. 检查记录更新权限
        try:
            # 先获取一条记录进行测试
            records = self.client.get_table_records(app_token, table_id, page_size=1)
            if records.get("code") == 0 and records.get("data", {}).get("items"):
                test_record = records["data"]["items"][0]
                record_id = test_record["record_id"]
                
                # 尝试更新一个测试字段
                update_result = self.client.update_table_record(
                    app_token, 
                    table_id, 
                    record_id, 
                    {"测试字段": "权限测试"}
                )
                
                if update_result.get("code") == 0:
                    result["checks"]["update_records"] = {
                        "status": "success",
                        "message": "可以更新记录"
                    }
                else:
                    result["checks"]["update_records"] = {
                        "status": "failed",
                        "message": f"更新记录失败: {update_result.get('msg', '未知错误')}"
                    }
                    result["errors"].append(f"更新记录失败: {update_result.get('msg', '未知错误')}")
            else:
                result["checks"]["update_records"] = {
                    "status": "failed",
                    "message": "没有记录可用于测试更新权限"
                }
                result["errors"].append("没有记录可用于测试更新权限")
                
        except Exception as e:
            result["checks"]["update_records"] = {
                "status": "failed",
                "message": f"更新记录测试失败: {e}"
            }
            result["errors"].append(f"更新记录测试失败: {e}")
        
        # 5. 检查AI建议字段权限
        try:
            # 检查AI建议字段是否存在
            table_fields = self._get_table_fields(app_token, table_id)
            if table_fields:
                ai_field_exists = any(
                    field.get("field_name") == "AI建议" 
                    for field in table_fields.get("data", {}).get("items", [])
                )
                
                if ai_field_exists:
                    result["checks"]["ai_field"] = {
                        "status": "success",
                        "message": "AI建议字段存在"
                    }
                else:
                    result["checks"]["ai_field"] = {
                        "status": "warning",
                        "message": "AI建议字段不存在"
                    }
                    result["recommendations"].append("请在飞书表格中添加'AI建议'字段")
            else:
                result["checks"]["ai_field"] = {
                    "status": "failed",
                    "message": "无法获取表格字段信息"
                }
                result["errors"].append("无法获取表格字段信息")
                
        except Exception as e:
            result["checks"]["ai_field"] = {
                "status": "failed",
                "message": f"检查AI建议字段失败: {e}"
            }
            result["errors"].append(f"检查AI建议字段失败: {e}")
        
        # 生成建议
        self._generate_recommendations(result)
        
        # 判断整体状态
        failed_checks = [check for check in result["checks"].values() 
                        if check["status"] == "failed"]
        if not failed_checks:
            result["success"] = True
        
        return result
    
    def _get_table_info(self, app_token: str, table_id: str) -> Dict[str, Any]:
        """获取表格信息"""
        try:
            url = f"{self.client.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}"
            return self.client._make_request("GET", url)
        except Exception as e:
            logger.error(f"获取表格信息失败: {e}")
            return None
    
    def _get_table_fields(self, app_token: str, table_id: str) -> Dict[str, Any]:
        """获取表格字段信息"""
        try:
            url = f"{self.client.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
            return self.client._make_request("GET", url)
        except Exception as e:
            logger.error(f"获取表格字段失败: {e}")
            return None
    
    def _generate_recommendations(self, result: Dict[str, Any]):
        """生成修复建议"""
        recommendations = result["recommendations"]
        
        # 基于检查结果生成建议
        if "access_token" in result["checks"] and result["checks"]["access_token"]["status"] == "failed":
            recommendations.append("检查飞书应用的app_id和app_secret是否正确")
            recommendations.append("确认飞书应用已启用并获取了必要的权限")
        
        if "table_access" in result["checks"] and result["checks"]["table_access"]["status"] == "failed":
            recommendations.append("检查app_token和table_id是否正确")
            recommendations.append("确认应用有访问该表格的权限")
        
        if "update_records" in result["checks"] and result["checks"]["update_records"]["status"] == "failed":
            recommendations.append("检查飞书应用是否有'编辑'权限")
            recommendations.append("确认表格没有被锁定或只读")
            recommendations.append("检查应用是否被添加到表格的协作者中")
        
        if "ai_field" in result["checks"] and result["checks"]["ai_field"]["status"] == "warning":
            recommendations.append("在飞书表格中添加'AI建议'字段")
            recommendations.append("确保字段类型为'多行文本'或'单行文本'")
        
        # 通用建议
        if result["errors"]:
            recommendations.append("查看飞书开放平台文档了解权限配置")
            recommendations.append("联系飞书管理员确认应用权限设置")
    
    def get_permission_summary(self) -> str:
        """获取权限检查摘要"""
        result = self.check_permissions()
        
        summary = "飞书权限检查结果:\n"
        summary += f"整体状态: {'✅ 正常' if result['success'] else '❌ 异常'}\n\n"
        
        summary += "检查项目:\n"
        for check_name, check_result in result["checks"].items():
            status_icon = "✅" if check_result["status"] == "success" else "⚠️" if check_result["status"] == "warning" else "❌"
            summary += f"  {status_icon} {check_name}: {check_result['message']}\n"
        
        if result["recommendations"]:
            summary += "\n修复建议:\n"
            for i, rec in enumerate(result["recommendations"], 1):
                summary += f"  {i}. {rec}\n"
        
        if result["errors"]:
            summary += "\n错误信息:\n"
            for i, error in enumerate(result["errors"], 1):
                summary += f"  {i}. {error}\n"
        
        return summary
