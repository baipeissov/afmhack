export type NodeType = "account" | "wallet" | "phone" | "victim" | "cluster" | "exchange";

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  centrality: number; // 0..1, drives size
  target?: boolean;
  x?: number; // precomputed layout coords (0..100 viewBox space)
  y?: number;
}

export type EdgeKind = "money" | "referral" | "device" | "admin" | "promotes";

export interface GraphEdge {
  source: string;
  target: string;
  kind: EdgeKind;
  weight?: number;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
