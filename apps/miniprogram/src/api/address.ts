import { request } from "./http";
import type { AddressListResponse, AddressPayload, UserAddress } from "../types/address";

export function fetchAddresses(): Promise<AddressListResponse> {
  return request<AddressListResponse>({
    url: "/addresses",
    auth: true,
  });
}

export function createAddress(payload: AddressPayload): Promise<UserAddress> {
  return request<UserAddress>({
    url: "/addresses",
    method: "POST",
    data: payload,
    auth: true,
  });
}

export function updateAddress(addressId: number, payload: AddressPayload): Promise<UserAddress> {
  return request<UserAddress>({
    url: `/addresses/${addressId}`,
    method: "PUT",
    data: payload,
    auth: true,
  });
}

export function deleteAddress(addressId: number): Promise<void> {
  return request<void>({
    url: `/addresses/${addressId}`,
    method: "DELETE",
    auth: true,
  });
}

export function setDefaultAddress(addressId: number): Promise<void> {
  return request<void>({
    url: `/addresses/${addressId}/default`,
    method: "POST",
    auth: true,
  });
}
