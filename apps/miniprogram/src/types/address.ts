export interface UserAddress {
  id: number;
  receiver_name: string;
  receiver_phone: string;
  province: string;
  city: string;
  district: string;
  detail_address: string;
  full_address: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface AddressListResponse {
  items: UserAddress[];
}

export interface AddressPayload {
  receiver_name: string;
  receiver_phone: string;
  province: string;
  city: string;
  district: string;
  detail_address: string;
  is_default: boolean;
}
