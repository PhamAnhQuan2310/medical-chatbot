import json
import uuid
import importlib
import inspect
from typing import Dict, Any, List, Callable
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkflowEngine")

class WorkflowNode:
    """Base class for all workflow nodes"""
    
    def __init__(self, node_id=None, node_type=None, name=None, position=None, inputs=None, outputs=None, parameters=None):
        self.id = node_id or str(uuid.uuid4())
        self.type = node_type or self.__class__.__name__
        self.name = name or self.type
        self.position = position or {"x": 0, "y": 0}
        self.inputs = inputs or {}
        self.outputs = outputs or {}
        self.parameters = parameters or {}
        self.status = "idle"
    
    def to_dict(self):
        """Convert node to dictionary representation"""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "position": self.position,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "parameters": self.parameters,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create node from dictionary representation"""
        return cls(
            node_id=data.get("id"),
            node_type=data.get("type"),
            name=data.get("name"),
            position=data.get("position"),
            inputs=data.get("inputs"),
            outputs=data.get("outputs"),
            parameters=data.get("parameters")
        )
    
    def process(self, input_data=None):
        """Process node with input data and return output"""
        raise NotImplementedError("Subclasses must implement this method")

class Connection:
    """Connection between two nodes"""
    
    def __init__(self, connection_id=None, source_id=None, target_id=None, 
                 source_handle=None, target_handle=None):
        self.id = connection_id or str(uuid.uuid4())
        self.source_id = source_id
        self.target_id = target_id
        self.source_handle = source_handle or "output"
        self.target_handle = target_handle or "input"
    
    def to_dict(self):
        """Convert connection to dictionary representation"""
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "sourceHandle": self.source_handle,
            "targetHandle": self.target_handle
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create connection from dictionary representation"""
        return cls(
            connection_id=data.get("id"),
            source_id=data.get("source"),
            target_id=data.get("target"),
            source_handle=data.get("sourceHandle"),
            target_handle=data.get("targetHandle")
        )

class Workflow:
    """Represents a complete workflow with nodes and connections"""
    
    def __init__(self, workflow_id=None, name=None, description=None, created_at=None, updated_at=None):
        self.id = workflow_id or str(uuid.uuid4())
        self.name = name or f"Workflow {self.id[:8]}"
        self.description = description or ""
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.nodes = {}  # Dict of node_id -> WorkflowNode
        self.connections = {}  # Dict of connection_id -> Connection
        self.status = "idle"
    
    def add_node(self, node):
        """Add a node to the workflow"""
        self.nodes[node.id] = node
        self.updated_at = datetime.now().isoformat()
        return node
    
    def remove_node(self, node_id):
        """Remove a node from the workflow"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Also remove any connections to/from this node
            connections_to_remove = []
            for conn_id, conn in self.connections.items():
                if conn.source_id == node_id or conn.target_id == node_id:
                    connections_to_remove.append(conn_id)
            
            for conn_id in connections_to_remove:
                del self.connections[conn_id]
            
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def add_connection(self, connection):
        """Add a connection between nodes"""
        if connection.source_id in self.nodes and connection.target_id in self.nodes:
            self.connections[connection.id] = connection
            self.updated_at = datetime.now().isoformat()
            return connection
        return None
    
    def remove_connection(self, connection_id):
        """Remove a connection"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def to_dict(self):
        """Convert workflow to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "connections": [conn.to_dict() for conn in self.connections.values()],
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create workflow from dictionary representation"""
        workflow = cls(
            workflow_id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
        
        # Load nodes
        for node_data in data.get("nodes", []):
            node = NodeRegistry.create_node(node_data.get("type"), node_data)
            workflow.nodes[node.id] = node
        
        # Load connections
        for conn_data in data.get("connections", []):
            conn = Connection.from_dict(conn_data)
            workflow.connections[conn.id] = conn
        
        return workflow

class WorkflowEngine:
    """Executes and manages workflows"""
    
    def __init__(self):
        self.workflows = {}  # Dict of workflow_id -> Workflow
        self.execution_cache = {}  # Cache for node execution results
    
    def load_workflow(self, workflow_data):
        """Load workflow from dictionary data"""
        workflow = Workflow.from_dict(workflow_data)
        self.workflows[workflow.id] = workflow
        return workflow
    
    def save_workflow(self, workflow_id):
        """Get workflow data for saving"""
        if workflow_id in self.workflows:
            return self.workflows[workflow_id].to_dict()
        return None
    
    def execute_workflow(self, workflow_id, input_data=None):
        """Execute a workflow with optional input data"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return {"error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        workflow.status = "running"
        
        # Clear execution cache
        self.execution_cache = {}
        
        try:
            # Find start nodes (those with no incoming connections)
            start_nodes = self._find_start_nodes(workflow)
            
            if not start_nodes:
                logger.warning(f"No start nodes found in workflow {workflow_id}")
                workflow.status = "error"
                return {"error": "No start nodes found"}
            
            # Execute each start node and continue the flow
            results = {}
            for node_id in start_nodes:
                if input_data and node_id in input_data:
                    node_input = input_data[node_id]
                else:
                    node_input = input_data
                
                node_result = self._execute_node(node_id, workflow, node_input)
                if node_result:
                    results[node_id] = node_result
            
            workflow.status = "completed"
            return results
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            workflow.status = "error"
            return {"error": str(e)}
    
    def _find_start_nodes(self, workflow):
        """Find nodes that have no incoming connections"""
        incoming_connections = {node_id: 0 for node_id in workflow.nodes}
        
        for conn in workflow.connections.values():
            if conn.target_id in incoming_connections:
                incoming_connections[conn.target_id] += 1
        
        return [node_id for node_id, count in incoming_connections.items() if count == 0]
    
    def _find_next_nodes(self, node_id, workflow):
        """Find nodes connected to the output of the given node"""
        next_nodes = []
        
        for conn in workflow.connections.values():
            if conn.source_id == node_id:
                next_nodes.append((conn.target_id, conn.source_handle, conn.target_handle))
        
        return next_nodes
    
    def _execute_node(self, node_id, workflow, input_data=None):
        """Execute a node and its downstream nodes"""
        # Check if we've already executed this node with the same input
        cache_key = f"{node_id}_{hash(str(input_data))}"
        if cache_key in self.execution_cache:
            return self.execution_cache[cache_key]
        
        if node_id not in workflow.nodes:
            logger.error(f"Node {node_id} not found in workflow")
            return None
        
        node = workflow.nodes[node_id]
        
        try:
            node.status = "running"
            node_output = node.process(input_data)
            node.status = "completed"
            
            # Cache the result
            self.execution_cache[cache_key] = node_output
            
            # Find and execute next nodes
            next_nodes = self._find_next_nodes(node_id, workflow)
            
            for next_node_id, source_handle, target_handle in next_nodes:
                # Determine the input for the next node based on connection handles
                if source_handle == "output" and node_output:
                    next_input = node_output
                else:
                    # Get specific output if available
                    next_input = node_output.get(source_handle.replace("output_", "")) if node_output else None
                
                # Execute next node
                self._execute_node(next_node_id, workflow, next_input)
            
            return node_output
            
        except Exception as e:
            logger.error(f"Error executing node {node_id}: {str(e)}")
            node.status = "error"
            return {"error": str(e)}

class NodeRegistry:
    """Registry for node types and their implementations"""
    
    _node_types = {}
    
    @classmethod
    def register(cls, node_type):
        """Decorator to register node types"""
        def register_node_type(node_class):
            cls._node_types[node_type] = node_class
            return node_class
        return register_node_type
    
    @classmethod
    def create_node(cls, node_type, node_data=None):
        """Create a node of the specified type"""
        if node_type not in cls._node_types:
            logger.error(f"Node type '{node_type}' not registered")
            raise ValueError(f"Node type '{node_type}' not registered")
        
        node_class = cls._node_types[node_type]
        
        if node_data:
            return node_class.from_dict(node_data)
        return node_class()
    
    @classmethod
    def get_all_node_types(cls):
        """Get all registered node types"""
        return list(cls._node_types.keys())
    
    @classmethod
    def get_node_info(cls, node_type):
        """Get information about a node type"""
        if node_type not in cls._node_types:
            return None
        
        node_class = cls._node_types[node_type]
        return {
            "type": node_type,
            "description": node_class.__doc__ or "",
            "inputs": getattr(node_class, "DEFAULT_INPUTS", {}),
            "outputs": getattr(node_class, "DEFAULT_OUTPUTS", {}),
            "parameters": getattr(node_class, "DEFAULT_PARAMETERS", {})
        }


# Register some basic node types

@NodeRegistry.register("InputNode")
class InputNode(WorkflowNode):
    """Node that serves as an entry point for workflow data"""
    
    DEFAULT_OUTPUTS = {"output": {"type": "any", "description": "Output data"}}
    DEFAULT_PARAMETERS = {
        "default_value": {"type": "any", "description": "Default value to output if no input is provided"}
    }
    
    def process(self, input_data=None):
        """Process input data or use default value"""
        if input_data is None:
            input_data = self.parameters.get("default_value")
        return input_data

@NodeRegistry.register("OutputNode")
class OutputNode(WorkflowNode):
    """Node that represents the final output of a workflow"""
    
    DEFAULT_INPUTS = {"input": {"type": "any", "description": "Input data to output"}}
    DEFAULT_PARAMETERS = {
        "output_key": {"type": "string", "description": "Key for the output data"}
    }
    
    def process(self, input_data=None):
        """Process and return input data"""
        output_key = self.parameters.get("output_key", "result")
        if output_key:
            return {output_key: input_data}
        return input_data

@NodeRegistry.register("IntentClassifierNode")
class IntentClassifierNode(WorkflowNode):
    """Node that classifies user intent"""
    
    DEFAULT_INPUTS = {"input": {"type": "string", "description": "User message"}}
    DEFAULT_OUTPUTS = {"output": {"type": "string", "description": "Classified intent"}}
    DEFAULT_PARAMETERS = {
        "use_gemini": {"type": "boolean", "default": True, "description": "Whether to use Gemini for classification"},
        "gemini_api_url": {"type": "string", "description": "Gemini API URL"},
        "gemini_api_key": {"type": "string", "description": "Gemini API key"}
    }
    
    def process(self, input_data=None):
        """Process user message and classify intent"""
        if not input_data:
            return {"intent": None}
        
        user_message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Import intent module
        from utils.intent import classify_intent_combined
        
        # Get parameters
        use_gemini = self.parameters.get("use_gemini", True)
        gemini_api_url = self.parameters.get("gemini_api_url")
        gemini_api_key = self.parameters.get("gemini_api_key")
        
        if use_gemini and gemini_api_url and gemini_api_key:
            intent = classify_intent_combined(user_message, gemini_api_url, gemini_api_key)
        else:
            intent = classify_intent_combined(user_message)
        
        return {"intent": intent}

@NodeRegistry.register("RAGNode")
class RAGNode(WorkflowNode):
    """Node that processes RAG requests"""
    
    DEFAULT_INPUTS = {"input": {"type": "string", "description": "User query"}}
    DEFAULT_OUTPUTS = {"output": {"type": "string", "description": "RAG response"}}
    DEFAULT_PARAMETERS = {}
    
    def process(self, input_data=None):
        """Process user query and return RAG response"""
        if not input_data:
            return {"response": "No input provided"}
        
        user_message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Import RAG module
        from chat_routes.chatbotrag import rag_chat
        
        try:
            response = rag_chat(user_message)
            return {"response": response}
        except Exception as e:
            logger.error(f"Error in RAG processing: {str(e)}")
            return {"response": "Error processing your request", "error": str(e)}

@NodeRegistry.register("SQLNode")
class SQLNode(WorkflowNode):
    """Node that processes SQL queries"""
    
    DEFAULT_INPUTS = {"input": {"type": "string", "description": "User query"}}
    DEFAULT_OUTPUTS = {"output": {"type": "string", "description": "SQL response"}}
    DEFAULT_PARAMETERS = {
        "db_path": {"type": "string", "description": "Path to SQLite database"}
    }
    
    def process(self, input_data=None):
        """Process user query and return SQL response"""
        if not input_data:
            return {"response": "No input provided"}
        
        user_message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Import SQL module
        from utils.utils import execute_sql_query
        
        db_path = self.parameters.get("db_path")
        if not db_path:
            return {"response": "No database path specified", "error": "No database path specified"}
        
        try:
            sql_query = f"SELECT '{user_message}'"  # This is a placeholder. In reality, you'd generate real SQL
            result = execute_sql_query(sql_query, db_path)
            return {"response": str(result), "query": sql_query}
        except Exception as e:
            logger.error(f"Error in SQL processing: {str(e)}")
            return {"response": "Error processing your request", "error": str(e)}

@NodeRegistry.register("FHIRPatientNode")
class FHIRPatientNode(WorkflowNode):
    """Node that processes FHIR patient requests"""
    
    DEFAULT_INPUTS = {"input": {"type": "string", "description": "User query with patient ID"}}
    DEFAULT_OUTPUTS = {"output": {"type": "string", "description": "Patient information"}}
    DEFAULT_PARAMETERS = {}
    
    def process(self, input_data=None):
        """Process user query and return patient information"""
        if not input_data:
            return {"response": "No input provided"}
        
        user_message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Import MCP patient module
        from utils.mcpconnection import get_patient_info_from_mcp, extract_patient_id
        
        try:
            patient_id = extract_patient_id(user_message)
            if not patient_id:
                return {"response": "No patient ID found in the query"}
            
            response = get_patient_info_from_mcp(user_message)
            if isinstance(response, dict) and "response" in response:
                return {"response": response["response"]}
            return {"response": "No data returned from MCP server"}
        except Exception as e:
            logger.error(f"Error in FHIR patient processing: {str(e)}")
            return {"response": "Error retrieving patient information", "error": str(e)}

@NodeRegistry.register("ScriptNode")
class ScriptNode(WorkflowNode):
    """Node that processes script messages (greetings, etc.)"""
    
    DEFAULT_INPUTS = {"input": {"type": "string", "description": "User message"}}
    DEFAULT_OUTPUTS = {"output": {"type": "string", "description": "Script response"}}
    DEFAULT_PARAMETERS = {}
    
    def process(self, input_data=None):
        """Process user message and return script response"""
        if not input_data:
            return {"response": "Hello! How can I help you?"}
        
        user_message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Import script handler
        from chat_routes.Scripts import handle_script_message
        
        try:
            response = handle_script_message(user_message)
            return {"response": response}
        except Exception as e:
            logger.error(f"Error in script processing: {str(e)}")
            return {"response": "Hello! How can I help you?", "error": str(e)}

@NodeRegistry.register("ConditionalNode")
class ConditionalNode(WorkflowNode):
    """Node that routes flow based on conditions"""
    
    DEFAULT_INPUTS = {"input": {"type": "any", "description": "Input data"}}
    DEFAULT_OUTPUTS = {
        "true_output": {"type": "any", "description": "Output when condition is true"},
        "false_output": {"type": "any", "description": "Output when condition is false"}
    }
    DEFAULT_PARAMETERS = {
        "condition_type": {
            "type": "string", 
            "enum": ["equals", "contains", "greater_than", "less_than"],
            "default": "equals",
            "description": "Type of condition to evaluate"
        },
        "value_path": {
            "type": "string",
            "description": "Path to value in input data (e.g. 'intent')"
        },
        "comparison_value": {
            "type": "any",
            "description": "Value to compare against"
        }
    }
    
    def process(self, input_data=None):
        """Process input data based on condition"""
        if input_data is None:
            return {"true_output": None, "false_output": input_data}
        
        # Extract parameters
        condition_type = self.parameters.get("condition_type", "equals")
        value_path = self.parameters.get("value_path", "")
        comparison_value = self.parameters.get("comparison_value")
        
        # Get value from input data using the path
        input_value = input_data
        if value_path:
            for key in value_path.split('.'):
                if isinstance(input_value, dict) and key in input_value:
                    input_value = input_value[key]
                else:
                    input_value = None
                    break
        
        # Evaluate condition
        condition_result = False
        
        try:
            if condition_type == "equals":
                condition_result = input_value == comparison_value
            elif condition_type == "contains":
                if isinstance(input_value, str) and isinstance(comparison_value, str):
                    condition_result = comparison_value in input_value
                elif isinstance(input_value, (list, tuple)):
                    condition_result = comparison_value in input_value
            elif condition_type == "greater_than":
                condition_result = input_value > comparison_value
            elif condition_type == "less_than":
                condition_result = input_value < comparison_value
        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            condition_result = False
        
        # Return appropriate output
        if condition_result:
            return {"true_output": input_data, "false_output": None}
        else:
            return {"true_output": None, "false_output": input_data}

@NodeRegistry.register("ChatbotNode")
class ChatbotNode(WorkflowNode):
    """Node that integrates the entire chatbot processing pipeline"""
    
    DEFAULT_INPUTS = {"input": {"type": "string", "description": "User message"}}
    DEFAULT_OUTPUTS = {"output": {"type": "string", "description": "Bot response"}}
    DEFAULT_PARAMETERS = {
        "language": {"type": "string", "default": "vi", "description": "Language for the response"},
        "gemini_api_url": {"type": "string", "description": "Gemini API URL"},
        "gemini_api_key": {"type": "string", "description": "Gemini API key"},
        "db_path": {"type": "string", "description": "Path to SQLite database"}
    }
    
    def process(self, input_data=None):
        """Process user message through the entire chatbot pipeline"""
        if not input_data:
            return {"response": "Hello! How can I help you?"}
        
        user_message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Get parameters
        language = self.parameters.get("language", "vi")
        gemini_api_url = self.parameters.get("gemini_api_url")
        gemini_api_key = self.parameters.get("gemini_api_key")
        db_path = self.parameters.get("db_path")
        
        # Classify intent
        from utils.intent import classify_intent_combined
        intent = classify_intent_combined(user_message, gemini_api_url, gemini_api_key, language)
        
        # Process based on intent
        if intent == "script":
            from chat_routes.Scripts import handle_script_message
            response = handle_script_message(user_message)
        
        elif intent == "fhir_patient":
            from utils.mcpconnection import get_patient_info_from_mcp
            mcp_response = get_patient_info_from_mcp(user_message)
            if isinstance(mcp_response, dict) and "response" in mcp_response:
                response = mcp_response["response"]
            else:
                response = "Could not retrieve patient information"
        
        elif intent == "sql":
            from utils.utils import execute_sql_query
            try:
                sql_query = f"SELECT '{user_message}'"  # Placeholder
                result = execute_sql_query(sql_query, db_path)
                response = str(result)
            except Exception as e:
                response = f"Error executing SQL query: {str(e)}"
        
        elif intent == "rag":
            from chat_routes.chatbotrag import rag_chat
            response = rag_chat(user_message)
        
        else:
            response = "I'm not sure how to respond to that"
        
        # Analyze sentiment
        sentiment = "neutral"
        try:
            from utils.utils import analyze_sentiment
            sentiment = analyze_sentiment(user_message, gemini_api_url, gemini_api_key)
        except:
            pass
        
        return {
            "response": response,
            "intent": intent,
            "sentiment": sentiment
        }