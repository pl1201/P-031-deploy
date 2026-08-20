import { WorkspaceShell } from '@/components/workspace-shell'

export default function DietitianLayout({ children }: { children: React.ReactNode }) {
  return <WorkspaceShell role="dietitian">{children}</WorkspaceShell>
}
