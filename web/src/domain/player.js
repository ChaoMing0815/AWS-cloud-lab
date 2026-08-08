import { DomainError } from "./domain-error.js";

export function normalizeNickname(value) {
  const nickname = String(value ?? "").trim();
  if (nickname.length < 1 || nickname.length > 12) {
    throw new DomainError("INVALID_NICKNAME", "暱稱必須是 1–12 個字元。");
  }
  if (/\p{Cc}/u.test(nickname)) {
    throw new DomainError("INVALID_NICKNAME", "暱稱不能包含控制字元。");
  }
  return nickname;
}

export function normalizeRole(value) {
  const role = String(value ?? "").trim();
  if (role.length < 1 || role.length > 20) {
    throw new DomainError("INVALID_ROLE", "角色概念必須是 1–20 個字元。");
  }
  if (/\p{Cc}/u.test(role)) {
    throw new DomainError("INVALID_ROLE", "角色概念不能包含控制字元。");
  }
  return role;
}
