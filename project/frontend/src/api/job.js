import request from "./request";

export function fetchJobDashboard() {
  return request.get("/job/dashboard/");
}

export function fetchJobList(params) {
  return request.get("/job/list/", { params });
}

export function fetchJobDetail(jobId) {
  return request.get(`/job/detail/${encodeURIComponent(jobId)}/`);
}
