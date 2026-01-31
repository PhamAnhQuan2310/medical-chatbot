
import React, { useState, useRef, useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
  type Node,
  type Edge,
  type Connection,
  type ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
import './WorkflowDesigner.css';
import NodePanel from './NodePanel';
import CustomNode from './CustomNode';
import WorkflowToolbar from './WorkflowToolbar';
import WorkflowSidebar from './WorkflowSidebar';

// Define node types for the workflow
type NodeType =
  | 'InputNode'
  | 'OutputNode'
  | 'IntentClassifierNode'
  | 'RAGNode'
  | 'SQLNode'
  | 'FHIRPatientNode';

interface NodeData {
  label: string;
  nodeType: NodeType;
  parameters: Record<string, string | number | boolean | undefined>;
}

interface Workflow {
  id: string | null;
  name: string;
  nodes: Node<NodeData>[];
  edges: Edge[];
}

interface NodeTypeConfig {
  type: NodeType;
  label: string;
}

// Node types mapping
const nodeTypes = {
  customNode: CustomNode,
};

const WorkflowDesigner: React.FC = () => {
  // Workflow states
  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node<NodeData> | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [edgeLabel, setEdgeLabel] = useState<string | undefined>(undefined);
  const [workflowName, setWorkflowName] = useState<string>('My Workflow');
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingDefault, setIsLoadingDefault] = useState<boolean>(true);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

  const chatbotNodeTypes: NodeTypeConfig[] = [
    { type: 'InputNode', label: 'Đầu vào' },
    { type: 'OutputNode', label: 'Đầu ra' },
    { type: 'IntentClassifierNode', label: 'Phân loại ý định' },
    { type: 'RAGNode', label: 'RAG' },
    { type: 'SQLNode', label: 'SQL' },
    { type: 'FHIRPatientNode', label: 'Thông tin bệnh nhân' },
  ];

  // Load available node types from backend
  const [availableNodeTypes, setAvailableNodeTypes] = useState<NodeTypeConfig[]>(chatbotNodeTypes);

  // Handle keydown events for deleting nodes or edges
  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
        return;
      }
      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (selectedNode) {
          setNodes((nodes) => nodes.filter((node) => node.id !== selectedNode.id));
          setEdges((edges) =>
            edges.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id)
          );
          setSelectedNode(null);
        } else if (selectedEdge) {
          setEdges((eds) =>
            eds.map((edge) => {
              if (edge.id === selectedEdge.id) {
                return { ...edge, label: '' };
              }
              return edge;
            })
          );
          setSelectedEdge(null);
        }
      } else if (event.key === 'Escape') {
        setSelectedNode(null);
        setSelectedEdge(null);
      }
    },
    [selectedNode, selectedEdge, setNodes, setEdges]
  );

  // Fetch available node types
  const fetchNodeTypes = async () => {
    try {
      const response = await fetch('http://localhost:8000/workflow/node_types');
      const data: { success: boolean; node_types?: NodeTypeConfig[] } = await response.json();
      if (data.success && data.node_types && data.node_types.length > 0) {
        setAvailableNodeTypes(data.node_types);
      } else {
        setAvailableNodeTypes(chatbotNodeTypes);
      }
    } catch (error) {
      console.error('Error fetching node types:', error);
      setAvailableNodeTypes(chatbotNodeTypes);
    }
  };

  // Fetch available workflows
  const fetchWorkflows = async () => {
    try {
      const response = await fetch('http://localhost:8000/workflow/list');
      const data: { success: boolean; workflows?: Workflow[] } = await response.json();
      if (data.success) {
        setWorkflows(data.workflows || []);
      }
    } catch (error) {
      console.error('Error fetching workflows:', error);
    }
  };

  // Load default workflow
  const loadDefaultWorkflow = async () => {
  try {
    setIsLoadingDefault(true);

    console.log('Checking for existing default workflow...');

    try {
      const settingsResponse = await fetch('http://localhost:8000/settings/get_default_workflows');
      const settingsData: { success: boolean; default_workflow?: Workflow } = await settingsResponse.json();

      if (settingsData.success && settingsData.default_workflow) {
        console.log('Found existing default workflow, loading...');
        const workflow = settingsData.default_workflow;
        setWorkflowName(workflow.name);
        setNodes(workflow.nodes || []);
        setEdges(workflow.edges || []);
        setCurrentWorkflowId(workflow.id);
        return;
      }
    } catch {
      // Không dùng biến settingsError nếu không cần, tránh warning "is defined but never used"
      console.log('No existing default workflow found, will generate new one');
    }

    console.log('Generating new system workflow...');
    const generateResponse = await fetch('http://localhost:8000/workflow/generate_system_workflow');
    const generateData: { success: boolean; workflow?: Workflow } = await generateResponse.json();

    if (generateData.success && generateData.workflow) {
      const workflow = generateData.workflow;
      setWorkflowName(workflow.name);
      setNodes(workflow.nodes || []);
      setEdges(workflow.edges || []);
      setCurrentWorkflowId(null);
    } else {
      setWorkflowName('New Workflow');
      setNodes([]);
      setEdges([]);
      setCurrentWorkflowId(null);
    }
  } catch (error) {
    console.error('Error in loadDefaultWorkflow:', error);
    setWorkflowName('New Workflow');
    setNodes([]);
    setEdges([]);
    setCurrentWorkflowId(null);
  } finally {
    setIsLoadingDefault(false);
  }
};

  // Set up event listeners and initial data fetching
  useEffect(() => {
    window.addEventListener('keydown', onKeyDown);
    fetchNodeTypes();
    fetchWorkflows();
    loadDefaultWorkflow();

    return () => {
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [onKeyDown]);

  // Handle edge click
  const onEdgeClick = useCallback((_: React.MouseEvent, edge: Edge) => {
    setSelectedEdge(edge);
    setEdgeLabel(edge.label ? String(edge.label) : '');
  }, []);

  // Update edge label
  const updateEdgeLabel = () => {
    if (!selectedEdge) return;

    setEdges((eds) =>
      eds.map((edge) => {
        if (edge.id === selectedEdge.id) {
          return { ...edge, label: edgeLabel || '' };
        }
        return edge;
      })
    );

    setSelectedEdge(null);
    setEdgeLabel(undefined);
  };

  // Cancel edge edit
  const cancelEdgeEdit = () => {
    setSelectedEdge(null);
    setEdgeLabel(undefined);
  };

  // Connection handlers
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges]
  );

  // Drag & drop functionality
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      console.log('Drop event triggered');

      if (!reactFlowInstance) {
        console.error('ReactFlow instance is not initialized');
        return;
      }

      const nodeType = event.dataTransfer.getData('application/reactflow') as NodeType;
      console.log('Node type from drop event:', nodeType);

      if (!nodeType) {
        console.error('No node type data found in drag event');
        return;
      }

      const nodeName = event.dataTransfer.getData('nodeName') || nodeType;

      try {
        const reactFlowBounds = reactFlowWrapper.current!.getBoundingClientRect();
        const position = reactFlowInstance.project({
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        });

        console.log('Calculated position:', position);

        const newNode: Node<NodeData> = {
          id: `${nodeType}_${Date.now()}`,
          type: 'customNode',
          position,
          data: {
            label: nodeName,
            nodeType,
            parameters: {},
          },
        };

        console.log('Adding new node:', newNode);
        setNodes((nds) => nds.concat(newNode));
      } catch (error) {
        console.error('Error during node drop:', error);
      }
    },
    [reactFlowInstance, setNodes]
  );

  // Node selection handler
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node<NodeData>) => {
    setSelectedEdge(null);
    setSelectedNode(node);
  }, []);

  // Delete node
  const deleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nodes) => nodes.filter((node) => node.id !== nodeId));
      setEdges((edges) =>
        edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
      );
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode(null);
      }
    },
    [selectedNode, setNodes, setEdges]
  );

  // Save workflow
  const saveWorkflow = async () => {
    if (!workflowName) {
      alert('Please enter a workflow name');
      return;
    }

    setIsLoading(true);

    try {
      const workflowData: Workflow = {
        id: currentWorkflowId,
        name: workflowName,
        nodes,
        edges,
      };

      const response = await fetch('http://localhost:8000/workflow/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflowData),
      });

      const result: { success: boolean; workflow_id?: string; message?: string } = await response.json();

      if (result.success && result.workflow_id) {
        setCurrentWorkflowId(result.workflow_id);
        alert('Workflow saved successfully!');
        await fetchWorkflows();
      } else {
        throw new Error(result.message || 'Failed to save workflow');
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      alert(`Error saving workflow: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Load workflow
  const loadWorkflow = async (workflowId: string) => {
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/workflow/${workflowId}`);
      const data: { success: boolean; workflow?: Workflow; message?: string } = await response.json();

      if (data.success && data.workflow) {
        setWorkflowName(data.workflow.name);
        setNodes(data.workflow.nodes || []);
        setEdges(data.workflow.edges || []);
        setCurrentWorkflowId(workflowId);
      } else {
        throw new Error(data.message || 'Failed to load workflow');
      }
    } catch (error) {
      console.error('Error loading workflow:', error);
      alert(`Error loading workflow: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Create new workflow
  const createNewWorkflow = () => {
    setWorkflowName('My Workflow');
    setNodes([]);
    setEdges([]);
    setCurrentWorkflowId(null);
    setSelectedNode(null);
    setSelectedEdge(null);
  };

  // Update node parameters
  const updateNodeParameters = (id: string, parameters: Record<string, string | number | boolean | undefined>) => {
  setNodes((nds) =>
    nds.map((node) => {
      if (node.id === id) {
        return {
          ...node,
          data: {
            ...node.data,
            parameters,
          },
        };
      }
      return node;
    })
  );
};

  return (
    <div className="workflow-designer">
      {isLoadingDefault ? (
        <div className="workflow-loading">
          <div>Đang tải workflow mặc định...</div>
        </div>
      ) : (
        <>
          <WorkflowToolbar
            workflowName={workflowName}
            setWorkflowName={setWorkflowName}
            saveWorkflow={saveWorkflow}
            createNewWorkflow={createNewWorkflow}
            isLoading={isLoading}
            workflows={workflows}
            loadWorkflow={loadWorkflow}
            currentWorkflowId={currentWorkflowId}
          />
          <div className="workflow-container">
            <NodePanel nodeTypes={availableNodeTypes} workflowType="chatbot" />
            <div className="reactflow-wrapper" ref={reactFlowWrapper}>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onInit={setReactFlowInstance}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onNodeClick={onNodeClick}
                onEdgeClick={onEdgeClick}
                nodeTypes={nodeTypes}
                fitView
              >
                <Controls />
                <MiniMap />
                <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
                {selectedEdge && (
                  <Panel position="top-left" className="edge-panel">
                    <div className="edge-panel-content" onClick={(e) => e.stopPropagation()}>
                      <div className="edge-panel-title">Chỉnh sửa điều kiện kết nối:</div>
                      <input
                        type="text"
                        value={edgeLabel ?? ''}
                        onChange={(e) => setEdgeLabel(e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        onKeyDown={(e) => e.stopPropagation()}
                        placeholder="Nhập điều kiện"
                        className="edge-panel-input"
                        autoFocus
                      />
                      <div className="edge-panel-buttons">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            updateEdgeLabel();
                          }}
                          className="edge-panel-button update"
                        >
                          Cập nhật
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            cancelEdgeEdit();
                          }}
                          className="edge-panel-button cancel"
                        >
                          Hủy
                        </button>
                      </div>
                    </div>
                  </Panel>
                )}
              </ReactFlow>
            </div>
            <WorkflowSidebar
              selectedNode={selectedNode}
              updateNodeParameters={updateNodeParameters}
              deleteNode={deleteNode}
            />
          </div>
        </>
      )}
    </div>
  );
};

export default WorkflowDesigner;