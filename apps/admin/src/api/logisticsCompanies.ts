import { request } from "./http";
import type { LogisticsCompanyListResponse } from "../types/admin";

export function fetchAdminLogisticsCompanies(): Promise<LogisticsCompanyListResponse> {
  return request<LogisticsCompanyListResponse>({
    path: "/admin/logistics-companies",
  });
}
