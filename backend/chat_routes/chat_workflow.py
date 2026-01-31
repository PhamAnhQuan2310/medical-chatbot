from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, Optional, List
import json
import os
import uuid
from datetime import datetime
import re
import requests

router = APIRouter(prefix="/chat", tags=["chat"])


WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflow', 'saved_workflows')

@router.post("/process")
async def process_message(data: Dict[str, Any] = Body(...)):
    try:
        message = data.get("message", "")
        workflow_id = data.get("workflow_id")
        conversation_id = data.get("conversation_id", str(uuid.uuid4()))
        
        if not workflow_id:
            return {"success": False, "message": "Thiếu workflow_id"}
        
        # Đọc workflow từ file lưu trữ
        workflow_path = os.path.join(WORKFLOWS_DIR, f"{workflow_id}.json")
        if not os.path.exists(workflow_path):
            return {"success": False, "message": f"Không tìm thấy workflow với id {workflow_id}"}
        
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        

        workflow_engine = WorkflowEngine(workflow_data)
        result = workflow_engine.process(message, conversation_id)
        

        return {
            "success": True,
            "response": result["response"],
            "intent": result.get("intent", "chat"),
            "workflow_path": result["path"],
            "execution_details": {
                "workflow_id": workflow_id,
                "conversation_id": conversation_id,
                "execution_time": result.get("execution_time"),
                "context": result.get("context", {}),
                "nodes_executed": len(result["path"])
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Lỗi xử lý tin nhắn: {str(e)}"}


class WorkflowEngine:
    def __init__(self, workflow_data):
        self.workflow = workflow_data
        self.nodes = {node["id"]: node for node in workflow_data.get("nodes", [])}
        self.edges = workflow_data.get("edges", [])
        self.context = {}
        

        self.node_handlers = {
            "InputNode": self.handle_input_node,
            "INPUTNODE": self.handle_input_node,
            "OutputNode": self.handle_output_node,
            "OUTPUTNODE": self.handle_output_node,
            "ResponseNode": self.handle_output_node,
            "RESPONSENODE": self.handle_output_node,
            "LLMNode": self.handle_llm_node,
            "LLMNODE": self.handle_llm_node,
            "ConditionalNode": self.handle_conditional_node,
            "CONDITIONALNODE": self.handle_conditional_node,
            "RAGNode": self.handle_rag_node,
            "RAGNODE": self.handle_rag_node,
            "IntentClassifierNode": self.handle_intent_classifier_node,
            "INTENTCLASSIFIERNODE": self.handle_intent_classifier_node,
            "SQLNode": self.handle_sql_node,
            "SQLNODE": self.handle_sql_node,
            "FormatResponseNode": self.handle_format_response_node,
            "FORMATRESPONSENODE": self.handle_format_response_node
        }
    
    def process(self, message: str, conversation_id: str) -> Dict[str, Any]:

        start_time = datetime.now()
        

        self.context = {
            "message": message,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "variables": {},
            "response": None,
            "intent": None
        }
        

        start_node = None
        for node in self.nodes.values():
            node_type = node.get("type", "").upper()
            if node_type == "INPUTNODE":
                start_node = node
                break
        

        if not start_node:
            target_ids = [edge["target"] for edge in self.edges]
            for node_id, node in self.nodes.items():
                if node_id not in target_ids:  
                    start_node = node
                    break
        
        if not start_node:
            return {
                "response": "Lỗi: Không tìm thấy node bắt đầu trong workflow.",
                "path": [],
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "context": self.context
            }
        
        
        path = []
        current_node = start_node
        max_steps = 50 
        
        for _ in range(max_steps):
            if not current_node:
                break
                

            node_type = current_node.get("type", "Unknown")
            node_label = current_node.get("data", {}).get("label", "Unnamed")
            node_info = f"{node_type} ({node_label})"
            path.append(node_info)
            
            
            node_type = current_node.get("type")
            handler = self.node_handlers.get(node_type)
            if not handler:
                handler = self.node_handlers.get(node_type.upper() if node_type else None, self.handle_default_node)
            
            handler_result = handler(current_node, self.context)
            
            
            if isinstance(handler_result, dict):
                self.context.update(handler_result)
            
            
            next_node = self.find_next_node(current_node)
            
            
            node_type_upper = node_type.upper() if node_type else ""
            if not next_node or node_type_upper in ["OUTPUTNODE", "RESPONSENODE"]:
                break
                
            current_node = next_node
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return {
            "response": self.context.get("response", "Không có phản hồi từ workflow."),
            "path": path,
            "intent": self.context.get("intent"),
            "execution_time": execution_time,
            "context": self.context
        }
    
    def find_next_node(self, current_node):
        """Tìm node tiếp theo dựa vào edges và điều kiện"""
        current_id = current_node["id"]
        
        
        candidate_edges = [e for e in self.edges if e["source"] == current_id]
        
        if not candidate_edges:
            return None
            
        
        node_type_upper = current_node.get("type", "").upper()
        if node_type_upper == "CONDITIONALNODE":
            condition_result = self.context.get("condition_result", False)
            
            for edge in candidate_edges:
                
                edge_label = edge.get("label", "").lower()
                
                if condition_result and (edge_label == "true" or edge_label == "có"):
                    return self.nodes.get(edge["target"])
                elif not condition_result and (edge_label == "false" or edge_label == "không"):
                    return self.nodes.get(edge["target"])
                    
            
            for edge in candidate_edges:
                if not edge.get("label"):
                    return self.nodes.get(edge["target"])
        
        
        return self.nodes.get(candidate_edges[0]["target"]) if candidate_edges else None
    
    
    def handle_input_node(self, node, context):
        """Xử lý InputNode - node đầu vào của workflow"""
        node_label = node.get("data", {}).get("label", "")
        print(f"Xử lý InputNode: {node_label}")
        return {
            "input": context["message"],
            "node_type": "input"
        }
    
    def handle_output_node(self, node, context):
        """Xử lý OutputNode hoặc ResponseNode - node đầu ra của workflow"""
        
        if not context.get("response"):
            template = node.get("data", {}).get("responseTemplate", "")
            if template:
                
                response = template
                for var_name, var_value in context.get("variables", {}).items():
                    if var_value is not None:
                        response = response.replace(f"{{${var_name}}}", str(var_value))
                
                
                response = response.replace("{{$input}}", context["message"])
                context["response"] = response
            else:
                context["response"] = f"Xin chào! Tôi đã nhận được tin nhắn: '{context['message']}'"
        
        return {"node_type": "output"}
    
    def handle_llm_node(self, node, context):
        """Xử lý LLMNode - gọi API LLM"""
        prompt_template = node.get("data", {}).get("promptTemplate", "")
        system_prompt = node.get("data", {}).get("systemPrompt", "")
        
        if not prompt_template:
            prompt_template = "{{$input}}"
        
       
        prompt = prompt_template
        for var_name, var_value in context.get("variables", {}).items():
            if var_value is not None:
                prompt = prompt.replace(f"{{${var_name}}}", str(var_value))
        
        
        prompt = prompt.replace("{{$input}}", context["message"])
        
        try:
            
            response = f"Đây là phản hồi AI cho tin nhắn: '{prompt}'"
            
            
            var_name = node.get("data", {}).get("variableName", "llm_response")
            context["variables"][var_name] = response
            context["response"] = response  
            context["node_type"] = "llm"
            
            return {"node_type": "llm"}
        except Exception as e:
            context["error"] = f"Lỗi khi gọi LLM API: {str(e)}"
            return {"node_type": "llm", "error": str(e)}
    
    def handle_conditional_node(self, node, context):
        condition = node.get("data", {}).get("condition", "")
        
        if not condition:
            context["condition_result"] = True
            return {"node_type": "conditional", "condition_result": True}
            
        
        for var_name, var_value in context.get("variables", {}).items():
            if var_value is not None:
                condition = condition.replace(f"{{${var_name}}}", f"'{var_value}'")
        
        
        condition = condition.replace("{{$input}}", f"'{context['message']}'")
        
        
        try:
            
            result = False
            
            
            if "contains" in condition.lower():
                matches = re.findall(r"'([^']*)'\s+contains\s+'([^']*)'", condition, re.IGNORECASE)
                if matches:
                    for text, substring in matches:
                        if substring.lower() in text.lower():
                            result = True
                            break
            
            elif "==" in condition:
                parts = condition.split("==")
                if len(parts) == 2:
                    left = parts[0].strip().replace("'", "")
                    right = parts[1].strip().replace("'", "")
                    result = (left == right)
                    
            context["condition_result"] = result
            return {"node_type": "conditional", "condition_result": result}
        except Exception as e:
            context["error"] = f"Lỗi xử lý điều kiện: {str(e)}"
            context["condition_result"] = False
            return {"node_type": "conditional", "condition_result": False, "error": str(e)}
    
    def handle_rag_node(self, node, context):
        """Xử lý RAGNode - truy xuất tài liệu tương tự"""
        query = context["message"]
        
        try:
            
            results = [
                {"text": "Đây là một đoạn văn tương tự với câu hỏi của bạn.", "score": 0.92},
                {"text": "Đây là thông tin bổ sung có thể hữu ích.", "score": 0.85}
            ]
            
            
            var_name = node.get("data", {}).get("variableName", "rag_results")
            context["variables"][var_name] = results
            
            
            rag_response = "Dựa trên tìm kiếm tài liệu:\n\n"
            for idx, result in enumerate(results):
                rag_response += f"{idx+1}. {result['text']} (Độ tương đồng: {result['score']})\n"
                
            context["response"] = rag_response
            context["node_type"] = "rag"
            context["intent"] = "rag"
            
            return {"node_type": "rag"}
        except Exception as e:
            context["error"] = f"Lỗi khi thực hiện RAG: {str(e)}"
            return {"node_type": "rag", "error": str(e)}
    
    def handle_intent_classifier_node(self, node, context):
        """Xử lý IntentClassifierNode - phân loại ý định của người dùng"""
        message = context["message"]
        
        
        
        intents = {
            "greeting": ["xin chào", "chào", "hello", "hi", "hey"],
            "question": ["ai", "gì", "sao", "như thế nào", "?", "tại sao"],
            "command": ["hãy", "làm", "tìm", "kiểm tra", "thực hiện"]
        }
        
        message_lower = message.lower()
        detected_intent = "general"
        
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_intent = intent
                    break
        
        
        var_name = node.get("data", {}).get("variableName", "intent")
        context["variables"][var_name] = detected_intent
        context["intent"] = detected_intent
        
        return {"node_type": "intent_classifier", "intent": detected_intent}
    
    def handle_sql_node(self, node, context):
        """Xử lý SQLNode - thực hiện truy vấn SQL"""
        query_template = node.get("data", {}).get("query", "SELECT 'Demo query' AS result")
        
        
        query = query_template
        for var_name, var_value in context.get("variables", {}).items():
            if var_value is not None:
                query = query.replace(f"{{${var_name}}}", str(var_value))
        
        
        query = query.replace("{{$input}}", context["message"])
        
        try:
            
            sql_result = {
                "columns": ["id", "name", "value"],
                "rows": [
                    [1, "Item 1", 100],
                    [2, "Item 2", 200],
                    [3, "Item 3", 300]
                ],
                "sql": query
            }
            
           
            var_name = node.get("data", {}).get("variableName", "sql_result")
            context["variables"][var_name] = sql_result
            
            
            sql_response = f"Kết quả truy vấn: {len(sql_result['rows'])} dòng.\n"
            sql_response += "\n| " + " | ".join(sql_result["columns"]) + " |\n"
            sql_response += "|" + "---|" * len(sql_result["columns"]) + "\n"
            
            for row in sql_result["rows"]:
                sql_response += "| " + " | ".join(str(cell) for cell in row) + " |\n"
                
            context["response"] = sql_response
            context["node_type"] = "sql"
            context["intent"] = "sql"
            
            return {"node_type": "sql"}
        except Exception as e:
            context["error"] = f"Lỗi khi thực hiện truy vấn SQL: {str(e)}"
            return {"node_type": "sql", "error": str(e)}
    
    def handle_format_response_node(self, node, context):
        """Xử lý FormatResponseNode - định dạng phản hồi"""
        template = node.get("data", {}).get("template", "")
        
        if not template:
            return {"node_type": "format_response"}
            
        
        response = template
        for var_name, var_value in context.get("variables", {}).items():
            if var_value is not None:
                response = response.replace(f"{{${var_name}}}", str(var_value))
        
        
        response = response.replace("{{$input}}", context["message"])
        
       
        context["response"] = response
        
        return {"node_type": "format_response"}
    
    def handle_default_node(self, node, context):
        """Handler mặc định cho các loại node khác"""
        node_type = node.get("type", "unknown")
        context["variables"][f"{node_type}_result"] = f"Processed by {node_type}"
        return {"node_type": node_type}