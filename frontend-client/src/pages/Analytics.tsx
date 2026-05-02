import { AppLayout } from '@/components/layout/AppLayout'
import { Card } from '@/components/ui/card'

export function Analytics() {
  return (
    <AppLayout>
      <div className="h-full overflow-y-auto p-6">
        <Card className="p-6">
          <h1 className="text-2xl font-bold text-foreground mb-2">Analytics</h1>
          <p className="text-muted-foreground">This page is under construction.</p>
        </Card>
      </div>
    </AppLayout>
  )
}