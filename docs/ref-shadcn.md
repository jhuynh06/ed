# shadcn/ui — Component Reference for Theodore Dashboard

Source: ui.shadcn.com

## Install (Next.js)
```bash
pnpm dlx shadcn@latest init
```

## Add Components
```bash
pnpm dlx shadcn@latest add button card badge dialog tabs toast
pnpm dlx shadcn@latest add alert separator skeleton scroll-area
```

## Components Theodore Needs

### Card (episode cards, status card, vitals)
```tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

<Card>
  <CardHeader>
    <CardTitle>Current Status</CardTitle>
    <CardDescription>Last updated 2 minutes ago</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Agitation: 22 (Calm)</p>
  </CardContent>
</Card>
```

### Badge (severity indicators)
```tsx
import { Badge } from "@/components/ui/badge"

<Badge variant="default">Calm</Badge>        {/* green-ish */}
<Badge variant="secondary">Mild</Badge>      {/* yellow */}
<Badge variant="destructive">Severe</Badge>  {/* red */}
<Badge variant="outline">Info</Badge>
```

### Toast (notifications)
```tsx
import { useToast } from "@/hooks/use-toast"

const { toast } = useToast()

toast({
  title: "Notification",
  description: "Margaret had a restless moment this afternoon.",
  variant: "default",  // or "destructive" for urgent
})
```

### Dialog (MAR debate trace, episode detail)
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

<Dialog>
  <DialogTrigger asChild>
    <Button variant="outline">View MAR Trace</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Notification Review</DialogTitle>
    </DialogHeader>
    {/* MAR debate trace content */}
  </DialogContent>
</Dialog>
```

### Tabs (dashboard sections)
```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

<Tabs defaultValue="timeline">
  <TabsList>
    <TabsTrigger value="timeline">Timeline</TabsTrigger>
    <TabsTrigger value="episodes">Episodes</TabsTrigger>
  </TabsList>
  <TabsContent value="timeline">{/* chart */}</TabsContent>
  <TabsContent value="episodes">{/* list */}</TabsContent>
</Tabs>
```

### Skeleton (loading states)
```tsx
import { Skeleton } from "@/components/ui/skeleton"

<Skeleton className="h-[200px] w-full rounded-xl" />  {/* chart placeholder */}
<Skeleton className="h-4 w-[250px]" />                 {/* text placeholder */}
```

### Separator
```tsx
import { Separator } from "@/components/ui/separator"
<Separator className="my-4" />
```

## Color Mapping for Theodore

```tsx
// Agitation severity → Tailwind classes
const SEVERITY_COLORS = {
  calm:     "bg-emerald-500 text-white",
  mild:     "bg-amber-400 text-black",
  moderate: "bg-orange-500 text-white",
  severe:   "bg-red-600 text-white",
} as const

// Notification priority → Badge variant
const PRIORITY_BADGE = {
  info:    "default",
  warning: "secondary",
  urgent:  "destructive",
} as const
```
