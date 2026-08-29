import { describe, expect, it } from "vitest";

import { resolveRoute } from "../router/guards";

describe("initial route guard", () => {
  it("sends a fresh installation to setup", () => {
    expect(resolveRoute({ path: "/dashboard", isPublic: false, setupCompleted: false, isAuthenticated: false })).toBe("/setup");
    expect(resolveRoute({ path: "/", isPublic: true, setupCompleted: false, isAuthenticated: false })).toBe("/setup");
  });

  it("keeps setup public and protects authenticated routes after setup", () => {
    expect(resolveRoute({ path: "/setup", isPublic: true, setupCompleted: false, isAuthenticated: false })).toBe(true);
    expect(resolveRoute({ path: "/dashboard", isPublic: false, setupCompleted: true, isAuthenticated: false })).toBe("/login");
  });
});
