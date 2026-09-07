// Общие типы данных фронтенда, соответствующие Pydantic-схемам бэкенда.

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  login: string
  password: string
}

export interface Role {
  id: string
  code: string
  name: string
}

export interface User {
  id: string
  login: string
  full_name: string
  position: string | null
  is_active: boolean
  created_at: string
  roles: Role[]
}

export interface Permission {
  id: string
  code: string
  name: string
  description: string | null
}

// --- Структура ---
export interface Building {
  id: string
  name: string
  address: string | null
  building_code: string | null
  description: string | null
  created_at: string
}

export interface Room {
  id: string
  building_id: string
  name: string
  room_number: string | null
  room_type: string | null
  department: string | null
  description: string | null
  created_at: string
}

// --- Справочники ---
export interface AssetType {
  id: string
  code: string
  name: string
  description: string | null
  number_template: string | null
}

export interface AssetAttribute {
  id: string
  asset_type_id: string
  name: string
  value_type: string
  is_required: boolean
  sort_order: number
}

export interface AssetStatus {
  id: string
  code: string
  name: string
  description: string | null
  is_active: boolean
}

export interface Unit {
  id: string
  code: string
  name: string
  abbreviation: string | null
  is_active: boolean
}

export interface Material {
  id: string
  code: string
  name: string
  description: string | null
  is_active: boolean
}

// --- Имущество ---
export type AssetStatusValue =
  | 'IN_STOCK'
  | 'MOVED'
  | 'ON_REPAIR'
  | 'ISSUED'
  | 'WRITTEN_OFF'
  | 'RESERVED'

export interface Asset {
  id: string
  inventory_number: string
  asset_type_id: string
  room_id: string | null
  name: string
  model: string | null
  brand: string | null
  serial_number: string | null
  purchase_year: number | null
  commissioning_date: string | null
  status: AssetStatusValue
  warranty_until: string | null
  quantity: number
  unit: string | null
  material: string | null
  cost: number | null
  write_off_date: string | null
  description: string | null
  photo_path: string | null
  custom_attributes: Record<string, unknown> | null
  responsible_user_id: string | null
  created_at: string
  updated_at: string
}

export interface AssetCreate {
  asset_type_id: string
  room_id?: string | null
  name: string
  model?: string | null
  brand?: string | null
  serial_number?: string | null
  purchase_year?: number | null
  commissioning_date?: string | null
  warranty_until?: string | null
  quantity?: number
  unit?: string | null
  material?: string | null
  cost?: number | null
  description?: string | null
  custom_attributes?: Record<string, unknown> | null
  responsible_user_id?: string | null
  use_custom_number?: boolean
  inventory_number?: string | null
}

// --- Инвентаризация ---
export interface Inventory {
  id: string
  name: string
  inv_type: string
  status: string
  start_date: string | null
  end_date: string | null
  coverage: string | null
  commission: string | null
  building_id: string | null
  room_id: string | null
  department: string | null
  created_by_id: string
  approved_by_id: string | null
  approved_at: string | null
  created_at: string
}

export interface InventoryItem {
  id: string
  inventory_id: string
  asset_id: string
  accounting_quantity: number | null
  accounting_status: string | null
  actual_quantity: number | null
  actual_status: string | null
  actual_condition: string | null
  photo_path: string | null
  is_checked: boolean
  checked_by_id: string | null
  checked_at: string | null
  comment: string | null
}

export interface Discrepancy {
  id: string
  inventory_id: string
  inventory_item_id: string | null
  asset_id: string | null
  discrepancy_type: string
  accounting_quantity: number | null
  actual_quantity: number | null
  difference: number | null
  estimated_cost: number | null
  status: string
  responsible_user_id: string | null
  explanation: string | null
  resolution: string | null
}

// --- Операции ---
export interface AssetMove {
  id: string
  asset_id: string
  from_room_id: string | null
  to_room_id: string | null
  reason: string | null
  moved_by_id: string
  moved_at: string
}

export interface WriteOff {
  id: string
  asset_id: string
  reason: string
  commission_members: string | null
  write_off_date: string | null
  document_id: string | null
  created_by_id: string
  status: string
  created_at: string
}

export interface Repair {
  id: string
  asset_id: string
  contractor: string | null
  description: string | null
  start_date: string | null
  end_date: string | null
  cost: number | null
  warranty_until: string | null
  is_guarantee: boolean
  act_number: string | null
  document_id: string | null
  created_by_id: string
  created_at: string
}

export interface Issuance {
  id: string
  asset_id: string
  issued_to_id: string
  issued_by_id: string
  issued_at: string | null
  return_at: string | null
  expected_return: string | null
  reason: string | null
  returned_condition: string | null
  is_returned: boolean
  created_by_id: string
}

// --- Документы ---
export interface Document {
  id: string
  doc_number: string
  doc_type: string
  title: string
  description: string | null
  status: string
  file_name: string | null
  file_size: number | null
  mime_type: string | null
  created_by_id: string
  created_at: string
}

// --- Аудит ---
export interface AuditLogEntry {
  id: string
  user_id: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  field_name: string | null
  old_value: string | null
  new_value: string | null
  ip_address: string | null
  comment: string | null
  created_at: string
}

// --- Отчёты ---
export interface ReportJob {
  id: string
  report_type: string
  format: string
  status: string
  params: Record<string, unknown> | null
  result_path: string | null
  error_message: string | null
  created_by_id: string
  started_at: string | null
  completed_at: string | null
  notified: boolean
  created_at: string
}