import { request } from "./http";
import type { AdminImageUploadResponse } from "../types/admin";

export function uploadAdminImage(file: File): Promise<AdminImageUploadResponse> {
  const formData = new FormData();
  formData.set("image", file);

  return request<AdminImageUploadResponse>({
    path: "/admin/uploads/images",
    method: "POST",
    formData,
  });
}
