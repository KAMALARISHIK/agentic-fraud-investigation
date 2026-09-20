import React, { useState, useRef, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { ZoomIn, ZoomOut, Maximize2, Layers, Info, X } from 'lucide-react';
import { GraphData, GraphNode, GraphEdge } from '../../lib/api';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { EmptyState } from '../ui/EmptyState';

interface CaseGraphViewProps {
  graphData: GraphData | null;
  isLoading?: boolean;
}

const TYPE_COLORS: Record<string, string> = {
  Customer: '#D97757',       // Terracotta
  Card: '#2B6CB0',           // Navy blue
  Transaction: '#C0392B',    // Crimson red
  DeviceProfile: '#805AD5',  // Purple
  EmailDomain: '#319795',    // Teal
  BillingRegion: '#D69E2E',  // Amber
  ClosedCase: '#718096',     // Gray
};

interface GraphDisplayNode {
  id: string;
  name: string;
  type: string;
  color: string;
  properties?: Record<string, any>;
  val?: number;
}

export const CaseGraphView: React.FC<CaseGraphViewProps> = ({ graphData, isLoading }) => {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<GraphDisplayNode | null>(null);
  const [dimensions, setDimensions] = useState({ width: 700, height: 500 });

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 700,
          height: Math.max(450, containerRef.current.clientHeight || 500),
        });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const formattedData = useMemo(() => {
    if (!graphData || !graphData.nodes?.length) {
      return { nodes: [], links: [] };
    }

    const nodeIds = new Set(graphData.nodes.map((n) => n.id));

    const nodes = graphData.nodes.map((n) => ({
      id: n.id,
      name: n.label || n.id,
      type: n.type || 'Entity',
      properties: n.properties || {},
      color: TYPE_COLORS[n.type] || '#4A5568',
      val: n.type === 'Customer' ? 14 : n.type === 'Card' ? 11 : n.type === 'Transaction' ? 8 : 6,
    }));

    // Filter out dangling edges
    const links = (graphData.edges || [])
      .filter((e) => nodeIds.has(e.from_id) && nodeIds.has(e.to_id))
      .map((e) => ({
        source: e.from_id,
        target: e.to_id,
        type: e.type,
        properties: e.properties || {},
      }));

    return { nodes, links };
  }, [graphData]);

  if (!isLoading && (!graphData || !graphData.nodes?.length)) {
    return (
      <EmptyState
        title="No graph entities available"
        description="This case has no connected graph nodes in TigerGraph yet."
      />
    );
  }

  return (
    <div className="relative w-full rounded-xl border border-[#E8E6DC] bg-[#FFFFFF] overflow-hidden" ref={containerRef}>
      {/* Graph Toolbar */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-2 bg-white/90 backdrop-blur-xs p-1.5 px-3 rounded-xl border border-[#E8E6DC] shadow-xs text-xs">
        <span className="font-semibold text-[#141413] flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-[#D97757]" />
          TigerGraph Subgraph ({formattedData.nodes.length} nodes, {formattedData.links.length} edges)
        </span>
      </div>

      {/* Graph Zoom Controls */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1 bg-white/90 backdrop-blur-xs p-1 rounded-xl border border-[#E8E6DC] shadow-xs">
        <button
          onClick={() => fgRef.current?.zoom(fgRef.current.zoom() * 1.3, 400)}
          className="p-1.5 hover:bg-[#FAF9F5] rounded-lg text-[#6B6A65] hover:text-[#141413] transition-colors cursor-pointer"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={() => fgRef.current?.zoom(fgRef.current.zoom() / 1.3, 400)}
          className="p-1.5 hover:bg-[#FAF9F5] rounded-lg text-[#6B6A65] hover:text-[#141413] transition-colors cursor-pointer"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={() => fgRef.current?.zoomToFit(400, 30)}
          className="p-1.5 hover:bg-[#FAF9F5] rounded-lg text-[#6B6A65] hover:text-[#141413] transition-colors cursor-pointer"
          title="Fit View"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* 2D Canvas Force Graph */}
      <div className="h-[500px] w-full bg-[#FAF9F5]/40">
        <ForceGraph2D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={formattedData}
          nodeLabel={(node: any) => `${node.type}: ${node.name}`}
          nodeColor={(node: any) => node.color}
          nodeRelSize={4}
          linkColor={() => '#D5D3C8'}
          linkWidth={1.5}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.1}
          onNodeClick={(node: any) => setSelectedNode(node)}
          cooldownTicks={100}
          onEngineStop={() => fgRef.current?.zoomToFit(400, 40)}
        />
      </div>

      {/* Color Legend Footer */}
      <div className="p-3 border-t border-[#E8E6DC] bg-[#FAF9F5] flex flex-wrap items-center justify-between gap-3 text-[11px] text-[#6B6A65]">
        <div className="flex flex-wrap items-center gap-3">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span className="font-medium text-[#141413]">{type}</span>
            </div>
          ))}
        </div>
        <span className="text-[10px]">Click any node for properties</span>
      </div>

      {/* Node Details Slide-in Panel */}
      {selectedNode && (
        <div className="absolute bottom-12 right-3 z-20 w-72 bg-white rounded-xl border border-[#E8E6DC] shadow-xl p-4 text-xs">
          <div className="flex items-start justify-between pb-2 mb-2 border-b border-[#E8E6DC]">
            <div>
              <Badge
                variant="neutral"
                size="sm"
                className="mb-1 text-[10px]"
                style={{ borderColor: selectedNode.color, color: selectedNode.color }}
              >
                {selectedNode.type}
              </Badge>
              <h4 className="font-semibold text-sm text-[#141413] break-all">{selectedNode.name || selectedNode.id}</h4>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="p-1 text-[#6B6A65] hover:text-[#141413] rounded-md hover:bg-[#FAF9F5] cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            <div className="text-[#6B6A65]">
              <span className="font-medium text-[#141413]">Node ID:</span> {selectedNode.id}
            </div>
            {selectedNode.properties &&
              Object.entries(selectedNode.properties).map(([key, val]) => (
                <div key={key} className="text-[#6B6A65] break-words">
                  <span className="font-medium text-[#141413]">{key}:</span> {String(val)}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};
