import http from "./http";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface UserSummary {
  id: number;
  username: string;
  role: string;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  user: UserSummary;
}

export async function login(payload: LoginPayload): Promise<LoginResult> {
  const response = await http.post("/auth/login", payload);
  return response.data.data;
}
