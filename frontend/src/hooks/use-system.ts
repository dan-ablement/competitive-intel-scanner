import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listCheckRuns, getSettings, updateSettings, triggerFeedCheck, triggerProfileReview, getKVSetting, setKVSetting, type SystemSettings } from "@/api/system";

export function useCheckRuns() {
  return useQuery({
    queryKey: ["check-runs"],
    queryFn: listCheckRuns,
  });
}

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings: SystemSettings) => updateSettings(settings),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });
}

export function useTriggerFeedCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ generateBriefing }: { generateBriefing?: boolean } = {}) =>
      triggerFeedCheck(generateBriefing),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["check-runs"] }),
  });
}

export function useTriggerProfileReview() {
  return useMutation({
    mutationFn: triggerProfileReview,
  });
}

export function useKVSetting(key: string) {
  return useQuery({
    queryKey: ["kv-settings", key],
    queryFn: () => getKVSetting(key),
    enabled: !!key,
  });
}

export function useSetKVSetting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: string | null }) =>
      setKVSetting(key, value),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["kv-settings", variables.key] });
    },
  });
}

