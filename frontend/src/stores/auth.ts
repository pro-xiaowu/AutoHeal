import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { login as loginRequest, type LoginPayload, type UserSummary } from "../api/auth";

function readUser(): UserSummary | null {
  try {
    return JSON.parse(localStorage.getItem("autoheal_user") || "null");
  } catch {
    return null;
  }
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("autoheal_token"));
  const currentUser = ref<UserSummary | null>(readUser());
  const isAuthenticated = computed(() => Boolean(token.value));

  async function login(payload: LoginPayload) {
    const result = await loginRequest(payload);
    token.value = result.access_token;
    currentUser.value = result.user;
    localStorage.setItem("autoheal_token", result.access_token);
    localStorage.setItem("autoheal_user", JSON.stringify(result.user));
  }

  function logout() {
    token.value = null;
    currentUser.value = null;
    localStorage.removeItem("autoheal_token");
    localStorage.removeItem("autoheal_user");
  }

  return { token, currentUser, isAuthenticated, login, logout };
});
