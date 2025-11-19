import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { ProcessingModal } from '@/components/ProcessingModal'
import { apiClient } from '@/lib/api'
import type { TransformRequest } from '@/lib/api'

function App() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalStatus, setModalStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [modalMessage, setModalMessage] = useState('')
  const [modalProgressPercent, setModalProgressPercent] = useState<number>(0)
  const [downloadUrl, setDownloadUrl] = useState<string | undefined>()
  const [inputMethod, setInputMethod] = useState<'text' | 'file'>('file')
  const [transcriptText, setTranscriptText] = useState('')

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsProcessing(true)
    setModalOpen(true)
    setModalStatus('processing')
    setModalMessage('Processing transcript...')
    setModalProgressPercent(0)

    // Start progress bar animation (90 seconds total)
    const progressInterval = setInterval(() => {
      setModalProgressPercent(prev => {
        const next = prev + (100 / 90) // Increment by ~1.11% per second
        return next >= 95 ? 95 : next // Cap at 95% until completion
      })
    }, 1000)

    try {
      const formData = new FormData(e.currentTarget)

      // Get the file based on input method
      let file: File
      if (inputMethod === 'file') {
        const fileInput = e.currentTarget.querySelector('#file') as HTMLInputElement
        if (!fileInput?.files?.[0]) {
          throw new Error('Please select a file')
        }
        file = fileInput.files[0]
      } else {
        // Create a file from the text input
        if (!transcriptText.trim()) {
          throw new Error('Please enter transcript text')
        }
        file = new File([transcriptText], 'transcript.txt', { type: 'text/plain' })
      }

      // Create the request data
      const requestData: TransformRequest = {
        template_id: 'progress_minutes_v1',
        project: formData.get('project') as string,
        job_min_no: formData.get('job_min_no') as string,
        description: formData.get('description') as string,
        date: formData.get('date') as string,
        time: formData.get('time') as string,
        location: formData.get('location') as string,
        file: file,
      }

      // Call the API
      const response = await apiClient.transform(requestData)

      // Create download link from base64
      const blob = new Blob([
        Uint8Array.from(atob(response.docx_base64), c => c.charCodeAt(0))
      ], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })

      const url = URL.createObjectURL(blob)

      // Clear progress interval and complete progress
      clearInterval(progressInterval)
      setModalProgressPercent(100)

      setModalStatus('success')
      setModalMessage(`Successfully generated minutes for "${requestData.project}". ${response.minutes.attendees.length} attendees and ${response.minutes.sections.length} sections extracted.`)
      setDownloadUrl(url)

    } catch (error) {
      console.error('Processing failed:', error)
      clearInterval(progressInterval)
      setModalProgressPercent(0)
      setModalStatus('error')
      setModalMessage(error instanceof Error ? error.message : 'An unexpected error occurred')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleModalClose = () => {
    setModalOpen(false)
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl)
      setDownloadUrl(undefined)
    }
  }

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-center text-slate-900" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>
            OKII TG DOCS
          </h1>
          <p className="text-center text-slate-600 mt-2" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>
            Transform meeting transcripts into documented minutes
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-2xl mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Upload Transcript</CardTitle>
            <CardDescription style={{ fontFamily: 'Instrument Sans, sans-serif' }}>
              Upload a meeting transcript file (.txt, .docx, .vtt) or paste text along with meeting details to generate documented minutes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Transcript Input Tabs */}
              <div className="space-y-2">
                <Label style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Transcript Input</Label>
                <Tabs value={inputMethod} onValueChange={(value) => setInputMethod(value as 'text' | 'file')}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="file" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>File Upload</TabsTrigger>
                    <TabsTrigger value="text" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Text Input</TabsTrigger>
                  </TabsList>
                  <TabsContent value="file" className="space-y-2">
                    <Label htmlFor="file" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Transcript File</Label>
                    <Input
                      id="file"
                      type="file"
                      accept=".txt,.docx,.vtt"
                      required={inputMethod === 'file'}
                      className="cursor-pointer"
                    />
                  </TabsContent>
                  <TabsContent value="text" className="space-y-2">
                    <Label htmlFor="transcript-text" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Transcript Text</Label>
                    <Textarea
                      id="transcript-text"
                      placeholder="Paste your meeting transcript here..."
                      value={transcriptText}
                      onChange={(e) => setTranscriptText(e.target.value)}
                      required={inputMethod === 'text'}
                      rows={8}
                      style={{ fontFamily: 'Instrument Sans, sans-serif' }}
                    />
                  </TabsContent>
                </Tabs>
              </div>

              {/* Metadata Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="project" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Project</Label>
                  <Input
                    id="project"
                    name="project"
                    placeholder="e.g. City Central Redevelopment"
                    required
                    style={{ fontFamily: 'Instrument Sans, sans-serif' }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="job_min_no" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Job Min No</Label>
                  <Input
                    id="job_min_no"
                    name="job_min_no"
                    placeholder="e.g. A-92"
                    required
                    style={{ fontFamily: 'Instrument Sans, sans-serif' }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Description</Label>
                  <Input
                    id="description"
                    name="description"
                    placeholder="e.g. Progress Meeting"
                    defaultValue="Progress Meeting"
                    required
                    style={{ fontFamily: 'Instrument Sans, sans-serif' }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Date</Label>
                  <Input
                    id="date"
                    name="date"
                    type="date"
                    required
                    style={{ fontFamily: 'Instrument Sans, sans-serif' }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="time" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Time</Label>
                  <Input
                    id="time"
                    name="time"
                    placeholder="e.g. 10:00"
                    required
                    style={{ fontFamily: 'Instrument Sans, sans-serif' }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location" style={{ fontFamily: 'Instrument Sans, sans-serif' }}>Location</Label>
                  <Input
                    id="location"
                    name="location"
                    placeholder="e.g. Site Office"
                    required
                    style={{ fontFamily: 'Instrument Sans, sans-serif' }}
                  />
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex justify-center pt-4">
                <button
                  type="submit"
                  disabled={isProcessing}
                  className="px-8 py-3 bg-blue-400 text-white rounded-lg font-medium hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  style={{
                    fontFamily: 'Instrument Sans, sans-serif',
                    border: 'none',
                    outline: 'none'
                  }}
                >
                  {isProcessing ? 'Processing...' : 'Generate Minutes'}
                </button>
              </div>
            </form>

          </CardContent>
        </Card>

        {/* Processing Modal */}
        <ProcessingModal
          isOpen={modalOpen}
          status={modalStatus}
          message={modalMessage}
          progressPercent={modalProgressPercent}
          downloadUrl={downloadUrl}
          onClose={handleModalClose}
        />
      </main>
    </div>
  )
}

export default App
