import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

interface ProcessingModalProps {
  isOpen: boolean
  status: 'processing' | 'success' | 'error'
  message: string
  progressPercent?: number // 0-100
  downloadUrl?: string
  onClose: () => void
}

export function ProcessingModal({ isOpen, status, message, progressPercent = 0, downloadUrl, onClose }: ProcessingModalProps) {
  const getIcon = () => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      case 'success':
        return <CheckCircle className="h-8 w-8 text-green-500" />
      case 'error':
        return <XCircle className="h-8 w-8 text-red-500" />
    }
  }

  const getTitle = () => {
    switch (status) {
      case 'processing':
        return 'Processing Transcript'
      case 'success':
        return 'Minutes Generated Successfully'
      case 'error':
        return 'Processing Failed'
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-white border shadow-lg">
        <DialogHeader>
          <div className="flex items-center space-x-3">
            {getIcon()}
            <div>
              <DialogTitle>{getTitle()}</DialogTitle>
              <DialogDescription className="mt-1">
                {message}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Progress bar for processing */}
        {status === 'processing' && (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Processing transcript...</span>
              <span>{progressPercent}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progressPercent}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-500 text-center">
              This typically takes 1-2 minutes
            </div>
          </div>
        )}

        <div className="flex justify-end space-x-2 mt-4">
          {status === 'success' && downloadUrl && (
            <Button asChild>
              <a href={downloadUrl} download>
                Download Minutes
              </a>
            </Button>
          )}
          <Button variant="outline" onClick={onClose}>
            {status === 'processing' ? 'Cancel' : 'Close'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
