import type { Metadata } from 'next'
import { Source_Serif_4, IBM_Plex_Sans, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'
import { PatientProvider } from '@/lib/patient-context'
import { PatientSidebar } from '@/components/patient-sidebar'

const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
})

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600'],
  variable: '--font-sans',
  display: 'swap',
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Theodore — Caregiver Dashboard',
  description: 'Emotionally intelligent companion bear dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${sourceSerif.variable} ${ibmPlexSans.variable} ${ibmPlexMono.variable}`}>
      <body>
        <PatientProvider>
          <PatientSidebar />
          {children}
        </PatientProvider>
      </body>
    </html>
  )
}