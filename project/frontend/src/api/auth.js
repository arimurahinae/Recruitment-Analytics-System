import request from "./request";

export function loginApi(data) {
  return request.post("/auth/login/", data);
}

export function registerApi(data) {
  return request.post("/auth/register/", data);
}

export function meApi() {
  return request.get("/auth/me/");
}

export function updateMeApi(data) {
  return request.put("/auth/me/", data);
}

export function logoutApi() {
  return request.post("/auth/logout/");
}

