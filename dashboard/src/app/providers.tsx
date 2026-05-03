"use client"

import { PatientProvider } from '@/lib/patient-context'
import { SSEProvider } from '@/lib/sse-context'
import { PatientSidebar } from '@/components/patient-sidebar'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <PatientProvider>
      <SSEProvider>
        <PatientSidebar />
        {children}
      </SSEProvider>
    </PatientProvider>
  )
}
