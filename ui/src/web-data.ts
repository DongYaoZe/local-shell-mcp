type WorkloadSnapshot = {
  jobs?: unknown[]
  sessions?: unknown[]
}

export function visibleWorkloadCount(data: WorkloadSnapshot): number {
  return (data.jobs?.length || 0) + (data.sessions?.length || 0)
}
