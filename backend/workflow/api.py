from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import uuid
from datetime import datetime
import time

router = APIRouter(prefix="/workflow", tags=["workflow"])

# File path for storing workflows
WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_workflows")
os.makedirs(WORKFLOWS_DIR, exist_ok=True)

# Models for request/response
class WorkflowRequest(BaseModel):
    id: Optional[str] = None
    name: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class WorkflowResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow: Optional[Dict[str, Any]] = None

# Get all available node types
@router.get("/node_types")
async def get_node_types_route():
    # Mẫu node types
    node_types = [
        {"type": "InputNode", "label": "Đầu vào", "description": "Node đầu vào cho workflow"},
        {"type": "OutputNode", "label": "Đầu ra", "description": "Node đầu ra cho workflow"},
        {"type": "IntentClassifierNode", "label": "Phân loại ý định", "description": "Phân loại ý định người dùng"},
        {"type": "RAGNode", "label": "RAG", "description": "Retrieval Augmented Generation"},
        {"type": "SQLNode", "label": "SQL", "description": "Thực thi truy vấn SQL"},
        {"type": "FHIRPatientNode", "label": "Thông tin bệnh nhân", "description": "Lấy thông tin bệnh nhân FHIR"}
    ]
    return {"success": True, "node_types": node_types}

# List all workflows
@router.get("/list")
async def list_workflows():
    try:
        workflows = []
        
        # Load from files
        if os.path.exists(WORKFLOWS_DIR):
            for filename in os.listdir(WORKFLOWS_DIR):
                if filename.endswith(".json"):
                    file_path = os.path.join(WORKFLOWS_DIR, filename)
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        workflow_data = json.load(f)
                    
                    workflows.append({
                        "id": workflow_data.get("id"),
                        "name": workflow_data.get("name"),
                        "created_at": workflow_data.get("created_at"),
                        "updated_at": workflow_data.get("updated_at")
                    })
        
        return {"success": True, "workflows": workflows}
    except Exception as e:
        return {"success": False, "message": f"Lỗi: {str(e)}", "workflows": []}

# ĐẶT CÁC ROUTE CỤ THỂ TRƯỚC ROUTE ĐỘNG /{workflow_id}
@router.get("/generate_system_workflow")
async def generate_system_workflow():
    """Tự động tạo workflow dựa trên cấu trúc hệ thống hiện tại"""
    try:
        print("Generating system workflow...")  # Debug log
        
        # Phân tích cấu trúc thư mục và file để tạo workflow
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        print(f"Base directory: {base_dir}")  # Debug log
        
        # Các node cơ bản của hệ thống
        system_nodes = []
        system_edges = []
        
        node_positions = {
            'input': {'x': 100, 'y': 100},
            'intent': {'x': 300, 'y': 100},
            'rag': {'x': 500, 'y': 50},
            'sql': {'x': 500, 'y': 150},
            'fhir': {'x': 500, 'y': 250},
            'output': {'x': 700, 'y': 150}
        }
        
        # 1. Input Node (luôn có)
        system_nodes.append({
            'id': 'input_1',
            'type': 'customNode',
            'position': node_positions['input'],
            'data': {
                'label': 'Đầu vào người dùng',
                'nodeType': 'InputNode',
                'parameters': {
                    'description': 'Nhận câu hỏi từ người dùng'
                }
            }
        })
        
        # 2. Intent Classifier (luôn thêm)
        system_nodes.append({
            'id': 'intent_1',
            'type': 'customNode',
            'position': node_positions['intent'],
            'data': {
                'label': 'Phân loại ý định',
                'nodeType': 'IntentClassifierNode',
                'parameters': {
                    'description': 'Phân loại ý định người dùng'
                }
            }
        })
        
        system_edges.append({
            'id': 'e_input_intent',
            'source': 'input_1',
            'target': 'intent_1',
            'label': 'Câu hỏi'
        })
        
        # 3. RAG Node (luôn thêm)
        system_nodes.append({
            'id': 'rag_1',
            'type': 'customNode',
            'position': node_positions['rag'],
            'data': {
                'label': 'RAG Retrieval',
                'nodeType': 'RAGNode',
                'parameters': {
                    'description': 'Tìm kiếm thông tin từ knowledge base'
                }
            }
        })
        
        system_edges.append({
            'id': 'e_intent_rag',
            'source': 'intent_1',
            'target': 'rag_1',
            'label': 'Câu hỏi tổng quát'
        })
        
        # 4. SQL Node (luôn thêm)
        system_nodes.append({
            'id': 'sql_1',
            'type': 'customNode',
            'position': node_positions['sql'],
            'data': {
                'label': 'SQL Query',
                'nodeType': 'SQLNode',
                'parameters': {
                    'description': 'Truy vấn dữ liệu từ database'
                }
            }
        })
        
        system_edges.append({
            'id': 'e_intent_sql',
            'source': 'intent_1',
            'target': 'sql_1',
            'label': 'Câu hỏi dữ liệu'
        })
        
        # 5. Output Node (luôn có)
        system_nodes.append({
            'id': 'output_1',
            'type': 'customNode',
            'position': node_positions['output'],
            'data': {
                'label': 'Đầu ra cho người dùng',
                'nodeType': 'OutputNode',
                'parameters': {
                    'description': 'Trả lời cho người dùng'
                }
            }
        })
        
        # Kết nối RAG và SQL với output
        system_edges.extend([
            {
                'id': 'e_rag_output',
                'source': 'rag_1',
                'target': 'output_1',
                'label': 'Kết quả RAG'
            },
            {
                'id': 'e_sql_output',
                'source': 'sql_1',
                'target': 'output_1',
                'label': 'Kết quả SQL'
            }
        ])
        
        workflow_data = {
            'id': f'system_generated_{int(time.time())}',
            'name': 'System Generated Workflow',
            'nodes': system_nodes,
            'edges': system_edges,
            'generated': True,
            'generated_time': time.time()
        }
        
        print(f"Generated workflow with {len(system_nodes)} nodes and {len(system_edges)} edges")
        
        return {
            "success": True,
            "workflow": workflow_data,
            "analysis": {
                "total_nodes": len(system_nodes),
                "total_edges": len(system_edges)
            }
        }
        
    except Exception as e:
        print(f"Error in generate_system_workflow: {str(e)}")
        return {"success": False, "message": f"Error generating system workflow: {str(e)}"}

@router.get("/generate_system_data_workflow")
async def generate_system_data_workflow():
    """Tự động tạo data workflow dựa trên cấu trúc dữ liệu hệ thống"""
    try:
        system_nodes = []
        system_edges = []
        
        node_positions = {
            'data_input': {'x': 100, 'y': 150},
            'condition': {'x': 350, 'y': 100},
            'no_path': {'x': 550, 'y': 100},
            'yes_path': {'x': 350, 'y': 250},
            'vector_db_top': {'x': 750, 'y': 100},
            'vector_db_middle': {'x': 550, 'y': 250},
            'json_file': {'x': 350, 'y': 370},
            'chatbot_db': {'x': 1000, 'y': 250}
        }
        
        # 1. Data Input Node
        system_nodes.append({
            'id': 'data_input',
            'type': 'customNode',
            'position': node_positions['data_input'],
            'data': {
                'label': 'Dữ liệu',
                'nodeType': 'InputNode',
                'parameters': {}
            }
        })
        
        # 2. Condition Node
        system_nodes.append({
            'id': 'condition',
            'type': 'customNode',
            'position': node_positions['condition'],
            'data': {
                'label': 'Có phải dạng bảng không?',
                'nodeType': 'ConditionalNode',
                'parameters': {}
            }
        })
        
        # 3. No Path - Intent Classifier
        system_nodes.append({
            'id': 'no_path',
            'type': 'customNode',
            'position': node_positions['no_path'],
            'data': {
                'label': 'Dự đoán ngữ cảnh',
                'nodeType': 'IntentClassifierNode',
                'parameters': {}
            }
        })
        
        # 4. Yes Path - Intent Classifier
        system_nodes.append({
            'id': 'yes_path',
            'type': 'customNode',
            'position': node_positions['yes_path'],
            'data': {
                'label': 'Dự đoán ngữ cảnh',
                'nodeType': 'IntentClassifierNode',
                'parameters': {}
            }
        })
        
        # 5. Vector DB Top
        system_nodes.append({
            'id': 'vector_db_top',
            'type': 'customNode',
            'position': node_positions['vector_db_top'],
            'data': {
                'label': 'Lưu trong vector database',
                'nodeType': 'RAGNode',
                'parameters': {}
            }
        })
        
        # 6. Vector DB Middle
        system_nodes.append({
            'id': 'vector_db_middle',
            'type': 'customNode',
            'position': node_positions['vector_db_middle'],
            'data': {
                'label': 'Lưu trong vector database',
                'nodeType': 'RAGNode',
                'parameters': {}
            }
        })
        
        # 7. JSON File Output
        system_nodes.append({
            'id': 'json_file',
            'type': 'customNode',
            'position': node_positions['json_file'],
            'data': {
                'label': 'Lưu ngữ cảnh vào file json dưới dạng dict',
                'nodeType': 'OutputNode',
                'parameters': {}
            }
        })
        
        # 8. Chatbot Database
        system_nodes.append({
            'id': 'chatbot_db',
            'type': 'customNode',
            'position': node_positions['chatbot_db'],
            'data': {
                'label': 'Kho Dữ liệu cho chatbot',
                'nodeType': 'OutputNode',
                'parameters': {}
            }
        })
        
        # Tạo edges theo mẫu có sẵn
        system_edges = [
            {'id': 'e1-2', 'source': 'data_input', 'target': 'condition'},
            {'id': 'e2-3', 'source': 'condition', 'target': 'no_path', 'label': 'Không'},
            {'id': 'e2-4', 'source': 'condition', 'target': 'yes_path', 'label': 'Có'},
            {'id': 'e3-5', 'source': 'no_path', 'target': 'vector_db_top', 'label': 'Bao gồm ngữ cảnh'},
            {'id': 'e4-6', 'source': 'yes_path', 'target': 'vector_db_middle'},
            {'id': 'e4-7', 'source': 'yes_path', 'target': 'json_file'},
            {'id': 'e5-8', 'source': 'vector_db_top', 'target': 'chatbot_db'},
            {'id': 'e6-8', 'source': 'vector_db_middle', 'target': 'chatbot_db'},
            {'id': 'e7-8', 'source': 'json_file', 'target': 'chatbot_db'}
        ]
        
        workflow_data = {
            'id': f'system_data_generated_{int(time.time())}',
            'name': 'System Generated Data Workflow',
            'nodes': system_nodes,
            'edges': system_edges,
            'generated': True,
            'generated_time': time.time()
        }
        
        return {
            "success": True,
            "workflow": workflow_data
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error generating system data workflow: {str(e)}"}

# Save workflow
@router.post("/save")
async def save_workflow(workflow_req: WorkflowRequest):
    try:
        # Generate ID if needed
        if not workflow_req.id:
            workflow_req.id = f"workflow_{uuid.uuid4().hex[:8]}"
        
        # Prepare workflow data
        now = datetime.now().isoformat()
        workflow_data = {
            "id": workflow_req.id,
            "name": workflow_req.name,
            "nodes": workflow_req.nodes,
            "edges": workflow_req.edges,
            "created_at": now,
            "updated_at": now
        }
        
        # Save to file
        file_path = os.path.join(WORKFLOWS_DIR, f"{workflow_req.id}.json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": "Đã lưu workflow thành công",
            "workflow_id": workflow_req.id
        }
    except Exception as e:
        return {"success": False, "message": f"Lỗi: {str(e)}"}

# ĐẶT ROUTE ĐỘNG /{workflow_id} CUỐI CÙNG
@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    try:
        file_path = os.path.join(WORKFLOWS_DIR, f"{workflow_id}.json")
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"Không tìm thấy workflow với ID {workflow_id}"
            }
        
        with open(file_path, "r", encoding="utf-8") as f:
            workflow_data = json.load(f)
        
        return {
            "success": True,
            "workflow": workflow_data
        }
    except Exception as e:
        return {"success": False, "message": f"Lỗi: {str(e)}"}