export type UserStatus = "active" | "disabled";

export interface UserProfile {
  id: number;
  nickname: string | null;
  avatar_url: string | null;
  status: UserStatus;
  created_at: string;
  updated_at: string;
}

export interface WechatLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}
