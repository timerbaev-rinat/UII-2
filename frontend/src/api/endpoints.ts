// Функции вызова API бэкенда.

import { api, apiUpload } from './client'
import type {
  Asset,
  AssetCreate,
  AssetMove,
  AssetType,
  AuditLogEntry,
  Building,
  Discrepancy,
  Document,
  Inventory,
  InventoryItem,
  Issuance,
  LoginRequest,
  Permission,
  ReportJob,
  Repair,
  Role,
  Room,
  TokenPair,
  Unit,
  User,
  WriteOff,
} from '@/types'

// --- Аутентификация ---
export const authApi = {
  login: (payload: LoginRequest) =>
    api<TokenPair>('/auth/login', { method: 'POST', body: payload }),
  me: () => api<User>('/auth/me'),
}

// --- Пользователи ---
export const usersApi = {
  list: () => api<User[]>('/users'),
  listActive: () => api<User[]>('/users', { params: { active: true } }),
  create: (payload: Partial<User> & { password: string }) =>
    api<User>('/auth/users', { method: 'POST', body: payload }),
  update: (id: string, payload: Partial<User>) =>
    api<User>(`/auth/users/${id}`, { method: 'PATCH', body: payload }),
  roles: () => api<Role[]>('/auth/roles'),
  permissions: () => api<Permission[]>('/auth/permissions'),
}

// --- Структура ---
export const structureApi = {
  buildings: () => api<Building[]>('/structure/buildings'),
  createBuilding: (payload: Partial<Building>) =>
    api<Building>('/structure/buildings', { method: 'POST', body: payload }),
  rooms: (buildingId?: string) =>
    api<Room[]>('/structure/rooms', { params: buildingId ? { building_id: buildingId } : {} }),
  createRoom: (payload: Partial<Room>) =>
    api<Room>('/structure/rooms', { method: 'POST', body: payload }),
}

// --- Справочники ---
export const referenceApi = {
  assetTypes: () => api<AssetType[]>('/reference/asset-types'),
  statuses: () => api<Unit[]>('/reference/statuses'),
  units: () => api<Unit[]>('/reference/units'),
  materials: () => api<Unit[]>('/reference/materials'),
}

// --- Имущество ---
export const assetsApi = {
  list: (params?: Record<string, string | number | boolean>) =>
    api<Asset[]>('/assets', { params }),
  get: (id: string) => api<Asset>(`/assets/${id}`),
  uploadPhoto: (id: string, file: File) =>
    apiUpload<Asset>(`/assets/${id}/photo`, file),
  create: (payload: AssetCreate) => api<Asset>('/assets', { method: 'POST', body: payload }),
  update: (id: string, payload: Partial<AssetCreate>) =>
    api<Asset>(`/assets/${id}`, { method: 'PATCH', body: payload }),
  remove: (id: string) => api<{ detail: string }>(`/assets/${id}`, { method: 'DELETE' }),
  reserve: (payload: { asset_type_id: string; comment?: string }) =>
    api<{ inventory_number: string }>('/assets/reserve', { method: 'POST', body: payload }),
  stats: () => api<{ total: number; by_status: Record<string, number> }>('/assets/stats/summary'),
  moves: (assetId?: string) =>
    api<AssetMove[]>('/operations/moves', { params: assetId ? { asset_id: assetId } : {} }),
  createMove: (payload: { asset_id: string; to_room_id?: string | null; reason?: string }) =>
    api<AssetMove>('/operations/moves', { method: 'POST', body: payload }),
  writeOffs: () => api<WriteOff[]>('/operations/write-offs'),
  createWriteOff: (payload: {
    asset_id: string
    reason: string
    commission_members?: string | null
  }) => api<WriteOff>('/operations/write-offs', { method: 'POST', body: payload }),
  repairs: (assetId?: string) =>
    api<Repair[]>('/operations/repairs', { params: assetId ? { asset_id: assetId } : {} }),
  createRepair: (payload: { asset_id: string; contractor?: string | null; description?: string }) =>
    api<Repair>('/operations/repairs', { method: 'POST', body: payload }),
  issuances: (assetId?: string) =>
    api<Issuance[]>('/operations/issuances', { params: assetId ? { asset_id: assetId } : {} }),
  createIssuance: (payload: { asset_id: string; issued_to_id: string; reason?: string }) =>
    api<Issuance>('/operations/issuances', { method: 'POST', body: payload }),
  returnIssuance: (id: string, payload: { returned_condition?: string }) =>
    api<Issuance>(`/operations/issuances/${id}/return`, { method: 'POST', body: payload }),
}

// --- Инвентаризация ---
export const inventoryApi = {
  list: () => api<Inventory[]>('/inventories'),
  create: (payload: Partial<Inventory>) =>
    api<Inventory>('/inventories', { method: 'POST', body: payload }),
  get: (id: string) => api<Inventory>(`/inventories/${id}`),
  start: (id: string) => api<Inventory>(`/inventories/${id}/start`, { method: 'POST' }),
  complete: (id: string) => api<Inventory>(`/inventories/${id}/complete`, { method: 'POST' }),
  approve: (id: string, payload: { comment?: string }) =>
    api<Inventory>(`/inventories/${id}/approve`, { method: 'POST', body: payload }),
  items: (id: string) => api<InventoryItem[]>(`/inventories/${id}/items`),
  updateItem: (inventoryId: string, itemId: string, payload: Partial<InventoryItem>) =>
    api<InventoryItem>(`/inventories/${inventoryId}/items/${itemId}`, {
      method: 'PATCH',
      body: payload,
    }),
  discrepancies: (id: string) => api<Discrepancy[]>(`/inventories/${id}/discrepancies`),
}

// --- Документы ---
export const documentsApi = {
  list: () => api<Document[]>('/documents'),
  create: (payload: Partial<Document>) =>
    api<Document>('/documents', { method: 'POST', body: payload }),
  uploadFile: (id: string, file: File) =>
    apiUpload<Document>(`/documents/${id}/upload`, file),
  changeStatus: (id: string, payload: { status: string; comment?: string }) =>
    api<Document>(`/documents/${id}/status`, { method: 'POST', body: payload }),
  sign: (id: string, payload: { comment?: string }) =>
    api<Document>(`/documents/${id}/sign`, { method: 'POST', body: payload }),
}

// --- Аудит ---
export const auditApi = {
  list: (params?: Record<string, string>) => api<AuditLogEntry[]>('/audit-log', { params }),
  actions: () => api<{ actions: string[] }>('/audit-log/actions'),
  integrity: () => api<{ status: string; issues: unknown[]; counts: Record<string, number> }>(
    '/audit-log/integrity',
  ),
}

// --- Отчёты ---
export const reportsApi = {
  list: () => api<ReportJob[]>('/reports'),
  create: (payload: { report_type: string; format?: string; params?: Record<string, unknown> }) =>
    api<ReportJob>('/reports', { method: 'POST', body: payload }),
  get: (id: string) => api<ReportJob>(`/reports/${id}`),
  downloadUrl: (id: string) => `/api/reports/${id}/download`,
}