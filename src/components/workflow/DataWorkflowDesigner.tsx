import React, { useState, useRef, useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
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
  | 'ConditionalNode'
  | 'IntentClassifierNode'
  | 'RAGNode'
  | 'OutputNode'
  | 'DatabaseNode';

// Define parameters type (aligned with WorkflowSidebar)
interface NodeParameters {
  [key: string]: string | number | boolean | undefined;
}

interface NodeData {
  label: string;
  nodeType: NodeType;
  parameters: NodeParameters;
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

// Define initial nodes for the data workflow (fallback)
const initialNodes: Node<NodeData>[] = [
  {
    id: 'data-input',
    type: 'customNode',
    position: { x: 100, y: 150 },
    data: {
      label: 'Dữ liệu',
      nodeType: 'InputNode',
      parameters: {},
    },
  },
  {
    id: 'condition',
    type: 'customNode',
    position: { x: 350, y: 100 },
    data: {
      label: 'Có phải dạng bảng không?',
      nodeType: 'ConditionalNode',
      parameters: {},
    },
  },
  {
    id: 'no-path',
    type: 'customNode',
    position: { x: 550, y: 100 },
    data: {
      label: 'Dự đoán ngữ cảnh',
      nodeType: 'IntentClassifierNode',
      parameters: {},
    },
  },
  {
    id: 'yes-path',
    type: 'customNode',
    position: { x: 350, y: 250 },
    data: {
      label: 'Dự đoán ngữ cảnh',
      nodeType: 'IntentClassifierNode',
      parameters: {},
    },
  },
  {
    id: 'vector-db-top',
    type: 'customNode',
    position: { x: 750, y: 100 },
    data: {
      label: 'Lưu trong vector database',
      nodeType: 'RAGNode',
      parameters: {},
    },
  },
  {
    id: 'vector-db-middle',
    type: 'customNode',
    position: { x: 550, y: 250 },
    data: {
      label: 'Lưu trong vector database',
      nodeType: 'RAGNode',
      parameters: {},
    },
  },
  {
    id: 'json-file',
    type: 'customNode',
    position: { x: 350, y: 370 },
    data: {
      label: 'Lưu ngữ cảnh vào file json dưới dạng dict',
      nodeType: 'OutputNode',
      parameters: {},
    },
  },
  {
    id: 'chatbot-db',
    type: 'customNode',
    position: { x: 1000, y: 250 },
    data: {
      label: 'Kho Dữ liệu cho chatbot',
      nodeType: 'OutputNode',
      parameters: {},
    },
  },
];

// Define initial edges for the data workflow (fallback)
const initialEdges: Edge[] = [
  { id: 'e1-2', source: 'data-input', target: 'condition' },
  { id: 'e2-3', source: 'condition', target: 'no-path', label: 'Không' },
  { id: 'e2-4', source: 'condition', target: 'yes-path', label: 'Có' },
  { id: 'e3-5', source: 'no-path', target: 'vector-db-top', label: 'Bao gồm ngữ cảnh' },
  { id: 'e4-6', source: 'yes-path', target: 'vector-db-middle' },
  { id: 'e4-7', source: 'yes-path', target: 'json-file' },
  { id: 'e5-8', source: 'vector-db-top', target: 'chatbot-db' },
  { id: 'e6-8', source: 'vector-db-middle', target: 'chatbot-db' },
  { id: 'e7-8', source: 'json-file', target: 'chatbot-db' },
];

const DataWorkflowDesigner: React.FC = () => {
  // Workflow states
  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node<NodeData> | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [edgeLabel, setEdgeLabel] = useState<string>('');
  const [workflowName, setWorkflowName] = useState<string>('Xử lý dữ liệu');
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingDefault, setIsLoadingDefault] = useState<boolean>(true);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

  // Define node types for data workflow
  const dataNodeTypes: NodeTypeConfig[] = [
    { type: 'InputNode', label: 'Dữ liệu' },
    { type: 'ConditionalNode', label: 'Điều kiện' },
    { type: 'IntentClassifierNode', label: 'Dự đoán ngữ cảnh' },
    { type: 'RAGNode', label: 'Lưu trong vector DB' },
    { type: 'OutputNode', label: 'Lưu vào file JSON' },
    { type: 'DatabaseNode', label: 'Kho dữ liệu' },
  ];

  // Load default data workflow
  const loadDefaultDataWorkflow = useCallback(async () => {
    try {
      setIsLoadingDefault(true);

      console.log('Checking for existing default data workflow...');

      try {
        const settingsResponse = await fetch('http://localhost:8000/settings/get_default_workflows');
        const settingsData = await settingsResponse.json();

        if (settingsData.success && settingsData.default_data_workflow) {
          console.log('Found existing default data workflow, loading...');
          const workflow: Workflow = settingsData.default_data_workflow;
          setWorkflowName(workflow.name);
          setNodes(workflow.nodes || []);
          setEdges(workflow.edges || []);
          setCurrentWorkflowId(workflow.id);
          return;
        }
      } catch {
        console.log('No existing default workflow found, will generate new one');
      }

      console.log('Generating new system data workflow...');
      const generateResponse = await fetch('http://localhost:8000/workflow/generate_system_data_workflow');
      const generateData = await generateResponse.json();

      if (generateData.success && generateData.workflow) {
        const workflow: Workflow = generateData.workflow;
        setWorkflowName(workflow.name);
        setNodes(workflow.nodes || []);
        setEdges(workflow.edges || []);
        setCurrentWorkflowId(null);
      } else {
        setWorkflowName('Xử lý dữ liệu mới');
        setNodes(initialNodes);
        setEdges(initialEdges);
        setCurrentWorkflowId(null);
      }
    } catch (error) {
      console.error('Error in loadDefaultDataWorkflow:', error);
      setWorkflowName('Xử lý dữ liệu mới');
      setNodes(initialNodes);
      setEdges(initialEdges);
      setCurrentWorkflowId(null);
    } finally {
      setIsLoadingDefault(false);
    }
  }, [setNodes, setEdges]);

  // Handle keydown events for deleting nodes or edges
  const onKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
        return;
      }

      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (selectedNode) {
          setNodes((nodes) => nodes.filter((node) => node.id !== selectedNode.id));
          setEdges((edges) => edges.filter(
            (edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id
          ));
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

  // Add event listener for keydown and load default workflow
  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const response = await fetch('http://localhost:8000/workflow/list');
        const data = await response.json();
        if (data.success && data.workflows) {
          const dataWorkflows = data.workflows.filter((w: Workflow) =>
            w.name.toLowerCase().includes('data') || w.name.toLowerCase().includes('dữ liệu')
          );
          setWorkflows(dataWorkflows);
        }
      } catch (error) {
        console.error('Error fetching workflows:', error);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    fetchWorkflows();
    loadDefaultDataWorkflow();

    return () => {
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [onKeyDown, loadDefaultDataWorkflow]);

  // Delete node
  const deleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nodes) => nodes.filter((node) => node.id !== nodeId));
      setEdges((edges) => edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode(null);
      }
    },
    [selectedNode, setNodes, setEdges]
  );

  // Handle edge click
  const onEdgeClick = useCallback((_: React.MouseEvent, edge: Edge) => {
    setSelectedNode(null);
    setSelectedEdge(edge);
    setEdgeLabel(typeof edge.label === 'string' ? edge.label : String(edge.label ?? ''));
  }, []);

  // Update edge label
  const updateEdgeLabel = () => {
    if (!selectedEdge) return;

    setEdges((eds) =>
      eds.map((edge) => {
        if (edge.id === selectedEdge.id) {
          return { ...edge, label: edgeLabel };
        }
        return edge;
      })
    );

    setSelectedEdge(null);
  };

  // Cancel edge edit
  const cancelEdgeEdit = () => {
    setSelectedEdge(null);
    setEdgeLabel('');
  };

  // Handle Enter key for edge label input
  const handleEdgeLabelKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      updateEdgeLabel();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdgeEdit();
    }
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

  // Save workflow
  const saveWorkflow = async () => {
    if (!workflowName) {
      alert('Vui lòng nhập tên workflow' as string);
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

      const result = await response.json();

      if (result.success) {
        setCurrentWorkflowId(result.workflow_id);
        alert('Workflow đã được lưu thành công!' as string);

        const workflowsResponse = await fetch('http://localhost:8000/workflow/list');
        const workflowsData = await workflowsResponse.json();
        if (workflowsData.workflows) {
          const dataWorkflows = workflowsData.workflows.filter((w: Workflow) =>
            w.name.toLowerCase().includes('data') || w.name.toLowerCase().includes('dữ liệu')
          );
          setWorkflows(dataWorkflows);
        }
      } else {
        throw new Error(result.message || 'Lỗi khi lưu workflow');
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      alert(`Lỗi khi lưu workflow: ${(error as Error).message}` as string);
    } finally {
      setIsLoading(false);
    }
  };

  // Load workflow
  const loadWorkflow = async (workflowId: string) => {
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/workflow/${workflowId}`);
      const data = await response.json();

      if (data.success) {
        setWorkflowName(data.workflow.name);
        setNodes(data.workflow.nodes);
        setEdges(data.workflow.edges);
        setCurrentWorkflowId(workflowId);
      } else {
        throw new Error(data.message || 'Lỗi khi tải workflow');
      }
    } catch (error) {
      console.error('Error loading workflow:', error);
      alert(`Lỗi khi tải workflow: ${(error as Error).message}` as string);
    } finally {
      setIsLoading(false);
    }
  };

  // Create new workflow
  const createNewWorkflow = () => {
    setWorkflowName('Xử lý dữ liệu mới');
    setNodes([]);
    setEdges([]);
    setCurrentWorkflowId(null);
    setSelectedNode(null);
    setSelectedEdge(null);
  };

  // Update node parameters
  const updateNodeParameters = (id: string, parameters: NodeParameters) => {
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
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '400px',
          }}
        >
          <div>Đang tải data workflow mặc định...</div>
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
            <NodePanel key="data-workflow-node-panel" nodeTypes={dataNodeTypes} workflowType="data" />

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
              </ReactFlow>
            </div>

            <WorkflowSidebar
              selectedNode={selectedNode}
              updateNodeParameters={updateNodeParameters}
              deleteNode={deleteNode}
            />
          </div>

          {selectedEdge && (
            <div className="edge-edit-modal" onClick={() => setSelectedEdge(null)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h3>Chỉnh sửa điều kiện kết nối</h3>
                <input
                  type="text"
                  value={edgeLabel}
                  onChange={(e) => setEdgeLabel(e.target.value)}
                  onKeyDown={handleEdgeLabelKeyDown}
                  placeholder="Nhập điều kiện"
                  autoFocus
                />
                <div className="button-container">
                  <button className="cancel" onClick={cancelEdgeEdit}>
                    Hủy
                  </button>
                  <button className="update" onClick={updateEdgeLabel}>
                    Cập nhật
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DataWorkflowDesigner;