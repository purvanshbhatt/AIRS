import { useActiveOrg } from './useActiveOrg';

export function useActiveOrgId(): string {
  const { orgId } = useActiveOrg();
  return orgId;
}

