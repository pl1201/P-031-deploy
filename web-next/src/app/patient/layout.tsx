import { WorkspaceShell } from '@/components/workspace-shell'

export default function PatientLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell role="patient">{children}</WorkspaceShell>
}
