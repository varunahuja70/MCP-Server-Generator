/**
 * Central TanStack Query hooks for Forge REST API.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";
import type { components } from "@/types/api";

export type SampleSpec = components["schemas"]["SampleSummary"];
export type Project = components["schemas"]["ProjectResponse"];
export type ProjectSettings = components["schemas"]["ProjectSettingsResponse"];
export type SpecVersion = components["schemas"]["SpecVersionResponse"];
export type OperationItem = components["schemas"]["OperationItemResponse"];
export type OperationsList = components["schemas"]["OperationsListResponse"];
export type ReviewReport = components["schemas"]["ReviewResponse"];
export type BuildSummary = components["schemas"]["BuildSummaryResponse"];
export type FileContent = components["schemas"]["FileContentResponse"];

export interface AuthStatus {
  authenticated: boolean;
  mode: "local" | "exposed";
  playground_enabled: boolean;
}

// 1. Auth & System queries
export function useAuthStatus() {
  return useQuery<AuthStatus>({
    queryKey: ["auth", "status"],
    queryFn: () => apiRequest<AuthStatus>("/api/auth/status"),
  });
}

export function useLoginMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (token: string) =>
      apiRequest<{ status: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ token }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth"] });
    },
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<{ status: string }>("/api/auth/logout", {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth"] });
    },
  });
}

// 2. Samples queries
export function useSamples() {
  return useQuery<SampleSpec[]>({
    queryKey: ["samples"],
    queryFn: () => apiRequest<SampleSpec[]>("/api/samples"),
  });
}

export function useCreateSampleProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sampleId: string) =>
      apiRequest<Project>("/api/samples/create-project", {
        method: "POST",
        body: JSON.stringify({ sample_id: sampleId }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

// 3. Projects queries
export function useProjects() {
  return useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: () => apiRequest<Project[]>("/api/projects"),
  });
}

export function useProject(projectId: string) {
  return useQuery<Project>({
    queryKey: ["projects", projectId],
    queryFn: () => apiRequest<Project>(`/api/projects/${projectId}`),
    enabled: Boolean(projectId),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; slug?: string }) =>
      apiRequest<Project>("/api/projects", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, confirmSlug }: { projectId: string; confirmSlug: string }) =>
      apiRequest<void>(`/api/projects/${projectId}`, {
        method: "DELETE",
        body: JSON.stringify({ confirm_slug: confirmSlug }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

// 4. Spec Versions & Diff queries
export function useSpecVersions(projectId: string) {
  return useQuery<SpecVersion[]>({
    queryKey: ["projects", projectId, "specs"],
    queryFn: () => apiRequest<SpecVersion[]>(`/api/projects/${projectId}/specs`),
    enabled: Boolean(projectId),
  });
}

export function useCreateSpecVersion(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      source_type: "upload" | "paste" | "link";
      content?: string;
      url?: string;
      filename?: string;
    }) =>
      apiRequest<SpecVersion>(`/api/projects/${projectId}/specs`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "specs"] });
    },
  });
}

export type SpecDiffReport = components["schemas"]["SpecDiffReport"];

export function useSpecDiff(projectId: string, vid: string, againstVid: string) {
  return useQuery<SpecDiffReport>({
    queryKey: ["projects", projectId, "specs", vid, "diff", againstVid],
    queryFn: () =>
      apiRequest<SpecDiffReport>(
        `/api/projects/${projectId}/specs/${vid}/diff?against=${encodeURIComponent(againstVid)}`
      ),
    enabled: Boolean(projectId && vid && againstVid),
  });
}

// 5. Operations queries & mutations
export function useOperations(projectId: string) {
  return useQuery<OperationsList>({
    queryKey: ["projects", projectId, "operations"],
    queryFn: () => apiRequest<OperationsList>(`/api/projects/${projectId}/operations`),
    enabled: Boolean(projectId),
  });
}

export function useBulkUpdateOperations(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (operations: components["schemas"]["OperationUpdateItem"][]) =>
      apiRequest<Record<string, unknown>>(`/api/projects/${projectId}/operations`, {
        method: "PUT",
        body: JSON.stringify({ operations }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "operations"] });
    },
  });
}

export function useApplyOperationsPreset(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { preset: "read-only" | "all" | "none" | "by-tag"; tags?: string[] }) =>
      apiRequest<Record<string, unknown>>(`/api/projects/${projectId}/operations/preset`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "operations"] });
    },
  });
}

// 6. Settings queries & mutations
export function useProjectSettings(projectId: string) {
  return useQuery<ProjectSettings>({
    queryKey: ["projects", projectId, "settings"],
    queryFn: () => apiRequest<ProjectSettings>(`/api/projects/${projectId}/settings`),
    enabled: Boolean(projectId),
  });
}

export function useUpdateProjectSettings(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: components["schemas"]["ProjectSettingsUpdateRequest"]) =>
      apiRequest<ProjectSettings>(`/api/projects/${projectId}/settings`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "settings"] });
    },
  });
}

// 7. Review queries & mutations
export function useRunReview(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<ReviewReport>(`/api/projects/${projectId}/review`, {
        method: "POST",
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["projects", projectId, "review"], data);
    },
  });
}

export function useReviewData(projectId: string) {
  return useQuery<ReviewReport>({
    queryKey: ["projects", projectId, "review"],
    queryFn: () =>
      apiRequest<ReviewReport>(`/api/projects/${projectId}/review`, {
        method: "POST",
      }),
    enabled: Boolean(projectId),
  });
}

export function useAcknowledgeFindings(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (findingCodes: string[]) =>
      apiRequest<ReviewReport>(`/api/projects/${projectId}/review/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ finding_codes: findingCodes }),
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["projects", projectId, "review"], data);
    },
  });
}

// 8. Builds queries & mutations
export function useProjectBuilds(projectId: string) {
  return useQuery<BuildSummary[]>({
    queryKey: ["projects", projectId, "builds"],
    queryFn: () => apiRequest<BuildSummary[]>(`/api/projects/${projectId}/builds`),
    enabled: Boolean(projectId),
  });
}

export function useTriggerBuild(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<BuildSummary>(`/api/projects/${projectId}/builds`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId, "builds"] });
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export interface FileTreeItem {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  children?: FileTreeItem[];
}

export function useBuildFiles(buildId: string) {
  return useQuery<FileTreeItem[]>({
    queryKey: ["builds", buildId, "files"],
    queryFn: () => apiRequest<FileTreeItem[]>(`/api/builds/${buildId}/files`),
    enabled: Boolean(buildId),
  });
}

export function useBuildFileContent(buildId: string, path: string) {
  return useQuery<FileContent>({
    queryKey: ["builds", buildId, "files", "content", path],
    queryFn: () =>
      apiRequest<FileContent>(
        `/api/builds/${buildId}/files/content?path=${encodeURIComponent(path)}`
      ),
    enabled: Boolean(buildId && path),
  });
}

export interface ConnectSnippets {
  claude_desktop: string;
  cursor: string;
  cli_stdio: string;
  cli_http: string;
  required_env_vars: string[];
}

export function useConnectSnippets(buildId: string) {
  return useQuery<ConnectSnippets>({
    queryKey: ["builds", buildId, "connect"],
    queryFn: () => apiRequest<ConnectSnippets>(`/api/builds/${buildId}/connect`),
    enabled: Boolean(buildId),
  });
}

// 9. Playground queries & mutations
export interface PlaygroundSession {
  id?: string;
  session_id: string;
  status: string;
  target: "mock" | "live";
  created_at: string;
  tool_count: number;
}

export interface PlaygroundTool {
  name: string;
  description?: string;
  input_schema?: Record<string, unknown>;
  annotations?: Record<string, unknown>;
}

export interface ToolCallResult {
  content?: { type: string; text?: string }[];
  isError?: boolean;
  structured_content?: unknown;
  [key: string]: unknown;
}

export interface ProtocolTraceMessage {
  direction: "in" | "out";
  timestamp: string;
  payload: Record<string, unknown>;
  duration_ms?: number;
}

export function useCreatePlaygroundSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { build_id: string; target: "mock" | "live"; env_vars?: Record<string, string> }) =>
      apiRequest<PlaygroundSession>("/api/playground/sessions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["playground", "session", data.session_id], data);
    },
  });
}

export function useDeletePlaygroundSession() {
  return useMutation({
    mutationFn: (sessionId: string) =>
      apiRequest<{ status: string }>(`/api/playground/sessions/${sessionId}`, {
        method: "DELETE",
      }),
  });
}

export function usePlaygroundTools(sessionId: string) {
  return useQuery<{ tools: PlaygroundTool[] }>({
    queryKey: ["playground", "session", sessionId, "tools"],
    queryFn: () => apiRequest<{ tools: PlaygroundTool[] }>(`/api/playground/sessions/${sessionId}/tools`),
    enabled: Boolean(sessionId),
  });
}

export function useCallPlaygroundTool(sessionId: string) {
  return useMutation({
    mutationFn: (data: { name: string; arguments?: Record<string, unknown>; timeout_s?: number }) =>
      apiRequest<ToolCallResult>(`/api/playground/sessions/${sessionId}/call`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}
