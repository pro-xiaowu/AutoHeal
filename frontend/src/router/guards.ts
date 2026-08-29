export interface RouteGuardInput {
  path: string;
  isPublic: boolean;
  setupCompleted: boolean;
  isAuthenticated: boolean;
}

export function resolveRoute(input: RouteGuardInput): string | true {
  if (!input.setupCompleted && input.path !== "/setup") return "/setup";
  if (input.path === "/login" && input.isAuthenticated) return "/dashboard";
  if (!input.isPublic && !input.isAuthenticated) return "/login";
  return true;
}
